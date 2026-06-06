# Rotor Noise SNR Matrix

Status: preliminary for paper until manager approves full-split support policy

## Summary

This is an offline acoustic-recognizer robustness evaluation. It is not safety
validation, flight validation, or an ESP32 firmware test. Prediction uses argmax
over the model softmax output; no confidence threshold is tuned on the test set.

| Condition | Acc. | Macro F1 | Emerg. R | Unknown false event rate | n |
|---|---:|---:|---:|---:|---:|
| No added rotor noise | 0.918 | 0.919 | 0.938 | 0.107 | 10008 |
| Rotor noise, 0 dB SNR | 0.592 | 0.568 | 0.266 | 0.298 | 10008 |
| Rotor noise, -5 dB SNR | 0.491 | 0.435 | 0.097 | 0.382 | 10008 |
| Rotor noise, -10 dB SNR | 0.421 | 0.349 | 0.030 | 0.539 | 10008 |
| Rotor noise, -15 dB SNR | 0.377 | 0.294 | 0.012 | 0.690 | 10008 |

## Artifacts

- `snr_matrix.csv`: `weeklyresult/weekly_drone_2026w23/teacher_clean_on_rotor_noise_snr_matrix_20260606/snr_matrix.csv`
- `per_class_metrics.csv`: `weeklyresult/weekly_drone_2026w23/teacher_clean_on_rotor_noise_snr_matrix_20260606/per_class_metrics.csv`
- `confusion_matrices.json`: `weeklyresult/weekly_drone_2026w23/teacher_clean_on_rotor_noise_snr_matrix_20260606/confusion_matrices.json`
- `run_manifest.json`: `weeklyresult/weekly_drone_2026w23/teacher_clean_on_rotor_noise_snr_matrix_20260606/run_manifest.json`
- `report.md`: `weeklyresult/weekly_drone_2026w23/teacher_clean_on_rotor_noise_snr_matrix_20260606/report.md`

## Exact Commands

Environment:

```bash
MPLCONFIGDIR=/tmp/matplotlib
NUMBA_CACHE_DIR=/tmp/numba_cache
NUMBA_DISABLE_JIT=1
```

Shell command:

```bash
MPLCONFIGDIR=/tmp/matplotlib NUMBA_CACHE_DIR=/tmp/numba_cache NUMBA_DISABLE_JIT=1 conda run -n drone python scripts/eval_rotor_noise_snr_matrix.py --weights saved_models/weekly_drone_2026w14/baseline/teacher_clean_best.weights.h5 --run-config /tmp/akouo_teacher_eval_run_config.json --output-dir weeklyresult/weekly_drone_2026w23/teacher_clean_on_rotor_noise_snr_matrix_20260606
```

Python argv recorded by the evaluator:

```bash
scripts/eval_rotor_noise_snr_matrix.py --weights saved_models/weekly_drone_2026w14/baseline/teacher_clean_best.weights.h5 --run-config /tmp/akouo_teacher_eval_run_config.json --output-dir weeklyresult/weekly_drone_2026w23/teacher_clean_on_rotor_noise_snr_matrix_20260606
```

## Inputs

- checkpoint: `saved_models/weekly_drone_2026w14/baseline/teacher_clean_best.weights.h5`
- run config: `/private/tmp/akouo_teacher_eval_run_config.json`
- processed split: `dataset/processed/data_paths.npz`
- label encoder: `saved_models/label_encoder.joblib`
- noise source directory: `dataset/raw/tellonoise`
- seed: `20260603`
- SNR formula: `P_noise_target = P_speech / 10^(SNR_dB/10); scaled_noise = noise * sqrt(P_noise_target / P_noise); mixed = clean + scaled_noise`

## LaTeX Table Body

```latex
No added rotor noise & 0.918 & 0.919 & 0.938 & 0.107 \\
Rotor noise, 0 dB SNR & 0.592 & 0.568 & 0.266 & 0.298 \\
Rotor noise, -5 dB SNR & 0.491 & 0.435 & 0.097 & 0.382 \\
Rotor noise, -10 dB SNR & 0.421 & 0.349 & 0.030 & 0.539 \\
Rotor noise, -15 dB SNR & 0.377 & 0.294 & 0.012 & 0.690 \\
```

## Caveats / Failure Modes

- The matrix evaluates the offline acoustic reference recognizer only; it does not validate flight behavior or the safety bridge.
- The clean row is the clean held-out dataset split with no added local rotor noise, not a live no-rotor recording condition.
- The run uses the full X_test/y_test split. The older w14 classification_report_noisy.txt used 9984 samples because its Keras Sequence length floored by batch size.
- Rotor-noise mixtures use local dataset/raw/tellonoise clips selected by the w14 run config; source files are treated as local recorded/collected noise assets, not as flight validation.
- If peak amplitude exceeded 1.0 after mixing, the whole mixture was peak-normalized; this avoids clipping while preserving SNR ratio.
