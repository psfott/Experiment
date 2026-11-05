"""Local integration tests; no external network or paid calls."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import io
import urllib.error
from unittest.mock import patch
import unittest

import run_experiment as runner


class RunnerTest(unittest.TestCase):
    def test_full_plan_and_no_label_leakage(self):
        manifest = runner.read_yaml(runner.ROOT / 'experiment_manifest.yaml')
        models = [dict(alias=str(i), provider='openai-compatible', model_id='test') for i in range(5)]
        plan = runner.build_plan(manifest, models, manifest['tasks'], None, None, None)
        self.assertEqual(len(plan), 600)
        self.assertEqual(len({r['request_id'] for r in plan}), 600)
        for row in plan:
            messages = [m for m in row['messages'] if m['role'] != 'system']
            self.assertEqual(len(messages), 1 if row['task'] == 'single_turn' else 3)
            self.assertEqual(messages[0]['content'], row['ed_user_1'])
            if row['condition_id'] == 'NR_NP':
                self.assertNotEqual(row['messages'][0]['role'], 'system')
            self.assertNotIn('metadata', row['request_body'])

    def test_api_error_resume_and_blinding(self):
        received = []
        class FakeOpener:
            def open(self, request, timeout):
                self_key = request.get_header('Authorization')
                if self_key != 'Bearer test-secret':
                    raise AssertionError('Wrong authorization header')
                received.append(json.loads(request.data))
                if len(received) == 1:
                    raise urllib.error.HTTPError(request.full_url, 429, 'rate limited', {}, None)
                return io.BytesIO(json.dumps(dict(id='local', model='mock', choices=[dict(message=dict(content='A natural reply.'), finish_reason='stop')], usage=dict(prompt_tokens=3, completion_tokens=4))).encode())
        transport = patch.object(runner.urllib.request, 'build_opener', return_value=FakeOpener())
        transport.start()
        original = runner.ROOT
        previous_key = os.environ.get('MOCK_KEY')
        try:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                for name in ('data','tables','prompts'):
                    shutil.copytree(original / name, root / name)
                shutil.copy(original / 'experiment_manifest.yaml', root)
                config = root / 'models.yaml'
                config.write_text(f'models:\n  - alias: mock\n    provider: openai-compatible\n    model_id: mock\n    base_url: http://127.0.0.1:12345\n    api_key_env: MOCK_KEY\n', encoding='utf-8')
                os.environ['MOCK_KEY'] = 'test-secret'
                runner.ROOT = root
                args = ['--models',str(config),'--manifest',str(root/'experiment_manifest.yaml'),'--run-id','test','--model','mock','--case','sad_dog_001','--condition','NR_NP','--retries','0','--delay','0','--ignore-proxy']
                self.assertEqual(runner.main(args), 1)
                self.assertEqual(len(received), 2)
                self.assertEqual(runner.main(args + ['--resume']), 0)
                self.assertEqual(len(received), 3)
                # Switch to a literal YAML credential; it must not change the plan
                # fingerprint, leak to artifacts, or be overridden by the env key.
                config.write_text(config.read_text() + '    api_key: "test-secret"\n', encoding='utf-8')
                os.environ['MOCK_KEY'] = 'wrong-env-key'
                self.assertEqual(runner.main(args + ['--run-id','literal']), 0)
                for path in (root/'outputs/literal').iterdir():
                    self.assertNotIn('test-secret', path.read_text(encoding='utf-8-sig'))
                count_after_literal = len(received)
                self.assertEqual(runner.main(args + ['--resume']), 0)
                self.assertEqual(len(received), count_after_literal)
                directory = root/'outputs/test'
                text = (directory/'blinded.csv').read_text(encoding='utf-8-sig')
                self.assertNotIn('mock', text)
                self.assertNotIn('NR_NP', text)
                for path in directory.iterdir():
                    self.assertNotIn('test-secret', path.read_text(encoding='utf-8-sig'))
                with self.assertRaises(ValueError):
                    runner.main(args + ['--resume','--order-seed','99'])
        finally:
            runner.ROOT = original
            if previous_key is None:
                os.environ.pop('MOCK_KEY', None)
            else:
                os.environ['MOCK_KEY'] = previous_key
            transport.stop()


if __name__ == '__main__':
    unittest.main()
