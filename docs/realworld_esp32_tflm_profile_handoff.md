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

## Latest W17 Deployment Receipt

Date: 2026-04-30

Deployment-agent report:

- `docs/realworld_esp32_weekly_project_report_handoff.md`

Candidate:

- model: `B_small_teacher_student`
- profile: `xiao_bottleneck256_tflm`
- frozen model copy: `realworld/esp32/models/B_small_teacher_student/`
- full-integer TFLite: `realworld/esp32/phase2_artifacts/B_small_teacher_student_full_integer.tflite`
- precheck: `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/tflm_candidate_precheck.json`

Compatibility gate:

- flatbuffer size: `780416` bytes
- quantization: full-integer int8 I/O
- op mix: `CONV_2D=6`, `DEPTHWISE_CONV_2D=1`, `FULLY_CONNECTED=11`, `SOFTMAX=2`
- grouped temporal `CONV_2D`: not detected

Board-side result:

- stable firmware: `realworld/esp32/firmware/esp32_local_cdc_fast/esp32_local_cdc_fast.ino`
- local loop: onboard mic capture -> logmel frontend -> int8 TFLM inference -> USB CDC result reporting
- stability report: `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_report.md`
- stability result: `30/30` triggers succeeded, drop rate `0.0`, no uniform raw outputs
- timing: capture p50 about `926 ms`, frontend p50 about `55 ms`, inference p50 about `2094 ms`, total p50 about `3075 ms`

Meeting decision:

- Treat the current ESP32 local inference implementation as the W18 demo baseline.
- Do not prioritize more compression or retraining unless the safe-control demo proves `~2.1 s` inference latency unacceptable.
- Next technical gate is not model feasibility; it is safe control integration and repeatable demo evidence.

## Latest W19 RT1S Deployment Receipt

Date: 2026-05-17

Candidate:

- model/run: `xiao_rt1s_c32_b256_samearch_ts`
- source commit: `6909f45667f455398a1d6dcdade24d129d6ecbbd`
- student checkpoint:
  `saved_models/weekly_drone_2026w19/xiao_rt1s_c32_b256_samearch_ts/student_kd_best.weights.h5`
- validation output:
  `weeklyresult/weekly_drone_2026w19/realworld/esp32_rt1s_c32_validation/validation_report.md`

Offline quality boundary:

- noisy accuracy: about `0.85`
- emergency precision/recall/F1: `0.95 / 0.70 / 0.81`
- This is below the W17 `B_small_teacher_student` quality result, so keep
  `w14 preprocess_ext` as the main model-quality anchor and describe this W19
  candidate as the runtime deployment candidate.

Compatibility gate:

- full-integer TFLite size: `589488` bytes
- SHA256:
  `e43cc3f7b7f7e2413bdc35765bca5d45473b5b1b63fdee1a0a28d3e9de0d2ab8`
- op mix: `CONV_2D=6`, `DEPTHWISE_CONV_2D=1`, `FULLY_CONNECTED=10`, `SOFTMAX=2`
- grouped temporal `CONV_2D`: `false`
- Dense per-channel issue count: `0`

Board-side result:

- XIAO smoke `Invoke()` returned successfully.
- smoke latency: `667382 us`
- smoke top label: `emergency`
- local CDC stability: `30/30` triggers succeeded, drop rate `0.0`,
  raw uniform count `0`
- local CDC p50/p95:
  - capture: `923/927 ms`
  - frontend: `55/55 ms`
  - pure TFLM `Invoke()`: `627/627 ms`
  - total: `1605/1609 ms`
- speedup versus W17 `B_small_teacher_student`: `2094 ms -> 627 ms`, about
  `3.34x`

Decision:

- `GO` for replacing `B_small_teacher_student` as the ESP32 runtime deployment
  candidate.
- This satisfies the board-side pure `Invoke <= 1 s` target.
- Do not describe it as end-to-end response below `1 s`, because the full
  1-second capture + frontend + inference path is about `1.6 s`.
- Do not describe it as semantic safety validation; live semantic checks and
  drone-control safety gates remain separate work.

