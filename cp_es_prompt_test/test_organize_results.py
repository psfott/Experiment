import csv
import json
from pathlib import Path
import tempfile
import unittest

from organize_results import GROUPS, organize


class ExportTest(unittest.TestCase):
    def test_six_groups_latest_attempt_and_unicode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rows = []
            for condition in GROUPS:
                rows.append(dict(request_id=condition, task='single_turn', condition_id=condition,
                                 status='success', messages=[dict(role='user', content='你好,\n世界')],
                                 model_response='回复,\n第二行'))
            rows.append(dict(rows[0], status='error', model_response='', error_message='Truncated response'))
            (root/'single_turn_responses.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows),encoding='utf-8')
            groups = organize(root)
            self.assertEqual(sum(map(len,groups.values())), 6)
            self.assertEqual(groups['NR_NP'][0]['status'], 'error')
            self.assertEqual(groups['NR_NP'][0]['attempt_records'], 2)
            with (root/'classified_csv/by_input.csv').open(encoding='utf-8-sig',newline='') as stream:
                compared = list(csv.DictReader(stream))
            self.assertEqual(len(compared), 1)
            self.assertEqual(compared[0]['available_conditions'], '6')
            self.assertEqual(compared[0]['successful_conditions'], '5')
            self.assertEqual(compared[0]['No_no_prompt_status'], 'error')
            self.assertEqual(compared[0]['CP_with_prompt_output'], '回复,\n第二行')
            with (root/'classified_csv/CP_no_prompt.csv').open(encoding='utf-8-sig',newline='') as stream:
                row = next(csv.DictReader(stream))
                self.assertEqual(row['current_input'], '你好,\n世界')
                self.assertEqual(row['model_response'], '回复,\n第二行')
            groups = organize(root, root/'success', True)
            self.assertEqual(sum(map(len,groups.values())), 5)
            self.assertTrue((root/'success/No_no_prompt.csv').exists())
            with (root/'success/by_input.csv').open(encoding='utf-8-sig',newline='') as stream:
                self.assertEqual(next(csv.DictReader(stream))['No_no_prompt_status'], 'missing')

    def test_same_input_different_history_stays_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rows = [dict(request_id=str(i), task='multi_turn', case_id='same',
                         model_alias='mock', repeat_id=1, condition_id='CP_NP', status='success',
                         messages=[dict(role='user',content=history),dict(role='user',content='same input')])
                    for i, history in enumerate(['history A','history B'])]
            (root/'multi_turn_responses.jsonl').write_text('\n'.join(map(json.dumps,rows)),encoding='utf-8')
            organize(root)
            with (root/'classified_csv/multi_turn_by_input.csv').open(encoding='utf-8-sig',newline='') as stream:
                self.assertEqual(len(list(csv.DictReader(stream))),2)

    def test_malformed_line_fails_before_export(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'multi_turn_responses.jsonl').write_text('{broken',encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'multi_turn_responses.jsonl:1'):
                organize(root)
            self.assertFalse((root/'classified_csv').exists())


if __name__ == '__main__':
    unittest.main()
