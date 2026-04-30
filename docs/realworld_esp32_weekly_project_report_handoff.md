# ESP32 Realworld Weekly Project Handoff

Date: 2026-04-30

## Revised Core Conclusion

This week the ESP32 realworld line crossed the key feasibility boundary: XIAO ESP32-S3 Sense can now run the complete local pipeline of microphone capture, logmel frontend, full-integer TFLM inference, and USB CDC result reporting. The measured inference cost is about `2.1 s` and total trigger-to-result cost is about `3.1 s`. After lab discussion, we treat this as a normal and acceptable cost for the current ESP32-S3 class prototype, not as the primary blocker.

The next project priority should therefore shift away from additional model compression and toward an actual system demo: connect the ESP32 inference result to a safe drone-control path, produce repeatable demo evidence, and update the SenSys 2027 paper plan around a working voice-safety-layer prototype.

## Completed Work

### Phase 1: ESP32 Audio Capture -> Mac Host Inference

- Built the Phase 1 bench loop under `realworld/esp32/`.
- ESP32 captures fixed-format audio: `16 kHz`, mono, `1.0 s`, `16000 int16 PCM`.
- Host inference uses the frozen mel-only model copy and locked label encoder.
- Protocol includes CRC-checked PCM frames and ack/error handling.
- Manual host-trigger mode works: one Enter on host triggers one ESP32 capture and one inference result.
- Manual sanity checks passed during bring-up:
  - `stop -> emergency`
  - `go -> movement`
- Phase 1 closeout artifact:
  - `weeklyresult/weekly_drone_2026w16/realworld/esp32_bench/phase1_closeout.md`
- Closeout-recorded metrics:
  - `success_rate=1.000000`
  - `drop_rate=0.010526`
  - `rtt_p50_ms=204.000`
  - `rtt_p95_ms=209.300`
  - `pass_overall=1`

Note: the current `weeklyresult/weekly_drone_2026w16/realworld/esp32_bench/metrics_summary.csv` appears to have been overwritten by a later short WiFi/TCP run with only 8 frames and `drop_rate=0.375`. Do not use that current CSV as the Phase 1 closeout reference.

### Frozen Models And Conversion Artifacts

- Frozen original Phase 1 model:
  - `realworld/esp32/models/preprocess_ext_w14/student_kd_best.weights.h5`
  - `realworld/esp32/models/preprocess_ext_w14/MODEL_INFO.json`
- Frozen current board candidate:
  - `realworld/esp32/models/B_small_teacher_student/student_kd_best.weights.h5`
  - `realworld/esp32/models/B_small_teacher_student/MODEL_INFO.json`
  - `realworld/esp32/models/B_small_teacher_student/label_encoder.joblib`
- Current int8 TFLite artifact:
  - `realworld/esp32/phase2_artifacts/B_small_teacher_student_full_integer.tflite`

### Phase 2: XIAO On-Board TFLM Inference

- Built and debugged multiple XIAO TFLM smoke and local-inference firmware variants:
  - `realworld/esp32/firmware/esp32_tflm_candidate_test/`
  - `realworld/esp32/firmware/esp32_local_cdc/`
  - `realworld/esp32/firmware/esp32_local_cdc_fast/`
  - `realworld/esp32/firmware/esp32_local_cdc_profile_ops/`
- Resolved earlier board blockers:
  - PSRAM had to be enabled.
  - Original large checkpoint failed `AllocateTensors()` because arena demand exceeded available contiguous PSRAM.
  - `xiao_bottleneck256` exported grouped temporal Conv as `CONV_2D`, causing TFLM invoke abort.
  - `xiao_bottleneck256_tflm` fixed this by exporting temporal conv as `DEPTHWISE_CONV_2D`.
  - ESP-NN plus custom local Softmax caused uniform or invalid outputs; the stable path uses ESP-NN Conv with default TFLM Softmax through `RecordingMicroInterpreter`.
- Current stable local firmware:
  - `realworld/esp32/firmware/esp32_local_cdc_fast/esp32_local_cdc_fast.ino`
  - build tag: `local_cdc_fast_v4_espnn_recording_default_softmax`
  - kernel path: `espnn_recording_default_softmax`
- Current full on-board loop:
  - Host sends trigger over USB CDC.
  - ESP32 captures 1 s audio from onboard mic.
  - ESP32 computes logmel frontend.
  - ESP32 runs int8 TFLM inference.
  - ESP32 returns label, confidence, timing, raw output.

## Board-Side Stability Result

Stability report:

- `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_report.md`

Summary:

- `total_triggers=30`
- `success_count=30`
- `failure_count=0`
- `timeout_count=0`
- `success_rate=1.0000`
- `drop_rate=0.0000`
- `capture_p50_ms=926`
- `capture_p95_ms=930`
- `frontend_p50_ms=55`
- `frontend_p95_ms=55`
- `infer_p50_ms=2094`
- `infer_p95_ms=2094`
- `total_p50_ms=3075`
- `total_p95_ms=3079`
- `raw_uniform_count=0`
- `gate_pass=1`

Interpretation:

- The on-board inference path is functionally stable.
- The result is a runtime stability result, not a full labeled real-world accuracy benchmark.
- The `2.1 s` inference cost is now considered acceptable for this ESP32-S3 prototype after lab discussion.
- The project should stop treating latency as the main blocker and should move to control-link integration and demo evidence.

## Runtime Profiling Result

Per-op profiler artifact:

- `realworld/esp32/PHASE2_OPTIMIZATION_ATTEMPTS.md`

Latest profiled sample:

- `infer_ms=2095`
- `cpu_mhz=240`
- `op_conv_us=1572668`
- `op_fc_us=273764`
- `op_depthwise_us=11828`
- `op_softmax_us=6686`
- `op_unprofiled_est_us=230054`
- `op_conv_us_by_idx=[324408, 969348, 241323, 12759, 12470, 12360]`
- `op_fc_us_by_idx=[163739, 13097, 15958, 11264, 11209, 11139, 16130, 13571, 16029, 1598, 30]`

Reading:

- Conv2D consumes about `1.57 s` of the `2.10 s` inference path.
- The first three CNN stem Conv2D calls alone consume about `1.535 s`.
- This explains the observed runtime and gives a useful paper-level resource profile.
- It should not trigger another immediate model-search loop unless demo requirements later prove the runtime unacceptable.

## WiFi/TCP And Drone-Control Status

- WiFi diagnostics confirmed the board can connect to `NETGEAR64` and obtain an IP.
- TCP host mode has connected and exchanged status frames in testing.
- Current WiFi metric gate is not closed because the current `metrics_summary.csv` is a short run with `drop_rate=0.375`.
- Tello/drone control has not been integrated in this ESP32 local-inference path yet.
- The next system milestone is to connect ESP32 inference output to a safe control bridge and log the full decision-to-command path.

## Current Gate Status

- Phase 1 USB CDC host inference gate: passed and closed.
- Phase 2 board memory/op compatibility gate for current B candidate: passed.
- Phase 2 board stability gate over USB CDC: passed over 30 triggers.
- Runtime acceptance for current ESP32-S3 prototype: acceptable after lab discussion.
- WiFi/TCP formal metric gate: not closed with current artifacts.
- Drone-control demo gate: not started.
- Paper-writing pivot gate: ready to start using the deployment evidence above.

## Revised Next Actions

1. Freeze the current on-board inference implementation as the demo baseline.
2. Do not prioritize new model compression unless the control demo shows that the `2.1 s` inference cost is unacceptable in practice.
3. Build the control path in stages:
   - ESP32 local inference -> USB CDC or WiFi result event
   - result event -> host-side safety state machine
   - safety state machine -> dry-run command log
   - dry-run command log -> Tello SDK command bridge
   - no-propeller or grounded bench test
   - controlled low-risk demo
4. Define a safety state machine before any flight demo:
   - `IDLE`
   - `LISTENING`
   - `INTENT_PENDING`
   - `CONFIRMED_EMERGENCY`
   - `CONFIRMED_MOVEMENT`
   - `SAFE_HOLD`
   - `ERROR_HOLD`
5. Required demo logs:
   - timestamp
   - predicted label
   - confidence
   - inference latency
   - state-machine transition
   - command selected
   - command sent
   - command ack or timeout
6. Writing work should start now:
   - update `docs/paper_sensys2027/` to reflect completed on-board ESP32 inference
   - present the `2.1 s` inference profile as measured systems evidence
   - describe the next demo as the missing control-loop evidence, not as model feasibility work

## Main Evidence Paths

- Phase 1 closeout:
  - `weeklyresult/weekly_drone_2026w16/realworld/esp32_bench/phase1_closeout.md`
- Current local board stability:
  - `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_report.md`
  - `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_summary.csv`
  - `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_events.csv`
- Optimization and profiling diagnosis:
  - `realworld/esp32/PHASE2_OPTIMIZATION_ATTEMPTS.md`
- TFLM compatibility handoff:
  - `docs/realworld_esp32_tflm_profile_handoff.md`
- XIAO training/profile handoff:
  - `docs/realworld_esp32_xiao_entry_training_handoff.md`
- Existing real-world deployment plan:
  - `realworld/deployment_plan_xiaoesp32s3_tello_2026w16.md`
- Main firmware:
  - `realworld/esp32/firmware/esp32_bench/esp32_bench.ino`
  - `realworld/esp32/firmware/esp32_local_cdc_fast/esp32_local_cdc_fast.ino`
  - `realworld/esp32/firmware/esp32_local_cdc_profile_ops/esp32_local_cdc_profile_ops.ino`
- Host scripts:
  - `realworld/esp32/host/bench_server.py`
  - `realworld/esp32/host/local_cdc_trigger.py`

## Repo State For Handoff

- Current local commit: `ec30982a50e50c67d7a32944a8c0f25c28dd20fe`
- Current untracked item observed during handoff:
  - `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/tflm_candidate_precheck.json`
- Many `realworld/` and `weeklyresult/` artifacts are runtime artifacts and may not be git-tracked. Use the evidence paths above directly when preparing the project report.
