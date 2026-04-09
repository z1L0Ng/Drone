#!/usr/bin/env python3

import argparse
import csv
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/numba_cache")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import joblib
import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import tensorflow as tf
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.optimizers import Adam
from scipy import signal
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

def _detect_repo_root() -> str:
    """Find repo root by walking up until src/model.py exists."""
    here = Path(__file__).resolve()
    for p in [here.parent, *here.parents]:
        if (p / "src" / "model.py").exists():
            return str(p)
    # Fallback keeps previous behavior if structure is unexpected.
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


ROOT = _detect_repo_root()
sys.path.insert(0, os.path.join(ROOT, "src"))

from model import build_model
from model_config import (
    FMAX,
    FMIN,
    HOP_LENGTH,
    MAX_FRAMES,
    MODEL_KWARGS,
    N_FFT,
    N_MELS,
    SAMPLE_RATE,
    TOP_DB,
    TARGET_LEN,
)


INPUT_SHAPE = (N_MELS, MAX_FRAMES, 1)
LANGS = ["Quechua", "Polish"]


@dataclass
class ModelSpec:
    name: str
    weights: str


def _as_abs(path: str) -> str:
    return path if os.path.isabs(path) else os.path.abspath(os.path.join(ROOT, path))


def setup_tf_seed(seed: int) -> None:
    tf.keras.utils.set_random_seed(seed)


def load_audio_1s(filepath: str) -> np.ndarray:
    try:
        y, sr = sf.read(filepath, dtype="float32")
        if y.ndim > 1:
            y = np.mean(y, axis=1)
        if sr != SAMPLE_RATE:
            y = signal.resample_poly(y, SAMPLE_RATE, sr).astype(np.float32)
        if len(y) < TARGET_LEN:
            y = np.pad(y, (0, TARGET_LEN - len(y)))
        else:
            y = y[:TARGET_LEN]
        return y.astype(np.float32)
    except Exception:
        return np.zeros(TARGET_LEN, dtype=np.float32)


def extract_logmel(y: np.ndarray) -> np.ndarray:
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=SAMPLE_RATE,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        center=False,
        n_mels=N_MELS,
        fmin=FMIN,
        fmax=FMAX,
        power=2.0,
    )
    feat = librosa.power_to_db(mel, ref=np.max, top_db=TOP_DB)
    if feat.shape[1] < MAX_FRAMES:
        feat = np.pad(feat, ((0, 0), (0, MAX_FRAMES - feat.shape[1])), mode="constant")
    else:
        feat = feat[:, :MAX_FRAMES]
    return feat.astype(np.float32)


def resolve_audio_paths(
    df: pd.DataFrame,
    quechua_root: str,
    polish_root: str,
) -> pd.DataFrame:
    roots = {
        "Quechua": _as_abs(quechua_root),
        "Polish": _as_abs(polish_root),
    }

    paths = []
    missing = []
    for row in df.itertuples(index=False):
        root = roots[row.language]
        p = os.path.join(root, row.sample_id)
        if not os.path.exists(p):
            missing.append((row.language, row.sample_id))
        paths.append(p if p is not None else "")
    if missing:
        preview = ", ".join([f"{k[0]}:{k[1]}" for k in missing[:8]])
        raise FileNotFoundError(f"Missing resolved audio paths for {len(missing)} rows. Examples: {preview}")

    out = df.copy()
    out["audio_path"] = paths
    print(f"[audio] resolved {len(out)} benchmark rows from local cache roots", flush=True)
    return out


def build_feature_tensor(paths: List[str]) -> np.ndarray:
    x = np.empty((len(paths), *INPUT_SHAPE), dtype=np.float32)
    for i, p in enumerate(paths):
        if i % 500 == 0:
            print(f"[feature] {i}/{len(paths)}", flush=True)
        x[i] = np.expand_dims(extract_logmel(load_audio_1s(p)), axis=-1)
    return x


