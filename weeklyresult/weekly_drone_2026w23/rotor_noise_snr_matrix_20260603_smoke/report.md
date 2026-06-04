# Rotor Noise SNR Matrix

Status: smoke test only; not paper-ready

## Summary

This is an offline acoustic-recognizer robustness evaluation. It is not safety
validation, flight validation, or an ESP32 firmware test. Prediction uses argmax
over the model softmax output; no confidence threshold is tuned on the test set.

| Condition | Acc. | Macro F1 | Emerg. R | Unknown false event rate | n |
|---|---:|---:|---:|---:|---:|
| No added rotor noise | 0.885 | 0.886 | 0.794 | 0.069 | 96 |
| Rotor noise, 0 dB SNR | 0.833 | 0.833 | 0.794 | 0.172 | 96 |
| Rotor noise, -5 dB SNR | 0.875 | 0.874 | 0.912 | 0.103 | 96 |
| Rotor noise, -10 dB SNR | 0.854 | 0.857 | 0.912 | 0.103 | 96 |
| Rotor noise, -15 dB SNR | 0.750 | 0.749 | 0.853 | 0.172 | 96 |

## Artifacts

- `snr_matrix.csv`: `weeklyresult/weekly_drone_2026w23/rotor_noise_snr_matrix_20260603_smoke/snr_matrix.csv`
- `per_class_metrics.csv`: `weeklyresult/weekly_drone_2026w23/rotor_noise_snr_matrix_20260603_smoke/per_class_metrics.csv`
- `confusion_matrices.json`: `weeklyresult/weekly_drone_2026w23/rotor_noise_snr_matrix_20260603_smoke/confusion_matrices.json`
- `run_manifest.json`: `weeklyresult/weekly_drone_2026w23/rotor_noise_snr_matrix_20260603_smoke/run_manifest.json`
- `report.md`: `weeklyresult/weekly_drone_2026w23/rotor_noise_snr_matrix_20260603_smoke/report.md`

## Exact Commands

Environment:

```bash
MPLCONFIGDIR=/tmp/matplotlib
NUMBA_CACHE_DIR=/tmp/numba_cache
NUMBA_DISABLE_JIT=1
```

Python argv recorded by the evaluator:

```bash
scripts/eval_rotor_noise_snr_matrix.py --limit 96 --output-dir weeklyresult/weekly_drone_2026w23/rotor_noise_snr_matrix_20260603_smoke
```

## Inputs

- checkpoint: `saved_models/weekly_drone_2026w14/preprocess_ext/student_kd_best.weights.h5`
- run config: `weeklyresult/weekly_drone_2026w14/preprocess_ext/run_config.json`
- processed split: `dataset/processed/data_paths.npz`
- label encoder: `saved_models/label_encoder.joblib`
- noise source directory: `dataset/raw/tellonoise`
- seed: `20260603`
- SNR formula: `P_noise_target = P_speech / 10^(SNR_dB/10); scaled_noise = noise * sqrt(P_noise_target / P_noise); mixed = clean + scaled_noise`

## LaTeX Table Body

```latex
No added rotor noise & 0.885 & 0.886 & 0.794 & 0.069 \\
Rotor noise, 0 dB SNR & 0.833 & 0.833 & 0.794 & 0.172 \\
Rotor noise, -5 dB SNR & 0.875 & 0.874 & 0.912 & 0.103 \\
Rotor noise, -10 dB SNR & 0.854 & 0.857 & 0.912 & 0.103 \\
Rotor noise, -15 dB SNR & 0.750 & 0.749 & 0.853 & 0.172 \\
```

## Caveats / Failure Modes

- The matrix evaluates the offline acoustic reference recognizer only; it does not validate flight behavior or the safety bridge.
- The clean row is the clean held-out dataset split with no added local rotor noise, not a live no-rotor recording condition.
- The run uses the full X_test/y_test split. The older w14 classification_report_noisy.txt used 9984 samples because its Keras Sequence length floored by batch size.
- Rotor-noise mixtures use local dataset/raw/tellonoise clips selected by the w14 run config; source files are treated as local recorded/collected noise assets, not as flight validation.
- If peak amplitude exceeded 1.0 after mixing, the whole mixture was peak-normalized; this avoids clipping while preserving SNR ratio.
- Only the first 96 examples were evaluated because --limit was set.
