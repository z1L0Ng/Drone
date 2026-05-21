# Weekly TODO (CDT, Thursday-cycle 2026w19)

Meeting checkpoint: Thursday 2026-05-21.

Planning cycle: Friday 2026-05-15 -> Thursday morning 2026-05-21.

Project target: SenSys 2027 first-round submission.

## Current Repo Audit

Initial audit time: 2026-05-16 CDT.

- Branch: `main`
- HEAD: `3d5eba17ade035f030020db283897f0765916b7a`
- Initial worktree status: clean
- Current note: the user later updated `docs/paper_sensys2027/` from the latest
  Overleaf version, so downstream agents must re-run `git status` and treat the
  current paper files as user-provided draft state.
- Latest tracked `weeklyresult/` on `main`: `weekly_drone_2026w18`
- W19 first-batch baseline results are retained on
  `codex/track-d-baseline-results-20260514` and are not merged into `main`.

## Weekly Goal

This week is focused on converting the current voice-recognition prototype into
a stronger SenSys 2027 system story:

1. Establish whether the ESP32 on-device path can support a credible
   real-time onboard story with inference latency at or below the 1 s audio
   capture window.
2. Build the host-mediated control chain from ESP32 event output to a
   conservative Tello command boundary, with Bluetooth as the preferred event
   transport and USB CDC retained as fallback.
3. Redesign evaluation beyond offline accuracy: testing conditions, response
   time, safety-state behavior, and user-study/data collection protocol.
4. Prepare paper restructuring after VP's introduction pass: related work after
   introduction, reduced subsections, clearer motivation, stronger figures, and
   a first-page representative visual.

## Management Rule

Planning may use four tracks for readability, but execution prompts must be
addressed to the active agent role rather than to a track name.

Active agent mapping:

- `esp32部署agent`: real-time onboard latency audit, ESP32 deployment
  optimization, Bluetooth/USB host bridge, Tello dry/no-prop/grounded
  validation.
- `模型设计agent`: model architecture analysis and compression planning for the
  `<=1 s` ESP32 inference target. This agent proposes model profiles and
  training plans, but does not train.
- `论文写作agent`: paper structure rewrite, section rewrite outside
  intro/abstract, figure plan, terminology alignment.
- `evaluation agent`: testing-condition matrix, response-time comparison,
  user-study protocol, safety-state metrics.
- `服务器训练agent`: full training or new deployment model training only after
  explicit project-management approval.
- `项目管理agent`: planning, dispatch, acceptance, Notion/repo docs sync, and
  handoff logging.

Execution prompts must not use `Track A/B/C/D` labels. They must specify the
agent role, scope, forbidden actions, evidence inputs, deliverables, and
acceptance criteria.

## 2026-05-14 Meeting Notes

Summary:

- The voice-command safety mechanism should be framed as an additional UAV
  safety layer, not a replacement for existing safety mechanisms.
- Direct quantitative comparison with other safety mechanisms is difficult
  because the fault types, trigger sources, and response semantics differ.
- Response time may be a feasible comparison axis.
- Current recognizer quality is better than the first-batch baselines, but the
  paper should not rely only on accuracy/F1.
- Paper revisions should reorganize sections, place related work after the
  introduction, clarify motivation, reduce subsection fragmentation, and improve
  visuals.
- A one-minute demo video with multiple people issuing voice commands and drone
  responses is proposed for reviewer understanding.
- VP will complete a first pass of the introduction for later alignment.

Meeting action items:

- [ ] Expand baseline comparisons under different testing conditions and write
  the evaluation section.
- [ ] Revise paper structure: related works after introduction, motivation
  clarified, fewer subsections.
- [x] Approve an AI-generated representative first-page picture as a temporary
  visual candidate.
- [ ] Produce a one-minute demo video storyboard and, later, the demo video.
- [ ] After VP introduction first pass, rewrite the remaining paper sections.

## Planning Tracks

### Track A: Real-time onboard inference

Planning owner: `esp32部署agent` after project-management dispatch.

Objective:
- Determine whether the current ESP32 deployment path can reach or credibly
  approach `<=1 s` inference latency.

Tasks:
- [x] Audit current timing source for capture, frontend, TFLM invoke,
  serialization, and host transfer.
- [x] Confirm whether the reported `~2094 ms` inference p50 is pure TFLM invoke
  time or includes overhead.
- [x] Identify low-risk optimization opportunities before proposing new model
  training.
- [x] Return a go/no-go decision for current `B_small_teacher_student` versus a
  future smaller deployment student.
- [ ] Ask `模型设计agent` to analyze how to reduce early CNN stem compute while
  preserving recognizer quality before any server training is launched.

Acceptance criteria:
- [x] A timing breakdown exists.
- [x] The bottleneck is explicitly identified.
- [x] No new training is started.
- [x] If a new deployment model is needed, only a server-training handoff plan is
  returned.

### Track B: Host-mediated Tello control chain

Planning owner: `esp32部署agent` after project-management dispatch.

