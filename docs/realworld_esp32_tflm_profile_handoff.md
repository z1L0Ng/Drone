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
