"""Paired no-role versus ES-role experiment on implicit CP scenarios.

Uses OpenAI-compatible chat/completions. No network call is made in --dry-run.
"""
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

ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = ("no_role", "es_role")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def load_cases(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list) or not data:
        raise ValueError("Dataset must be a nonempty JSON array")
    cases = []
    for index, case in enumerate(data, 1):
        if not isinstance(case, dict) or not all(key in case for key in
                ("user_profile", "situation", "history", "query")):
            raise ValueError(f"Case {index} is missing a required field")
        if not isinstance(case["history"], list) or not case["history"]:
            raise ValueError(f"Case {index} has no dialogue history")
        for turn in case["history"]:
            if not isinstance(turn, dict) or not all(
                    isinstance(turn.get(key), str) and turn[key].strip()
                    for key in ("seeker", "supporter")):
                raise ValueError(f"Case {index} has an invalid history turn")
        if not all(isinstance(case[key], str) and case[key].strip() for key in
                   ("user_profile", "situation", "query")):
            raise ValueError(f"Case {index} has empty text fields")
        cases.append({"case_id": f"case_{index:03d}", **case})
    return cases


def build_messages(case: dict, condition: str, prompts: dict) -> list[dict]:
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")
    role_line = prompts["conditions"][condition]["role_line"].strip()
    common = prompts["common_system"].strip()
    background = prompts["background_context"].format(
        user_profile=case["user_profile"], situation=case["situation"])
    system = "\n\n".join(part for part in (role_line, common, background) if part)
    messages = [{"role": "system", "content": system}]
    for turn in case["history"]:
        messages.append({"role": "user", "content": turn["seeker"]})
        messages.append({"role": "assistant", "content": turn["supporter"]})
    messages.append({"role": "user", "content": case["query"]})
    return messages


def make_plan(cases: list[dict], models: list[dict], prompts: dict,
              selected_cases: list[str] | None, selected_models: list[str] | None,
              selected_conditions: list[str] | None, repeats: int,
              temperature: float, top_p: float, max_tokens: int) -> list[dict]:
    if repeats < 1 or max_tokens < 1 or not 0 <= temperature <= 2 or not 0 <= top_p <= 1:
        raise ValueError("Invalid generation settings")
    if set(prompts["conditions"]) != set(CONDITIONS):
        raise ValueError("Prompt file must define exactly no_role and es_role")
    case_ids = {case["case_id"] for case in cases}
    model_ids = {model["alias"] for model in models}
    for selected, available, label in (
        (selected_cases, case_ids, "case"),
        (selected_models, model_ids, "model"),
        (selected_conditions, set(CONDITIONS), "condition"),
    ):
        if selected and set(selected) - available:
            raise ValueError(f"Unknown {label}: {sorted(set(selected) - available)}")
    if len(model_ids) != len(models):
        raise ValueError("Duplicate model aliases")
    plan = []
    for model in models:
        if not model.get("enabled", True) or (selected_models and model["alias"] not in selected_models):
            continue
        if model.get("provider") != "openai-compatible":
            raise ValueError("Only openai-compatible providers are supported")
        extra = model.get("extra_body") or {}
        if not isinstance(extra, dict) or set(extra) & {"model", "messages", "stream"}:
            raise ValueError("extra_body cannot override model, messages, or stream")
        for case in cases:
            if selected_cases and case["case_id"] not in selected_cases:
                continue
            for condition in CONDITIONS:
                if selected_conditions and condition not in selected_conditions:
                    continue
                messages = build_messages(case, condition, prompts)
                body = {"model": model["model_id"], "messages": messages,
                        "temperature": temperature, "top_p": top_p,
                        "max_tokens": max_tokens}
                body.update(extra)
                body = {key: value for key, value in body.items() if value is not None}
                for repeat in range(1, repeats + 1):
                    row = {"case_id": case["case_id"], "condition": condition,
                           "model_alias": model["alias"], "model_id": model["model_id"],
                           "repeat": repeat, "user_profile": case["user_profile"],
                           "situation": case["situation"], "history": case["history"],
                           "query": case["query"], "reference_gt": case.get("GT"),
                           "messages": messages, "request_body": body,
                           "base_url": model.get("base_url", ""),
                           "api_key_env": model.get("api_key_env", "")}
                    row["request_id"] = fingerprint(row)
                    plan.append(row)
    if not plan:
        raise ValueError("No requests selected")
    return plan


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def append_jsonl(path: Path, value: dict) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")
        stream.flush()


