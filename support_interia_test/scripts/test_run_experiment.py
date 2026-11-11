"""Offline tests for paired prompt construction and the local run pipeline."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_experiment as runner


class ExperimentTest(unittest.TestCase):
    def test_shared_local_key_reference(self):
        models = [{"alias": "qwen", "api_key": "test-only-key"},
                  {"alias": "kimi", "api_key_from": "qwen"}]
        self.assertEqual(runner.resolve_api_key(models[1], models), "test-only-key")

    def test_pair_is_identical_except_for_role_and_never_sends_gt(self):
        cases = runner.load_cases(runner.ROOT / "data/implicit_cp_scenarios_en.json")
        prompts = runner.read_json(runner.ROOT / "prompt_template/prompts.json")
        models = [{"alias": "mock", "provider": "openai-compatible",
                   "model_id": "mock-model", "base_url": "http://127.0.0.1:1234",
                   "api_key_env": "MOCK_KEY"}]
        plan = runner.make_plan(cases, models, prompts, None, None, None,
                                1, 0.7, 0.9, 512)
        self.assertEqual(len(plan), 20)
        self.assertEqual(len({row["request_id"] for row in plan}), 20)
        for index in range(1, 11):
            pair = [row for row in plan if row["case_id"] == f"case_{index:03d}"]
            no_role = next(row for row in pair if row["condition"] == "no_role")
            es_role = next(row for row in pair if row["condition"] == "es_role")
            self.assertEqual(no_role["messages"][1:], es_role["messages"][1:])
            self.assertEqual(no_role["messages"][0]["content"],
                             es_role["messages"][0]["content"].replace(
                                 prompts["conditions"]["es_role"]["role_line"].strip() + "\n\n", "", 1))
            self.assertEqual([message["role"] for message in no_role["messages"]],
                             ["system", "user", "assistant", "user", "assistant", "user"])
            self.assertEqual(no_role["messages"][-1]["content"], no_role["query"])
            self.assertNotIn(no_role["reference_gt"], runner.canonical(no_role["messages"]))
            self.assertIn("20 and 60 English words", no_role["messages"][0]["content"])

    def test_chinese_length_constraint_is_shared(self):
        cases = runner.load_cases(runner.ROOT / "data/implicit_cp_scenarios.json")
        prompts = runner.read_json(runner.ROOT / "prompt_template/prompts.json")
        no_role = runner.build_messages(cases[0], "no_role", prompts, "zh")
        es_role = runner.build_messages(cases[0], "es_role", prompts, "zh")
        self.assertIn("40到120个汉字", no_role[0]["content"])
        self.assertIn("40到120个汉字", es_role[0]["content"])
        self.assertEqual(no_role[1:], es_role[1:])

    def test_dry_run_mock_api_and_resume(self):
        original_root = runner.ROOT
        with tempfile.TemporaryDirectory(dir=original_root / "results") as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "prompt_template").mkdir()
            (root / "data/implicit_cp_scenarios_en.json").write_bytes(
                (original_root / "data/implicit_cp_scenarios_en.json").read_bytes())
            (root / "data/implicit_cp_scenarios.json").write_bytes(
                (original_root / "data/implicit_cp_scenarios.json").read_bytes())
            (root / "prompt_template/prompts.json").write_bytes(
                (original_root / "prompt_template/prompts.json").read_bytes())
            config = root / "models.local.json"
            config.write_text(json.dumps({"models": [{
                "alias": "mock", "provider": "openai-compatible",
                "model_id": "mock-model", "base_url": "http://127.0.0.1:1234",
                "api_key": "test-secret"}]}), encoding="utf-8")
            runner.ROOT = root
            received = []

            def fake_urlopen(request, timeout):
                self.assertEqual(request.get_header("Authorization"), "Bearer test-secret")
                received.append(json.loads(request.data))
                payload = {"id": "mock-response", "choices": [
                    {"message": {"content": "Let's talk about the movie."},
                     "finish_reason": "stop"}]}
                return io.BytesIO(json.dumps(payload).encode())

            try:
                args = ["--models", str(config), "--language", "en", "--run-id", "pilot",
                        "--model", "mock", "--case", "case_001", "--delay", "0"]
                self.assertEqual(runner.main(args + ["--dry-run"]), 0)
                self.assertEqual(len(received), 0)
                both_args = ["--models", str(config), "--language", "both",
                             "--run-id", "both", "--case", "case_001", "--dry-run"]
                self.assertEqual(runner.main(both_args), 0)
                snapshot = json.loads((root / "results/both/run_snapshot.json").read_text(encoding="utf-8"))
                self.assertEqual(len(snapshot["plan"]), 4)
                self.assertEqual({r["language"] for r in snapshot["plan"]}, {"en", "zh"})
                self.assertEqual(len({r["request_id"] for r in snapshot["plan"]}), 4)
                # A fresh live run is used because the dry-run plan used the same model
                # but may be reviewed before execution.
                live_args = args[:]
                live_args[live_args.index("pilot")] = "live"
                with patch.object(runner.urllib.request, "urlopen", side_effect=fake_urlopen):
                    self.assertEqual(runner.main(live_args), 0)
                    self.assertEqual(len(received), 2)
                    self.assertEqual(runner.main(live_args + ["--resume"]), 0)
                    self.assertEqual(len(received), 2)
                csv_text = (root / "results/live/comparison.csv").read_text(encoding="utf-8-sig")
                self.assertIn("no_role_response", csv_text)
                self.assertIn("es_role_response", csv_text)
                self.assertIn("language,", csv_text)
                for path in (root / "results/live").iterdir():
                    self.assertNotIn("test-secret", path.read_text(encoding="utf-8-sig"))
            finally:
                runner.ROOT = original_root


if __name__ == "__main__":
    unittest.main()