Objective:
- Build toward ESP32 event output -> Bluetooth/USB host transport -> Mac host
  safety state machine -> Tello SDK command boundary.

Tasks:
- [x] Evaluate ESP32-S3 Bluetooth event transport to Mac.
- [x] Preserve USB CDC as fallback if Bluetooth is unstable.
- [ ] Keep event schema compatible with existing safety fields:
  `safety_hold`, `manual_override`, `command_result`, `result_detail`.
- [ ] Validate dry/no-prop/grounded command behavior before any flight-adjacent
  claim.
- [ ] Cover `emergency`, `movement`, and `unknown` event paths.

Acceptance criteria:
- No direct coarse `movement` -> flight command mapping.
- Manual override remains first-class.
- Evidence type is clearly labeled as dry-run, no-prop, grounded, or flight.

### Track C: Paper restructuring and writing

Planning owner: `论文写作agent` after VP introduction first pass.

Objective:
- Rewrite sections outside intro/abstract so the paper reads as a
  voice-command UAV safety mechanism paper, not a generic noisy KWS paper.

Tasks:
- [ ] Move related work after introduction.
- [ ] Simplify motivation and make it directly serve the safety-layer problem.
- [ ] Rewrite system/architecture around
  `audio -> intent evidence -> safety state -> conservative control boundary`.
- [ ] Rewrite evaluation around baseline quality, latency/runtime,
  safety-state behavior, user study, and demo evidence.
- [ ] Reduce subsection fragmentation.
- [ ] Prepare figure plan and one-minute demo storyboard.

Acceptance criteria:
- No claim that the system has already validated drone safety.
- No claim that runtime stability proves semantic real-world accuracy.
- Contributions emphasize additional safety layer, intent-state mediation,
  real-time onboard constraint, and end-to-end safety-state/control evidence.

### Track D: Evaluation and user-study design

Planning owner: `evaluation agent` after project-management dispatch.

Objective:
- Expand evaluation into a defensible system-evaluation plan for the
  voice-command UAV safety layer.

Tasks:
- [x] Define testing-condition matrix: SNR, rotor playback / real rotor,
  speaker distance, angle, volume, and background noise.
- [x] Define user-study/data-collection protocol with participant metadata,
  utterance list, environment metadata, labeling fields, and output structure.
- [x] Define response-time comparison against manual stop/controller action and
  host-command path.
- [x] Define safety-state metrics: safe-hold ratio, fallback correctness,
  manual override coverage, unsafe-command attempt count, and ack/timeout rate.
- [x] Clarify how paper should explain lack of a shared benchmark against
  geofencing, obstacle avoidance, return-to-home, and RC failsafe.

Acceptance criteria:
- [x] Recognizer accuracy, latency/runtime, safety-state behavior, and user-study
  evidence are separated.
- [x] Existing UAV safety mechanisms are not treated as classifier baselines.
- [x] The plan can be inserted into `docs/paper_sensys2027/sections/6evaluation.tex`
  after approval.

## Receipts: 2026-05-16

### Evaluation protocol receipt

Scope:
- Planning only.
- No training, no server task, no ESP32/Tello code changes, no `references.bib`
  update.

Outputs:
- `weeklyresult/weekly_drone_2026w19/evaluation_protocol/testing_condition_matrix.md`
- `weeklyresult/weekly_drone_2026w19/evaluation_protocol/user_study_protocol.md`
- `weeklyresult/weekly_drone_2026w19/evaluation_protocol/response_time_metric_plan.md`
- `weeklyresult/weekly_drone_2026w19/evaluation_protocol/safety_state_metrics.md`
- `weeklyresult/weekly_drone_2026w19/evaluation_protocol/paper_integration_plan.md`

Key decisions:
- `6evaluation.tex` should separate four evidence classes:
  recognizer quality, latency/runtime, safety-state/bridge behavior, and
  user-study/demo evidence.
- W19 baseline results remain unmerged branch evidence and cannot be mixed into
  a final leaderboard without comparability audit.
- UAV safety mechanisms should be compared by mechanism matrix and response-time
  definitions, not as classifier baselines.

### ESP32 latency audit receipt

Scope:
- ESP32/XIAO runtime timing audit only.
- No model training, no server job, no paper edit, no Tello control.

Outputs:
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/latency_audit.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/timing_breakdown.csv`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/one_second_feasibility_decision.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/training_handoff_plan.md`

Key findings:
- Runtime stability gate remains `PASS`: W17 30/30 triggers succeeded, drop rate
  `0.0`.
- `<=1s` inference gate is `FAIL`: current pure TFLM `Invoke()` p50 is
  `2094 ms`.
- Current timing p50: capture `926 ms`, frontend `55 ms`, TFLM invoke
  `2094 ms`, USB/host receive about `5.5 ms`, device total `3075 ms`, host
  elapsed `3080 ms`.
- Bottleneck is early CNN stem `CONV_2D`, not host/USB/frontend/measurement.
- First three CNN stem `CONV_2D` calls account for about `1535 ms`, with the
  largest single conv about `969 ms`.
