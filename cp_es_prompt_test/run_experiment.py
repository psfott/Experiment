"""Reproducible CP/ES generation through OpenAI-compatible chat/completions."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import re
import sys
import time
from datetime import datetime, timezone
import urllib.error
import urllib.parse
import urllib.request

import yaml

ROOT = Path(__file__).resolve().parent


def read_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def append_json(path, value):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")
        stream.flush()


def load_records(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def build_plan(manifest, models, tasks, aliases, conditions, case_ids):
    prompts = read_yaml(ROOT / "prompts/prompt_templates.yaml")
    cases = read_csv(ROOT / "data/cases_master.csv")
    matrix = read_csv(ROOT / "tables/condition_matrix.csv")
    for selected, available, label in [
        (aliases, {m['alias'] for m in models}, 'model'),
        (conditions, {c['condition_id'] for c in matrix}, 'condition'),
        (case_ids, {c['case_id'] for c in cases}, 'case'),
    ]:
        if selected and set(selected) - available:
            raise ValueError(f"Unknown {label}: {set(selected) - available}")
    if len({m['alias'] for m in models}) != len(models):
        raise ValueError("Duplicate model aliases")
    if len({c['case_id'] for c in cases}) != len(cases):
        raise ValueError("Duplicate case IDs")
    generation = manifest['generation']
    if not isinstance(generation['repeats'], int) or generation['repeats'] < 1:
        raise ValueError("repeats must be a positive integer")
    plan = []
    for model in models:
        if not model.get('enabled', True) or (aliases and model['alias'] not in aliases):
            continue
        if model['provider'] != 'openai-compatible':
            raise ValueError("Only provider: openai-compatible is supported")
        for task in tasks:
            for case in cases:
                if case_ids and case['case_id'] not in case_ids:
                    continue
                for condition in matrix:
                    if conditions and condition['condition_id'] not in conditions:
                        continue
                    role = condition['role_type']
                    level = condition['prompt_level']
                    system = prompts['composition']['separator'].join(filter(None, [
                        prompts['roles'][condition['role_template']]['text'],
                        prompts['task_prompts'][condition['task_prompt_template']]['text'],
                    ]))
                    messages = [{'role': 'system', 'content': system}] if system else []
                    if task == 'single_turn':
                        messages += [{'role': 'user', 'content': case[manifest[task]['input_field']]}]
                    else:
                        fields = manifest[task]['history_fields']
                        if len(fields) != 2:
                            raise ValueError('multi_turn requires exactly user/assistant history fields')
                        messages += [dict(role=r, content=case[f]) for r, f in zip(['user', 'assistant'], fields)]
                        messages += [{'role': 'user', 'content': case[manifest[task]['current_input_field']]}]
                    body = dict(model=model['model_id'], messages=messages,
                                temperature=generation['temperature'], top_p=generation['top_p'],
                                max_tokens=generation['max_output_tokens'])
                    if generation.get('seed') is not None:
                        body['seed'] = generation['seed']
                    extra = model.get('extra_body', {})
                    if set(extra) & {'model', 'messages', 'stream'}:
                        raise ValueError('extra_body cannot override model/messages/stream')
                    body.update(extra)
                    body = {k: v for k, v in body.items() if v is not None}
                    for repeat in range(1, generation['repeats'] + 1):
                        row = dict(task=task, case_id=case['case_id'], emotion=case['emotion'],
                                   model_alias=model['alias'], provider=model['provider'],
                                   model_id=model['model_id'], condition_id=condition['condition_id'],
                                   role_type=role, prompt_level=level, messages=messages,
                                   repeat_id=repeat, ed_user_1=case['ed_user_1'],
                                   prompt_version=manifest['prompt_version'], dataset_version=manifest['dataset_version'],
                                   generation_params={k:v for k,v in body.items() if k not in ('model','messages')},
                                   request_body=body, base_url=model.get('base_url', ''),
                                   api_key_env=model.get('api_key_env', ''))
                        row['ed_ground_truth' if task == 'single_turn' else 'constructed_user_2'] = case[
                            'ed_assistant_1' if task == 'single_turn' else 'constructed_user_2']
                        row['request_id'] = digest(row)
                        plan.append(row)
    if not plan:
        raise ValueError('No requests selected')
    return plan


def resolve_api_key(model):
    """Keep credentials outside the serializable request plan and snapshots."""
    key = model.get('api_key')
    if key is not None and not isinstance(key, str):
        raise ValueError(f"api_key must be a quoted string for {model['alias']}")
    return (key or '').strip() or os.environ.get(model.get('api_key_env') or '', '')


def call_api(row, timeout, retries, ignore_proxy=False, api_key=None):
    url = row['base_url'].rstrip('/') + '/chat/completions'
    key = api_key or os.environ[row['api_key_env']]
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if ignore_proxy else urllib.request.build_opener()
    for attempt in range(retries + 1):
        request = urllib.request.Request(url, data=canonical(row['request_body']).encode(),
                   headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        try:
            with opener.open(request, timeout=timeout) as response:
                result = json.load(response)
            return result, attempt + 1
        except urllib.error.HTTPError as exc:
            # Do not persist raw provider error bodies: they may echo credentials.
            if exc.code not in (408, 429, 500, 502, 503, 504) or attempt == retries:
                raise RuntimeError(f'HTTP {exc.code}') from None
            retry_after = exc.headers.get('Retry-After', '')
            delay = min(float(retry_after), 30) if retry_after.isdigit() else min(2 ** attempt, 16)
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == retries:
                raise RuntimeError('Network connection failed or timed out') from None
            delay = min(2 ** attempt, 16)
        time.sleep(delay)


def export_blind(directory):
    if not directory.is_dir() or not (directory / 'run_snapshot.json').exists():
        raise ValueError('Export requires an existing run directory with run_snapshot.json')
    latest = {}
    for task in ('single_turn', 'multi_turn'):
        for row in load_records(directory / f'{task}_responses.jsonl'):
            latest[row['request_id']] = row
    rows = [r for r in latest.values() if r['status'] == 'success']
    random.Random(42).shuffle(rows)
    mapping = []
    with (directory / 'blinded.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['blind_id','task','history','current_input','response','overall_appropriateness','over_support','under_support','topic_following','naturalness'])
        writer.writeheader()
        for i, row in enumerate(rows, 1):
            blind_id = f'B{i:06d}'
            messages = [m for m in row['messages'] if m['role'] != 'system']
            writer.writerow(dict(blind_id=blind_id, task=row['task'], history=canonical(messages[:-1]),
                                 current_input=messages[-1]['content'], response=row['model_response']))
            mapping.append(dict(blind_id=blind_id, request_id=row['request_id'], case_id=row['case_id'],
                                model_alias=row['model_alias'], condition_id=row['condition_id'], repeat_id=row['repeat_id']))
    (directory / 'blinded_key.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Blinded export: {len(rows)} responses (keep blinded_key.json private)')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', type=Path, default=ROOT / 'models.local.yaml')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'experiment_manifest.yaml')
    parser.add_argument('--model', nargs='+')
    parser.add_argument('--task', nargs='+', choices=['single_turn','multi_turn'])
    parser.add_argument('--condition', nargs='+')
    parser.add_argument('--case', nargs='+')
    parser.add_argument('--run-id', default=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--export-blind', type=Path, help='Export an existing run; no API calls')
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--retries', type=int, default=3)
    parser.add_argument('--delay', type=float, default=0.2)
    parser.add_argument('--order-seed', type=int, default=42)
    parser.add_argument('--ignore-proxy', action='store_true')
    args = parser.parse_args(argv)
    if args.export_blind:
        export_blind(args.export_blind)
        return 0
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.run_id):
        raise ValueError('run-id must contain only letters, numbers, underscores or hyphens')
    if args.timeout <= 0 or args.retries < 0 or args.delay < 0:
        raise ValueError('Invalid timeout/retries/delay')
    manifest = read_yaml(args.manifest)
    models = read_yaml(args.models)['models']
    plan = build_plan(manifest, models, args.task or manifest['tasks'], args.model, args.condition, args.case)
    random.Random(args.order_seed).shuffle(plan)
    directory = ROOT / 'outputs' / args.run_id
    snapshot = dict(manifest=manifest, plan=plan, order_seed=args.order_seed,
                    runtime=dict(timeout=args.timeout, retries=args.retries, ignore_proxy=args.ignore_proxy))
    fingerprint = digest(snapshot)
    snapshot_path = directory / 'run_snapshot.json'
    if directory.exists():
        if not args.resume or not snapshot_path.exists():
            raise ValueError('Run directory exists. Use a new run-id or --resume.')
        if json.loads(snapshot_path.read_text(encoding='utf-8'))['fingerprint'] != fingerprint:
            raise ValueError('Run configuration changed; use a new run-id')
    if not args.dry_run:
        credentials = {m['alias']: resolve_api_key(m) for m in models
                       if m['alias'] in {r['model_alias'] for r in plan}}
        for row in plan:
            parsed_url = urllib.parse.urlsplit(row['base_url'])
            if parsed_url.username or parsed_url.password or parsed_url.query or parsed_url.fragment:
                raise ValueError('base_url must not contain credentials, query strings or fragments')
            if not row['base_url'].startswith(('https://', 'http://localhost:', 'http://127.0.0.1:')):
                raise ValueError('Set an HTTPS base_url (HTTP allowed only for local testing)')
            if any(x in row['model_id'] for x in ('TBD', 'YOUR_')) or 'YOUR_' in row['base_url']:
                raise ValueError('Replace placeholder model_id/base_url before execution')
            if not credentials[row['model_alias']]:
                raise ValueError(f"Missing API key for {row['model_alias']}: set api_key in YAML or api_key_env")
    directory.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(dict(fingerprint=fingerprint, **snapshot), ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Planned: {len(plan)} requests. Output: {directory}")
    if args.dry_run:
        print('Dry run only: no API calls. Inspect run_snapshot.json for complete messages.')
        return 0
    latest = {}
    for task in ('single_turn','multi_turn'):
        for row in load_records(directory / f'{task}_responses.jsonl'):
            latest[row['request_id']] = row
    failed = 0
    for i, row in enumerate(plan, 1):
        if latest.get(row['request_id'], {}).get('status') == 'success':
            continue
        output = dict(row, run_id=args.run_id, model_response=None, status='error', error_type=None,
                      error_message=None, input_tokens=None, output_tokens=None, finish_reason=None)
        started = time.monotonic()
        try:
            raw, attempts = call_api(row, args.timeout, args.retries, args.ignore_proxy,
                                     api_key=credentials[row['model_alias']])
            choice = raw['choices'][0]
            message = choice['message']
            content = message.get('content')
            output.update(provider_response_id=raw.get('id'), returned_model=raw.get('model'),
                          attempts=attempts, finish_reason=choice.get('finish_reason'),
                          usage=raw.get('usage', {}), refusal=message.get('refusal'))
            usage = raw.get('usage') or {}
            output.update(input_tokens=usage.get('prompt_tokens'), output_tokens=usage.get('completion_tokens'))
            if not isinstance(content, str) or not content.strip():
                raise ValueError('Empty response or refusal (no user-visible text)')
            output['model_response'] = content
            if message.get('refusal') or choice.get('finish_reason') == 'content_filter':
                raise ValueError('Refused or content-filtered response')
            if choice.get('finish_reason') == 'length':
                raise ValueError('Truncated response')
            output['status'] = 'success'
        except Exception as exc:
            output.update(error_type=type(exc).__name__, error_message=str(exc) if isinstance(exc, (ValueError, RuntimeError)) else 'Malformed API response')
            failed += 1
        output.update(latency_ms=round((time.monotonic()-started)*1000), timestamp=datetime.now(timezone.utc).isoformat())
        append_json(directory / f"{row['task']}_responses.jsonl", output)
        print(f"[{i}/{len(plan)}] {row['model_alias']} {row['task']} {row['case_id']} {row['condition_id']}: {output['status']}", flush=True)
        time.sleep(args.delay)
    export_blind(directory)
    print(f'Completed; {failed} failed requests in this invocation. Resume retries errors; success is skipped.')
    return 1 if failed else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, yaml.YAMLError) as exc:
        print(f'Configuration/input error: {exc}', file=sys.stderr)
        sys.exit(2)
