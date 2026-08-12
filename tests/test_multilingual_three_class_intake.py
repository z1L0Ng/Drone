from __future__ import annotations

import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.multilingual_three_class_intake import (
    CANONICAL_CLASSES,
    ContractError,
    load_json_yaml,
    run_feasibility,
    sha256_file,
    validate_config,
    validate_report,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config/multilingual_three_class/es_de_v1.yaml"
FIXTURE_ROOT = REPO_ROOT / "tests/fixtures/multilingual_three_class"


def build_index(path: Path) -> Path:
    fixtures = [
        (
            "gsc-en",
            "gsc_en_metadata.csv",
            "gsc_v2",
            "raw_v0.02",
            "en",
            "inventory",
            "archive_etag_6b74f3901214cb2c2934e98196829835",
        ),
        (
            "mswc-es",
            "mswc_es_metadata.csv",
            "mswc",
            "1.0",
            "es",
            "inventory",
            "0bc9df68e92fd6bb54176bf7eb29e2b9e97cb218",
        ),
        (
            "mswc-de",
            "mswc_de_metadata.csv",
            "mswc",
            "1.0",
            "de",
            "inventory",
            "0bc9df68e92fd6bb54176bf7eb29e2b9e97cb218",
        ),
    ]
    entries = []
    for entry_id, filename, dataset, version, language, split, revision in fixtures:
        fixture_path = FIXTURE_ROOT / filename
        entries.append(
            {
                "entry_id": entry_id,
                "adapter": "normalized_csv",
                "path": str(fixture_path),
                "sha256": sha256_file(fixture_path),
                "dataset_key": dataset,
                "dataset_version": version,
                "language": language,
                "original_split": split,
                "source_revision": revision,
                "coverage": "synthetic_fixture",
            }
        )
    payload = {
        "schema_version": "talk-to-me-drone.metadata-index.v1",
        "entries": entries,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


class ThreeClassIntakeTests(unittest.TestCase):
    def test_config_freezes_exact_three_class_schema(self) -> None:
        config = load_json_yaml(CONFIG_PATH)
        unresolved = validate_config(config)
        self.assertEqual(
            tuple(config["model_contract"]["canonical_classes"]), CANONICAL_CLASSES
        )
        self.assertFalse(config["model_contract"]["source_words_are_model_outputs"])
        self.assertIn(
            "datasets.gsc_v2.receipt.archive_sha256='UNKNOWN_metadata_intake_required'",
            unresolved,
        )

    def test_invalid_output_schema_is_rejected(self) -> None:
        config = copy.deepcopy(load_json_yaml(CONFIG_PATH))
        config["model_contract"]["canonical_classes"].append("fine_grained")
        config["model_contract"]["output_count"] = 4
        with self.assertRaisesRegex(ContractError, "exactly emergency/movement/unknown"):
            validate_config(config)

    def test_determinism_and_global_speaker_family_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            index_path = build_index(temp / "metadata_index.json")
            first_dir = temp / "first"
            second_dir = temp / "second"
            first = run_feasibility(CONFIG_PATH, index_path, first_dir, True)
            second = run_feasibility(CONFIG_PATH, index_path, second_dir, True)

            self.assertEqual(
                first["hashes"]["proposal_manifest_sha256"],
                second["hashes"]["proposal_manifest_sha256"],
            )
            self.assertEqual(first["support"], second["support"])
            self.assertEqual(
                first["lexical_engineering_gate_status"], "PASS_MANAGEMENT_PROVISIONAL"
            )
            for language in ("es", "de"):
                for canonical_class in CANONICAL_CLASSES:
                    for split in ("train", "val", "test"):
                        self.assertEqual(
                            first["support"][language][canonical_class][split][
                                "not_admitted_samples"
                            ],
                            0,
                        )
            self.assertEqual(
                first["overlap_assertions"],
                {
                    "speaker_overlap_across_proposed_splits": 0,
                    "source_clip_family_overlap_across_proposed_splits": 0,
                    "passed": True,
                },
            )
            validate_report(first, load_json_yaml(CONFIG_PATH))

            with (first_dir / "metadata_split_proposal.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))

            by_speaker = {}
            by_family = {}
            for row in rows:
                speaker_key = (row["dataset_key"], row["speaker_id"])
                family_key = (row["dataset_key"], row["source_clip_family"])
                by_speaker.setdefault(speaker_key, set()).add(row["proposed_split"])
                by_family.setdefault(family_key, set()).add(row["proposed_split"])
            self.assertTrue(all(len(value) == 1 for value in by_speaker.values()))
            self.assertTrue(all(len(value) == 1 for value in by_family.values()))

            shared_family_rows = [
                row
                for row in rows
                if row["source_clip_family"] in {"es_fam_shared", "de_fam_shared"}
            ]
            for family in {"es_fam_shared", "de_fam_shared"}:
                self.assertEqual(
                    len(
                        {
                            row["proposed_split"]
                            for row in shared_family_rows
                            if row["source_clip_family"] == family
                        }
                    ),
                    1,
                )

    def test_protected_words_never_enter_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            report = run_feasibility(
                CONFIG_PATH,
                build_index(temp / "metadata_index.json"),
                temp / "out",
                True,
            )
            with (temp / "out/metadata_split_proposal.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))
            words = {row["source_word"] for row in rows}
            self.assertNotIn("para", words)
            self.assertNotIn("stopp", words)
            self.assertEqual(
                report["counts"]["excluded_by_language_and_role"]["es:protected"], 1
            )
            self.assertEqual(
                report["counts"]["excluded_by_language_and_role"]["de:protected"], 1
            )

    def test_missing_identity_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            broken = temp / "broken.csv"
            broken.write_text(
                "source_record_id,dataset_key,dataset_version,language,source_word,speaker_id,source_clip_family,original_split\n"
                "bad,mswc,1.0,es,alto,,family,train\n",
                encoding="utf-8",
            )
            index = {
                "schema_version": "talk-to-me-drone.metadata-index.v1",
                "entries": [
                    {
                        "entry_id": "broken",
                        "adapter": "normalized_csv",
                        "path": str(broken),
                        "sha256": sha256_file(broken),
                        "dataset_key": "mswc",
                        "dataset_version": "1.0",
                        "language": "es",
                        "original_split": "train",
                        "source_revision": "0bc9df68e92fd6bb54176bf7eb29e2b9e97cb218",
                    }
                ],
            }
            index_path = temp / "index.json"
            index_path.write_text(json.dumps(index), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "fail-closed"):
                run_feasibility(CONFIG_PATH, index_path)

    def test_checksum_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            index_path = build_index(temp / "metadata_index.json")
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["entries"][0]["sha256"] = "0" * 64
            index_path.write_text(json.dumps(index), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "checksum mismatch"):
                run_feasibility(CONFIG_PATH, index_path)

    def test_duplicate_source_record_id_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            duplicate = temp / "duplicate.csv"
            duplicate.write_text(
                "source_record_id,dataset_key,dataset_version,language,source_word,speaker_id,source_clip_family,original_split\n"
                "same,mswc,1.0,es,alto,speaker_a,family_a,train\n"
                "same,mswc,1.0,es,arriba,speaker_b,family_b,train\n",
                encoding="utf-8",
            )
            index = {
                "schema_version": "talk-to-me-drone.metadata-index.v1",
                "entries": [
                    {
                        "entry_id": "duplicate",
                        "adapter": "normalized_csv",
                        "path": str(duplicate),
                        "sha256": sha256_file(duplicate),
                        "dataset_key": "mswc",
                        "dataset_version": "1.0",
                        "language": "es",
                        "original_split": "train",
                        "source_revision": "0bc9df68e92fd6bb54176bf7eb29e2b9e97cb218",
                    }
                ],
            }
            index_path = temp / "index.json"
            index_path.write_text(json.dumps(index), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "duplicate mapped source_record_id"):
                run_feasibility(CONFIG_PATH, index_path)

    def test_raw_mswc_adapter_uses_link_as_family_and_valid_rows_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            raw = FIXTURE_ROOT / "mswc_raw_minimal.csv"
            index = {
                "schema_version": "talk-to-me-drone.metadata-index.v1",
                "entries": [
                    {
                        "entry_id": "raw-mswc-es",
                        "adapter": "mswc_csv",
                        "path": str(raw),
                        "sha256": sha256_file(raw),
                        "dataset_key": "mswc",
                        "dataset_version": "1.0",
                        "language": "es",
                        "original_split": "train",
                        "source_revision": "0bc9df68e92fd6bb54176bf7eb29e2b9e97cb218",
                    }
                ],
            }
            index_path = temp / "index.json"
            index_path.write_text(json.dumps(index), encoding="utf-8")
            report = run_feasibility(CONFIG_PATH, index_path, temp / "out", True)
            self.assertEqual(report["counts"]["included_rows"], 2)
            self.assertEqual(
                report["counts"]["excluded_by_language_and_role"]["es:protected"], 1
            )
            with (temp / "out/metadata_split_proposal.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual({row["source_clip_family"] for row in rows}, {"cv_es_family_001.opus"})
            self.assertEqual(len({row["proposed_split"] for row in rows}), 1)

    def test_complete_split_unknown_count_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            index_path = build_index(temp / "metadata_index.json")
            index = json.loads(index_path.read_text(encoding="utf-8"))
            complete_entries = [entry for entry in index["entries"] if entry["dataset_key"] == "gsc_v2"]
            for entry in index["entries"]:
                if entry["dataset_key"] != "mswc":
                    continue
                for split in ("train", "dev", "test"):
                    source_path = Path(entry["path"])
                    target_path = temp / f"{entry['language']}_{split}.csv"
                    with source_path.open("r", encoding="utf-8", newline="") as source:
                        rows = list(csv.DictReader(source))
                        fieldnames = list(rows[0])
                    with target_path.open("w", encoding="utf-8", newline="") as target:
                        writer = csv.DictWriter(target, fieldnames=fieldnames)
                        writer.writeheader()
                        for row in rows:
                            row["source_record_id"] = f"{split}_{row['source_record_id']}"
                            row["original_split"] = split
                            writer.writerow(row)
                    clone = dict(entry)
                    clone["entry_id"] = f"{entry['entry_id']}-{split}"
                    clone["coverage"] = "complete_split"
                    clone["original_split"] = split
                    clone["path"] = str(target_path)
                    clone["sha256"] = sha256_file(target_path)
                    complete_entries.append(clone)
            index["entries"] = complete_entries
            index_path.write_text(json.dumps(index), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "approved_unknown_count_mismatch"):
                run_feasibility(CONFIG_PATH, index_path)


if __name__ == "__main__":
    unittest.main()