- Low-risk firmware optimization is unlikely to reduce current inference from
  `2094 ms` to `<=1000 ms`.

Next decision:
- Ask `模型设计agent` for a no-training architecture analysis focused on
  reducing early CNN stem compute while preserving accuracy/emergency recall.
- Only after model-design review should `服务器训练agent` receive a training
  handoff for `rt1s_tiny_student` or an equivalent candidate.

### Model design `<=1s` receipt

Scope:
- Read-only architecture analysis only.
- No model training, no code changes, no server task, no ESP32/Tello changes,
  no paper edit.

Key findings:
- The current `2094 ms` p50 is pure TFLM `Invoke()` time.
- The dominant bottleneck is the current `xiao_bottleneck256_tflm` early CNN
  stem over input `(256, 32, 1)`, not the frontend, USB/host transfer, softmax,
  or temporal depthwise convolution.
- Current stem pattern uses three high-resolution `Conv2D(3x3, C=64)` stages
  with pooling `(4,1)/(4,1)/(2,1)`.
- Estimated stem MAC is about `99M`; the first three stem Conv2D calls account
  for about `1535 ms` on board.
- Keep the first training batch on the existing `(256,32,1)` logmel frontend to
  preserve W14/W17 comparability and the current paper story.

Recommended first-batch candidates:
- `xiao_rt1s_c32_b256_tflm`
  - Intended as the accuracy-preserving candidate.
  - Proposed structure: `conv_filters=32`, `num_layers=1`, attention
    `head_size=32`, `num_heads=4`, `ff_dim=128`, `fnn=[128]`,
    `branchformer_bottleneck_dim=256`, `branchformer_conv_impl=depthwise_conv1d`.
  - Expected Invoke range: about `850-1100 ms`.
  - Risk: medium; emergency recall may drop.
- `xiao_rt1s_c24_b192_tflm`
  - Intended as the latency-prioritizing candidate.
  - Proposed structure: `conv_filters=24`, `num_layers=1`, attention
    `head_size=24`, `num_heads=3`, `ff_dim=96`, `fnn=[96]`,
    `branchformer_bottleneck_dim=192`, `branchformer_conv_impl=depthwise_conv1d`.
  - Expected Invoke range: about `650-900 ms`.
  - Risk: medium-high; stronger accuracy and emergency-recall drop risk.

Deferred candidates:
- `xiao_rt1s_c24_tpool2_b192_tflm`: defer because time pooling may damage short
  emergency cues.
- `xiao_rt1s_dsstem_c24_b192_tflm`: defer because it requires `model.py`
  changes and introduces more implementation/training risk.

Manager interpretation:
- First training lane should be A + B only.
- A/B give a clean Pareto test: preserve quality versus pass `<=1s`.
- Server training is not yet approved. The next approval gate is local profile
  integration, smoke validation, commit, and push.

### RT1S profile integration receipt

Scope:
- Local profile integration only.
- No training, no server task, no paper edit, no ESP32/Tello edit, no weekly
  todo edit by the model-design agent.

Code change:
- `src/model_config.py`
- `src/model.py` unchanged.

Added profiles:
- `xiao_rt1s_c32_b256_tflm`
  - `conv_filters=32`, `num_layers=1`, `head_size=32`, `num_heads=4`,
    `ff_dim=128`, `fnn_units=[128]`, `branchformer_bottleneck_dim=256`,
    `branchformer_conv_impl=depthwise_conv1d`.
  - smoke parameter count: `524,675`.
- `xiao_rt1s_c24_b192_tflm`
  - `conv_filters=24`, `num_layers=1`, `head_size=24`, `num_heads=3`,
    `ff_dim=96`, `fnn_units=[96]`, `branchformer_bottleneck_dim=192`,
    `branchformer_conv_impl=depthwise_conv1d`.
  - smoke parameter count: `279,387`.

Added aliases:
- `rt1s_c32_b256_tflm` -> `xiao_rt1s_c32_b256_tflm`
- `rt1s_c24_b192_tflm` -> `xiao_rt1s_c24_b192_tflm`

Smoke validation reported by model-design agent:
- `python -m py_compile src/model_config.py src/model.py`: pass.
- Keras build + summary + synthetic forward: pass for both profiles.
- Structure-level TFLite graph precheck with random weights:
  - both profiles keep `DEPTHWISE_CONV_2D=1`.
  - no grouped temporal `CONV_2D` fallback observed.
  - op family remains aligned with the current TFLM candidate family.

Important caveats:
- Random-weight TFLite graph precheck proves structure compatibility only; it
  does not prove accuracy or real board latency.
- Current worktree now includes a generated `src/__pycache__/model.cpython-311.pyc`
  modification from smoke execution; this should be cleaned or excluded before
  committing.
- Server training still requires a clean committed SHA and push.

Next decision:
- Selectively stage and commit `src/model_config.py` plus W19 management docs
  after cleanup, leaving user-provided paper draft changes untouched.
- W19 RT1S training will be a documented Mac-local exception so it can be
  managed inside the Codex app. It must still use a committed SHA and write
  complete logs/artifacts.
