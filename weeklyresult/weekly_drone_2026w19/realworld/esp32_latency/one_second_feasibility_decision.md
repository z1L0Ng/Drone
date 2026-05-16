# One-Second Onboard Inference Feasibility Decision

Date: 2026-05-16

## Decision

Current checkpoint:

- `B_small_teacher_student`
- profile: `xiao_bottleneck256_tflm`
- firmware: `realworld/esp32/firmware/esp32_local_cdc_fast/esp32_local_cdc_fast.ino`
- kernel path: `espnn_recording_default_softmax`

Decision:

- `<=1s` pure onboard TFLM inference is **not feasible** via low-risk
  engineering-only changes on the current checkpoint.
- A `<=1s` paper-facing onboard story likely requires a new tiny deployment
  student or an equivalent architecture-level change.

## Why

The W17 stable runtime report records:

- `infer_p50_ms=2094.0`
- `infer_p95_ms=2094.0`
- `total_p50_ms=3075.0`
- `total_p95_ms=3079.0`

Source:

- `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_report.md`
- `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_summary.csv`

Firmware timing confirms `infer_ms` is measured only around:

```cpp
const uint32_t infer_start = millis();
const TfLiteStatus status = g_interpreter->Invoke();
const uint32_t infer_ms = millis() - infer_start;
```

Source:

- `realworld/esp32/firmware/esp32_local_cdc_fast/esp32_local_cdc_fast.ino:491-493`

Therefore `2094 ms` is not capture time, frontend time, USB time, or host time.

## Breakdown

Generated table:

- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/timing_breakdown.csv`

Key p50 values:

- capture: `926.0 ms`
- frontend: `55.0 ms`
- TFLM invoke: `2094.0 ms`
- USB status + host receive delta: `5.5 ms`

Prior op-level profile:

- Conv2D total: `1572.668 ms`
- first three CNN stem Conv2D calls: `1535.079 ms`
- FC total: `273.764 ms`
- unprofiled estimate: `230.054 ms`
- depthwise total: `11.828 ms`
- softmax total: `6.686 ms`

Source:

- `realworld/esp32/PHASE2_OPTIMIZATION_ATTEMPTS.md`

The first three Conv2D calls alone exceed the `<=1s` target.

## Low-Risk Engineering Feasibility

Not enough.

Possible low-risk checks:

- Re-run per-op profiler under W19.
- Add `cpu_mhz` and heap fields to normal status logs.
- Try a compiler flag A/B if the Arduino/TFLM build actually recompiles the
  relevant kernels.
- Reduce arena reservation for memory headroom only.

Expected impact:

- Useful for confidence and reporting.
- Unlikely to remove the required `>=1094 ms`.

## Training Need

If the project requires a credible `<=1s` onboard inference result, train a new
tiny deployment student with the same frontend and labels but much lower early
CNN stem cost.

This audit does not launch training. See:

- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/training_handoff_plan.md`

## Gate

- Current runtime stability gate: passed.
- Semantic accuracy gate: not evaluated by this audit.
- Safety/demo gate: not evaluated by this audit.
- `<=1s` onboard inference gate: not passed.
