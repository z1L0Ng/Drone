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
- [ ] Evaluate ESP32-S3 Bluetooth event transport to Mac.
- [ ] Preserve USB CDC as fallback if Bluetooth is unstable.
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

## Approved Decisions

- [x] Keep W19 first-batch baseline results on
  `codex/track-d-baseline-results-20260514`; do not merge into `main` yet.
- [x] Prepare an AI-generated representative first-page picture as a temporary
  visual candidate; later replace it with higher-quality custom drawing if
  needed.

## Approval Still Needed

- [x] Dispatch `论文写作agent` for a read-only audit of the latest Overleaf
  synced draft before dispatching evaluation protocol work.
- [ ] Dispatch `esp32部署agent` for real-time onboard latency audit.
- [ ] Dispatch `esp32部署agent` for Bluetooth host-mediated Tello control-loop
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
- [ ] Start W19 Mac-local RT1S training after a clean committed SHA exists.

## Risks

- If inference cannot be reduced to `<=1 s`, the paper should not make a strong
  real-time onboard claim.
- Bluetooth may be less stable than USB CDC for demo evidence; USB fallback must
  remain available.
- Coarse `movement` intent is not a safe movement command.
- User-study expansion may create data-management and annotation overhead.
- W19 baseline results are evidence-branch artifacts until an explicit merge or
  paper-integration decision is made.