- Dispatch local Mac training for `xiao_rt1s_c32_b256_tflm` first and
  `xiao_rt1s_c24_b192_tflm` second, using `WEEKLY_TAG=drone_2026w19` and
  `weeklyresult/weekly_drone_2026w19/<candidate>/`.

### W19 local training exception

Reason:
- User explicitly approved running this week's RT1S training on the Mac instead
  of the server so Codex app can manage the runs more directly.

Scope:
- Applies only to W19 RT1S tiny-student training candidates:
  `xiao_rt1s_c32_b256_tflm` and `xiao_rt1s_c24_b192_tflm`.
- Does not change the default policy: future full training normally belongs on
  the server unless separately approved.

Local-run requirements:
- Training still needs a clean committed SHA before launch.
- Use the local `drone` conda environment unless a blocker is found.
- Write logs under `logs/`.
- Write outputs under:
  - `saved_models/weekly_drone_2026w19/<candidate>/`
  - `weeklyresult/weekly_drone_2026w19/<candidate>/`
- Record startup receipt with first 30 log lines.
- Record completion receipt with last 50 log lines, checkpoint path, result tree,
  and key metrics.
- Do not overwrite the current `B_small_teacher_student` deployment baseline.
- Do not edit paper text during training.

Expected local training priority:
1. `xiao_rt1s_c32_b256_tflm`
2. `xiao_rt1s_c24_b192_tflm`

### RT1S local training receipt: Candidate A

Scope:
- Mac-local training exception.
- Candidate B was not started.
- No paper, ESP32, Tello, weekly todo, or technical spec edits by the training
  agent.

Run:
- Candidate: `xiao_rt1s_c32_b256_tflm`
- Commit SHA: `6909f45667f455398a1d6dcdade24d129d6ecbbd`
- Log:
  `logs/weekly_drone_2026w19_xiao_rt1s_c32_b256_tflm_local_20260516_133056.log`
- Checkpoint:
  `saved_models/weekly_drone_2026w19/xiao_rt1s_c32_b256_tflm/student_kd_best.weights.h5`
- Result dir:
  `weeklyresult/weekly_drone_2026w19/xiao_rt1s_c32_b256_tflm/`

Metrics:
- Clean test accuracy: `0.3354`
- Noisy test accuracy at `SNR=-10 dB`: `0.3344`
- Emergency precision/recall/F1: `0.80 / 0.00 / 0.00`
- Movement precision/recall/F1: `0.33 / 1.00 / 0.50`
- Unknown precision/recall/F1: `0.00 / 0.00 / 0.00`

Manager decision:
- Candidate A is not usable as a recognizer candidate.
- Do not start Candidate B with the same recipe.
- This failure is likely a teacher/student recipe issue, not enough evidence to
  reject the `xiao_rt1s_c32_b256_tflm` architecture. The failed run used
  `teacher_profile=xiao_bottleneck256_tflm` and
  `student_profile=xiao_rt1s_c32_b256_tflm`.
- The prior successful W17 `B_small_teacher_student` run also used
  `embed_only`, but it used the same architecture/scale for teacher and student:
  `teacher_profile=xiao_bottleneck256_tflm` and
  `student_profile=xiao_bottleneck256_tflm`. That makes same-profile clean
  teacher -> noisy student the next more evidence-aligned retry.

Next action:
- Rerun Candidate A as a same-profile teacher/student experiment:
  `teacher_profile=xiao_rt1s_c32_b256_tflm`,
  `student_profile=xiao_rt1s_c32_b256_tflm`, clean teacher then noisy student.
- Keep `embed_only` as the first retry to preserve comparability with the W17
  same-profile success.
- Only if the same-profile retry still collapses should we switch to
  `ce_logits_embed` or supervised prewarm.
- Candidate B remains paused until Candidate A shows non-collapsed validation
  behavior under the same-profile recipe.

### RT1S local training receipt: Candidate A same-profile rerun

Scope:
- Mac-local training exception.
- Candidate B was not started.
- No OOM, NaN, or traceback reported.

Run:
- Candidate/run name: `xiao_rt1s_c32_b256_samearch_ts`
- Commit SHA: `6909f45667f455398a1d6dcdade24d129d6ecbbd`
- Log:
  `logs/weekly_drone_2026w19_xiao_rt1s_c32_b256_samearch_ts_local_20260516_181748.log`
- Teacher checkpoint:
  `saved_models/weekly_drone_2026w19/xiao_rt1s_c32_b256_samearch_ts/teacher_clean_best.weights.h5`
- Student checkpoint:
  `saved_models/weekly_drone_2026w19/xiao_rt1s_c32_b256_samearch_ts/student_kd_best.weights.h5`
- Result dir:
  `weeklyresult/weekly_drone_2026w19/xiao_rt1s_c32_b256_samearch_ts/`

