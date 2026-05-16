# ESP32 On-Device Inference Latency Audit

Date: 2026-05-16

## Scope

This audit covers only the ESP32/XIAO on-device runtime path. It does not train
models, launch server jobs, edit the paper, connect Tello flight control, or
interpret runtime stability as semantic accuracy or safety validation.

## Git Audit

- Branch: `main`
- HEAD: `3d5eba17ade035f030020db283897f0765916b7a`
- `git status --short` at audit start showed unrelated dirty files:
  - `.DS_Store`
  - `docs/paper_sensys2027/*`
  - `docs/weekly_todo/handoff_log.md`
  - `docs/weekly_todo/2026/2026w19/`
- This audit did not touch paper text, weekly TODO files, model training code, or
  Tello control code.

## Evidence Read

- TFLM handoff:
  `docs/realworld_esp32_tflm_profile_handoff.md`
- Stability report:
  `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_report.md`
- Stability events:
  `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_events.csv`
- Stability summary:
  `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_summary.csv`
- Firmware:
  `realworld/esp32/firmware/esp32_local_cdc_fast/esp32_local_cdc_fast.ino`
  `realworld/esp32/firmware/esp32_local_cdc_fast/config.h`
- Frozen candidate:
  `realworld/esp32/models/B_small_teacher_student/MODEL_INFO.json`
  `realworld/esp32/models/B_small_teacher_student/student_kd_best.weights.h5`
- TFLite/precheck:
  `realworld/esp32/phase2_artifacts/B_small_teacher_student_full_integer.tflite`
  `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/tflm_candidate_precheck.json`
- Prior op profile:
  `realworld/esp32/PHASE2_OPTIMIZATION_ATTEMPTS.md`

## Current Path

The stable firmware path is:

```text
host trigger over USB CDC
-> XIAO I2S/PDM microphone capture
-> board-side logmel frontend
-> int8 TFLM Invoke()
-> status JSON over USB CDC
-> host receive/log
```

The firmware locks the audio window at `16000` samples and `16000 Hz` in
`realworld/esp32/firmware/esp32_local_cdc_fast/config.h:14-17`. The current
kernel path is `espnn_recording_default_softmax` with `TFLM_TEST_FORCE_ANSI_CONV
= 0` in `config.h:6-8` and `config.h:24-27`.

## Timing Boundary

The current `infer_ms` is pure TFLM invocation time. In firmware:

- `total_start` begins at `runOne()` entry:
  `esp32_local_cdc_fast.ino:467-469`
- capture is timed around `readPcmWindow()`:
  `esp32_local_cdc_fast.ino:471-479`
- frontend is timed around `extractLogmelToInput()`:
  `esp32_local_cdc_fast.ino:481-489`
- inference is timed only around `g_interpreter->Invoke()`:
  `esp32_local_cdc_fast.ino:491-493`
- `sendStatus()` reports `capture_ms`, `frontend_ms`, `infer_ms`, and
  `total_ms`:
  `esp32_local_cdc_fast.ino:429-463`

Therefore the reported `infer_p50_ms=2094` is not frontend time, not USB
serialization time, and not host receive time.

## Timing Breakdown

Generated CSV:

- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/timing_breakdown.csv`

Key p50 values from the 30-trigger W17 stability run:

| Component | p50 ms | p95 ms | Source |
| --- | ---: | ---: | --- |
| 1 s PCM capture | `926.0` | `930.0` | W17 stability events |
| logmel frontend | `55.0` | `55.0` | W17 stability events |
| TFLM `Invoke()` | `2094.0` | `2094.0` | W17 stability events |
| firmware total | `3075.0` | `3079.0` | W17 stability events |
| host elapsed | `3080.0` | `3084.0` | W17 stability events |
| USB status + host receive delta | `5.5` | `7.0` | `host_elapsed_ms - total_ms` |
| device residual | `0.0` | `0.0` | `total_ms - capture - frontend - infer` |

There is no Bluetooth path in the current measured implementation. The only
measured transport is USB CDC status JSON, and it contributes about `5.5 ms`
p50 after the board-side total.

## Bottleneck

The bottleneck is TFLM model execution, specifically early Conv2D compute in
the CNN stem.

Prior op profiling in `realworld/esp32/PHASE2_OPTIMIZATION_ATTEMPTS.md` reports:

- `infer_ms=2095`
- `op_conv_us=1572678`
- `op_fc_us=273823`
- `op_unprofiled_est_us=230296`
- `op_depthwise_us=11836`
- `op_softmax_us=6686`
- `op_conv_us_by_idx=[324408, 969348, 241323, 12759, 12470, 12360]`

Interpretation:

- Conv2D consumes about `1572.7 ms` of the `2095 ms` profiled inference sample.
- The first three CNN stem Conv2D calls consume about `1535.1 ms`.
- The largest single call is Conv2D index 1 at about `969.3 ms`.
- Depthwise temporal convolution and Softmax are not material bottlenecks.
- Frontend cost is only about `55 ms`.
- USB/host receive cost is only about `5.5 ms`.

The TFLite candidate is already full-integer int8 and TFLM-compatible:

- `B_small_teacher_student_full_integer.tflite` size: `780416` bytes
- op mix from `weeklyresult/.../tflm_candidate_precheck.json`:
  `CONV_2D=6`, `DEPTHWISE_CONV_2D=1`, `FULLY_CONNECTED=11`, `SOFTMAX=2`
- grouped temporal `CONV_2D` is not detected in the current candidate.

## Classification Of Causes

| Candidate cause | Audit result |
| --- | --- |
| Measurement artifact | Unlikely. Firmware lines `491-493` isolate `Invoke()` only. |
| Host overhead | Not the cause. Host delta p50 is about `5.5 ms`. |
| USB/Bluetooth serialization | USB status JSON is negligible; Bluetooth is not implemented/measured. |
| Audio capture | Capture is expected near `1 s`; it is not part of `infer_ms`. |
| Frontend | Not the cause; p50 is `55 ms`. |
| CPU frequency | Not the likely cause. Existing optimization note records the baseline as already at `CPUFreq=240`, `F_CPU=240000000`, and `CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ=240`. |
| TFLM op implementation | Partially. ESP-NN Conv is enabled, but early Conv2D is still slow. A custom kernel would be nontrivial and high risk. |
| Arena/memory layout | Possible contributor because tensors live in PSRAM, but not a low-risk path to a 2x speedup. The actual arena used is around `699 KB`, larger than practical internal RAM headroom for this full pipeline. |
| Model structure | Primary cause. Early stem Conv2D on large feature maps dominates runtime. |

## Low-Risk No-Retrain Options

These are worth doing only as instrumentation or small sanity checks. They are
not expected to reduce `Invoke()` from `2094 ms` to `<=1000 ms`.

1. Re-run `esp32_local_cdc_profile_ops` for 10 live triggers under W19 output
   to confirm the per-op profile still matches the W17 sample.
2. Add `cpu_mhz`, `free_heap`, `free_psram`, and `largest_free_block` to the
   regular `esp32_local_cdc_fast` status line for future runs.
3. Build one A/B firmware with only compiler optimization flags changed, if the
   Arduino/TFLM library build allows it, and record whether the precompiled TFLM
   library is actually affected.
4. Reduce `kModelArenaBytes` only after confirming allocation still passes.
   This may improve memory headroom but should not materially improve speed.
5. Keep frontend changes out of the critical path for this goal because frontend
   is only `55 ms` p50.

## One-Second Feasibility

Current pure inference p50 is `2094 ms`. To reach `<=1000 ms`, engineering-only
changes must remove at least `1094 ms`, or about `52%` of current invocation
time.

The first three Conv2D calls alone are about `1535 ms`, already above the
target. This means even eliminating frontend, host overhead, Softmax, and most
non-Conv work would still not satisfy the `<=1s` target unless the early Conv2D
path is substantially changed.

Conclusion:

- `<=1s` pure TFLM inference is not realistically achievable through low-risk
  firmware or measurement cleanup on the current checkpoint.
- A custom Conv kernel or deep TFLM/PSRAM placement rewrite might help, but that
  is not low risk and is not the right first path for a paper schedule.
- If the paper requires a credible `<=1s` onboard story, the project needs a new
  tiny deployment student or equivalent architecture change that reduces early
  CNN stem compute.

## Output Files

- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/timing_breakdown.csv`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/latency_audit.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/one_second_feasibility_decision.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/training_handoff_plan.md`
