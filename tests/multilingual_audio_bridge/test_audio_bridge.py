from __future__ import annotations

import csv
import io
import json
import os
import tarfile
import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock

import numpy as np

from src.multilingual_audio_bridge.acquisition import (
    _download_stream,
    _tar_expansion_limit,
    acquire,
    load_plan,
    safe_extract,
)
from src.multilingual_audio_bridge.contracts import (
    PROPOSAL_RECEIPT_SCHEMA,
    BridgeError,
    canonical_json_bytes,
    sha256_bytes,
    sha256_file,
)
from src.multilingual_audio_bridge.manifest import produce_frozen_manifest
from src.multilingual_audio_bridge.metadata_bootstrap import (
    bootstrap_metadata,
    validate_mswc_metadata_audio,
)
from src.multilingual_audio_bridge.materialize import (
    PROPOSAL_REQUIRED_FIELDS,
    freeze_metadata_proposal,
    load_frozen_proposal,
    materialize,
)
from src.multilingual_audio_bridge.orchestrator import _run_stage, run_orchestrator
from src.multilingual_retraining.contracts import LABELS, LANGUAGES, SPLITS
from src.multilingual_retraining.manifest import REQUIRED_FIELDS, load_frozen_manifest
from src.multilingual_three_class_intake import (
    canonical_json_sha256,
    iter_entry_records,
    load_json_yaml,
    load_metadata_index,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = REPO_ROOT / "config/multilingual_three_class/server_audio_bridge_v0.json"
INTAKE_CONFIG = REPO_ROOT / "config/multilingual_three_class/es_de_v1.yaml"


def _write_wave(
    path: Path,
    sample_rate: int,
    frames: int,
    frequency: float,
    channels: int = 1,
    amplitude: float = 0.12,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    time = np.arange(frames, dtype=np.float64) / sample_rate
    mono = amplitude * np.sin(2.0 * np.pi * frequency * time)
    if channels == 2:
        waveform = np.stack([mono, mono * 0.8], axis=1)
    else:
        waveform = mono[:, None]
    samples = np.rint(waveform * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(samples.tobytes(order="C"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value) + b"\n")


class SyntheticBridgeFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.sources = root / "sources"
        self.gsc_root = self.sources / "gsc"
        self.mswc_root = self.sources / "mswc"
        self.proposal = root / "proposal.csv"
        self.proposal_receipt = root / "proposal_receipt.json"
        self.acquisition_receipt = root / "acquisition_receipt.json"
        self.output = root / "output"
        self.config_sha = sha256_file(INTAKE_CONFIG)
        self.rows: list[dict[str, str]] = []

    def build(self, duplicate_cross_split: bool = False) -> None:
        counter = 0
        for split in SPLITS:
            for language in LANGUAGES:
                for label in LABELS:
                    dataset = "gsc_v2" if language == "en" else "mswc"
                    word = {
                        "emergency": {"en": "stop", "es": "alto", "de": "halt"},
                        "movement": {"en": "go", "es": "adelante", "de": "los"},
                        "unknown": {"en": "zero", "es": "cero", "de": "null"},
                    }[label][language]
                    family = f"{language}-family-{split}-{label}.opus"
                    if dataset == "gsc_v2":
                        relative = f"{word}/{language}-{split}-{label}.wav"
                        audio_path = self.gsc_root / relative
                    else:
                        relative = f"{word}_{Path(family).stem}.wav"
                        audio_path = self.mswc_root / relative
                    if duplicate_cross_split and counter in {0, 9}:
                        frequency = 310.0
                    else:
                        frequency = 200.0 + counter * 13.0
                    if language == "en":
                        _write_wave(audio_path, 8000, 4000, frequency)
                    elif language == "es":
                        _write_wave(audio_path, 16000, 8000, frequency, channels=2)
                    else:
                        _write_wave(audio_path, 16000, 16000, frequency)
                    self.rows.append(
                        {
                            "source_record_id": f"record-{counter:03d}",
                            "dataset_key": dataset,
                            "dataset_version": "raw_v0.02" if dataset == "gsc_v2" else "1.0",
                            "language": language,
                            "source_word": word,
                            "canonical_class": label,
                            "mapping_role": label,
                            "mapping_status": "synthetic_fixture",
                            "mapping_admitted": "true",
                            "speaker_id": f"speaker-{counter:03d}",
                            "source_clip_family": family,
                            "source_audio_relpath": relative,
                            "isolation_component_id": f"component-{counter:03d}",
                            "proposed_split": split,
                            "original_split": "train",
                            "metadata_entry_id": f"entry-{dataset}",
                            "metadata_row": str(counter + 2),
                            "crop_start_sample": "",
                            "speech_start_sample": "",
                            "speech_end_sample": "",
                        }
                    )
                    counter += 1
        with self.proposal.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=PROPOSAL_REQUIRED_FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(self.rows)
        _write_json(
            self.proposal_receipt,
            {
                "schema_version": PROPOSAL_RECEIPT_SCHEMA,
                "owner": "dataset",
                "status": "pass",
                "frozen": True,
                "canonical_manifest_created": False,
                "proposal_sha256": sha256_file(self.proposal),
                "config_sha256": self.config_sha,
                "labels": list(LABELS),
                "languages": list(LANGUAGES),
                "splits": list(SPLITS),
                "isolation_audit": {
                    "speaker_overlap_count": 0,
                    "source_family_overlap_count": 0,
                },
            },
        )
        fake_archive_gsc = "1" * 64
        fake_archive_mswc = "2" * 64
        _write_json(
            self.acquisition_receipt,
            {
                "schema_version": "drone.multilingual_acquisition_receipt.v0",
                "status": "pass",
                "plan_sha256": "3" * 64,
                "assets": [
                    {
                        "dataset_key": "gsc_v2",
                        "release": "raw_v0.02",
                        "asset_id": "gsc-fixture",
                        "asset_role": "audio_archive",
                        "language": "en",
                        "download": {"archive_sha256": fake_archive_gsc},
                        "extraction": {"destination": str(self.gsc_root)},
                    },
                    {
                        "dataset_key": "mswc",
                        "release": "1.0",
                        "asset_id": "mswc-es-fixture",
                        "asset_role": "audio_archive",
                        "language": "es",
                        "download": {"archive_sha256": fake_archive_mswc},
                        "extraction": {"destination": str(self.mswc_root)},
                    },
                    {
                        "dataset_key": "mswc",
                        "release": "1.0",
                        "asset_id": "mswc-de-fixture",
                        "asset_role": "audio_archive",
                        "language": "de",
                        "download": {"archive_sha256": fake_archive_mswc},
                        "extraction": {"destination": str(self.mswc_root)},
                    },
                ],
                "license_receipts": [
                    {
                        "dataset_key": "gsc_v2",
                        "license_id": "CC-BY-4.0",
                        "attribution_source": "Google Speech Commands project and contributors",
                    },
                    {
                        "dataset_key": "mswc",
                        "license_id": "CC-BY-4.0",
                        "attribution_source": "MLCommons MSWC and Common Voice contributors",
                    },
                ],
                "no_reidentification_performed": True,
                "redistribution_authorized": False,
            },
        )

    def materialize(self) -> dict[str, object]:
        return materialize(
            self.proposal,
            self.proposal_receipt,
            self.acquisition_receipt,
            self.output,
            "synthetic-v0",
        )


class AudioBridgeTests(unittest.TestCase):
    def test_metadata_bootstrap_produces_intake_accepted_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            gsc_root = root / "sources/gsc_v2/raw_v0.02"
            validation: list[str] = []
            testing: list[str] = []
            for word_index, word in enumerate(("stop", "go", "zero")):
                for utterance in range(4):
                    relative = f"{word}/speaker-{word_index}-{utterance}_nohash_{utterance}.wav"
                    frequency = 300.0 if (word_index, utterance) in {(0, 0), (1, 0)} else (
                        350.0 + word_index * 40.0 + utterance
                    )
                    _write_wave(gsc_root / relative, 16000, 8000, frequency)
                    if utterance == 0:
                        validation.append(relative)
                    elif utterance == 1:
                        testing.append(relative)
            gsc_root.mkdir(parents=True, exist_ok=True)
            (gsc_root / "validation_list.txt").write_text(
                "\n".join(validation) + "\n", encoding="utf-8"
            )
            (gsc_root / "testing_list.txt").write_text(
                "\n".join(testing) + "\n", encoding="utf-8"
            )

            assets: list[dict[str, object]] = [
                {
                    "dataset_key": "gsc_v2",
                    "release": "raw_v0.02",
                    "asset_id": "gsc-fixture",
                    "asset_role": "audio_archive",
                    "language": None,
                    "download": {"archive_sha256": "1" * 64},
                    "extraction": {"destination": str(gsc_root)},
                }
            ]
            for language, words in {
                "es": ("alto", "adelante", "cero"),
                "de": ("halt", "los", "null"),
            }.items():
                metadata_root = root / f"sources/mswc/1.0/metadata/{language}"
                audio_root = root / f"sources/mswc/1.0/{language}/all/fixture"
                metadata_root.mkdir(parents=True, exist_ok=True)
                for split in ("train", "dev", "test"):
                    rows = [
                        {
                            "LINK": f"non-target/common_voice_{language}_{split}_ignored.opus",
                            "WORD": "non-target",
                            "VALID": "True",
                            "SPEAKER": f"published-{language}-{split}-ignored",
                            "GENDER": "NAN",
                        }
                    ]
                    for word_index, word in enumerate(words):
                        family = f"common_voice_{language}_{split}_{word_index}.opus"
                        rows.append(
                            {
                                "LINK": f"{word}/{family}",
                                "WORD": word,
                                "VALID": "True",
                                "SPEAKER": f"published-{language}-{split}-{word_index}",
                                "GENDER": "NAN",
                            }
                        )
                        _write_wave(
                            audio_root / f"{word}_{Path(family).stem}.wav",
                            16000,
                            16000,
                            510.0 + word_index * 20.0,
                        )
                    with (metadata_root / f"{split}.csv").open(
                        "w", encoding="utf-8", newline=""
                    ) as handle:
                        writer = csv.DictWriter(
                            handle,
                            fieldnames=("LINK", "WORD", "VALID", "SPEAKER", "GENDER"),
                            lineterminator="\n",
                        )
                        writer.writeheader()
                        writer.writerows(rows)
                (metadata_root / "version.txt").write_text(
                    "version 1.0, Multilingual Spoken Words Corpus", encoding="utf-8"
                )
                assets.extend(
                    [
                        {
                            "dataset_key": "mswc",
                            "release": "1.0",
                            "asset_id": f"mswc-{language}-metadata-fixture",
                            "asset_role": "split_metadata",
                            "language": language,
                            "download": {"archive_sha256": "2" * 64},
                            "extraction": {"destination": str(metadata_root)},
                        },
                        {
                            "dataset_key": "mswc",
                            "release": "1.0",
                            "asset_id": f"mswc-{language}-audio-fixture",
                            "asset_role": "audio_archive",
                            "language": language,
                            "original_split": "all",
                            "download": {"archive_sha256": "3" * 64},
                            "extraction": {"destination": str(audio_root)},
                        },
                    ]
                )

            acquisition_receipt = root / "receipts/acquisition_fixture.json"
            _write_json(
                acquisition_receipt,
                {
                    "schema_version": "drone.multilingual_acquisition_receipt.v0",
                    "status": "pass",
                    "plan_sha256": sha256_file(PLAN_PATH),
                    "assets": assets,
                    "no_reidentification_performed": True,
                    "redistribution_authorized": False,
                },
            )
            preview = bootstrap_metadata(
                PLAN_PATH, INTAKE_CONFIG, acquisition_receipt, root, execute=False
            )
            self.assertFalse(preview["writes_performed"])
            self.assertFalse((root / "intake").exists())
            with mock.patch.dict(
                os.environ, {"DRONE_W33_DATA_DOWNLOAD_APPROVED": "YES"}, clear=True
            ):
                result = bootstrap_metadata(
                    PLAN_PATH,
                    INTAKE_CONFIG,
                    acquisition_receipt,
                    root,
                    execute=True,
                    fixture_only=True,
                )
                resumed = bootstrap_metadata(
                    PLAN_PATH,
                    INTAKE_CONFIG,
                    acquisition_receipt,
                    root,
                    execute=True,
                    fixture_only=True,
                )
            self.assertEqual(result["metadata_index_entry_count"], 7)
            self.assertTrue(result["no_reidentification_performed"])
            self.assertGreaterEqual(result["gsc"]["duplicate_raw_sha256_clusters"], 1)
            self.assertEqual(result["gsc"]["official_split_counts"], {
                "dev": 3,
                "test": 3,
                "train": 6,
            })
            self.assertTrue(resumed["resumed"])
            index = json.loads(Path(result["metadata_index"]).read_text(encoding="utf-8"))
            self.assertEqual(index["schema_version"], "talk-to-me-drone.metadata-index.v1")
            config = load_json_yaml(INTAKE_CONFIG)
            _, verified_entries = load_metadata_index(Path(result["metadata_index"]), config)
            mswc_source_rows = {
                record.metadata_row
                for entry in verified_entries
                if entry["dataset_key"] == "mswc"
                for record in iter_entry_records(entry)
            }
            self.assertEqual(mswc_source_rows, {3, 4, 5})
            with (root / "intake/gsc_v2_normalized.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                normalized_rows = list(csv.DictReader(handle))
            self.assertEqual(len(normalized_rows), 12)
            self.assertTrue(
                all(row["speaker_id"].startswith("speaker-") for row in normalized_rows)
            )
            for language_receipt in result["mswc"]:
                self.assertEqual(
                    language_receipt["locator_audit_scope"],
                    "current three-class target vocabulary only",
                )
                for split_receipt in language_receipt["splits"].values():
                    self.assertEqual(split_receipt["valid_rows"], 3)
                    self.assertEqual(
                        split_receipt[
                            "valid_non_target_rows_not_materialization_audited"
                        ],
                        1,
                    )
                    self.assertEqual(split_receipt["coverage"], "resolved_target_vocabulary")
                    with Path(split_receipt["path"]).open(
                        "r", encoding="utf-8", newline=""
                    ) as handle:
                        derived_rows = list(csv.DictReader(handle))
                    self.assertEqual(len(derived_rows), 3)
                    self.assertTrue(
                        all(row["SOURCE_METADATA_ROW"] for row in derived_rows)
                    )
                self.assertEqual(language_receipt["quarantine"]["rows"], 0)

    def test_metadata_bootstrap_missing_target_audio_is_quarantined(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata_root = root / "metadata"
            audio_root = root / "audio"
            metadata_root.mkdir(parents=True)
            audio_root.mkdir(parents=True)
            for split in ("train", "dev", "test"):
                family = f"common_voice_es_{split}.opus"
                with (metadata_root / f"{split}.csv").open(
                    "w", encoding="utf-8", newline=""
                ) as handle:
                    writer = csv.DictWriter(
                        handle,
                        fieldnames=("LINK", "WORD", "VALID", "SPEAKER", "GENDER"),
                        lineterminator="\n",
                    )
                    writer.writeheader()
                    writer.writerow(
                        {
                            "LINK": f"alto/{family}",
                            "WORD": "alto",
                            "VALID": "True",
                            "SPEAKER": f"speaker-{split}",
                            "GENDER": "NAN",
                        }
                    )
                if split != "train":
                    _write_wave(
                        audio_root / f"alto_{Path(family).stem}.wav",
                        16000,
                        16000,
                        440.0,
                    )
            assets = [{"extraction": {"destination": str(audio_root)}}]
            result = validate_mswc_metadata_audio(
                "es", metadata_root, assets, root, root / "validated", ("alto",)
            )
            self.assertEqual(result["validated_unique_audio_rows"], 2)
            self.assertEqual(result["quarantine"]["rows"], 1)
            self.assertEqual(
                result["quarantine"]["counts_by_split_word"], {"train:alto": 1}
            )
            with Path(result["quarantine"]["path"]).open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                quarantine_rows = list(csv.DictReader(handle))
            self.assertEqual(
                quarantine_rows[0]["reason"],
                "official_valid_target_row_missing_published_audio",
            )

    def test_end_to_end_36_cell_manifest_is_consumer_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SyntheticBridgeFixture(Path(temporary))
            fixture.build()
            materialized = fixture.materialize()
            result = produce_frozen_manifest(
                materialized["materialization_index"],
                materialized["lineage"],
                fixture.acquisition_receipt,
                materialized["audio_root"],
                fixture.root / "frozen",
                fixture.config_sha,
                sha256_file(fixture.proposal),
                fixture_only=True,
            )
            self.assertEqual(result["record_count"], 36)
            self.assertEqual(len(REQUIRED_FIELDS), 21)
            self.assertTrue(result["consumer_compatibility"]["loaded"])
            self.assertEqual(set(result["support"].values()), {1})
            frozen = load_frozen_manifest(
                result["manifest"],
                result["validation_receipt"],
                selected_languages=LANGUAGES,
                expected_manifest_languages=LANGUAGES,
            )
            self.assertEqual(frozen.full_record_count, 36)
            self.assertEqual({row["split"] for row in frozen.records}, set(SPLITS))
            manifest_rows = [json.loads(line) for line in Path(result["manifest"]).read_text().splitlines()]
            self.assertTrue(all(set(row) == set(REQUIRED_FIELDS) for row in manifest_rows))

    def test_resample_downmix_and_padding_are_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SyntheticBridgeFixture(Path(temporary))
            fixture.build()
            result = fixture.materialize()
            lineage = [json.loads(line) for line in Path(result["lineage"]).read_text().splitlines()]
            english = next(row for row in lineage if row["source_dataset"] == "gsc_v2")
            spanish = next(row for row in lineage if row["source_dataset"] == "mswc" and "es" in row["source_audio_path"])
            self.assertTrue(english["transform"]["resample"]["applied"])
            self.assertEqual(english["transform"]["pad_right"], 8000)
            self.assertEqual(spanish["transform"]["downmix"], "arithmetic_mean_float64")
            self.assertEqual(spanish["transform"]["pad_right"], 8000)

    def test_duplicate_decoded_audio_crossing_splits_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SyntheticBridgeFixture(Path(temporary))
            fixture.build(duplicate_cross_split=True)
            with self.assertRaisesRegex(BridgeError, "duplicate family crosses splits"):
                fixture.materialize()

    def test_full_scale_audio_is_rejected_without_repair(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SyntheticBridgeFixture(Path(temporary))
            fixture.build()
            first = fixture.gsc_root / fixture.rows[0]["source_audio_relpath"]
            samples = np.full((4000,), -32768, dtype="<i2")
            with wave.open(str(first), "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(8000)
                handle.writeframes(samples.tobytes())
            with self.assertRaisesRegex(BridgeError, "full-scale/clipped"):
                fixture.materialize()

    def test_overlength_without_word_boundaries_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SyntheticBridgeFixture(Path(temporary))
            fixture.build()
            first = fixture.gsc_root / fixture.rows[0]["source_audio_relpath"]
            _write_wave(first, 16000, 20000, 321.0)
            with self.assertRaisesRegex(BridgeError, "requires explicit speech/crop boundaries"):
                fixture.materialize()

    def test_proposal_speaker_overlap_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SyntheticBridgeFixture(Path(temporary))
            fixture.build()
            fixture.rows[0]["speaker_id"] = fixture.rows[27]["speaker_id"]
            with fixture.proposal.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=PROPOSAL_REQUIRED_FIELDS, lineterminator="\n")
                writer.writeheader()
                writer.writerows(fixture.rows)
            receipt = json.loads(fixture.proposal_receipt.read_text())
            receipt["proposal_sha256"] = sha256_file(fixture.proposal)
            _write_json(fixture.proposal_receipt, receipt)
            with self.assertRaisesRegex(BridgeError, "speaker crosses proposal splits"):
                load_frozen_proposal(fixture.proposal, fixture.proposal_receipt)

    def test_safe_extract_rejects_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "unsafe.tar"
            with tarfile.open(archive, "w") as handle:
                payload = b"bad"
                info = tarfile.TarInfo("../escape.wav")
                info.size = len(payload)
                handle.addfile(info, io.BytesIO(payload))
            with self.assertRaisesRegex(BridgeError, "unsafe archive member"):
                safe_extract(
                    archive,
                    root / "out",
                    "tar",
                    {"kind": "mswc_wav_shard", "minimum_wav_files": 1},
                )
            self.assertFalse((root / "escape.wav").exists())

    def test_safe_extract_allows_tar_root_directory_member(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "root-member.tar"
            payload = b"safe"
            with tarfile.open(archive, "w") as handle:
                root_info = tarfile.TarInfo("./")
                root_info.type = tarfile.DIRTYPE
                handle.addfile(root_info)
                file_info = tarfile.TarInfo("safe.wav")
                file_info.size = len(payload)
                handle.addfile(file_info, io.BytesIO(payload))

            receipt = safe_extract(
                archive,
                root / "out",
                "tar",
                {"kind": "mswc_wav_shard", "minimum_wav_files": 1},
            )

            self.assertEqual(receipt["tree"]["wav_files"], 1)
            self.assertEqual((root / "out" / "safe.wav").read_bytes(), payload)

    def test_mswc_pinned_shard_has_bounded_absolute_expansion_limit(self) -> None:
        expected = {
            "kind": "mswc_wav_shard",
            "maximum_declared_bytes": 2_000_000_000,
        }
        self.assertEqual(_tar_expansion_limit(237_079_627, expected), 2_000_000_000)
        with self.assertRaisesRegex(BridgeError, "declared-byte exception"):
            _tar_expansion_limit(
                237_079_627,
                {"kind": "mswc_wav_shard", "maximum_declared_bytes": 2_100_000_000},
            )

    def test_mswc_split_metadata_hash_mismatch_fails_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "splits.tar.gz"
            payloads = {
                "train.csv": b"LINK,WORD,VALID,SPEAKER,GENDER\n",
                "dev.csv": b"LINK,WORD,VALID,SPEAKER,GENDER\n",
                "test.csv": b"LINK,WORD,VALID,SPEAKER,GENDER\n",
                "version.txt": b"version 1.0",
            }
            with tarfile.open(archive, "w:gz") as handle:
                for name, payload in payloads.items():
                    info = tarfile.TarInfo(name)
                    info.size = len(payload)
                    handle.addfile(info, io.BytesIO(payload))
            hashes = {name: sha256_bytes(payload) for name, payload in payloads.items()}
            hashes["train.csv"] = "0" * 64
            with self.assertRaisesRegex(BridgeError, "file SHA-256 mismatch"):
                safe_extract(
                    archive,
                    root / "out",
                    "tar",
                    {
                        "kind": "mswc_split_metadata",
                        "required_file_sha256": hashes,
                    },
                )
            self.assertFalse((root / "out").exists())

    def test_download_hash_mismatch_fails_before_rename(self) -> None:
        payload = b"synthetic archive bytes"

        class Response(io.BytesIO):
            status = 200
            headers = {"ETag": "fixture", "Content-Length": str(len(payload))}

            def getcode(self) -> int:
                return self.status

            def geturl(self) -> str:
                return "https://storage.googleapis.com/fixture.tar"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.close()

        with tempfile.TemporaryDirectory() as temporary, mock.patch(
            "urllib.request.urlopen", return_value=Response(payload)
        ):
            asset = {
                "asset_id": "fixture",
                "url": "https://storage.googleapis.com/fixture.tar",
                "filename": "fixture.tar",
                "size_bytes": len(payload),
                "archive_sha256": "0" * 64,
            }
            with self.assertRaisesRegex(BridgeError, "SHA-256 mismatch"):
                _download_stream(asset, Path(temporary))
            self.assertFalse((Path(temporary) / "fixture.tar").exists())

    def test_dry_run_and_dual_execution_guard_do_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "future"
            plan = load_plan(PLAN_PATH)
            result = acquire(PLAN_PATH, root, execute=False)
            self.assertFalse(result["network_performed"])
            self.assertFalse(root.exists())
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(BridgeError, "requires --execute"):
                    acquire(PLAN_PATH, root, execute=True)
            self.assertEqual(result["expected_download_bytes"], 43236696213)
            self.assertEqual(result["direct_archive_count"], 3)
            self.assertEqual(len(plan["sources"]), 2)
            orchestration = run_orchestrator(
                PLAN_PATH,
                INTAKE_CONFIG,
                root,
                "future-v0",
                execute=False,
            )
            self.assertFalse(root.exists())
            self.assertNotIn("proposal", orchestration["inputs"])
            self.assertEqual(
                orchestration["generated_s1_artifacts"]["metadata_index"],
                str(root.resolve() / "intake/metadata_index.json"),
            )

    def test_stage_receipt_resumes_only_matching_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = _run_stage(root, "S0", {"x": "a"}, lambda: {"value": 1})
            second = _run_stage(root, "S0", {"x": "a"}, lambda: {"value": 2})
            self.assertFalse(first["resumed"])
            self.assertTrue(second["resumed"])
            self.assertEqual(second["result"]["value"], 1)
            with self.assertRaisesRegex(BridgeError, "does not match"):
                _run_stage(root, "S0", {"x": "b"}, lambda: {"value": 3})

    def test_executable_s0_does_not_require_preexisting_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
            for source in plan["sources"]:
                for asset in [
                    *source.get("assets", []),
                    *source.get("metadata_assets", []),
                ]:
                    asset["size_bytes"] = 1
                for tree in source.get("trees", []):
                    tree["archive_total_bytes"] = 1
            plan_path = root / "small_plan.json"
            _write_json(plan_path, plan)
            output = root / "future_server_root"
            with mock.patch.dict(
                os.environ, {"DRONE_W33_DATA_DOWNLOAD_APPROVED": "YES"}, clear=True
            ):
                result = run_orchestrator(
                    plan_path,
                    INTAKE_CONFIG,
                    output,
                    "future-v0",
                    stage="S0",
                    execute=True,
                )
            self.assertEqual(result["completed"]["S0"]["status"], "pass")
            self.assertFalse((output / "intake").exists())
            self.assertFalse((output / "intake/metadata_split_proposal.csv").exists())

    def test_proposal_freeze_is_independently_guarded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SyntheticBridgeFixture(Path(temporary))
            fixture.build()
            report_path = fixture.root / "feasibility_report.json"
            _write_json(
                report_path,
                {
                    "schema_version": "talk-to-me-drone.metadata-feasibility-report.v1",
                    "canonical_split_created": False,
                    "model_contract": {
                        "canonical_classes": list(LABELS),
                        "output_count": 3,
                        "source_words_are_model_outputs": False,
                    },
                    "overlap_assertions": {
                        "speaker_overlap_across_proposed_splits": 0,
                        "source_clip_family_overlap_across_proposed_splits": 0,
                        "passed": True,
                    },
                    "hashes": {
                        "proposal_manifest_sha256": sha256_file(fixture.proposal),
                        "config_canonical_sha256": canonical_json_sha256(
                            load_json_yaml(INTAKE_CONFIG)
                        ),
                    },
                },
            )
            output = fixture.root / "frozen_proposal_receipt.json"
            preview = freeze_metadata_proposal(
                INTAKE_CONFIG, fixture.proposal, report_path, output, execute=False
            )
            self.assertTrue(preview["dry_run"])
            self.assertFalse(output.exists())
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(BridgeError, "SPLIT_FREEZE_APPROVED"):
                    freeze_metadata_proposal(
                        INTAKE_CONFIG, fixture.proposal, report_path, output, execute=True
                    )
            with mock.patch.dict(
                os.environ, {"DRONE_W33_SPLIT_FREEZE_APPROVED": "YES"}, clear=True
            ):
                frozen = freeze_metadata_proposal(
                    INTAKE_CONFIG, fixture.proposal, report_path, output, execute=True
                )
            self.assertTrue(frozen["receipt_written"])
            rows, receipt = load_frozen_proposal(fixture.proposal, output)
            self.assertEqual(len(rows), 36)
            self.assertTrue(receipt["frozen"])

    def test_deterministic_manifest_hash(self) -> None:
        hashes = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as temporary:
                fixture = SyntheticBridgeFixture(Path(temporary))
                fixture.build()
                materialized = fixture.materialize()
                frozen = produce_frozen_manifest(
                    materialized["materialization_index"],
                    materialized["lineage"],
                    fixture.acquisition_receipt,
                    materialized["audio_root"],
                    fixture.root / "frozen",
                    fixture.config_sha,
                    sha256_file(fixture.proposal),
                    fixture_only=True,
                )
                hashes.append(frozen["manifest_sha256"])
        self.assertEqual(hashes[0], hashes[1])


if __name__ == "__main__":
    unittest.main()