Confirmed config:
- `KD_TEACHER_MODEL_PROFILE=xiao_rt1s_c32_b256_tflm`
- `KD_STUDENT_MODEL_PROFILE=xiao_rt1s_c32_b256_tflm`
- `KD_REUSE_TEACHER=0`
- `KD_DISTILL_VARIANT=embed_only`
- stats branch off for teacher/student
- emergency prosody augmentation on for student and off for teacher

Metrics:
- Student clean test accuracy: `0.8674`
- Student noisy test accuracy at `SNR=-10 dB`: `0.8481`
- Emergency noisy precision/recall/F1: `0.95 / 0.70 / 0.81`
- Movement noisy precision/recall/F1: `0.77 / 0.93 / 0.84`
- Unknown noisy precision/recall/F1: `0.87 / 0.92 / 0.89`

Manager decision:
- Same-profile clean teacher/noisy student fixed the prior collapse pattern.
- This is a usable RT1S quality candidate for deployment validation, but it is
  still below the W17 `B_small_teacher_student` quality anchor:
  W17 noisy accuracy about `0.8728`, emergency recall about `0.79`,
  emergency F1 about `0.86`.
- Do not start Candidate B yet. First validate whether C32 actually improves
  ESP32 Invoke latency enough to justify the quality tradeoff.

Next action:
- Dispatch ESP32 deployment agent for full-integer TFLite export, op precheck,
  XIAO allocation/invoke smoke, and board-side latency profile for
  `xiao_rt1s_c32_b256_samearch_ts`.
- Candidate B remains paused until C32 latency evidence is known.

### ESP32 RT1S C32 deployment validation receipt

Scope:
- ESP32 deployment/runtime validation only.
- No model training, no paper edit, no Tello control.

Inputs:
- Candidate: `xiao_rt1s_c32_b256_samearch_ts`
- Commit SHA: `6909f45667f455398a1d6dcdade24d129d6ecbbd`
- Student weights:
  `saved_models/weekly_drone_2026w19/xiao_rt1s_c32_b256_samearch_ts/student_kd_best.weights.h5`
- Run config:
  `weeklyresult/weekly_drone_2026w19/xiao_rt1s_c32_b256_samearch_ts/run_config.json`
- Noisy report:
  `weeklyresult/weekly_drone_2026w19/xiao_rt1s_c32_b256_samearch_ts/classification_report_noisy.txt`

