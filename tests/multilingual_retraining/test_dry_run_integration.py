from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.multilingual_retraining.runner import RunError, build_context, run_guarded_training, run_synthetic_dry_run

from tests.multilingual_retraining.fixture_factory import create_fixture


REPO_ROOT = Path(__file__).resolve().parents[2]


class DryRunIntegrationTest(unittest.TestCase):
    def test_balanced_lane_synthetic_dry_run_writes_nonclaim_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = create_fixture(root / "fixture")
            output = root / "dry_run_output"
            context = build_context(
                repo_root=REPO_ROOT,
                config_path=REPO_ROOT / "config/multilingual_2026w33/multilingual_balanced_main_v0.json",
                manifest_path=fixture["manifest"],
                validation_receipt_path=fixture["receipt"],
                audio_root=fixture["audio_root"],
                output_dir=output,
                seed_id=0,
            )
            completion = run_synthetic_dry_run(context)
            self.assertEqual(completion["status"], "synthetic_dry_run_pass")
            self.assertIsNone(completion["checkpoint_sha256"])
            self.assertTrue((output / "start_receipt.json").is_file())
            self.assertTrue((output / "completion_receipt.json").is_file())
            self.assertFalse((output / "abort_receipt.json").exists())
            feature_rows = (output / "synthetic_feature_receipt.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(feature_rows), 36)
            self.assertIn("synthetic fixtures only", completion["result_scope"])

    def test_training_guard_refuses_without_explicit_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = create_fixture(root / "fixture")
            context = build_context(
                repo_root=REPO_ROOT,
                config_path=REPO_ROOT / "config/multilingual_2026w33/en_only_anchor_v0.json",
                manifest_path=fixture["manifest"],
                validation_receipt_path=fixture["receipt"],
                audio_root=fixture["audio_root"],
                output_dir=root / "must_not_exist",
                seed_id=0,
            )
            with self.assertRaises(RunError):
                run_guarded_training(context, expected_git_commit="0" * 40, allow_execution=False)
            self.assertFalse((root / "must_not_exist").exists())


if __name__ == "__main__":
    unittest.main()
