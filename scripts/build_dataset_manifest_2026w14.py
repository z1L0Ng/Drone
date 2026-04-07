#!/usr/bin/env python3

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

AUDIO_EXTS = {".wav", ".flac", ".mp3", ".m4a", ".ogg"}

DEFAULT_SOURCES = {
    "esd": {
        "dataset_name": "ESD",
        "official_url": "https://github.com/HLTSingapore/Emotional-Speech-Data",
        "source_url": "https://www.sciencedirect.com/science/article/pii/S0167639321001308",
        "license_type": "Research-use license form (NUS/SUTD ESD agreement)",
        "academic_usable": "yes",
        "commercial_usable": "no",
        "languages": "english,mandarin",
        "sampling_rate": "unknown_public_page",
        "duration_range_sec": "unknown_public_page",
        "noise_condition": "controlled studio",
        "risks": "license_restriction; label_mapping_gap(no_fear); acted_speech_domain_shift",
        "estimated_counts": {
            "english": {
                "neutral": 3500,
                "anger": 3500,
                "fear": 0,
                "surprise": 3500,
                "calm": 0,
            }
        },
        "estimated_notes": "Derived from 350 sentences x 10 English speakers x 5 emotions",
    },
    "crema_d": {
        "dataset_name": "CREMA-D",
        "official_url": "https://audeering.github.io/datasets/datasets/crema-d.html",
        "source_url": "https://audeering.github.io/datasets/datasets/crema-d.html",
        "license_type": "ODbL v1.0",
        "academic_usable": "yes",
        "commercial_usable": "yes",
        "languages": "english",
        "sampling_rate": "16000",
        "duration_range_sec": "1.3-5.0",
        "noise_condition": "recorded acted speech; low environmental noise",
        "risks": "acted_speech_domain_shift; per_emotion_count_unknown_without_local_scan",
        "estimated_counts": {
            "english": {
                "neutral": 1240,
                "anger": 1240,
                "fear": 1240,
                "surprise": 0,
                "calm": 0,
            }
        },
        "estimated_notes": "Approx uniform split from 7441 files over 6 emotions",
    },
}

GENERIC_TOKEN_MAP = {
    "anger": "anger",
    "angry": "anger",
    "fear": "fear",
    "fearful": "fear",
    "surprise": "surprise",
    "surprised": "surprise",
    "neutral": "neutral",
    "calm": "calm",
    "neu": "neutral",
}

CREMA_CODE_MAP = {
    "ANG": "anger",
    "FEA": "fear",
    "NEU": "neutral",
    "DIS": "disgust",
    "HAP": "happy",
    "SAD": "sad",
}


@dataclass
class MappingVariant:
    name: str
    include_surprise: bool
    emergency_candidates: List[str]
    normal_candidates: List[str]
    excluded_labels: List[str]
    notes: str