Outputs:
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_rt1s_c32_validation/startup_receipt.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_rt1s_c32_validation/commands.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_rt1s_c32_validation/validation_report.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_rt1s_c32_validation/result_tree.txt`
- full-integer TFLite:
  `weeklyresult/weekly_drone_2026w19/realworld/esp32_rt1s_c32_validation/xiao_rt1s_c32_b256_samearch_ts_full_integer.tflite`

Key results:
- Full-integer TFLite size: `589488` bytes
- TFLite SHA256:
  `e43cc3f7b7f7e2413bdc35765bca5d45473b5b1b63fdee1a0a28d3e9de0d2ab8`
- Op precheck: `CONV_2D=6`, `DEPTHWISE_CONV_2D=1`,
  `FULLY_CONNECTED=10`, `SOFTMAX=2`
- grouped temporal `CONV_2D`: `false`
- Dense per-channel issue count: `0`
- Desktop probe: Keras `emergency:1.000000`, TFLite `emergency:0.996094`,
  labels match
- XIAO smoke Invoke: `667382 us`, top label `emergency`, raw
  `[127,-128,-128]`
- Local CDC 30-run: `30/30` success, `drop_rate=0.0`,
  `raw_uniform_count=0`
- Latency: `infer_p50=627 ms`, `infer_p95=627 ms`,
  `total_p50=1605 ms`, `total_p95=1609 ms`
- Speedup versus `B_small_teacher_student`: `2094 ms -> 627 ms`, about `3.34x`

Manager decision:
- `GO` for replacing `B_small_teacher_student` as the ESP32 runtime deployment
  candidate.
- This passes the board-side pure `Invoke <= 1s` gate.
- Do not frame this as end-to-end response below `1s`: total local CDC p50 is
  still about `1605 ms` because capture is about `923 ms` and frontend about
  `55 ms`.
- Do not frame this as semantic safety validation: noisy accuracy is about
  `0.85`, emergency recall is `0.70`, and live semantic/control safety gates
  remain separate.

Next action:
- Use `xiao_rt1s_c32_b256_samearch_ts` for the ESP32 runtime path in the
  host-mediated Tello control chain.
- Update paper/evaluation language to distinguish:
  `w14 preprocess_ext` as model-quality anchor,
  `xiao_rt1s_c32_b256_samearch_ts` as runtime deployment candidate, and
  `B_small_teacher_student` as the previous slower deployment baseline.

### RT1S C32 host-mediated control-chain receipt

Scope:
- ESP32 local inference -> host event log -> Tello dry/no-prop/grounded command
  decision.
- No UDP was sent, no Tello connection was made, no flight validation was run,
  and no semantic safety validation is claimed.

Outputs:
- `weeklyresult/weekly_drone_2026w19/realworld/tello_rt1s_c32_chain/rt1s_control_chain_report.md`
- `weeklyresult/weekly_drone_2026w19/realworld/tello_rt1s_c32_chain/result_tree.txt`

Runtime integration:
- `esp32_local_cdc_fast` now emits `runtime_candidate`, `build_tag`, and
  `model_sha256` in `hello` and `status`.
- `local_cdc_trigger.py` records and can validate the RT1S candidate, SHA, and
  kernel path.
- `dry_command_dispatch.py` defaults to RT1S C32 and rejects runtime metadata
  mismatch before command dispatch.
- `label_command_mapping.json` is versioned as `tello_dry_rt1s_c32_v1`.
- `movement` remains `noop` plus `manual_override` required.
- `udp_sent=false` remains the dry/no-prop/grounded boundary.

Key results:
- ESP32 metadata smoke: `3/3` success, runtime gate `PASS`.
- Observed runtime: `xiao_rt1s_c32_b256_samearch_ts`.
- Observed SHA:
  `e43cc3f7b7f7e2413bdc35765bca5d45473b5b1b63fdee1a0a28d3e9de0d2ab8`.
- Observed kernel path: `espnn_recording_default_softmax`.
- Latency smoke: `infer_p50=627 ms`, `total_p50=1606 ms`.
- Actual replay dispatch: `dry_gate_pass=1`, `error_count=0`,
  `flight=NO-GO`, `ground/no-prop=NO-GO`; all observed live labels were
  `unknown`.
- Manual fixture with override: `emergency_exercised=1`,
  `movement_seen=1`, `manual_override_path_pass=1`, `ground/no-prop=GO`,
  `flight=NO-GO`.
- Manual fixture without override: movement is correctly `dry_blocked`.

Manager decision:
- Runtime chain integration: `PASS`.
- RT1S C32 replacement as runtime path: `PASS`.
- Dry/no-prop/grounded boundary preservation: `PASS`.
- Flight validation: `NO-GO`.
- Live no-prop/grounded bench readiness: `CONDITIONAL GO`.

Next live gate:
- Run one live `emergency` utterance and one live `movement` utterance through
  the RT1S runtime with manual override enabled and
  `control_boundary=no_prop_grounded`.
- Passing condition: `emergency_exercised=1`, `movement_seen=1`,
  `manual_override_path_pass=1`, and `error_count=0`.
- Even if this passes, the evidence is only no-prop/grounded bench evidence,
  not flight validation.

### ESP32 dual-core streaming idea

Proposal:
- Use the XIAO ESP32-S3 dual-core runtime as a pipelined design: one core
  continuously captures audio windows while the other core performs frontend,
  TFLM inference, and host event reporting.

Manager interpretation:
- This is a promising path for continuous inference throughput, because the
  current measured timing is approximately capture `923 ms` plus
  frontend+invoke `55 + 627 = 682 ms`.
- With ping-pong buffers and FreeRTOS task separation, the steady-state window
  period could approach `max(923, 682)`, i.e., roughly one decision opportunity
  per 1-second audio window after pipeline fill.
- This does not reduce the first-window end-to-end latency below `1 s`; the
  first complete event still includes capture plus frontend plus inference,
  currently about `1.6 s`.

Required design checks before implementation:
- FreeRTOS tasks pinned to separate cores for capture and inference/reporting.
- Ping-pong PCM/logmel buffers with queue or semaphore ownership.
- No concurrent access to a shared TFLM interpreter.
- Explicit backpressure policy for late inference, dropped windows, and queue
  overflow.
- Timing fields for `capture_seq`, `capture_start/end`, `infer_start/end`,
  `queue_depth`, `dropped_windows`, `overrun_count`, steady-state window
  period, and end-to-end latency.

Next action:
- Dispatch `esp32部署agent` for a design-only dual-core streaming plan before
  firmware implementation.

### ESP32 dual-core streaming design-only receipt

Scope:
- Design-only analysis completed.
- No firmware changes, no model training, no Tello connection, and no UDP.

Outputs:
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_dual_core_pipeline_design/dual_core_pipeline_design.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_dual_core_pipeline_design/timing_fields.csv`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_dual_core_pipeline_design/implementation_plan.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_dual_core_pipeline_design/validation_plan.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_dual_core_pipeline_design/decision_summary.md`

Core conclusion:
- Dual-core pipelining is a plausible path to one inference opportunity per
  fixed 1-second audio window in steady state.
- It does not support a first-window end-to-end latency claim below `1 s`.
- Current first-window timing remains approximately
  `923 + 55 + 627 = 1605 ms`.
- The paper-safe claim today is design proposal only:
  implementation status `NOT IMPLEMENTED`, validation status `NOT VALIDATED`.

Design summary:
- `audio_capture_task` pinned to one core and `inference_report_task` pinned to
  the other core.
- Start with a three-buffer PCM pool if memory allows; each buffer stores one
  `16000 int16` window and moves through
  `FREE -> CAPTURING -> READY -> PROCESSING -> FREE`.
- Use `free_q` and `ready_q` for ownership transfer.
- If no free buffer is available, drop the new window and increment
  `dropped_windows` / `overrun_count`; do not overwrite a processing buffer.
- Keep `MicroInterpreter`, input/output tensors, and frontend scratch single
  owned by the inference task.

Validation plan:
- Mode A: capture-only cadence.
- Mode B: synthetic `682 ms` processing load.
- Mode C: full RT1S C32 frontend + TFLM + USB CDC pipeline.
- Mode D: core-affinity A/B.
- Mode E: optional transport stress after USB CDC passes.

Acceptance metrics for steady-state throughput:
- At least `120` windows.
- `steady_state_window_period_ms p95 <= 1050`.
- `infer_output_period_ms p95 <= 1050`.
- bounded `queue_depth`, no upward drift.
- bounded or zero `dropped_windows` and `overrun_count`.

Manager decision:
- Approve the analysis as a valid design basis.
- Do not yet count this as runtime evidence.
- Next implementation, if approved, should be narrowly limited to compile-time
  pipeline mode, buffer pool, timing instrumentation, USB CDC reporting only,
  and no Tello/UDP/paper edits.

### ESP32 dual-core pipeline validation receipt

Scope:
- Firmware/runtime validation of the XIAO ESP32-S3 dual-core capture/inference
  pipeline.
- Runtime candidate: `xiao_rt1s_c32_b256_samearch_ts`.
- USB CDC report only.
- No Tello, no UDP, no training, no paper edit.

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
- `steady_state_1s_throughput=PASS`.
- `first_window_subsecond_latency=FAIL`.
- `semantic_accuracy_validated=NO`.
- `flight_validation=NO`.

Key results:
- Mode A capture-only: `PASS`, `120/120`, drop `0`, overrun `0`,
  e2e p95 `1005.007 ms`.
- Mode B synthetic `682 ms`: `PASS`, `120/120`, drop `0`, overrun `0`,
  e2e p95 `1687.223 ms`.
- Mode C full RT1S C32: `PASS`, `120/120`, drop `0`, overrun `0`,
  output period p95 `1005.17 ms`, e2e p95 `1694.93 ms`,
  first-window e2e `1605.885 ms`.
- Mode C timing detail: capture p95 `1004 ms`, frontend p95 `56 ms`,
  infer p95 `632 ms`, processing latency p95 about `689.95 ms`,
  queue depth p95 `0.0`.

Implementation notes:
- Default runtime still falls back to the current single-path implementation.
- Pipeline validation uses a local header switch instead of
  `--build-property build.extra_flags=...`, because overriding
  `build.extra_flags` removes Arduino-generated USB CDC / PSRAM board macros.
- Pipeline validation uses 3-buffer PCM ownership with `free_q` / `ready_q`;
  PCM buffers are allocated in PSRAM.
- TFLM interpreter, input/output tensors, frontend scratch, and Invoke remain
  single-owned by the inference/report task in pipeline mode.
- Git tracking note: the reported firmware/host files live under ignored
  `realworld/`, and validation outputs live under ignored
  `weeklyresult/.../realworld/`. They are present as local artifacts but are not
  currently tracked by `git status`; consolidation is required before any commit
  or remote handoff.

Manager decision:
- Count this as runtime/throughput evidence: the RT1S C32 ESP32 path can sustain
  one inference opportunity per fixed `1 s` audio window in steady state.
- Do not claim first-command or first-window latency below `1 s`.
- Do not claim semantic accuracy or flight safety validation.
- Next use: make this pipeline the runtime baseline for grounded/no-prop
  control-chain timing, while keeping wording limited to steady-state
  throughput.

### ESP32 continuous BLE pipeline receipt

Scope:
- ESP32 dual-core continuous capture/inference pipeline with BLE notify to Mac.
- Runtime candidate: `xiao_rt1s_c32_b256_samearch_ts`.
- BLE payload returns compact `seq + label + confidence` only.
- Host continuous logger records CSV/summary only.
- No Tello UDP was sent, no Tello connection was made, no flight validation was
  run, and no semantic accuracy validation is claimed.

Outputs:
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_ble_continuous_pipeline/continuous_ble_pipeline_handoff.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_ble_continuous_pipeline/ble_continuous_rt1s_w30_summary.json`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_ble_continuous_pipeline/ble_continuous_rt1s_w30_events.csv`

Runtime integration:
- ESP32 firmware is flashed with Core 0 continuous audio capture
  (`16 kHz`, mono, `1 s`, `16000 int16 PCM`).
- Core 1 owns logmel preprocessing, TFLM inference, and BLE notify.
- BLE payload example: `{"s":1,"l":"e","c":0.996}`.
- Label codes: `e=emergency`, `m=movement`, `u=unknown`.
- USB CDC remains available for timing/debug diagnostics and fallback.

Key W30 results:
- Received windows: `30/30`.
- Success rate: `1.000`.
- Inter-arrival p50: `990.0 ms`.
- Inter-arrival p95: `1021.0 ms`.
- Label counts: `emergency=13`, `movement=17`.
- Tello UDP sent: `NO`.
- Semantic accuracy validated: `NO`.
- Flight validation: `NO`.

Gate verdict:
- ESP32 full firmware flash: `GO`.
- BLE continuous `1 s` throughput: `PASS`.
- Ground/no-prop Tello SDK chain: `PENDING`.
- Flight: `NO-GO`.

Manager decision:
- Count this as a meaningful runtime/control-plumbing step: the project has
  moved from single Enter-triggered inference to continuous BLE event reporting.
- The result strengthens the paper's real-time onboard throughput story, but
  only as steady-state throughput evidence.
- Do not claim that label counts prove semantic accuracy because no live labels
  were externally annotated in this run.
- Do not claim end-to-end Tello control because host safety-state dispatch and
  Tello SDK reachability are still pending.

Next action:
- Run a longer `--windows 120` BLE stability test to confirm drop-free p95
  behavior.
- Connect continuous label/confidence events into the host-side safety state
  machine, initially producing dry/no-prop command logs only.
- Validate Tello AP / SDK grounded reachability with `command` and `battery?`
  only; do not issue `takeoff`, movement, or flight commands.
- If grounded SDK reachability passes, prepare no-prop/grounded bench evidence.
  Flight remains blocked until the no-prop/grounded safety-state gate passes.

## Approved Decisions

- [x] Keep W19 first-batch baseline results on
  `codex/track-d-baseline-results-20260514`; do not merge into `main` yet.
- [x] Prepare an AI-generated representative first-page picture as a temporary
  visual candidate; later replace it with higher-quality custom drawing if
  needed.

## Approval Still Needed

- [x] Dispatch `论文写作agent` for a read-only audit of the latest Overleaf
  synced draft before dispatching evaluation protocol work.
- [x] Dispatch `esp32部署agent` for real-time onboard latency audit.
- [x] Dispatch `esp32部署agent` for Bluetooth/USB host-mediated Tello control-loop
  work.
- [x] Dispatch `evaluation agent` for user-study / testing-condition /
  response-time protocol after the writing audit receipt is reviewed.
- [x] Dispatch `模型设计agent` for no-training `<=1s` tiny-student architecture
  analysis.
- [x] Approve local profile integration for `xiao_rt1s_c32_b256_tflm` and
  `xiao_rt1s_c24_b192_tflm`.
- [ ] Clean generated smoke artifacts and selectively commit RT1S profile
  integration without paper draft changes.
- [ ] Dispatch `论文写作agent` after VP's introduction first pass arrives.
- [x] Start W19 Mac-local RT1S Candidate A from clean committed SHA.
- [x] Rerun Candidate A with same-profile clean teacher and noisy student.
- [ ] If same-profile Candidate A still collapses, try CE/logits-supervised
  recipe.
- [x] Export and validate `xiao_rt1s_c32_b256_samearch_ts` on TFLite/TFLM/ESP32.
- [ ] Start Candidate B only after Candidate A no longer collapses.
- [ ] Run live no-prop/grounded RT1S C32 bench with one `emergency`, one
  `movement`, manual override enabled, and `error_count=0`.
- [x] Dispatch `esp32部署agent` for design-only dual-core streaming/pipelining
  analysis.
- [x] Approve narrow firmware implementation for compile-time dual-core
  pipeline mode and USB CDC validation only.
- [x] Validate dual-core pipeline Mode A/B/C on board for steady-state
  throughput.
- [x] Validate continuous BLE event transport from ESP32 to Mac for W30.
- [ ] Run W120 continuous BLE stability validation.
- [ ] Use dual-core/BLE pipeline as grounded/no-prop control-chain timing
  baseline.
- [ ] Validate Tello AP / SDK grounded reachability with `command` and
  `battery?` only.
- [ ] Integrate continuous BLE labels into the host safety state machine for
  dry/no-prop logs.
- [ ] Consolidate ignored `realworld/` firmware/host changes and
  `weeklyresult/.../realworld/` validation receipts into tracked handoff
  artifacts before any commit/push.

## Risks

- If inference cannot be reduced to `<=1 s`, the paper should not make a strong
  real-time onboard claim.
- RT1S C32 passes pure Invoke `<=1 s`, but current total first-window path is
  still about `1.6 s`; use dual-core pipelining only as a continuous-throughput
  argument unless measured otherwise.
- Dual-core pipeline now has Mode A/B/C runtime validation, but it still cannot
  support first-window `<1 s`, semantic accuracy, or flight validation claims.
- BLE continuous W30 now passes, but it has not yet been run for 120 windows and
  has not been connected to a Tello SDK reachability test.
- Bluetooth may be less stable than USB CDC for demo evidence; USB fallback must
  remain available.
- Tello AP / SDK testing must start with `command` and `battery?` only; movement
  and takeoff remain blocked until no-prop/grounded safety-state logs pass.
- Coarse `movement` intent is not a safe movement command.
- User-study expansion may create data-management and annotation overhead.
- W19 baseline results are evidence-branch artifacts until an explicit merge or
  paper-integration decision is made.
