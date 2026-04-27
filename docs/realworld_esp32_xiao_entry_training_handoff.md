# ESP32 XIAO Entry Optimization Training Handoff

Date: 2026-04-27

## Current Decision

The next server training job should target the XIAO ESP32-S3 runtime bottleneck
at the Branchformer entry tensor `(32, 512)`.

Do **not** rerun the old `deploy_s_melonly` plan.

First run a short student-only smoke test for about 20 epochs with the existing
base teacher reused. Do **not** train a same-size teacher first. The current
distiller supports `student_embed_proj`, so teacher/student embedding-dimension
differences are explicitly projected before embedding KD loss is applied.

## Code Changes Required On Server

The server repo must include the current versions of:

- `src/model.py`
- `src/model_config.py`
- `src/train_logmel_kd.py`

New model profiles now available through `KD_STUDENT_MODEL_PROFILE`:

- `xiao_bottleneck256`
- `xiao_time16`
- `xiao_time16_bottleneck256`

## Candidate Order

Run first:

1. `xiao_bottleneck256`
2. `xiao_time16`

Only consider `xiao_time16_bottleneck256` after reviewing the first two.

## Why These Candidates

Current base model:

- input: `(256, 32, 1)`
- Branchformer entry: `(32, 512)`
- measured XIAO TFLM arena need: about `8.23 MB`
- `model_data` is already in flash
- persistent `tail` is only about `57 KB`

So the active blocker is runtime `head` memory from intermediate tensors and
scratch buffers, not flash placement.

Candidate intent:

- `xiao_bottleneck256`: keeps 32 log-mel frames, changes Branchformer entry from
  `(32, 512)` to `(32, 256)`.
- `xiao_time16`: keeps 512 channels, changes Branchformer sequence length from
  `32` to `16`.

## Server Command Template

Server repo root:

```bash
cd /files1/Zilong/Drone
```

For `xiao_bottleneck256`:

```bash
tmux new -s drone_w16_xiao_bottleneck256

export KD_MODEL_DIR=saved_models/weekly_drone_2026w16/xiao_bottleneck256_melonly
export KD_RESULT_DIR=weeklyresult/weekly_drone_2026w16/xiao_bottleneck256_melonly
export KD_HISTORY_DIR=weeklyresult/weekly_drone_2026w16/xiao_bottleneck256_melonly/history

export KD_TEACHER_CKPT=/files1/Zilong/Drone/saved_models/weekly_drone_2026w14/preprocess_ext/student_kd_best.weights.h5
export KD_REUSE_TEACHER=1
export KD_STRICT_REUSE_TEACHER_SHAPE=1
export KD_TEACHER_MODEL_PROFILE=base
export KD_STUDENT_MODEL_PROFILE=xiao_bottleneck256
export KD_STUDENT_INIT_MODE=random

export KD_USE_STATS_BRANCH=0
export KD_TEACHER_USE_STATS_BRANCH=0
export KD_DISTILL_VARIANT=ce_logits_embed
export KD_USE_EMBED_PROJECTION=1
export KD_STUDENT_EPOCHS=20

python src/train_logmel_kd.py
```

For `xiao_time16`, use the same template except:

```bash
tmux new -s drone_w16_xiao_time16
export KD_MODEL_DIR=saved_models/weekly_drone_2026w16/xiao_time16_melonly
export KD_RESULT_DIR=weeklyresult/weekly_drone_2026w16/xiao_time16_melonly
export KD_HISTORY_DIR=weeklyresult/weekly_drone_2026w16/xiao_time16_melonly/history
export KD_STUDENT_MODEL_PROFILE=xiao_time16
```

## Required Completion Report

For each run, report:

- tmux session name
- start/end time
- `student_kd_best.weights.h5` path
- `run_config.json` path
- `classification_report_noisy.txt` path
- `student_history.csv` path
- clean test accuracy
- noisy test accuracy at `SNR=-10 dB`
- emergency precision / recall / F1
- confirmation that stats branches were disabled for both teacher and student
- confirmation that `KD_USE_EMBED_PROJECTION=1`
- whether the 20-epoch student curve is still improving, flat, or collapsed

Gate:

- If noisy accuracy collapses near random or `emergency recall=0`, mark the
  candidate as `model-quality no-go`.
- If either candidate preserves usable model quality, sync it locally for
  full-integer export and XIAO TFLM smoke.

## Fallback If 20-Epoch Smoke Collapses

If both first-pass student smoke runs collapse, run a review before launching
more jobs. The first fallback to consider is a same-profile teacher/student
diagnostic, because it removes cross-profile teacher embedding mismatch as a
confound. That is a fallback, not the default path, because it doubles server
training time and makes the comparison less directly tied to the current best
base checkpoint.
