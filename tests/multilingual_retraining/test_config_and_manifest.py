from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.multilingual_retraining.config import load_config, parity_contract_sha256, sha256_file
from src.multilingual_retraining.manifest import ManifestError, load_frozen_manifest
from src.multilingual_retraining.runner import build_context, stage_records

from tests.multilingual_retraining.fixture_factory import create_fixture


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = REPO_ROOT / "config" / "multilingual_2026w33"


class ConfigAndManifestTest(unittest.TestCase):
    def test_three_lanes_share_parity_contract(self) -> None:
        paths = (
            CONFIG_ROOT / "en_only_anchor_v0.json",
            CONFIG_ROOT / "multilingual_naive_pooled_v0.json",
            CONFIG_ROOT / "multilingual_balanced_main_v0.json",
        )
        loaded = [load_config(path) for path in paths]
        self.assertEqual(len({parity_contract_sha256(item.effective) for item in loaded}), 1)
        self.assertEqual(loaded[0].effective["labels"], ["emergency", "movement", "unknown"])
        self.assertEqual(loaded[0].effective["model"]["input_shape"], [256, 32, 1])
        self.assertIsNone(loaded[0].effective["noise"]["snr_db_levels"])

    def test_en_anchor_uses_en_development_and_shared_multilingual_test(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = create_fixture(Path(temporary))
            context = build_context(
                repo_root=REPO_ROOT,
                config_path=CONFIG_ROOT / "en_only_anchor_v0.json",
                manifest_path=fixture["manifest"],
                validation_receipt_path=fixture["receipt"],
                audio_root=fixture["audio_root"],
                output_dir=None,
                seed_id=0,
            )
            self.assertEqual(
                {row["language"] for row in stage_records(context, "train", "train_languages")},
                {"en"},
            )
            self.assertEqual(
                {row["language"] for row in stage_records(context, "test", "evaluation_languages")},
                {"en", "es", "de"},
            )

    def test_en_lane_filters_full_frozen_manifest_without_resplitting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = create_fixture(Path(temporary))
            manifest = load_frozen_manifest(
                fixture["manifest"],
                fixture["receipt"],
                selected_languages=["en"],
                expected_manifest_languages=["en", "es", "de"],
            )
            self.assertEqual(manifest.full_record_count, 36)
            self.assertEqual(len(manifest.records), 12)
            self.assertEqual({row["language"] for row in manifest.records}, {"en"})
            self.assertEqual({row["split"] for row in manifest.records}, {
                "train", "validation_selection", "validation_calibration", "test"
            })

    def test_receipt_hash_and_group_isolation_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = create_fixture(Path(temporary))
            with fixture["manifest"].open("a", encoding="utf-8") as handle:
                handle.write("{}\n")
            with self.assertRaises(ManifestError):
                load_frozen_manifest(
                    fixture["manifest"], fixture["receipt"], ["en"], ["en", "es", "de"]
                )

        with tempfile.TemporaryDirectory() as temporary:
            fixture = create_fixture(Path(temporary))
            rows = [json.loads(line) for line in fixture["manifest"].read_text(encoding="utf-8").splitlines()]
            rows[9]["isolation_group_id"] = rows[0]["isolation_group_id"]
            fixture["manifest"].write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
            )
            receipt = json.loads(fixture["receipt"].read_text(encoding="utf-8"))
            receipt["manifest_sha256"] = sha256_file(fixture["manifest"])
            fixture["receipt"].write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaises(ManifestError):
                load_frozen_manifest(
                    fixture["manifest"], fixture["receipt"], ["en", "es", "de"], ["en", "es", "de"]
                )


if __name__ == "__main__":
    unittest.main()
