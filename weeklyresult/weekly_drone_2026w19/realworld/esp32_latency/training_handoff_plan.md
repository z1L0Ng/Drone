# Training Handoff Plan For <=1s ESP32 Deployment Candidate

Date: 2026-05-16

## Do Not Launch From This Audit

This file is a handoff plan only. This ESP32 deployment audit does not train a
model, start a server job, or merge any W19 baseline branch.

## Trigger Condition

Use this plan only if the project decides that the paper needs a credible
`<=1s` pure onboard inference path on XIAO ESP32-S3.

Current evidence says the existing `B_small_teacher_student` checkpoint has:

- TFLM `Invoke()` p50 about `2094 ms`
- first three CNN stem Conv2D calls about `1535 ms`

Sources:

- `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_report.md`
- `realworld/esp32/PHASE2_OPTIMIZATION_ATTEMPTS.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/latency_audit.md`

## Required Commit SHA

Audited local HEAD at planning time:

```text
3d5eba17ade035f030020db283897f0765916b7a
```

Before launching any server training, the manager/training agent must verify:

1. The intended model/config changes are committed.
2. The working tree is clean or all unrelated dirty files are explicitly
   excluded.
3. The launch receipt records the exact commit SHA used on the server.

## Proposed Training Target

WEEKLY_TAG:

```text
weekly_drone_2026w19
```

Candidate name:

```text
rt1s_tiny_student
```

tmux session:

```text
drone_w19_rt1s_tiny_student
```

Saved model output:

```text
saved_models/weekly_drone_2026w19/rt1s_tiny_student/
```

Weekly result output:

```text
weeklyresult/weekly_drone_2026w19/rt1s_tiny_student/
```

History output:

```text
weeklyresult/weekly_drone_2026w19/rt1s_tiny_student/history/
```

## Architecture Requirements

Keep:

- input frontend: `(256, 32, 1)` logmel unless the project explicitly approves
  a frontend change
- sample rate: `16000 Hz`
- window length: `1.0 s`
- labels: `emergency`, `movement`, `unknown`
- stats branch disabled
- full-integer int8 export target
- TFLM-compatible temporal conv: `DEPTHWISE_CONV_2D`, not grouped temporal
  `CONV_2D`

Change:

- reduce early CNN stem compute first
- target smaller stem channels, for example `64 -> 32` or lower
- consider earlier stride/pooling before large Conv2D maps
- consider depthwise-separable stem if the op mix remains TFLM-safe
- keep Branchformer entry substantially smaller than the current path if needed

Hard deployment target:

- board-side TFLM `Invoke()` p50 `<=1000 ms`
- preferred target `<=800 ms` to leave guard room
- no uniform raw output
- `AllocateTensors()` passes
- `Invoke()` returns

## Startup Receipt Requirements

The training agent must report before launch:

- commit SHA
- branch
- tmux session name
- `WEEKLY_TAG`
- full command or environment variable block
- model output directory
- weeklyresult output directory
- teacher checkpoint/provenance
- student profile/config
- confirmation that stats branch is disabled
- confirmation that no Tello/ESP32 runtime code is being changed by the training job

## Completion Receipt Requirements

The training agent must report after completion:

- start time and end time
- checkpoint path
- `run_config.json` path
- `classification_report_noisy.txt` path
- `student_history.csv` path
- clean test accuracy
- noisy test accuracy
- emergency precision/recall/F1
- parameter count
- Keras model summary
- full-integer TFLite path
- TFLite file size
- TFLite op counts, especially `CONV_2D`, `DEPTHWISE_CONV_2D`,
  `FULLY_CONNECTED`, `BATCH_MATMUL`
- confirmation that grouped temporal `CONV_2D` is absent
- desktop TFLite probe result
- ESP32 smoke result:
  - `AllocateTensors()`
  - `Invoke()`
  - output label
  - `arena_used_bytes`
  - TFLM `Invoke()` latency

## Acceptance Gate

Do not replace the current ESP32 baseline unless the new candidate shows:

- materially lower board-side `Invoke()` latency
- no TFLM op compatibility regression
- no obvious model-quality collapse
- better evidence for the paper's real-time onboard story

If accuracy collapses or emergency recall becomes unusable, keep the current
`B_small_teacher_student` baseline for demo work and report the `<=1s` path as a
future optimization.
