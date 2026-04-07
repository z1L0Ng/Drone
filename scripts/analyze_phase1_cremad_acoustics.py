#!/usr/bin/env python3

import argparse
import csv
import datetime as dt
import math
import os
from pathlib import Path
from typing import Dict, List, Tuple

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp")

import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
from scipy import signal

SR = 16000
N_FFT = 1024
HOP = 256
TARGET_POINTS = 120
CREMA_CODES = {"ANG", "FEA", "NEU", "DIS", "HAP", "SAD"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input-root", default="/tmp/drone_acoustic_2026w14_phase1_downloads/raw/crema_d")
    p.add_argument("--output-root", default="analysis/cross_language_emergency")
    p.add_argument("--max-files", type=int, default=0, help="0 means all files")
    return p.parse_args()


def parse_crema_code(path: Path) -> str:
    parts = path.stem.split("_")
    if len(parts) < 3:
        return ""
    code = parts[2].upper()
    return code if code in CREMA_CODES else ""


def list_audio_files(root: Path) -> List[Path]:
    return sorted([p for p in root.rglob("*.wav") if p.is_file()])


def to_mono_16k(path: Path) -> np.ndarray:
    y, sr = sf.read(str(path), always_2d=False)
    y = y.astype(np.float32)
    if y.ndim == 2:
        y = np.mean(y, axis=1)
    if sr != SR:
        g = math.gcd(sr, SR)
        up = SR // g
        down = sr // g
        y = signal.resample_poly(y, up=up, down=down).astype(np.float32)
    if y.size == 0:
        raise ValueError("empty audio")
    return y


def resample_curve(curve: np.ndarray, target_points: int = TARGET_POINTS) -> np.ndarray:
    if curve.size == 0:
        return np.zeros(target_points, dtype=np.float32)
    if curve.size == 1:
        return np.full(target_points, float(curve[0]), dtype=np.float32)
    x_old = np.linspace(0.0, 1.0, num=curve.size, dtype=np.float32)
    x_new = np.linspace(0.0, 1.0, num=target_points, dtype=np.float32)
    return np.interp(x_new, x_old, curve).astype(np.float32)


def frame_signal(y: np.ndarray, frame_len: int = N_FFT, hop: int = HOP) -> np.ndarray:
    if y.size < frame_len:
        y = np.pad(y, (0, frame_len - y.size))
    n_frames = 1 + (y.size - frame_len) // hop
    frames = np.zeros((n_frames, frame_len), dtype=np.float32)
    for i in range(n_frames):
        st = i * hop
        frames[i] = y[st : st + frame_len]
    return frames


def track_pitch_autocorr(y: np.ndarray, fmin: float = 65.0, fmax: float = 500.0) -> np.ndarray:
    frames = frame_signal(y)
    win = np.hanning(N_FFT).astype(np.float32)
    min_lag = max(1, int(SR / fmax))
    max_lag = min(N_FFT - 1, int(SR / fmin))

    out = np.full(frames.shape[0], np.nan, dtype=np.float32)
    for i, fr in enumerate(frames):
        x = (fr - np.mean(fr)) * win
        ac = signal.correlate(x, x, mode="full", method="fft")[N_FFT - 1 :]
        if ac[0] <= 1e-8:
            continue
        seg = ac[min_lag : max_lag + 1]
        if seg.size == 0:
            continue
        lag = int(np.argmax(seg) + min_lag)
        peak = ac[lag]
        if peak < 0.3 * ac[0]:
            continue
        out[i] = float(SR / lag)

    finite = np.isfinite(out)
    if not finite.any():
        return np.zeros_like(out)
    idx = np.arange(out.size)
    out[~finite] = np.interp(idx[~finite], idx[finite], out[finite]).astype(np.float32)
    return out


def extract_features(path: Path) -> Dict[str, np.ndarray]:
    y = to_mono_16k(path)

    f, _, Zxx = signal.stft(
        y,
        fs=SR,
        window="hann",
        nperseg=N_FFT,
        noverlap=N_FFT - HOP,
        nfft=N_FFT,
        boundary=None,
        padded=False,
    )
    power = (np.abs(Zxx) ** 2).astype(np.float32)
    if power.size == 0:
        raise ValueError("stft empty")

    def band_sum(f_lo: float, f_hi: float) -> float:
        mask = (f >= f_lo) & (f < f_hi)
        if not np.any(mask):
            return 0.0
        return float(np.sum(power[mask, :]))

    total = float(np.sum(power) + 1e-12)
    low_ref = band_sum(50.0, 1000.0)
    hi_band = band_sum(1000.0, 5000.0)
    alpha_ratio = hi_band / (low_ref + 1e-12)

    psum = np.sum(power, axis=0) + 1e-12
    centroid_frames = np.sum((f[:, None] * power), axis=0) / psum
    bandwidth_frames = np.sqrt(np.sum(((f[:, None] - centroid_frames[None, :]) ** 2) * power, axis=0) / psum)

    centroid = float(np.mean(centroid_frames))
    bandwidth = float(np.mean(bandwidth_frames))

    low_prop = band_sum(0.0, 500.0) / total
    mid_prop = band_sum(500.0, 2000.0) / total
    high_prop = band_sum(2000.0, 8000.0) / total

    frames = frame_signal(y)
    rms = np.sqrt(np.mean(np.square(frames), axis=1) + 1e-12)
    rms_norm = rms / (float(np.max(rms)) + 1e-12)
    energy_curve = resample_curve(rms_norm)

    f0 = track_pitch_autocorr(y)
    pitch_curve = resample_curve(f0)

    return {
        "alpha_ratio": np.array(alpha_ratio, dtype=np.float32),
        "centroid": np.array(centroid, dtype=np.float32),
        "bandwidth": np.array(bandwidth, dtype=np.float32),
        "low_prop": np.array(low_prop, dtype=np.float32),
        "mid_prop": np.array(mid_prop, dtype=np.float32),
        "high_prop": np.array(high_prop, dtype=np.float32),
        "pitch_curve": pitch_curve,
        "energy_curve": energy_curve,
    }


def make_group_arrays(rows: List[Dict[str, np.ndarray]]) -> Dict[str, np.ndarray]:
    keys = ["alpha_ratio", "centroid", "bandwidth", "low_prop", "mid_prop", "high_prop"]
    out: Dict[str, np.ndarray] = {}
    for k in keys:
        out[k] = np.array([float(r[k]) for r in rows], dtype=np.float32)
    out["pitch_curve"] = np.stack([r["pitch_curve"] for r in rows], axis=0) if rows else np.zeros((0, TARGET_POINTS), dtype=np.float32)
    out["energy_curve"] = np.stack([r["energy_curve"] for r in rows], axis=0) if rows else np.zeros((0, TARGET_POINTS), dtype=np.float32)
    return out


def safe_mean(arr: np.ndarray) -> float:
    return float(np.mean(arr)) if arr.size > 0 else 0.0


def cohen_d(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 2 or b.size < 2:
        return 0.0
    va = float(np.var(a, ddof=1))
    vb = float(np.var(b, ddof=1))
    pooled = ((a.size - 1) * va + (b.size - 1) * vb) / float((a.size - 1) + (b.size - 1))
    if pooled <= 0:
        return 0.0
    return (safe_mean(a) - safe_mean(b)) / math.sqrt(pooled)


def plot_alpha_ratio(path: Path, em: np.ndarray, no: np.ndarray) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot([em, no], tick_labels=["emergency", "normal"], showfliers=False)
    ax.set_title("Alpha Ratio (1000-5000Hz / 50-1000Hz)")
    ax.set_ylabel("ratio")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_centroid_bandwidth(path: Path, em_c: np.ndarray, no_c: np.ndarray, em_b: np.ndarray, no_b: np.ndarray) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].boxplot([em_c, no_c], tick_labels=["emergency", "normal"], showfliers=False)
    axes[0].set_title("Spectral Centroid")
    axes[0].set_ylabel("Hz")
    axes[0].grid(alpha=0.25)

    axes[1].boxplot([em_b, no_b], tick_labels=["emergency", "normal"], showfliers=False)
    axes[1].set_title("Spectral Bandwidth")
    axes[1].set_ylabel("Hz")
    axes[1].grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_energy_distribution(path: Path, em_low: np.ndarray, em_mid: np.ndarray, em_high: np.ndarray, no_low: np.ndarray, no_mid: np.ndarray, no_high: np.ndarray) -> None:
    labels = ["low(0-500)", "mid(500-2000)", "high(2000-8000)"]
    em_means = [safe_mean(em_low), safe_mean(em_mid), safe_mean(em_high)]
    no_means = [safe_mean(no_low), safe_mean(no_mid), safe_mean(no_high)]

    x = np.arange(len(labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width / 2, em_means, width=width, label="emergency")
    ax.bar(x + width / 2, no_means, width=width, label="normal")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("energy proportion")
    ax.set_title("Frequency-band Energy Distribution")
    ax.set_ylim(0.0, max(0.6, max(em_means + no_means) * 1.2))
    ax.grid(axis="y", alpha=0.25)
    ax.legend()

    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_pitch_energy(path: Path, em_pitch: np.ndarray, no_pitch: np.ndarray, em_energy: np.ndarray, no_energy: np.ndarray) -> None:
    x = np.linspace(0.0, 1.0, TARGET_POINTS)

    def mean_std(curves: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if curves.size == 0:
            return np.zeros(TARGET_POINTS, dtype=np.float32), np.zeros(TARGET_POINTS, dtype=np.float32)
        return np.mean(curves, axis=0), np.std(curves, axis=0)

    emp_m, emp_s = mean_std(em_pitch)
    nop_m, nop_s = mean_std(no_pitch)
    eme_m, eme_s = mean_std(em_energy)
    noe_m, noe_s = mean_std(no_energy)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].plot(x, emp_m, label="emergency")
    axes[0].fill_between(x, emp_m - emp_s, emp_m + emp_s, alpha=0.2)
    axes[0].plot(x, nop_m, label="normal")
    axes[0].fill_between(x, nop_m - nop_s, nop_m + nop_s, alpha=0.2)
    axes[0].set_title("Pitch Envelope (autocorr)")
    axes[0].set_xlabel("normalized time")
    axes[0].set_ylabel("Hz")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    axes[1].plot(x, eme_m, label="emergency")
    axes[1].fill_between(x, eme_m - eme_s, eme_m + eme_s, alpha=0.2)
    axes[1].plot(x, noe_m, label="normal")
    axes[1].fill_between(x, noe_m - noe_s, noe_m + noe_s, alpha=0.2)
    axes[1].set_title("Energy Envelope (RMS, normalized)")
    axes[1].set_xlabel("normalized time")
    axes[1].set_ylabel("relative energy")
    axes[1].grid(alpha=0.25)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_findings_main(path: Path, stats: Dict[str, Dict[str, float]], counts: Dict[str, int], code_counts: Dict[str, int]) -> None:
    lines = [
        "# Findings Phase1 (CREMA-D, Main Mapping: surprise_excluded)",
        "",
        f"- Generated at: {dt.datetime.now().isoformat(timespec='seconds')}",
        "- Mapping: emergency=anger+fear; normal=neutral (+ calm if present)",
        f"- Sample counts: emergency={counts['emergency']}, normal={counts['normal']}, total={counts['total']}",
        f"- Code counts used: ANG={code_counts.get('ANG',0)}, FEA={code_counts.get('FEA',0)}, NEU={code_counts.get('NEU',0)}, CAL={code_counts.get('CAL',0)}",
        "",
        "## Metric Summary",
        "",
        "| metric | emergency_mean | normal_mean | delta(em-normal) | cohen_d |",
        "|---|---:|---:|---:|---:|",
    ]

    for key, label in [
        ("alpha_ratio", "alpha_ratio"),
        ("centroid", "spectral_centroid_hz"),
        ("bandwidth", "spectral_bandwidth_hz"),
        ("low_prop", "energy_low_prop"),
        ("mid_prop", "energy_mid_prop"),
        ("high_prop", "energy_high_prop"),
    ]:
        em = stats["emergency"][f"{key}_mean"]
        no = stats["normal"][f"{key}_mean"]
        delta = em - no
        d = stats["diff"][f"{key}_cohen_d"]
        lines.append(f"| {label} | {em:.4f} | {no:.4f} | {delta:.4f} | {d:.4f} |")

    lines += [
        "",
        "## Main Takeaways",
        "",
        "- Compare four figures jointly; no single acoustic feature should be over-interpreted.",
        "- This is evidence for class-level acoustic separability, not full model performance.",
    ]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_findings_sensitivity(path: Path, main_counts: Dict[str, int], sens_counts: Dict[str, int], surprise_count: int) -> None:
    lines = [
        "# Findings Phase1 Sensitivity (surprise_included)",
        "",
        f"- Generated at: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"- Main mapping counts: emergency={main_counts['emergency']}, normal={main_counts['normal']}, total={main_counts['total']}",
        f"- Sensitivity mapping counts: emergency={sens_counts['emergency']}, normal={sens_counts['normal']}, total={sens_counts['total']}",
        f"- Surprise files detected in CREMA-D scan: {surprise_count}",
        "",
        "## Sensitivity Result",
        "",
    ]

    if surprise_count == 0:
        lines += [
            "- No surprise class in scanned CREMA-D, so sensitivity mapping is numerically identical to mainline.",
            "- Main conclusions remain unchanged.",
        ]
    else:
        lines += [
            "- Surprise files are present; compare appendix metrics before final meeting claims.",
            "- Keep `surprise_excluded` as default mainline policy.",
        ]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(path: Path, counts: Dict[str, int], surprise_count: int, stats: Dict[str, Dict[str, float]]) -> None:
    lines = [
        "# Summary 2026W14 Phase1 (CREMA-D Acoustic Evidence)",
        "",
        "## Main Conclusion",
        f"- Mainline (`surprise_excluded`) sample counts: emergency={counts['emergency']}, normal={counts['normal']}.",
        f"- Alpha ratio delta (em-normal): {stats['emergency']['alpha_ratio_mean'] - stats['normal']['alpha_ratio_mean']:.4f}.",
        f"- Spectral centroid delta (em-normal, Hz): {stats['emergency']['centroid_mean'] - stats['normal']['centroid_mean']:.2f}.",
        "",
        "## Sensitivity Change",
        f"- Surprise detected in CREMA-D: {surprise_count}.",
        "- `surprise_included` kept as appendix-only policy.",
        "",
        "## Risks",
        "- Acted studio speech may not match real emergency acoustics.",
        "- ESD still not staged, so multilingual evidence is pending.",
        "",
        "## Expansion Decision",
        "- Continue with multilingual expansion after ESD ingestion; current CREMA-D evidence is meeting-ready for phase1.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_feature_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    fieldnames = [
        "path",
        "code",
        "main_class",
        "sensitivity_class",
        "alpha_ratio",
        "centroid",
        "bandwidth",
        "low_prop",
        "mid_prop",
        "high_prop",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    args = parse_args()
    in_root = Path(args.input_root)
    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)

    files = list_audio_files(in_root)
    if args.max_files > 0:
        files = files[: args.max_files]

    main_map = {"ANG": "emergency", "FEA": "emergency", "NEU": "normal", "CAL": "normal"}
    sens_map = {"ANG": "emergency", "FEA": "emergency", "SUR": "emergency", "NEU": "normal", "CAL": "normal"}

    main_groups: Dict[str, List[Dict[str, np.ndarray]]] = {"emergency": [], "normal": []}
    sens_groups: Dict[str, List[Dict[str, np.ndarray]]] = {"emergency": [], "normal": []}

    code_counts: Dict[str, int] = {}
    feature_rows: List[Dict[str, object]] = []

    processed = 0
    for p in files:
        code = parse_crema_code(p)
        if code not in {"ANG", "FEA", "NEU", "SUR", "CAL"}:
            continue

        try:
            feat = extract_features(p)
        except Exception:
            continue

        processed += 1
        code_counts[code] = code_counts.get(code, 0) + 1

        main_class = main_map.get(code, "")
        sens_class = sens_map.get(code, "")

        if main_class:
            main_groups[main_class].append(feat)
        if sens_class:
            sens_groups[sens_class].append(feat)

        feature_rows.append(
            {
                "path": str(p),
                "code": code,
                "main_class": main_class,
                "sensitivity_class": sens_class,
                "alpha_ratio": float(feat["alpha_ratio"]),
                "centroid": float(feat["centroid"]),
                "bandwidth": float(feat["bandwidth"]),
                "low_prop": float(feat["low_prop"]),
                "mid_prop": float(feat["mid_prop"]),
                "high_prop": float(feat["high_prop"]),
            }
        )

    if len(main_groups["emergency"]) == 0 or len(main_groups["normal"]) == 0:
        raise RuntimeError("Insufficient main-mapping samples for emergency/normal")

    em = make_group_arrays(main_groups["emergency"])
    no = make_group_arrays(main_groups["normal"])

    alpha_png = out_root / "alpha_ratio.png"
    spec_png = out_root / "spectral_centroid_bandwidth.png"
    energy_png = out_root / "energy_distribution.png"
    envelope_png = out_root / "pitch_energy_envelope.png"

    plot_alpha_ratio(alpha_png, em["alpha_ratio"], no["alpha_ratio"])
    plot_centroid_bandwidth(spec_png, em["centroid"], no["centroid"], em["bandwidth"], no["bandwidth"])
    plot_energy_distribution(
        energy_png,
        em["low_prop"],
        em["mid_prop"],
        em["high_prop"],
        no["low_prop"],
        no["mid_prop"],
        no["high_prop"],
    )
    plot_pitch_energy(envelope_png, em["pitch_curve"], no["pitch_curve"], em["energy_curve"], no["energy_curve"])

    stats = {
        "emergency": {
            "alpha_ratio_mean": safe_mean(em["alpha_ratio"]),
            "centroid_mean": safe_mean(em["centroid"]),
            "bandwidth_mean": safe_mean(em["bandwidth"]),
            "low_prop_mean": safe_mean(em["low_prop"]),
            "mid_prop_mean": safe_mean(em["mid_prop"]),
            "high_prop_mean": safe_mean(em["high_prop"]),
        },
        "normal": {
            "alpha_ratio_mean": safe_mean(no["alpha_ratio"]),
            "centroid_mean": safe_mean(no["centroid"]),
            "bandwidth_mean": safe_mean(no["bandwidth"]),
            "low_prop_mean": safe_mean(no["low_prop"]),
            "mid_prop_mean": safe_mean(no["mid_prop"]),
            "high_prop_mean": safe_mean(no["high_prop"]),
        },
        "diff": {
            "alpha_ratio_cohen_d": cohen_d(em["alpha_ratio"], no["alpha_ratio"]),
            "centroid_cohen_d": cohen_d(em["centroid"], no["centroid"]),
            "bandwidth_cohen_d": cohen_d(em["bandwidth"], no["bandwidth"]),
            "low_prop_cohen_d": cohen_d(em["low_prop"], no["low_prop"]),
            "mid_prop_cohen_d": cohen_d(em["mid_prop"], no["mid_prop"]),
            "high_prop_cohen_d": cohen_d(em["high_prop"], no["high_prop"]),
        },
    }

    main_counts = {
        "emergency": len(main_groups["emergency"]),
        "normal": len(main_groups["normal"]),
        "total": len(main_groups["emergency"]) + len(main_groups["normal"]),
    }
    sens_counts = {
        "emergency": len(sens_groups["emergency"]),
        "normal": len(sens_groups["normal"]),
        "total": len(sens_groups["emergency"]) + len(sens_groups["normal"]),
    }

    write_findings_main(out_root / "findings_phase1_cremad.md", stats, main_counts, code_counts)
    write_findings_sensitivity(
        out_root / "findings_phase1_sensitivity.md",
        main_counts,
        sens_counts,
        surprise_count=code_counts.get("SUR", 0),
    )
    write_summary(out_root / "summary_2026w14_phase1.md", main_counts, surprise_count=code_counts.get("SUR", 0), stats=stats)

    write_feature_csv(out_root / "cremad_feature_table_phase1.csv", feature_rows)

    print(f"Processed files: {processed}")
    print(f"Main counts: {main_counts}")
    print(f"Sensitivity counts: {sens_counts}")
    print(f"Saved: {alpha_png}")
    print(f"Saved: {spec_png}")
    print(f"Saved: {energy_png}")
    print(f"Saved: {envelope_png}")


if __name__ == "__main__":
    main()