def call_api(row: dict, api_key: str, timeout: float, retries: int) -> tuple[dict, int]:
    url = row["base_url"].rstrip("/") + "/chat/completions"
    for attempt in range(retries + 1):
        request = urllib.request.Request(
            url, data=canonical(row["request_body"]).encode("utf-8"),
            headers={"Authorization": "Bearer " + api_key,
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response), attempt + 1
        except urllib.error.HTTPError as exc:
            # Never persist provider error bodies, which can echo credentials.
            if exc.code not in (408, 429, 500, 502, 503, 504) or attempt == retries:
                raise RuntimeError(f"HTTP {exc.code}") from None
            retry_after = exc.headers.get("Retry-After", "")
            delay = min(float(retry_after), 30) if retry_after.isdigit() else min(2 ** attempt, 16)
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == retries:
                raise RuntimeError("Network connection failed or timed out") from None
            delay = min(2 ** attempt, 16)
        time.sleep(delay)
    raise RuntimeError("Unreachable retry state")


def export_comparison(run_dir: Path) -> None:
    latest = {}
    for row in load_jsonl(run_dir / "responses.jsonl"):
        latest[row["request_id"]] = row
    paired = {}
    for row in latest.values():
        key = (row["model_alias"], row["case_id"], row["repeat"])
        item = paired.setdefault(key, {
            "model_alias": row["model_alias"], "case_id": row["case_id"],
            "repeat": row["repeat"], "user_profile": row["user_profile"],
            "situation": row["situation"],
            "history": json.dumps(row["history"], ensure_ascii=False),
            "query": row["query"], "reference_gt": row.get("reference_gt")})
        item[row["condition"] + "_response"] = row.get("model_response")
        item[row["condition"] + "_status"] = row["status"]
    columns = ["model_alias", "case_id", "repeat", "user_profile", "situation",
               "history", "query", "reference_gt",
               "no_role_response", "no_role_status", "es_role_response", "es_role_status"]
    with (run_dir / "comparison.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(paired[key] for key in sorted(paired))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=("en", "zh"), default="en")
    parser.add_argument("--models", type=Path)
    parser.add_argument("--model", nargs="+")
    parser.add_argument("--case", nargs="+")
    parser.add_argument("--condition", nargs="+", choices=CONDITIONS)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--export-comparison", type=Path)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--order-seed", type=int, default=42)
    args = parser.parse_args(argv)
    if args.export_comparison:
        export_comparison(args.export_comparison)
        return 0
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
        raise ValueError("run-id may contain only letters, numbers, underscores, and hyphens")
    if args.timeout <= 0 or args.retries < 0 or args.delay < 0:
        raise ValueError("Invalid timeout, retries, or delay")
    dataset_name = "implicit_cp_scenarios_en.json" if args.language == "en" else "implicit_cp_scenarios.json"
    dataset_path = ROOT / "data" / dataset_name
    prompts_path = ROOT / "prompt_template" / "prompts.json"
    models_path = args.models or ROOT / ("models.example.json" if args.dry_run else "models.local.json")
    cases = load_cases(dataset_path)
    prompts = read_json(prompts_path)
    models = read_json(models_path)["models"]
    plan = make_plan(cases, models, prompts, args.case, args.model,
                     args.condition, args.repeats, args.temperature,
                     args.top_p, args.max_tokens)
    random.Random(args.order_seed).shuffle(plan)
    snapshot = {"dataset": dataset_name, "dataset_sha256": fingerprint(cases),
                "prompt_sha256": fingerprint(prompts), "order_seed": args.order_seed,
                "plan": plan}
    snapshot["fingerprint"] = fingerprint(snapshot)
    run_dir = ROOT / "results" / args.run_id
    snapshot_path = run_dir / "run_snapshot.json"
    if run_dir.exists():
        if not args.resume or not snapshot_path.exists():
            raise ValueError("Run directory already exists; use a new run-id or --resume")
        old = json.loads(snapshot_path.read_text(encoding="utf-8"))
        if old["fingerprint"] != snapshot["fingerprint"]:
            raise ValueError("Run plan changed; use a new run-id")
    credentials = {}
    if not args.dry_run:
        for model in models:
            if model["alias"] not in {row["model_alias"] for row in plan}:
                continue
            key = model.get("api_key") or os.environ.get(model.get("api_key_env") or "", "")
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"Missing API key for {model['alias']}")
            credentials[model["alias"]] = key.strip()
        for row in plan:
            url = row["base_url"]
            parsed = urllib.parse.urlsplit(url)
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError("base_url must not contain credentials, query, or fragment")
            if not (url.startswith("https://") or url.startswith("http://localhost:")
                    or url.startswith("http://127.0.0.1:")):
                raise ValueError("base_url must use HTTPS, except for localhost")
            if "YOUR_" in url or "YOUR_" in row["model_id"]:
                raise ValueError("Replace placeholder model ID and base URL")
    run_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Planned: {len(plan)} requests; output: {run_dir}")
    if args.dry_run:
        print("Dry run: no API calls. Inspect run_snapshot.json for exact messages.")
        return 0
    latest = {row["request_id"]: row for row in load_jsonl(run_dir / "responses.jsonl")}
    failed = 0
    for index, row in enumerate(plan, 1):
        if latest.get(row["request_id"], {}).get("status") == "success":
            continue
        output = {key: value for key, value in row.items() if key != "request_body"}
        output.update(status="error", model_response=None, error_type=None,
                      error_message=None, run_id=args.run_id)
        started = time.monotonic()
        try:
            raw, attempts = call_api(row, credentials[row["model_alias"]], args.timeout, args.retries)
            choice = raw["choices"][0]
            message = choice["message"]
            content = message.get("content")
            output.update(attempts=attempts, provider_response_id=raw.get("id"),
                          returned_model=raw.get("model"), usage=raw.get("usage", {}),
                          finish_reason=choice.get("finish_reason"))
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Empty response")
            output["model_response"] = content
            if message.get("refusal") or choice.get("finish_reason") in ("length", "content_filter"):
                raise ValueError("Refusal, content filter, or truncated response")
            output["status"] = "success"
        except Exception as exc:
            output["error_type"] = type(exc).__name__
            output["error_message"] = str(exc) if isinstance(exc, (ValueError, RuntimeError)) else "Malformed API response"
            failed += 1
        output["latency_ms"] = round((time.monotonic() - started) * 1000)
        output["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        append_jsonl(run_dir / "responses.jsonl", output)
        print(f"[{index}/{len(plan)}] {row['model_alias']} {row['case_id']} {row['condition']}: {output['status']}", flush=True)
        time.sleep(args.delay)
    export_comparison(run_dir)
    print(f"Finished; {failed} failed requests in this invocation. comparison.csv updated.")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Configuration/input error: {exc}", file=sys.stderr)
        sys.exit(2)