VARIANTS = [
    MappingVariant(
        name="surprise_included",
        include_surprise=True,
        emergency_candidates=["anger", "fear", "surprise"],
        normal_candidates=["neutral", "calm"],
        excluded_labels=["happy", "sad", "disgust", "frustration", "other"],
        notes="Sensitivity mapping with surprise included.",
    ),
    MappingVariant(
        name="surprise_excluded",
        include_surprise=False,
        emergency_candidates=["anger", "fear"],
        normal_candidates=["neutral", "calm"],
        excluded_labels=["happy", "sad", "disgust", "frustration", "surprise", "other"],
        notes="Default mapping for main analysis.",
    ),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", required=True)
    p.add_argument("--phase", default="phase1_en")
    p.add_argument("--download-root", required=True)
    p.add_argument("--datasets", default="esd,crema_d")
    return p.parse_args()


def _join(labels: List[str]) -> str:
    return "|".join(labels)


def _effective_labels(label_counts: Dict[str, int], candidates: List[str]) -> List[str]:
    return [lbl for lbl in candidates if int(label_counts.get(lbl, 0)) > 0]


def _compute_counts(label_counts: Dict[str, int], variant: MappingVariant) -> Tuple[List[str], List[str], Dict[str, int]]:
    em_labels = _effective_labels(label_counts, variant.emergency_candidates)
    no_labels = _effective_labels(label_counts, variant.normal_candidates)
    em = sum(int(label_counts.get(lbl, 0)) for lbl in em_labels)
    no = sum(int(label_counts.get(lbl, 0)) for lbl in no_labels)
    return em_labels, no_labels, {"emergency": em, "normal": no, "usable_total": em + no}


def _detect_label_esd(path: Path) -> List[str]:
    tokens = [t for t in re.split(r"[^a-z0-9]+", path.as_posix().lower()) if t]
    found = set()
    for t in tokens:
        mapped = GENERIC_TOKEN_MAP.get(t)
        if mapped:
            found.add(mapped)
    return sorted(found)


def _detect_label_cremad(path: Path) -> List[str]:
    m = re.search(r"_(ANG|FEA|NEU|DIS|HAP|SAD)_", path.name.upper())
    if not m:
        return []
    lbl = CREMA_CODE_MAP.get(m.group(1))
    return [lbl] if lbl else []


def _detect_labels(path: Path, dataset_key: str) -> List[str]:
    if dataset_key == "crema_d":
        labels = _detect_label_cremad(path)
        if labels:
            return labels
    if dataset_key == "esd":
        labels = _detect_label_esd(path)
        if labels:
            return labels

    tokens = [t for t in re.split(r"[^a-z0-9]+", path.as_posix().lower()) if t]
    found = set()
    for t in tokens:
        mapped = GENERIC_TOKEN_MAP.get(t)
        if mapped:
            found.add(mapped)
    return sorted(found)


def _scan_audio_counts(dataset_root: Path, dataset_key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {
        "neutral": 0,
        "calm": 0,
        "anger": 0,
        "fear": 0,
        "surprise": 0,
        "happy": 0,
        "sad": 0,
        "disgust": 0,
    }
    scanned = 0
    detected = 0
    unmapped = 0

    if not dataset_root.exists():
        return {**counts, "_scanned_files": 0, "_detected_files": 0, "_unmapped_files": 0}

    for p in dataset_root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in AUDIO_EXTS:
            continue
        scanned += 1
        labels = _detect_labels(p, dataset_key)
        if len(labels) == 1:
            counts[labels[0]] = counts.get(labels[0], 0) + 1
            detected += 1
        else:
            unmapped += 1

    counts["_scanned_files"] = scanned
    counts["_detected_files"] = detected
    counts["_unmapped_files"] = unmapped
    return counts


def _write_csv(path: Path, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = [d.strip() for d in args.datasets.split(",") if d.strip()]
    unknown = [d for d in selected if d not in DEFAULT_SOURCES]
    if unknown:
        raise ValueError(f"Unsupported datasets: {unknown}")

    download_root = Path(args.download_root).resolve()
    isolation_tag = "acoustic_2026w14_phase1"

    manifest_rows: List[Dict[str, object]] = []
    mapping_rows: List[Dict[str, object]] = []
    sample_rows: List[Dict[str, object]] = []

    combined = {
        "estimated": {v.name: {"emergency": 0, "normal": 0, "usable_total": 0} for v in VARIANTS},
        "scanned": {v.name: {"emergency": 0, "normal": 0, "usable_total": 0} for v in VARIANTS},
    }

    for ds_key in selected:
        meta = DEFAULT_SOURCES[ds_key]
        estimated_counts = meta["estimated_counts"].get("english", {})
        scanned_full = _scan_audio_counts(download_root / "raw" / ds_key, ds_key)
        scanned_counts = {k: v for k, v in scanned_full.items() if not k.startswith("_")}

        # default manifest mapping: main analysis without surprise
        default_variant = next(v for v in VARIANTS if v.name == "surprise_excluded")
        em_labels_def, no_labels_def, c_def = _compute_counts(estimated_counts, default_variant)

        manifest_rows.append(
            {
                "phase": args.phase,
                "dataset_name": meta["dataset_name"],
                "official_url": meta["official_url"],
                "license_type": meta["license_type"],
                "academic_usable": meta["academic_usable"],
                "commercial_usable": meta["commercial_usable"],
                "languages": meta["languages"],
                "label_mapping_emergency": _join(em_labels_def),
                "label_mapping_normal": _join(no_labels_def),
                "estimated_samples_by_language": json.dumps({"english": estimated_counts}, ensure_ascii=True),
                "estimated_samples_emergency": c_def["emergency"],
                "estimated_samples_normal": c_def["normal"],
                "count_type": "estimated",
                "sampling_rate": meta["sampling_rate"],
                "duration_range_sec": meta["duration_range_sec"],
                "noise_condition": meta["noise_condition"],
                "local_storage_root": str(download_root / "raw" / ds_key),
                "data_isolation_tag": isolation_tag,
                "risks": meta["risks"],
                "source_url": meta["source_url"],
                "source_date": "2026-04-07",
            }
        )

        for count_source, label_counts, count_type, count_notes in [
            ("estimated", estimated_counts, "estimated", meta["estimated_notes"]),
            (
                "scanned",
                scanned_counts,
                "exact_scan" if scanned_full["_scanned_files"] > 0 else "exact_scan_empty",
                f"Scanned files={scanned_full['_scanned_files']}, detected={scanned_full['_detected_files']}, unmapped={scanned_full['_unmapped_files']}",
            ),
        ]:
            for variant in VARIANTS:
                em_labels, no_labels, c = _compute_counts(label_counts, variant)

                mapping_rows.append(
                    {
                        "phase": args.phase,
                        "dataset_name": meta["dataset_name"],
                        "count_source": count_source,
                        "mapping_variant": variant.name,
                        "language_scope": "english",
                        "emergency_labels": _join(em_labels),
                        "normal_labels": _join(no_labels),
                        "excluded_labels": _join(variant.excluded_labels),
                        "mapping_notes": variant.notes,
                        "source_url": meta["source_url"],
                    }
                )

                sample_rows.append(
                    {
                        "phase": args.phase,
                        "dataset_name": meta["dataset_name"],
                        "count_source": count_source,
                        "mapping_variant": variant.name,
                        "include_surprise": "yes" if variant.include_surprise else "no",
                        "language": "english",
                        "emergency_labels": _join(em_labels),
                        "normal_labels": _join(no_labels),
                        "emergency_count": c["emergency"],
                        "normal_count": c["normal"],
                        "usable_total": c["usable_total"],
                        "audio_files_scanned": scanned_full["_scanned_files"] if count_source == "scanned" else "",
                        "label_detected_files": scanned_full["_detected_files"] if count_source == "scanned" else "",
                        "unmapped_files": scanned_full["_unmapped_files"] if count_source == "scanned" else "",
                        "count_type": count_type,
                        "count_notes": count_notes,
                        "source_url": meta["source_url"],
                    }
                )

                combined[count_source][variant.name]["emergency"] += c["emergency"]
                combined[count_source][variant.name]["normal"] += c["normal"]
                combined[count_source][variant.name]["usable_total"] += c["usable_total"]

    for count_source in ["estimated", "scanned"]:
        for variant in VARIANTS:
            cc = combined[count_source][variant.name]
            sample_rows.append(
                {
                    "phase": args.phase,
                    "dataset_name": "COMBINED_ESD_CREMA-D",
                    "count_source": count_source,
                    "mapping_variant": variant.name,
                    "include_surprise": "yes" if variant.include_surprise else "no",
                    "language": "english",
                    "emergency_labels": _join(variant.emergency_candidates),
                    "normal_labels": _join(variant.normal_candidates),
                    "emergency_count": cc["emergency"],
                    "normal_count": cc["normal"],
                    "usable_total": cc["usable_total"],
                    "audio_files_scanned": "",
                    "label_detected_files": "",
                    "unmapped_files": "",
                    "count_type": "estimated" if count_source == "estimated" else "exact_scan",
                    "count_notes": "Aggregated from dataset rows",
                    "source_url": "https://github.com/HLTSingapore/Emotional-Speech-Data|https://audeering.github.io/datasets/datasets/crema-d.html",
                }
            )

    manifest_path = out_dir / "dataset_manifest_2026w14.csv"
    mapping_path = out_dir / "label_mapping_table_2026w14.csv"
    sample_path = out_dir / "sample_count_table_2026w14.csv"
    risk_path = out_dir / "risk_and_limitations_2026w14.md"

    _write_csv(
        manifest_path,
        manifest_rows,
        [
            "phase",
            "dataset_name",
            "official_url",
            "license_type",
            "academic_usable",
            "commercial_usable",
            "languages",
            "label_mapping_emergency",
            "label_mapping_normal",
            "estimated_samples_by_language",
            "estimated_samples_emergency",
            "estimated_samples_normal",
            "count_type",
            "sampling_rate",
            "duration_range_sec",
            "noise_condition",
            "local_storage_root",
            "data_isolation_tag",
            "risks",
            "source_url",
            "source_date",
        ],
    )

    _write_csv(
        mapping_path,
        mapping_rows,
        [
            "phase",
            "dataset_name",
            "count_source",
            "mapping_variant",
            "language_scope",
            "emergency_labels",
            "normal_labels",
            "excluded_labels",
            "mapping_notes",
            "source_url",
        ],
    )

    _write_csv(
        sample_path,
        sample_rows,
        [
            "phase",
            "dataset_name",
            "count_source",
            "mapping_variant",
            "include_surprise",
            "language",
            "emergency_labels",
            "normal_labels",
            "emergency_count",
            "normal_count",
            "usable_total",
            "audio_files_scanned",
            "label_detected_files",
            "unmapped_files",
            "count_type",
            "count_notes",
            "source_url",
        ],
    )

    risk_path.write_text(
        """# Risk And Limitations (2026W14 Phase1)

## Speaker Risks
- ESD and CREMA-D are acted corpora; urgency expression may be exaggerated compared to real emergency calls.
- Speaker style concentration can bias prosodic thresholds.

## License Risks
- ESD requires research-use license agreement; not suitable for commercial redistribution.
- CREMA-D (ODbL) supports commercial use with attribution/database-share obligations.

## Domain Shift Risks
- Scripted utterances differ from spontaneous operational speech.
- Current scan in isolated download root may be empty until licensed assets are copied there.

## Mapping Risks
- Default main analysis excludes surprise; surprise is sensitivity-only appendix.
- Fear labels are removed per-dataset when absent (e.g., ESD).
""",
        encoding="utf-8",
    )

    print(f"Saved: {manifest_path}")
    print(f"Saved: {mapping_path}")
    print(f"Saved: {sample_path}")
    print(f"Saved: {risk_path}")


if __name__ == "__main__":
    main()
