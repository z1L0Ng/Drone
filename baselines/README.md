# Track D Offline Baseline Scaffold

This directory contains project-local baseline scaffolding for the SenSys 2027
Track D offline recognizer comparison. It is intentionally integrated with the
Drone repo data contract instead of depending on downloaded upstream training
repos.

Current scope:

- Model skeletons for BC-ResNet-1, TCResNet8, and DS-CNN-S.
- Shared project adapters for `dataset/processed/data_paths.npz`,
  `saved_models/label_encoder.joblib`, 1 s / 16 kHz audio, log-mel and MFCC
  frontends, tellonoise configuration, and output schema helpers.
- Smoke-test runner only. Full training must be approved separately and run
  from a committed SHA on the server.

Fairness contract for the offline baseline table:

- Use the same split from `dataset/processed/data_paths.npz`.
- Use the same label encoder from `saved_models/label_encoder.joblib`.
- Use the same labels: `emergency`, `movement`, and `unknown`.
- Use 1 s audio at 16 kHz.
- Use `dataset/raw/tellonoise` for noise mixing.
- Use training SNR sampled from `[-15, -5]` dB and noisy evaluation at `-10`
  dB.
- Write results under
  `weeklyresult/weekly_drone_2026w19/offline_baselines/<baseline_name>/`.
- Produce `run_config.json`, `classification_report_noisy.txt`,
  `metrics.json`, a confusion matrix, training history, and checkpoint pointers.

Boundary:

- These baselines are offline recognizer comparisons only.
- Deployment feasibility requires a separate TFLite/TFLM export and runtime
  compatibility check.
- MFCC rows should be labeled as `model+frontend` baselines unless the manager
  moves them to the frontend ablation layer.

No external repositories are vendored in this scaffold. See each
`UPSTREAM.md` file for source attribution and license notes.