def metric_bundle(y_true_bin: np.ndarray, y_pred_bin: np.ndarray) -> Dict[str, float]:
    p, r, f1, s = precision_recall_fscore_support(
        y_true_bin,
        y_pred_bin,
        labels=[1, 0],
        average=None,
        zero_division=0,
    )
    return {
        "acc": float(accuracy_score(y_true_bin, y_pred_bin)),
        "emergency_precision": float(p[0]),
        "emergency_recall": float(r[0]),
        "emergency_f1": float(f1[0]),
        "emergency_support": int(s[0]),
        "normal_precision": float(p[1]),
        "normal_recall": float(r[1]),
        "normal_f1": float(f1[1]),
        "normal_support": int(s[1]),
        "delta_emergency_minus_normal_recall": float(r[0] - r[1]),
        "delta_emergency_minus_normal_f1": float(f1[0] - f1[1]),
    }


def batched_predict(model: tf.keras.Model, x: np.ndarray, batch_size: int) -> np.ndarray:
    outputs = []
    total = len(x)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        if start % (batch_size * 20) == 0:
            print(f"[predict] {start}/{total}", flush=True)
        y = model(x[start:end], training=False).numpy()
        outputs.append(y)
    return np.concatenate(outputs, axis=0)


def language_scope_metrics(
    model_name: str,
    y_true_bin: np.ndarray,
    y_pred_bin: np.ndarray,
    languages: np.ndarray,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    by_language = []
    by_label = []

    scopes = [("all", np.ones(len(y_true_bin), dtype=bool))]
    scopes.extend((lang, languages == lang) for lang in LANGS)

    for scope, mask in scopes:
        yt = y_true_bin[mask]
        yp = y_pred_bin[mask]
        m = metric_bundle(yt, yp)
        row = {"model": model_name, "language": scope, "n_samples": int(mask.sum())}
        row.update(m)
        by_language.append(row)

        for label in ("emergency", "normal"):
            by_label.append(
                {
                    "model": model_name,
                    "language": scope,
                    "label": label,
                    "precision": m[f"{label}_precision"],
                    "recall": m[f"{label}_recall"],
                    "f1": m[f"{label}_f1"],
                    "support": m[f"{label}_support"],
                }
            )

    return by_language, by_label


def load_or_create_split(
    cache_path: str,
    y_bin: np.ndarray,
    finetune_ratio: float,
    val_ratio: float,
    seed: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    cache_path = _as_abs(cache_path)
    if os.path.exists(cache_path):
        cache = np.load(cache_path)
        return cache["idx_finetune"], cache["idx_val"], cache["idx_test"]

    test_ratio = 1.0 - (finetune_ratio + val_ratio)
    if test_ratio <= 0:
        raise ValueError("finetune_ratio + val_ratio must be < 1.0")

    _, _, idx_temp, idx_test = train_test_split(
        y_bin,
        np.arange(len(y_bin)),
        test_size=test_ratio,
        stratify=y_bin,
        random_state=seed,
    )
    val_ratio_adj = val_ratio / (finetune_ratio + val_ratio)
    _, _, idx_finetune, idx_val = train_test_split(
        y_bin[idx_temp],
        idx_temp,
        test_size=val_ratio_adj,
        stratify=y_bin[idx_temp],
        random_state=seed,
    )

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    np.savez(cache_path, idx_finetune=idx_finetune, idx_val=idx_val, idx_test=idx_test)
    return idx_finetune, idx_val, idx_test


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--benchmark-csv",
        default="analysis/cross_language_emergency/phase2_top2_strict_eval_benchmark_2026w14.csv",
    )
    parser.add_argument("--encoder", default="saved_models/label_encoder.joblib")
    parser.add_argument("--quechua-root", default="/tmp/audb_cache_2026w14_lexical/quechua/1.0.2/d3b62a9b")
    parser.add_argument("--polish-root", default="/tmp/audb_cache_2026w14_lexical/nemo/1.0.1/d3b62a9b")
    parser.add_argument("--output-eval-dir", default="result/weekly_wrapup_2026w14/phase2_top2_local_eval")
    parser.add_argument("--output-finetune-dir", default="result/weekly_wrapup_2026w14/phase2_top2_local_finetune")
    parser.add_argument("--split-cache", default="result/weekly_wrapup_2026w14/phase2_top2_local_finetune/split_indices_strict_top2.npz")
    parser.add_argument("--feature-cache", default="result/weekly_wrapup_2026w14/phase2_top2_local_finetune/strict_top2_features.npz")
    parser.add_argument("--finetune-ratio", type=float, default=0.3)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    setup_tf_seed(args.seed)

    benchmark_csv = _as_abs(args.benchmark_csv)
    output_eval_dir = _as_abs(args.output_eval_dir)
    output_finetune_dir = _as_abs(args.output_finetune_dir)
    os.makedirs(output_eval_dir, exist_ok=True)
    os.makedirs(output_finetune_dir, exist_ok=True)

    models = [
        ModelSpec("baseline", _as_abs("saved_models/weekly_drone_2026w14/baseline/best_embed_kd/student_kd_best.weights.h5")),
        ModelSpec("preprocess_ext", _as_abs("saved_models/weekly_drone_2026w14/preprocess_ext/student_kd_best.weights.h5")),
        ModelSpec("branch_trial", _as_abs("saved_models/weekly_drone_2026w14/branch_trial/student_kd_best.weights.h5")),
    ]
    for m in models:
        if not os.path.exists(m.weights):
            raise FileNotFoundError(f"Missing checkpoint: {m.weights}")

    print(f"[load] benchmark: {benchmark_csv}", flush=True)
    df = pd.read_csv(benchmark_csv)
    df = df[df["use_for_eval"] == 1].copy()
    df = df[df["language"].isin(LANGS)].copy()
    df = df[df["canonical_label"].isin(["emergency", "normal"])].copy()
    if df.empty:
        raise RuntimeError("No usable rows after applying use_for_eval=1 and label/language filters.")

    print(f"[load] usable rows after filter: {len(df)}", flush=True)
    df = resolve_audio_paths(df, args.quechua_root, args.polish_root)
    df = df.reset_index(drop=True)

    y_bin = (df["canonical_label"].values == "emergency").astype(np.int32)
    languages = df["language"].values
    feature_cache = _as_abs(args.feature_cache)
    if os.path.exists(feature_cache):
        cache = np.load(feature_cache, allow_pickle=True)
        ok = (
            "x" in cache
            and "sample_id" in cache
            and "language" in cache
            and np.array_equal(cache["sample_id"], df["sample_id"].values)
            and np.array_equal(cache["language"], df["language"].values)
        )
        if ok:
            x = cache["x"]
            print(f"[feature] loaded cache: {feature_cache} shape={x.shape}", flush=True)
        else:
            print(f"[feature] cache mismatch, rebuilding: {feature_cache}", flush=True)
            x = build_feature_tensor(df["audio_path"].tolist())
            os.makedirs(os.path.dirname(feature_cache), exist_ok=True)
            np.savez_compressed(
                feature_cache,
                x=x,
                sample_id=df["sample_id"].values,
                language=df["language"].values,
            )
            print(f"[feature] saved cache: {feature_cache}", flush=True)
    else:
        print("[feature] building features from wav...", flush=True)
        x = build_feature_tensor(df["audio_path"].tolist())
        os.makedirs(os.path.dirname(feature_cache), exist_ok=True)
        np.savez_compressed(
            feature_cache,
            x=x,
            sample_id=df["sample_id"].values,
            language=df["language"].values,
        )
        print(f"[feature] saved cache: {feature_cache}", flush=True)

    encoder = joblib.load(_as_abs(args.encoder))
    class_names = list(encoder.classes_)
    if "emergency" not in class_names:
        raise RuntimeError("Label encoder missing class 'emergency'.")
    emergency_idx = class_names.index("emergency")
    if "unknown" in class_names:
        normal_idx = class_names.index("unknown")
    elif "movement" in class_names:
        normal_idx = class_names.index("movement")
    else:
        normal_idx = next(i for i, c in enumerate(class_names) if c != "emergency")

    # ---------------------------
    # Inference comparison
    # ---------------------------
    inf_by_lang: List[Dict[str, object]] = []
    inf_by_label: List[Dict[str, object]] = []

    for m in models:
        print(f"[infer] model={m.name}", flush=True)
        model = build_model(INPUT_SHAPE, len(class_names), **MODEL_KWARGS)
        model.load_weights(m.weights)
        y_proba = batched_predict(model, x, batch_size=args.batch_size)
        y_pred_cls = np.argmax(y_proba, axis=1)
        y_pred_bin = (y_pred_cls == emergency_idx).astype(np.int32)

        rows_lang, rows_label = language_scope_metrics(m.name, y_bin, y_pred_bin, languages)
        inf_by_lang.extend(rows_lang)
        inf_by_label.extend(rows_label)

    df_inf_lang = pd.DataFrame(inf_by_lang)
    df_inf_label = pd.DataFrame(inf_by_label)
    df_inf_lang.to_csv(os.path.join(output_eval_dir, "comparison_by_language.csv"), index=False)
    df_inf_label.to_csv(os.path.join(output_eval_dir, "comparison_by_label.csv"), index=False)

    # ---------------------------
    # Finetune gate (fixed split)
    # ---------------------------
    idx_finetune, idx_val, idx_test = load_or_create_split(
        args.split_cache,
        y_bin=y_bin,
        finetune_ratio=args.finetune_ratio,
        val_ratio=args.val_ratio,
        seed=args.seed,
    )
    print(
        f"[split] finetune/val/test = {len(idx_finetune)}/{len(idx_val)}/{len(idx_test)} "
        f"(cache={_as_abs(args.split_cache)})",
        flush=True,
    )

    y_mc = np.where(y_bin == 1, emergency_idx, normal_idx).astype(np.int32)
    y_onehot = tf.keras.utils.to_categorical(y_mc, num_classes=len(class_names))

    x_train, y_train = x[idx_finetune], y_onehot[idx_finetune]
    x_val, y_val = x[idx_val], y_onehot[idx_val]
    x_test, y_test_bin = x[idx_test], y_bin[idx_test]
    test_languages = languages[idx_test]

    cls = np.unique(y_mc[idx_finetune])
    cls_w = compute_class_weight(class_weight="balanced", classes=cls, y=y_mc[idx_finetune])
    class_weight = {int(c): float(w) for c, w in zip(cls, cls_w)}

    ft_rows: List[Dict[str, object]] = []

    for m in models:
        print(f"[finetune] model={m.name}", flush=True)
        model = build_model(INPUT_SHAPE, len(class_names), **MODEL_KWARGS)
        model.load_weights(m.weights)
        model.compile(optimizer=Adam(learning_rate=args.lr), loss="categorical_crossentropy", metrics=["accuracy"])

        y_pred_orig_cls = np.argmax(batched_predict(model, x_test, batch_size=args.batch_size), axis=1)
        y_pred_orig_bin = (y_pred_orig_cls == emergency_idx).astype(np.int32)

        ckpt_path = os.path.join(output_finetune_dir, f"{m.name}_finetuned.weights.h5")
        callbacks = [
            ModelCheckpoint(ckpt_path, save_best_only=True, monitor="val_accuracy", save_weights_only=True, verbose=0),
            EarlyStopping(monitor="val_accuracy", patience=2, restore_best_weights=True, verbose=0),
        ]
        model.fit(
            x_train,
            y_train,
            validation_data=(x_val, y_val),
            epochs=args.epochs,
            batch_size=args.batch_size,
            class_weight=class_weight,
            verbose=2,
            callbacks=callbacks,
        )
        if os.path.exists(ckpt_path):
            model.load_weights(ckpt_path)

        y_pred_ft_cls = np.argmax(batched_predict(model, x_test, batch_size=args.batch_size), axis=1)
        y_pred_ft_bin = (y_pred_ft_cls == emergency_idx).astype(np.int32)

        scopes = [("all", np.ones(len(y_test_bin), dtype=bool))]
        scopes.extend((lang, test_languages == lang) for lang in LANGS)
        for scope, mask in scopes:
            orig = metric_bundle(y_test_bin[mask], y_pred_orig_bin[mask])
            ft = metric_bundle(y_test_bin[mask], y_pred_ft_bin[mask])
            ft_rows.append(
                {
                    "model": m.name,
                    "language": scope,
                    "n_samples": int(mask.sum()),
                    "acc_original": orig["acc"],
                    "acc_finetuned": ft["acc"],
                    "delta_acc": ft["acc"] - orig["acc"],
                    "emergency_recall_original": orig["emergency_recall"],
                    "emergency_recall_finetuned": ft["emergency_recall"],
                    "delta_emergency_recall": ft["emergency_recall"] - orig["emergency_recall"],
                    "emergency_f1_original": orig["emergency_f1"],
                    "emergency_f1_finetuned": ft["emergency_f1"],
                    "delta_emergency_f1": ft["emergency_f1"] - orig["emergency_f1"],
                    "normal_recall_original": orig["normal_recall"],
                    "normal_recall_finetuned": ft["normal_recall"],
                    "delta_normal_recall": ft["normal_recall"] - orig["normal_recall"],
                    "normal_f1_original": orig["normal_f1"],
                    "normal_f1_finetuned": ft["normal_f1"],
                    "delta_normal_f1": ft["normal_f1"] - orig["normal_f1"],
                    "delta_emergency_minus_normal_recall_original": orig["delta_emergency_minus_normal_recall"],
                    "delta_emergency_minus_normal_recall_finetuned": ft["delta_emergency_minus_normal_recall"],
                }
            )

    df_ft = pd.DataFrame(ft_rows)
    ft_csv = os.path.join(output_finetune_dir, "finetune_delta_summary.csv")
    df_ft.to_csv(ft_csv, index=False)

    # ---------------------------
    # Recommendation markdown
    # ---------------------------
    # Inference: score by mean emergency F1 on Quechua/Polish.
    inf_lang_only = df_inf_lang[df_inf_lang["language"].isin(LANGS)]
    inf_score = (
        inf_lang_only.groupby("model", as_index=False)["emergency_f1"].mean().rename(columns={"emergency_f1": "mean_emergency_f1_inference"})
    )

    # Finetune: score by mean emergency F1 finetuned on Quechua/Polish test split.
    ft_lang_only = df_ft[df_ft["language"].isin(LANGS)]
    ft_score = (
        ft_lang_only.groupby("model", as_index=False)["emergency_f1_finetuned"].mean().rename(columns={"emergency_f1_finetuned": "mean_emergency_f1_finetuned"})
    )
    overall_delta = (
        df_ft[df_ft["language"] == "all"][["model", "delta_acc", "delta_emergency_f1", "delta_normal_recall"]]
        .rename(columns={"delta_acc": "delta_acc_all", "delta_emergency_f1": "delta_emergency_f1_all", "delta_normal_recall": "delta_normal_recall_all"})
        .copy()
    )
    rank = inf_score.merge(ft_score, on="model", how="outer").merge(overall_delta, on="model", how="left")
    rank = rank.sort_values(["mean_emergency_f1_finetuned", "mean_emergency_f1_inference"], ascending=False)
    recommended = rank.iloc[0]["model"]

    rec_md = os.path.join(output_eval_dir, "phase2_top2_recommendation.md")
    with open(rec_md, "w", encoding="utf-8") as f:
        f.write("# Phase2 Top2 Local Recommendation (2026w14)\n\n")
        f.write("## Benchmark and Fairness Constraints\n")
        f.write("- Filter: `use_for_eval=1` only.\n")
        f.write("- Languages included: Quechua, Polish.\n")
        f.write("- Finetune split cache shared across all models.\n\n")

        f.write("## Inference Scoreboard (mean emergency F1 across Quechua/Polish)\n\n")
        f.write(rank[["model", "mean_emergency_f1_inference"]].to_markdown(index=False))
        f.write("\n\n")

        f.write("## Finetune Scoreboard (mean emergency F1 on test split, Quechua/Polish)\n\n")
        f.write(rank[["model", "mean_emergency_f1_finetuned", "delta_acc_all", "delta_emergency_f1_all", "delta_normal_recall_all"]].to_markdown(index=False))
        f.write("\n\n")

        f.write("## Recommendation\n\n")
        f.write(f"- Recommended model for 2026w14 phase2 local gate: `{recommended}`.\n")
        f.write("- Selection priority: language-balanced emergency performance (Quechua/Polish), then overall finetune stability.\n")
        f.write("- Review `comparison_by_language.csv`, `comparison_by_label.csv`, and `finetune_delta_summary.csv` before final lock.\n")

    print(f"Saved: {os.path.join(output_eval_dir, 'comparison_by_language.csv')}")
    print(f"Saved: {os.path.join(output_eval_dir, 'comparison_by_label.csv')}")
    print(f"Saved: {ft_csv}")
    print(f"Saved: {rec_md}")


if __name__ == "__main__":
    main()
