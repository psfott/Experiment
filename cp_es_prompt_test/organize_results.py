"""Export a run into six condition CSVs (UTF-8 BOM, Excel compatible)."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GROUPS = {
    'NR_NP': ('No_no_prompt', 'No', 'no_prompt'),
    'NR_SP': ('No_with_prompt', 'No', 'with_prompt'),
    'CP_NP': ('CP_no_prompt', 'CP', 'no_prompt'),
    'CP_SP': ('CP_with_prompt', 'CP', 'with_prompt'),
    'ES_NP': ('ES_no_prompt', 'ES', 'no_prompt'),
    'ES_SP': ('ES_with_prompt', 'ES', 'with_prompt'),
}
FIELDS = [
    'run_id', 'request_id', 'task', 'case_id', 'emotion', 'model_alias', 'model_id',
    'condition_id', 'role', 'prompt', 'repeat_id', 'status', 'attempt_records',
    'history', 'current_input', 'ed_ground_truth', 'model_response',
    'finish_reason', 'error_type', 'error_message', 'input_tokens', 'output_tokens',
    'latency_ms', 'timestamp', 'generation_params', 'messages',
]


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def export_by_input(output, grouped):
    """Compare six conditions on exactly the same visible conversation."""
    base_fields = ['run_id', 'task', 'case_id', 'emotion', 'model_alias', 'model_id',
                   'repeat_id', 'history', 'current_input', 'ed_ground_truth']
    fields = base_fields + ['available_conditions', 'successful_conditions']
    for name, _, _ in GROUPS.values():
        fields += [name + suffix for suffix in ('_output', '_status', '_error', '_finish_reason')]
    inputs = {}
    for condition, records in grouped.items():
        name = GROUPS[condition][0]
        for record in records:
            # Include history: identical last messages with different histories
            # must never be merged into one comparison.
            key = tuple(str(record.get(f, '')) for f in
                        ['run_id', 'task', 'case_id', 'model_alias', 'model_id',
                         'repeat_id', 'history', 'current_input'])
            if key not in inputs:
                row = {field: record.get(field, '') for field in base_fields}
                row.update(available_conditions=0, successful_conditions=0)
                for group_name, _, _ in GROUPS.values():
                    row.update({group_name+'_output': '', group_name+'_status': 'missing',
                                group_name+'_error': '', group_name+'_finish_reason': ''})
                inputs[key] = row
            row = inputs[key]
            if row[name+'_status'] != 'missing':
                raise ValueError(f'Duplicate condition for input: {condition}, {record.get("case_id")}')
            row[name+'_output'] = record.get('model_response', '')
            row[name+'_status'] = record.get('status', '')
            row[name+'_error'] = record.get('error_message', '')
            row[name+'_finish_reason'] = record.get('finish_reason', '')
            row['available_conditions'] += 1
            row['successful_conditions'] += record.get('status') == 'success'
    rows = [inputs[key] for key in sorted(inputs)]
    write_csv(output / 'by_input.csv', fields, rows)
    for task in ('single_turn', 'multi_turn'):
        write_csv(output / f'{task}_by_input.csv', fields, [r for r in rows if r['task'] == task])
    print(f'Input comparison: {len(rows)} rows (six outputs per row)')


def organize(directory, output=None, success_only=False):
    directory = Path(directory)
    files = [directory / f'{task}_responses.jsonl' for task in ('single_turn', 'multi_turn')]
    files = [p for p in files if p.is_file()]
    if not files:
        raise ValueError(f'No response JSONL files in {directory}')
    latest, attempts = {}, Counter()
    for path in files:
        with path.open(encoding='utf-8-sig') as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    key = (record['task'], record['request_id'])
                    if record['condition_id'] not in GROUPS:
                        raise ValueError(f"Unknown condition: {record['condition_id']}")
                    if not isinstance(record['messages'], list):
                        raise ValueError('messages must be a list')
                except (ValueError, KeyError, TypeError) as exc:
                    raise ValueError(f'{path.name}:{line_number}: {exc}') from exc
                latest[key] = record
                attempts[key] += 1
    grouped = {condition: [] for condition in GROUPS}
    for key, record in latest.items():
        if success_only and record.get('status') != 'success':
            continue
        messages = [m for m in record['messages'] if m.get('role') != 'system']
        _, role, prompt = GROUPS[record['condition_id']]
        row = {field: record.get(field, '') for field in FIELDS}
        row.update(role=role, prompt=prompt, attempt_records=attempts[key],
                   history=json.dumps(messages[:-1], ensure_ascii=False),
                   current_input=messages[-1].get('content', '') if messages else '',
                   generation_params=json.dumps(record.get('generation_params', {}), ensure_ascii=False),
                   messages=json.dumps(record['messages'], ensure_ascii=False))
        grouped[record['condition_id']].append(row)
    output = Path(output) if output else directory / 'classified_csv'
    output.mkdir(parents=True, exist_ok=True)
    summaries = []
    for condition, rows in grouped.items():
        rows.sort(key=lambda r: (str(r['model_alias']), str(r['task']), str(r['case_id']), str(r['repeat_id'])))
        name, role, prompt = GROUPS[condition]
        write_csv(output / f'{name}.csv', FIELDS, rows)
        counts = Counter(row['status'] for row in rows)
        summaries.append(dict(condition_id=condition, role=role, prompt=prompt,
                              rows=len(rows), success=counts['success'],
                              error=counts['error'], single_turn=sum(r['task']=='single_turn' for r in rows),
                              multi_turn=sum(r['task']=='multi_turn' for r in rows)))
    write_csv(output / 'summary.csv', ['condition_id','role','prompt','rows','success','error','single_turn','multi_turn'], summaries)
    export_by_input(output, grouped)
    print(f'Exported {sum(len(v) for v in grouped.values())} latest records into {output}')
    for summary in summaries:
        print(f"  {summary['condition_id']}: {summary['rows']} rows, {summary['success']} success, {summary['error']} error")
    return grouped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', help='Run ID under outputs/, or path to a run directory')
    parser.add_argument('--output', type=Path, help='Custom output folder')
    parser.add_argument('--success-only', action='store_true', help='Exclude errors (default keeps them)')
    args = parser.parse_args()
    directory = Path(args.run)
    if not directory.is_dir():
        directory = ROOT / 'outputs' / args.run
    try:
        organize(directory, args.output, args.success_only)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Export error: {exc}\n')


if __name__ == '__main__':
    main()
