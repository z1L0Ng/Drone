# ESP32 TFLM-Compatible Profile Handoff

Date: 2026-04-28

## Current Finding

The `xiao_bottleneck256` int8 candidate allocates on XIAO ESP32-S3, but fails
during `Invoke()`.

Measured on board:

- full-int flatbuffer: `818496` bytes
- arena allocation: `4194304` bytes
- `AllocateTensors()`: pass
- arena used with ANSI Conv fallback: `699004` bytes
- crash location: `Conv2D Eval`

Runtime trace:

```text
conv_invoke_start idx=5
input_dims=[1,1,32,256]
filter_dims=[256,1,31,1]
output_dims=[1,1,32,256]
```

This is the Branchformer temporal depthwise convolution. In the current model
code it is implemented as:

```python
Conv1D(input_feature_dim, kernel_size, padding="same", groups=input_feature_dim)
```

TensorFlow Lite converts that to grouped `CONV_2D`. Desktop TFLite can run it,
but the current TFLM Conv2D kernel path does not support this grouped shape and
aborts on ESP32-S3.

## Required Fix For Next Server Run

Use the new model profile:

- `KD_STUDENT_MODEL_PROFILE=xiao_bottleneck256_tflm`

This keeps the same deployment target shape:

- Branchformer entry: `(32, 256)`
- params: `712067`

The only architecture compatibility change is:

- old: grouped `Conv1D(..., groups=input_feature_dim)`
- new: `DepthwiseConv1D(..., depth_multiplier=1)`

Local export sanity check confirms the new profile exports the temporal
depthwise layer as `DEPTHWISE_CONV_2D`, not grouped `CONV_2D`:

```text
CONV_2D=6
DEPTHWISE_CONV_2D=1
```

## Suggested Server Command Delta

Use the same data, teacher, and training setup as the latest `xiao_b256`
candidate, except change result/model directories and student profile:

```bash
export KD_MODEL_DIR=saved_models/weekly_drone_2026w17/xiao_b256_tflm_reuse_on
export KD_RESULT_DIR=weeklyresult/weekly_drone_2026w17/xiao_b256_tflm_reuse_on
export KD_HISTORY_DIR=weeklyresult/weekly_drone_2026w17/xiao_b256_tflm_reuse_on/history

export KD_STUDENT_MODEL_PROFILE=xiao_bottleneck256_tflm
export KD_TEACHER_MODEL_PROFILE=base
export KD_REUSE_TEACHER=1
export KD_TEACHER_USE_STATS_BRANCH=0
export KD_USE_STATS_BRANCH=0
```

Keep the remaining training hyperparameters identical to the latest successful
server/local flow unless the training agent has a documented reason to change
them.

## Gate

Do not send another `xiao_bottleneck256` grouped-Conv model to ESP32 TFLM.

For the next candidate, the local gate is:

1. export full-integer TFLite
2. confirm op list has `DEPTHWISE_CONV_2D=1`
3. prepare `esp32_tflm_candidate_test`
4. confirm on XIAO:
   - `AllocateTensors()` passes
   - `Invoke()` returns
   - `top_label` prints

## Latest W17 Training Receipt

Date: 2026-04-29

Run:

- `weekly_drone_2026w17/B_small_teacher_student`

Why local:

- Server resources were occupied, so this run was completed locally as a
  documented exception. This does not change the default policy: future
  full-dataset training remains server-side unless explicitly approved.

Evidence log:

- `logs/weekly_drone_2026w17_B_small_teacher_student_resume_20260429_030603.log`

Model configuration from the log:

- teacher profile: `xiao_bottleneck256_tflm`
- student profile: `xiao_bottleneck256_tflm`
- teacher params: `712,067`
- student params: `712,067`
- Branchformer temporal convolution implementation: `depthwise_conv1d`
- stats branch disabled for both teacher and student

Metrics from the completion log:

- best visible student validation accuracy: `0.8635`
- clean test accuracy: `0.8862`
- noisy test accuracy at `SNR=-10 dB`: `0.8728`

Local testset summaries:

- original: `result/weekly_wrapup_2026w17/B_small_teacher_student_testset_eval/summary.md`
  - overall acc `0.6990`
  - emergency recall `0.6319`
  - emergency F1 `0.5698`
- finetuned: `result/weekly_wrapup_2026w17/B_small_teacher_student_finetuned_testset_eval/summary.md`
  - overall acc `0.7201`
  - emergency recall `0.6482`
  - emergency F1 `0.5940`

Artifact integrity gate before deployment:

- The log reports saved outputs at:
  - `saved_models/weekly_drone_2026w17/B_small_teacher_student/teacher_clean_best.weights.h5`
  - `saved_models/weekly_drone_2026w17/B_small_teacher_student/student_kd_best.weights.h5`
  - `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/classification_report_noisy.txt`
- Commit `6698cd389f5d4849ba8c456152927f3f39dc70ff` is local `HEAD` and
  contains the required Keras callback-mode fix in `src/train_logmel_kd.py`, but
  it does not contain the `B_small_teacher_student` checkpoint/result tree.
- At manager audit time on 2026-04-29, the expected `saved_models/.../B_small_teacher_student/`
  and `weeklyresult/.../B_small_teacher_student/` directories were not present in
  the current working tree.
- Restored on 2026-04-29 from `/private/tmp/drone_repo_cleanup_20260429_105129/`.
- Deployment agent may proceed from the restored `student_kd_best.weights.h5` and
  `run_config.json`.

Next deployment task:

1. Recover/confirm `student_kd_best.weights.h5`.
2. Export full-integer TFLite.
3. Confirm op list includes `DEPTHWISE_CONV_2D=1`.
4. Run XIAO smoke:
   - `AllocateTensors()`
   - `Invoke()`
   - `top_label`