## Latest W19 RT1S Control-Chain Receipt

Date: 2026-05-17

Scope:

- ESP32 local inference -> host event log -> Tello dry/no-prop/grounded command
  decision.
- No UDP was sent.
- No Tello connection or flight validation was performed.
- This is not semantic safety validation.

Runtime:

- candidate: `xiao_rt1s_c32_b256_samearch_ts`
- source commit: `6909f45667f455398a1d6dcdade24d129d6ecbbd`
- model SHA256:
  `e43cc3f7b7f7e2413bdc35765bca5d45473b5b1b63fdee1a0a28d3e9de0d2ab8`
- report:
  `weeklyresult/weekly_drone_2026w19/realworld/tello_rt1s_c32_chain/rt1s_control_chain_report.md`

Integration changes:

- firmware status/hello now emit `runtime_candidate`, `build_tag`, and
  `model_sha256`.
- host collector records runtime metadata and can gate on expected
  candidate/SHA/kernel.
- dry command dispatch defaults to RT1S C32 and rejects runtime mismatch before
  mapping labels to command decisions.
- command mapping is versioned as `tello_dry_rt1s_c32_v1`.
- `movement` remains `noop` plus manual override; coarse movement is not mapped
  to a direct flight command.

Validation:

- metadata smoke: `3/3` success, runtime gate `PASS`.
- observed kernel path: `espnn_recording_default_softmax`.
- latency smoke: `infer_p50=627 ms`, `total_p50=1606 ms`.
- actual replay: `dry_gate_pass=1`, `error_count=0`, all live labels were
  `unknown`, so `ground/no-prop=NO-GO` and `flight=NO-GO`.
- manual fixture with override: `emergency_exercised=1`, `movement_seen=1`,
  `manual_override_path_pass=1`, `ground/no-prop=GO`, `flight=NO-GO`.
- manual fixture without override: movement is correctly blocked.

Decision:

- Runtime chain integration is `PASS`.
- RT1S C32 is now the default ESP32 runtime candidate for the host-mediated
  control-chain lane.
- Live no-prop/grounded bench is `CONDITIONAL GO`, requiring one live emergency
  event, one live movement event, manual override enabled, and `error_count=0`.
- Flight validation remains `NO-GO`.

Design note:

- A dual-core ESP32-S3 pipeline may improve steady-state continuous inference:
  one core can capture the next 1-second audio window while the other core runs
  frontend/TFLM/reporting for the previous window.
- This should be treated as a throughput design, not as proof of first-event
  latency below `1 s`; current first-window total remains about `1.6 s`.

## Latest W19 Dual-Core Pipeline Design Receipt

Date: 2026-05-17

Scope:

- Design-only analysis.
- No firmware changes, no model training, no Tello connection, and no UDP.

Outputs:

- `weeklyresult/weekly_drone_2026w19/realworld/esp32_dual_core_pipeline_design/dual_core_pipeline_design.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_dual_core_pipeline_design/timing_fields.csv`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_dual_core_pipeline_design/implementation_plan.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_dual_core_pipeline_design/validation_plan.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_dual_core_pipeline_design/decision_summary.md`

Core timing:

- capture: about `923 ms`
- frontend: about `55 ms`
- TFLM `Invoke`: about `627 ms`
- sequential first-window total: about `1605 ms`
- processing after capture: about `55 + 627 = 682 ms`

Decision:

- Steady-state one inference opportunity per fixed `1 s` audio window is
  plausible if capture and frontend/TFLM/reporting truly overlap.
- First-window end-to-end latency below `1 s` is not supported, because the
  system must first collect a full `1 s` audio window.
- Current status is design proposal only:
  implementation `NOT IMPLEMENTED`, validation `NOT VALIDATED`.

Recommended implementation boundary if approved:

- Add a compile-time dual-core pipeline mode.
- Keep current single-path mode as default until validation passes.
- Use two FreeRTOS tasks:
  - `audio_capture_task`
  - `inference_report_task`
- Use a two- or three-buffer PCM pool; three buffers are preferred if memory
  allows.
- Enforce buffer ownership with `free_q` and `ready_q`.
- Keep `MicroInterpreter`, TFLM input/output tensors, and frontend scratch
  single-owned by the inference task.
- Use USB CDC reporting only for first validation.
- Do not connect Tello or send UDP in this validation lane.

Validation gates:

- Mode A: capture-only cadence.
- Mode B: synthetic `682 ms` processing load.
- Mode C: full RT1S C32 frontend + TFLM + USB CDC.
- Mode D: core-affinity A/B.
- Mode E: optional transport stress after USB CDC passes.

Paper boundary:

- Allowed after validation: steady-state `1 s` throughput language, if metrics
  pass.
- Not allowed from this design alone: first command under `1 s`, validated drone
  safety behavior, or real-world semantic recognition accuracy.

## Latest W19 Dual-Core Pipeline Validation Receipt

Date: 2026-05-18

Scope:

- Firmware/runtime validation of the ESP32-S3 dual-core capture/inference
  pipeline.
- Runtime candidate: `xiao_rt1s_c32_b256_samearch_ts`.
- USB CDC report only.
- No Tello connection, no UDP, no model training, and no paper edit.
- No new commit was created for this validation pass.

Changed files reported by deployment agent:

- `realworld/esp32/firmware/esp32_local_cdc_fast/esp32_local_cdc_fast.ino`
- `realworld/esp32/firmware/esp32_local_cdc_fast/config.h`
- `realworld/esp32/firmware/esp32_local_cdc_fast/pipeline_validation_config.h`
- `realworld/esp32/host/pipeline_validation_runner.py`

Outputs:

- `weeklyresult/weekly_drone_2026w19/realworld/esp32_dual_core_pipeline_validation/dual_core_pipeline_validation_report.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_dual_core_pipeline_validation/dual_core_pipeline_validation_summary.csv`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_dual_core_pipeline_validation/result_tree.txt`

Gate verdict:

- `steady_state_1s_throughput`: `PASS`
- `first_window_subsecond_latency`: `FAIL`
- `semantic_accuracy_validated`: `NO`
- `flight_validation`: `NO`

Mode summary:

- Mode A capture-only: `PASS`, success `120/120`, drop `0`, overrun `0`,
  e2e p95 `1005.007 ms`.
- Mode B synthetic `682 ms`: `PASS`, success `120/120`, drop `0`, overrun `0`,
  e2e p95 `1687.223 ms`.
- Mode C full RT1S C32: `PASS`, success `120/120`, drop `0`, overrun `0`,
  output period p95 `1005.17 ms`, e2e p95 `1694.93 ms`, first-window e2e
  `1605.885 ms`.

Full RT1S C32 timing detail:

- capture p95: `1004 ms`
- frontend p95: `56 ms`
- TFLM `Invoke` p95: `632 ms`
- processing latency p95: about `689.95 ms`
- queue depth p95: `0.0`

Implementation notes:

- Default firmware path still falls back to single-path mode.
- Pipeline validation uses a local header switch rather than
  `--build-property build.extra_flags=...`; overriding `build.extra_flags`
  removed Arduino-generated USB CDC / PSRAM macros.
- Pipeline mode uses 3-buffer PCM ownership with `free_q` / `ready_q`.
- PCM buffers are allocated in PSRAM to avoid static DRAM pressure.
- TFLM interpreter, tensors, frontend scratch, and `Invoke()` are single-owned
  by the inference/report task in pipeline mode.
- Git tracking note: `realworld/` and `weeklyresult/.../realworld/` are ignored
  in the current worktree. The firmware/host changes and validation receipts are
  local artifacts until explicitly consolidated into tracked handoff files or
  force-added with an approved commit plan.

Decision:

- The RT1S C32 ESP32 path now has runtime evidence for steady-state one
  inference opportunity per fixed `1 s` audio window.
- This evidence should become the runtime baseline for grounded/no-prop
  control-chain timing.
- Do not claim first-window latency below `1 s`.
- Do not claim semantic safety validation or flight validation.
