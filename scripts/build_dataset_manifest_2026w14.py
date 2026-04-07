#!/usr/bin/env python3

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


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
        "counts": {
            "english": {
                "neutral": 3500,
                "anger": 3500,
                "fear": 0,
                "surprise": 3500,
                "calm": 0,
            }
        },
        "count_type": "estimated",
        "count_notes": "Derived from 350 sentences x 10 English speakers x 5 emotions",
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
        "counts": {
            "english": {
                "neutral": 1240,
                "anger": 1240,
                "fear": 1240,
                "surprise": 0,
                "calm": 0,
            }
        },
        "count_type": "estimated",
        "count_notes": "Approx uniform split from 7441 files over 6 emotions",
    },
}


@dataclass
class MappingVariant:
    name: str
    include_surprise: bool
    emergency_labels: List[str]
    normal_labels: List[str]
    excluded_labels: List[str]
    notes: str


VARIANTS = [
    MappingVariant(
        name="surprise_included",
        include_surprise=True,
        emergency_labels=["anger", "fear", "surprise"],
        normal_labels=["neutral", "calm"],
        excluded_labels=["happy", "sad", "disgust", "frustration", "other"],
        notes="Primary phase-1 mapping for emergency sensitivity.",
    ),
    MappingVariant(
        name="surprise_excluded",
        include_surprise=False,
        emergency_labels=["anger", "fear"],
        normal_labels=["neutral", "calm"],
        excluded_labels=["happy", "sad", "disgust", "frustration", "surprise", "other"],
        notes="Conservative mapping to reduce ambiguity from surprise.",
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


def _compute_counts(label_counts: Dict[str, int], variant: MappingVariant) -> Dict[str, int]:
    em = sum(label_counts.get(lbl, 0) for lbl in variant.emergency_labels)
    no = sum(label_counts.get(lbl, 0) for lbl in variant.normal_labels)
    return {"emergency": int(em), "normal": int(no), "usable_total": int(em + no)}


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

    combined_by_variant = {v.name: {"emergency": 0, "normal": 0, "usable_total": 0} for v in VARIANTS}

    for ds_key in selected:
        meta = DEFAULT_SOURCES[ds_key]
        en_counts = meta["counts"].get("english", {})

        for variant in VARIANTS:
            c = _compute_counts(en_counts, variant)
            combined_by_variant[variant.name]["emergency"] += c["emergency"]
            combined_by_variant[variant.name]["normal"] += c["normal"]
            combined_by_variant[variant.name]["usable_total"] += c["usable_total"]

            mapping_rows.append(
                {
                    "phase": args.phase,
                    "dataset_name": meta["dataset_name"],
                    "mapping_variant": variant.name,
                    "language_scope": "english",
                    "emergency_labels": _join(variant.emergency_labels),
                    "normal_labels": _join(variant.normal_labels),
                    "excluded_labels": _join(variant.excluded_labels),
                    "mapping_notes": variant.notes,
                    "source_url": meta["source_url"],
                }
            )

            sample_rows.append(
                {
                    "phase": args.phase,
                    "dataset_name": meta["dataset_name"],
                    "mapping_variant": variant.name,
                    "include_surprise": "yes" if variant.include_surprise else "no",
                    "language": "english",
                    "emergency_labels": _join(variant.emergency_labels),
                    "normal_labels": _join(variant.normal_labels),
                    "emergency_count": c["emergency"],
                    "normal_count": c["normal"],
                    "usable_total": c["usable_total"],
                    "count_type": meta["count_type"],
                    "count_notes": meta["count_notes"],
                    "source_url": meta["source_url"],
                }
            )

        primary = next(v for v in VARIANTS if v.name == "surprise_included")
        primary_counts = _compute_counts(en_counts, primary)
        manifest_rows.append(
            {
                "phase": args.phase,
                "dataset_name": meta["dataset_name"],
                "official_url": meta["official_url"],
                "license_type": meta["license_type"],
                "academic_usable": meta["academic_usable"],
                "commercial_usable": meta["commercial_usable"],
                "languages": meta["languages"],
                "label_mapping_emergency": _join(primary.emergency_labels),
                "label_mapping_normal": _join(primary.normal_labels),
                "estimated_samples_by_language": json.dumps({"english": en_counts}, ensure_ascii=True),
                "estimated_samples_emergency": primary_counts["emergency"],
                "estimated_samples_normal": primary_counts["normal"],
                "count_type": meta["count_type"],
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

    for variant in VARIANTS:
        cc = combined_by_variant[variant.name]
        sample_rows.append(
            {
                "phase": args.phase,
                "dataset_name": "COMBINED_ESD_CREMA-D",
                "mapping_variant": variant.name,
                "include_surprise": "yes" if variant.include_surprise else "no",
                "language": "english",
                "emergency_labels": _join(variant.emergency_labels),
                "normal_labels": _join(variant.normal_labels),
                "emergency_count": cc["emergency"],
                "normal_count": cc["normal"],
                "usable_total": cc["usable_total"],
                "count_type": "estimated",
                "count_notes": "Dataset-level estimates aggregated",
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
            "mapping_variant",
            "include_surprise",
            "language",
            "emergency_labels",
            "normal_labels",
            "emergency_count",
            "normal_count",
            "usable_total",
            "count_type",
            "count_notes",
            "source_url",
        ],
    )

    risk_path.write_text(
        """# Risk And Limitations (2026W14 Phase1)

## Speaker Risks
- ESD and CREMA-D are acted corpora; urgency expression may be exaggerated compared to real emergency calls.
- Speaker overlap and style homogeneity can bias pitch and energy envelopes.

## License Risks
- ESD requires research-use license agreement; not suitable for commercial redistribution.
- CREMA-D (ODbL) supports commercial use but requires attribution/share obligations for database derivatives.

## Domain Shift Risks
- Scripted utterances differ from spontaneous command/control speech in real deployments.
- Environment mismatch: both corpora are mostly clean recordings, unlike noisy operational audio.

## Mapping Risks
- ESD has no explicit fear class; emergency mapping relies on anger (+ surprise in included variant).
- Surprise can be non-urgent in some contexts; include/exclude dual counting is provided for sensitivity analysis.
""",
        encoding="utf-8",
    )

    print(f"Saved: {manifest_path}")
    print(f"Saved: {mapping_path}")
    print(f"Saved: {sample_path}")
    print(f"Saved: {risk_path}")


if __name__ == "__main__":
    main()
