# Weekly TODO (CDT, Thursday-cycle 2026w18)

Meeting checkpoint: Thursday 2026-05-07.

Planning cycle: Sunday night 2026-05-03 -> Thursday morning 2026-05-07.

Project target: SenSys 2027 first-round submission.

## Weekly Goal
- Move from ESP32 local inference feasibility to safe control-chain evidence and
  an advisor-discussable SenSys draft.
- Keep `w14 preprocess_ext` as the reproducible mainline model anchor.
- Keep `B_small_teacher_student` as the only embedded small-student deployment
  candidate.
- Treat Track A gate + buffer as a board-side feasibility branch, not a new
  training loop.

## Hard Constraints
- Manager scope: planning, dispatch, acceptance, documentation, and reporting.
- Local scope: code/eval/reporting and deployment dry-run evidence.
- Server scope: training only after explicit approval, with commit SHA, tmux,
  `WEEKLY_TAG`, `weeklyresult/` output directory, startup receipt, and
  completion receipt.
- No server training is dispatched before the 2026-05-07 meeting.
- Do not claim final drone-control deployment until live/safe Tello evidence
  exists.
- Do not claim gate + buffer as a validated safety mechanism before board logs
  exist.

## Current Evidence Snapshot
- Main workspace audit at Track A receipt:
  - branch: `main`
  - HEAD: `97140dbebe11e2861838b593167abbef3b3dee62`
  - status: clean relative to `origin/main`
- Track A branch/worktree:
  - branch: `codex/track-a-gate-buffer-e2e-20260504`
  - worktree: `/Users/zilongzeng/.codex/worktrees/ca65/Drone`
  - design note is present there as an untracked file.
- Runtime/firmware artifacts in the main workspace are ignored by the repo-wide
  `realworld/` ignore rule, so they must be verified by explicit path checks.
- Latest stable ESP32 baseline:
  - `realworld/esp32/firmware/esp32_local_cdc_fast/esp32_local_cdc_fast.ino`
  - 30/30 local CDC triggers succeeded in W17 stability evidence.
  - Inference p50 about `2094 ms`, total p50 about `3075 ms`.

## Track B Receipt: Tello Dry Command Dispatch
Receipt time: 2026-05-04 13:14 CDT.

Scope:
- Dry-run only.
- No Tello UDP packets sent.
- No flight test.

Outputs:
- `realworld/shared/control_event_schema.json`
- `realworld/tello/label_command_mapping.json`
- `realworld/tello/dry_command_dispatch.py`
- `weeklyresult/weekly_drone_2026w18/realworld/tello_dryrun/20260504_local_cdc_replay_dry_command_log.csv`
- `weeklyresult/weekly_drone_2026w18/realworld/tello_dryrun/20260504_local_cdc_replay_report.md`
- `weeklyresult/weekly_drone_2026w18/realworld/tello_dryrun/20260504_local_cdc_replay_summary.json`

Result:
- [x] Event schema created.
- [x] Label -> command mapping created.
- [x] Dry dispatch script created.
- [x] Dry command replay log created from W17 ESP32 local inference stability log.
- [x] Static validation passed: `python3 -m py_compile realworld/tello/dry_command_dispatch.py`.
- [x] `dry_gate_pass=1`.
- [x] 30 dry events processed: `unknown=29`, `movement=1`, `emergency=0`.
- [x] Command results: `dry_noop=29`, `dry_blocked=1`.
- [x] Safety fields present in every row:
  `safety_hold`, `manual_override`, `command_result`, `result_detail`.

Mapping summary:
- `emergency` -> `SAFE_HOLD`, dry command `rc 0 0 0 0`,
  `command_result=dry_ack`.
- `movement` -> `INTENT_PENDING`, dry `noop`, manual override required,
  `command_result=dry_blocked`.
- `unknown` -> `SAFE_HOLD`, dry `noop`, `command_result=dry_noop`.

Decision:
- [x] Tuesday flight test: **NO-GO**.
- [x] Tuesday ground / no-prop / dry command bridge: **GO**.

Blockers before flight:
- No `emergency` sample coverage in the replay log.
- `movement` is too coarse to map directly to a safe Tello movement command.
- Need at least one live dry-run covering `emergency` and `movement`.
- Movement manual-override path must be explicitly validated.

## Track A Receipt: Gate + Buffer E2E
Receipt time: 2026-05-04 13:38 CDT.

Scope:
- Board-side gate + 1s buffer design and minimum validation preparation.
- No model training.
- No student input-shape change.
- No 500 ms / 250 ms classifier.
- No Tello integration.
- Stable baseline `esp32_local_cdc_fast` was not replaced.

Prepared artifacts:
- design note:
  `docs/realworld_esp32_gate_buffer_e2e_design_2026w18.md`
- firmware:
  `realworld/esp32/firmware/esp32_gate_buffer_e2e/esp32_gate_buffer_e2e.ino`
- firmware config:
  `realworld/esp32/firmware/esp32_gate_buffer_e2e/config.h`
- ESP-NN fallback copy:
  `realworld/esp32/firmware/esp32_gate_buffer_e2e/esp_nn_conv_ansi_fallback.cpp`
- host runner:
  `realworld/esp32/host/gate_buffer_e2e_runner.py`
- handoff outputs:
  `weeklyresult/weekly_drone_2026w18/realworld/gate_buffer_e2e/{README.md,gate_buffer_event_log.csv,timing_summary.md,board_trace_tail.txt,decision_note.md}`

Implementation summary:
- Board-side path: `20 ms` PCM hop -> `100 ms` energy gate -> `1s` PSRAM
  circular buffer -> `400 ms` pre-roll + `600 ms` post-roll -> existing logmel
  -> existing `B_small_teacher_student` TFLM inference.
- Static host validation passed in main workspace:
  - `python -m py_compile realworld/esp32/host/gate_buffer_e2e_runner.py`
  - `python realworld/esp32/host/gate_buffer_e2e_runner.py --help`

Validation verdict:
- [x] Design and validation-prep artifacts prepared.
- [x] Stable fallback preserved.
- [x] Board validation **BLOCKED** because no XIAO ESP32-S3 USB CDC serial port
  was visible.
- [ ] Arduino compile not run because `arduino-cli` is not installed locally.
- [ ] Board-attached silence/background, speech trigger, and repeated speech
  cases are not yet collected.

Important integrity note:
- In the current main workspace, the ignored firmware/host/output artifacts are
  present, but the design note is not present.
- In the Track A worktree, the design note is present as an untracked file, but
  the ignored firmware/host/output artifacts are not visible there.
- Before committing or handing to another machine, consolidate the Track A
  artifact set into one branch/worktree and decide which ignored artifacts must
  be force-added.

Recommendation:
- Proceed with board-attached validation of the heuristic gate.
- Keep `esp32_local_cdc_fast` as the stable fallback until W18 board logs show:
  silence/background does not frequently trigger; speech triggers produce
  `err_code=ok`; repeated speech records refractory behavior.
- Do not treat Track A as safety evidence yet.

## Track A Feedback: Clean Board Retest
Receipt time: 2026-05-04 15:35 CDT.

Correction:
- This feedback is Track A gate + buffer board validation, not Track B.

Scope:
- Previous gate-buffer run logs were deleted.
- Clean retest output contains only four cases:
  - `quiet_silence_baseline`
  - `quiet_speech_trigger`
  - `rotor_playback_background`
  - `rotor_playback_speech_trigger`

Outputs:
- `weeklyresult/weekly_drone_2026w18/realworld/gate_buffer_e2e/gate_buffer_event_log.csv`
- `weeklyresult/weekly_drone_2026w18/realworld/gate_buffer_e2e/timing_summary.md`
- `weeklyresult/weekly_drone_2026w18/realworld/gate_buffer_e2e/board_trace_tail.txt`
- `weeklyresult/weekly_drone_2026w18/realworld/gate_buffer_e2e/decision_note.md`

Board validation result:
- [x] Board compile/upload passed in the Track A worktree.
- [x] Board-side E2E path invoked the existing student successfully.
- [x] Timing for successful invocations is stable:
  `buffer_collect_ms=600`, `frontend_ms=55`, `infer_ms=2110`,
  `total_ms=2766`.
- [x] Clean retest generated board-side logs.
- [ ] Current heuristic did **not** pass background suppression.

Case results:
- `quiet_silence_baseline` 20 s: `4` false student invocations.
- `quiet_speech_trigger` 30 s: `6` triggers, not separable from quiet false
  triggers.
- `rotor_playback_background` 30 s: `6` false triggers.
- `rotor_playback_speech_trigger`: `6` triggers, not separable from
  background/rotor false triggers.

Rotor playback source:
- `/Users/zilongzeng/Research/Drone/dataset/raw/drone/bebop_1/B_S2_D1_098-bebop_002_.wav`
- Format: `16 kHz`, mono, int16 wav.
- Playback: looped to 30 s with `afplay -v 1.0`.
- Interpretation: useful bench stress input, not calibrated true rotor SPL at
  the XIAO microphone.

Decision:
- [x] `TEMPORARILY_PAUSE_CURRENT_GATE`.
- [x] Do not jump directly to a tiny learned gate.
- [x] First patch heuristic calibration.
- [x] Keep `esp32_local_cdc_fast` stable fallback.

Next Track A patch plan:
1. Collect 2-3 s startup background on the board.
2. Initialize `noise_floor_db` from median/percentile of observed gate scores.
3. Use threshold relative to calibrated floor instead of fixed
   `-58 + 12 dB`.
4. Add sustained/onset condition rather than raw level alone.
5. Rate-limit refractory monitor logs.
6. Rerun quiet silence before rotor playback.

Guardrail:
- This is board-side feasibility/timing evidence plus a failed current-gate
  result.
- It is not a safety mechanism and not real deployment rotor evidence.

## PM Decision: Pause Track A For W18 Pre-Meeting Cycle
Decision time: 2026-05-04 22:44 CDT.

- [x] Pause Track A implementation/calibration for the remainder of the
  2026-05-07 pre-meeting cycle.
- [x] Thursday meeting framing: Track A can report that an initial board-side
  demo path is possible and invoke timing is stable, but the current heuristic
  false-triggers in quiet and rotor-playback background.
- [x] Do not dispatch Track A calibration or new learned-gate work before the
  2026-05-07 meeting unless explicitly reopened.
- [x] Reallocate remaining W18 execution time to Track B Tello control loop and
  Track C SenSys paper writing.
- [x] Keep `esp32_local_cdc_fast` as the W18 stable demo baseline.

## Track C Receipt: SenSys Draft Audit and Plan
Receipt time: 2026-05-04 15:13 CDT.

Scope:
- Paper audit and writing plan only.
- No paper files were modified.
- Current `docs/paper_sensys2027/` status is clean.

Main compile path from `main.tex`:
- Abstract in `main.tex`.
- `sections/1introduction`
- `sections/2motivation`
- `sections/3system`
- `sections/4training`
- `sections/5prototype`
- `sections/6evaluation`
- `sections/7relatedwork`
- `sections/8conclusion`

Important structural finding:
- `sections/3overview.tex` and `sections/4implementation.tex` are not included
  by `main.tex`.
- Those two files are closer to the current project principles, but they do not
  currently enter the compiled draft.

Rewrite priorities:
- [ ] Update abstract to reflect: `w14` mainline + `B_small` deployment
  candidate + control loop not yet complete.
- [ ] Remove or rewrite contribution language that implies cross-platform or
  completed Tello generalization.
- [ ] Refresh motivation/prototype wording: ESP32 local inference is now stable;
  the open gate is control integration and repeatable demo evidence.
- [ ] Rewrite `4training.tex` around the `w14 preprocess_ext` recipe; remove
  old baseline numbers and do not promote cross-language/stats-branch content
  into the mainline.
- [ ] Rewrite `5prototype.tex` around ESP32 local pipeline, USB CDC, TFLM
  inference, and missing WiFi/control bridge.
- [ ] Rewrite `6evaluation.tex` to keep `w14` and `B_small` only; describe ESP32
  evidence as runtime stability, not labeled real-world accuracy.
- [ ] Update `WRITING_OUTLINE.md` to remove `branch_trial/E0/E2` as mainline and
  use `w14 preprocess_ext` + `B_small_teacher_student` + control-demo gap.

Evidence map accepted for writing:
- `w14 preprocess_ext`: noisy acc `0.88`, emergency recall `0.79`,
  emergency F1 `0.87`, support `9984`.
- `w14` recipe: base teacher/student, batch `32`, student epochs `50`,
  eval SNR `-10 dB`, emergency prosody augmentation enabled.
- `B_small_teacher_student`: both teacher and student use
  `xiao_bottleneck256_tflm`; noisy acc `0.87`, emergency recall `0.79`,
  emergency F1 `0.86`; close to but not stronger than `w14`.
- TFLM artifact: full-int `780416` bytes, `CONV_2D=6`,
  `DEPTHWISE_CONV_2D=1`, no grouped temporal Conv detected.
- ESP32 local inference: `30/30` triggers, drop rate `0.0000`,
  infer p50 `2094 ms`, total p50 `3075 ms`.
- Guardrail: ESP32 local inference evidence is runtime stability evidence, not
  labeled real-world semantic accuracy.
- Current missing system evidence: WiFi formal metric gate and drone-control
  demo are not closed.

Tuesday writing order for 2026-05-05:
1. Update `WRITING_OUTLINE.md`.
2. Decide `main.tex` include strategy for `3overview/4implementation` versus
   merging their content into `3system/4training/5prototype`.
3. Rewrite `6evaluation.tex`.
4. Rewrite `5prototype.tex`.
5. Rewrite `4training.tex`.
6. Update abstract and introduction contributions.
7. Polish `2motivation`, `3system`, `7relatedwork`, and `8conclusion`.

## Track C Receipt: Core Writing Review Memo
Receipt time: 2026-05-04 22:55 CDT.

Scope:
- Writing review and PM preparation only.
- No paper files modified.
- No experiments or code changes.

Audit:
- branch: `main`
- HEAD: `99bc1751852dde997282bf8639324c061df8f42c`
- status: PM docs dirty only:
  `docs/weekly_todo/2026/2026w18/todo.md`,
  `docs/weekly_todo/handoff_log.md`
- `main.tex` compile path remains:
  abstract, `1introduction`, `2motivation`, `3system`, `4training`,
  `5prototype`, `6evaluation`, `7relatedwork`, `8conclusion`.
- `sections/3overview.tex` and `sections/4implementation.tex` exist but are not
  compiled.

Core thesis for writing:
- English thesis:
  "A drone-side voice safety layer can make small UAVs more interruptible under
  severe self-noise when it is framed as narrow, reject-aware intent recognition
  first, and deployment-constrained control integration second."
- Chinese interpretation: prove reproducible noisy intent recognition first,
  then present ESP32/TFLM as deployment feasibility; do not claim completed
  safety mechanism, flight control loop, or cross-platform validation.

Confirmed claim map:
- `w14 preprocess_ext` is the main noisy-set anchor:
  acc `0.88`, emergency recall `0.79`, emergency F1 `0.87`, support `9984`.
- `B_small_teacher_student` is close but not stronger:
  deployment-oriented candidate, acc `0.87`, emergency F1 `0.86`.
- ESP32 local inference runtime loop is stable:
  30-trigger USB CDC loop success `1.0000`, drop `0.0000`,
  infer p50 `2094 ms`, total p50 `3075 ms`.
- TFLM compatibility is documented:
  full-int `780416` bytes, `CONV_2D=6`, `DEPTHWISE_CONV_2D=1`,
  no grouped temporal Conv detected.

Partially supported or missing:
- Voice safety layer architecture is an interface design with reject/unknown
  path, not a validated safety mechanism.
- Track B has dry-run dispatch and flight remains NO-GO.
- Track A is preliminary board-side demo feasibility only and is paused for the
  2026-05-07 pre-meeting cycle.
- Labeled real-world protocol, live dry-run coverage, no-prop/grounded bench,
  and paper-ready figures remain missing.

Section architecture decision for next writing pass:
- Keep `main.tex` include order unchanged for the first rewrite pass.
- Do not directly add both `3overview` and `4implementation`, because they
  duplicate compiled sections and would create structure churn.
- Use `3overview.tex` as source material for `3system.tex`.
- Use `4implementation.tex` as source material for `5prototype.tex` and
  `6evaluation.tex`.

Next writing execution order:
1. `WRITING_OUTLINE.md`: replace stale evidence list and add accepted claim map.
2. `main.tex`: rewrite abstract around `w14`, `B_small`, ESP32 runtime
   stability, and missing control evidence.
3. `sections/6evaluation.tex`: rebuild around only `w14`, `B_small`, ESP32
   runtime stability, and open control/gate gaps.
4. `sections/5prototype.tex`: write concrete XIAO ESP32-S3 USB CDC/TFLM local
   pipeline and separate Track A/Track B boundaries.
5. `sections/4training.tex`: rewrite around `w14 preprocess_ext` config,
   class-aware augmentation, distillation, and B candidate comparison.
6. `sections/3system.tex`: merge `3overview` boundary/evidence-stack logic.
7. `sections/1introduction.tex` and `2motivation.tex`: reduce safety and
   cross-platform claims while keeping a drone-first thesis.
8. `sections/8conclusion.tex` and `7relatedwork.tex`: update stale milestones
   and keep future work conservative.

Open meeting questions:
- Should the paper say "voice safety layer" or the more conservative
  "safety-oriented interrupt interface"?
- Is `2.1 s` inference acceptable for the emergency class, or should emergency
  be framed as interrupt/hold rather than immediate collision avoidance?
- What evidence is required before first-round submission: live dry-run,
  no-prop bench, or flight?
- Should Track A appear in the paper at all, or stay as meeting demo feasibility
  outside the draft?
- Should all multi-platform language be removed until another drone is tested?

## Track C Receipt: First Structural Rewrite And PM Writing Correction
Receipt time: 2026-05-05 00:40 CDT.

Scope:
- Paper writing only.
- No model changes.
- No experiments.
- No `realworld` firmware changes.
- `references.bib` unchanged.

Changed files:
- `docs/paper_sensys2027/WRITING_OUTLINE.md`
- `docs/paper_sensys2027/main.tex`
- `docs/paper_sensys2027/sections/1introduction.tex`
- `docs/paper_sensys2027/sections/2motivation.tex`
- `docs/paper_sensys2027/sections/3system.tex`
- `docs/paper_sensys2027/sections/4training.tex`
- `docs/paper_sensys2027/sections/5prototype.tex`
- `docs/paper_sensys2027/sections/6evaluation.tex`
- `docs/paper_sensys2027/sections/7relatedwork.tex`
- `docs/paper_sensys2027/sections/8conclusion.tex`
- `docs/paper_sensys2027/sections/3overview.tex`
- `docs/paper_sensys2027/sections/4implementation.tex`

Validation:
- `git diff --check -- docs/paper_sensys2027` passed.
- Diff summary: `12 files changed, 174 insertions(+), 173 deletions(-)`.
- LaTeX compile not run.

What improved:
- Draft now centers on a drone-side interruptible safety layer.
- `w14 preprocess_ext` is used as the paper anchor.
- `B_small_teacher_student` is framed as the deployment candidate.
- ESP32 evidence is treated as runtime feasibility.
- Track B remains dry-run only and flight `NO-GO`.
- Track A remains preliminary and not a validated gate.

PM writing correction:
- [x] First rewrite is accepted as a structural pass.
- [x] Next pass should move away from a "staged evidence" paper voice.
- [x] The draft should describe the intended system and design as a coherent
  target architecture.
- [x] Missing evidence should be marked as evaluation gaps, TODO evaluation
  hooks, or planned validation protocols, not as the main narrative frame.
- [x] System/design sections may use forward design language such as "the
  system is designed to..." and "the control bridge records...", while
  evaluation/results sections must keep actual evidence boundaries.
- [x] Existing evidence should support and constrain the draft, but the paper
  should not read like a weekly staged-progress report.

Required follow-up writing pass:
- Replace "staged evidence" framing in the abstract/introduction with a
  design-first systems thesis.
- Keep the target architecture front-and-center:
  voice input -> noisy intent recognizer -> reject/unknown handling ->
  embedded inference path -> safe control bridge -> command/state log.
- Convert unsupported result claims into planned evaluation or evidence-gap
  notes.
- Preserve no-overclaim rules:
  no flight evidence, no labeled real-world semantic accuracy, no validated
  gate/safety mechanism, no multi-platform validation.

## Track C Receipt: Talk-To-The-Drone Framing Revision
Receipt time: 2026-05-05 22:57 CDT.

Scope:
- Paper writing and figure organization only.
- No model changes.
- No experiments.
- No `realworld` firmware changes.
- `references.bib` unchanged.

Audit:
- branch: `main`
- HEAD: `20f4942a09dec7126be4b7cf504c624d7abf1fda`
- current dirty files are under `docs/paper_sensys2027/` only before this PM
  sync.
- `main.tex` compile path now uses:
  `1introduction`, `2motivation`, `3architecture`, `4recognizer`,
  `5prototype`, `6evaluation`, `7relatedwork`, `8conclusion`.
- Active section files are:
  `1introduction.tex`, `2motivation.tex`, `3architecture.tex`,
  `4recognizer.tex`, `5prototype.tex`, `6evaluation.tex`,
  `7relatedwork.tex`, `8conclusion.tex`.
- Old duplicate section files `3overview/3system/4implementation/4training`
  are no longer present in `docs/paper_sensys2027/sections/`.

Changed paper files:
- `docs/paper_sensys2027/WRITING_OUTLINE.md`
- `docs/paper_sensys2027/main.tex`
- `docs/paper_sensys2027/figures/system_architecture.tex`
- `docs/paper_sensys2027/figures/recognizer_architecture.tex`
- `docs/paper_sensys2027/figures/prototype_pipeline.tex`
- `docs/paper_sensys2027/sections/1introduction.tex`
- `docs/paper_sensys2027/sections/2motivation.tex`
- `docs/paper_sensys2027/sections/3architecture.tex`
- `docs/paper_sensys2027/sections/4recognizer.tex`
- `docs/paper_sensys2027/sections/5prototype.tex`
- `docs/paper_sensys2027/sections/6evaluation.tex`
- `docs/paper_sensys2027/sections/7relatedwork.tex`
- `docs/paper_sensys2027/sections/8conclusion.tex`

Validation:
- `git diff --check -- docs/paper_sensys2027` passed.
- Visible paper grep for `interrupt`, `interruption`, `AI`, `agent`, `Agent`
  returned no matches.
- `latexmk`, `pdflatex`, and `tectonic` are unavailable in the local
  environment, so PDF compile was not run.

Accepted framing:
- [x] The paper is no longer framed as an emergency-only interrupt path.
- [x] New mainline: talk-to-the-drone voice interaction under rotor noise.
- [x] On-device intent recognition is the safety mechanism.
- [x] `emergency` is a safety-critical intent class, not the sole paper target.
- [x] `unknown/reject` is kept as part of the safety-aware interface, not as the
  core contribution.
- [x] ESP32 runtime, Track B dry-run, and Track A gate/buffer are not written as
  validated safety or flight evidence.
- [x] Internal run names such as `w14` and `B_small` are kept for evidence
  mapping and comments, not as visible paper narrative.

Current evaluation stack:
1. Offline baseline comparison.
2. Frontend ablation.
3. Noise robustness curve.
4. Embedded deployment comparison.
5. On-board runtime / quantization fidelity.
6. Speaker and distance robustness.
7. Drone interaction / bridge behavior.

Visible repo-backed numbers currently retained:
- `w14` anchor.
- `B_small` embedded student.
- TFLM artifact.
- ESP32 30-trigger runtime.

Missing experiments now tracked with LaTeX `% TODO(evaluation)` comments:
- frontend ablation.
- noise robustness curve.
- speaker/distance live labeled data.
- deployment comparison table.
- quantization fidelity.
- no-propeller bridge logs.
- drone interaction figure/table.

## Track D Plan: Evaluation Agent Initialization
Planning time: 2026-05-05 23:49 CDT.

Purpose:
- Start a dedicated evaluation track that is explicitly bound to the current
  local SenSys draft, especially `docs/paper_sensys2027/sections/6evaluation.tex`.
- Keep this agent adaptable after the 2026-05-07 meeting, because the advisor
  may change which evaluation layers matter most.
- First evaluation item: offline baseline comparison against suitable baseline
  recognizers from related literature.

Binding to draft:
- Current draft mainline: talk-to-the-drone voice interaction under rotor noise.
- Evaluation section currently defines seven layers:
  1. Offline baseline comparison.
  2. Frontend ablation.
  3. Noise robustness curve.
  4. Embedded deployment comparison.
  5. On-board runtime / quantization fidelity.
  6. Speaker and distance robustness.
  7. Drone interaction / bridge behavior.
- The evaluation agent must maintain a mapping from each planned experiment to:
  paper subsection, claim supported, required metrics, repo paths, and missing
  artifacts.

Initial scope for Track D:
- [ ] Read `sections/6evaluation.tex` and `WRITING_OUTLINE.md`.
- [ ] Search related literature and papers for baseline recognizers suitable
  for direct speech-to-intent / keyword-style drone voice interaction.
- [ ] Propose 3-5 baseline model families with justification, citation,
  reproducibility path, expected input representation, and compute footprint.
- [ ] Decide which baselines are fair for the current dataset and labels:
  movement / emergency / unknown.
- [ ] Produce an evaluation design note before any training or implementation.

Baseline selection criteria:
- Must be relevant to audio intent recognition, keyword spotting, or compact
  speech command classification.
- Must be runnable or reasonably reproducible locally/server-side.
- Must support the same input/label contract or have a defensible adaptation.
- Must include enough implementation detail in paper or official repo to avoid
  speculative reproduction.
- Must be evaluated with the same split, same noise protocol, and same metrics
  as the anchor recognizer.
- Embedded baselines are preferred for later layers, but first comparison may
  include non-embedded recognizers if they are clearly identified as
  offline-quality baselines.

Allowed first-step output:
- Literature table.
- Baseline shortlist.
- Reproducibility risk table.
- Exact next experiment plan.
- No model training yet.
- No server dispatch yet.

Guardrails:
- Do not change `docs/paper_sensys2027/` in the first Track D step unless
  explicitly asked.
- Do not run training before PM approval.
- Do not claim a baseline is comparable until its dataset split, preprocessing,
  label mapping, and noise setup are checked.
- Do not use unverifiable citations or placeholder references.
- If server training is later needed, manager must approve and provide commit
  SHA, tmux session name, `WEEKLY_TAG`, output directory under `weeklyresult/`,
  startup receipt, and completion receipt.

## Track D Receipt: Baseline Literature And Shortlist
Receipt time: 2026-05-06 15:49 CDT.

Scope:
- Read-only audit and literature search.
- No file changes by Track D agent.
- No training.
- No server task.

Audit:
- branch: `main`.
- HEAD: `20f4942a09dec7126be4b7cf504c624d7abf1fda`.
- The worktree already had paper/weekly todo dirty files; Track D added no
  changes.
- `docs/paper_sensys2027/sections/6evaluation.tex` layer 1 is offline baseline
  comparison on the same noisy held-out set.
- `w14 preprocess_ext` remains the model-quality anchor.
- `B_small_teacher_student` remains the embedded student / deployment
  candidate, not a main-model victory claim.

Shortlist decision:
- First-batch candidates: BC-ResNet-1/2, TC-ResNet8-1.0, DS-CNN-S/M.
- Optional fourth row: MatchboxNet small or Google `ds_tc_resnet`.
- Direct SLU / FSC CRDNN-RNN is excluded from the fair main table unless the
  advisor explicitly wants a pretrained offline upper-bound row.

Candidate summary:
- BC-ResNet: modern compact log-mel/spectrogram KWS baseline; official
  Qualcomm repo; fair if trained from scratch on the same split/noise protocol.
- TC-ResNet: mobile temporal CNN; official Hyperconnect repo; MFCC path means
  it must either be disclosed as an MFCC baseline or adapted to the current
  log-mel frontend.
- DS-CNN: classic MCU KWS baseline; good embedded-deployment comparison; MFCC
  path may overlap the frontend ablation layer.
- MatchboxNet / `ds_tc_resnet`: compact higher-capacity KWS-style baseline;
  keep as offline-quality evidence unless export/TFLM compatibility is
  explicitly validated.
- Direct SLU / FSC: task/pretraining mismatch; related work or upper-bound
  only, not a fair main comparison.

First experiment design candidate:
- Do not train until approved.
- Proposed first batch names: `bcresnet1_logmel`, `tcresnet8_mfcc`,
  `dscnn_mfcc`.
- Proposed output root if approved:
  `weeklyresult/weekly_drone_2026w19/offline_baselines/<name>/`.
- Required outputs per run: `run_config.json`, `classification_report_noisy.txt`,
  confusion matrix, macro F1, and per-class precision/recall/F1.
- Fixed inputs: `dataset/processed/data_paths.npz`,
  `saved_models/label_encoder.joblib`, `dataset/raw/tellonoise`,
  `eval_snr_db=-10.0`, labels `emergency/movement/unknown`, support `9984`.

Manager/advisor decisions:
- Are MFCC baselines allowed in the offline baseline table, or should they move
  to the frontend ablation layer?
- Should Direct SLU be included as an explicitly labeled upper-bound row?
- Should the first-round draft use a 3-row or 5-row baseline table?
- Should small-baseline training run locally or follow the usual server/tmux
  handoff policy?
- When should verified citations be added to `references.bib`?

## Track D Execution Boundary: Conda Isolation And Baseline Management
Update time: 2026-05-13 CDT.

Manager decision:
- Track D can move from read-only shortlist into implementation planning, but
  not into dependency installation, external repo download, baseline training,
  or paper-result claims until an exact run plan is approved.

Environment isolation:
- Do not contaminate the current `drone` conda environment.
- Use a dedicated Track D environment, proposed names:
  `drone-baselines` or `drone-trackd-baselines`.
- First output must include an `environment.yml` or `requirements.txt` draft
  plus dependency risk notes, especially for old TensorFlow/PyTorch repos.
- Record Python version, framework version, CPU/GPU assumption, and any CUDA
  dependency per baseline.

Baseline code management:
- Baseline code should live inside the Drone project so Codex can audit,
  modify, and commit it coherently.
- Proposed root: `baselines/` or `third_party_baselines/`.
- Proposed subdirectories: `bc_resnet/`, `tc_resnet/`, `ds_cnn/`.
- Official upstream repositories may be used as references, but copied code
  must preserve license, attribution, source URL, source commit, and local
  modification notes.
- Do not commit large checkpoints, downloaded datasets, or training caches.

Project adapter requirements:
- Each baseline must expose a local adapter that uses the same project data
  split, label mapping, noisy evaluation protocol, and metrics as the anchor
  recognizer.
- Required inputs remain:
  `dataset/processed/data_paths.npz`, `saved_models/label_encoder.joblib`,
  `dataset/raw/tellonoise`, `eval_snr_db=-10.0`, labels
  `emergency/movement/unknown`.
- Required output root if approved:
  `weeklyresult/weekly_drone_2026w19/offline_baselines/<baseline_name>/`.
- Required files per completed run:
  `run_config.json`, `classification_report_noisy.txt`, confusion matrix,
  macro F1, and per-class precision/recall/F1.

Exact run plan must answer before implementation:
- Official repo vs project-local reimplementation vs wrapper with minimal local
  copy.
- Frontend policy: log-mel, MFCC, or both; if frontend differs, decide whether
  the row belongs in offline baseline comparison or frontend ablation.
- Final config per baseline: parameter scale, epochs, batch size, optimizer,
  learning rate, augmentation/noise mix, early stopping, and seed policy.
- Whether the first pass is offline-quality only or also includes deployment
  feasibility precheck.
- Execution location: local smoke test, local full run, or server/tmux run.
  Default full training remains server-side unless PM approves a local
  exception.
- How results will be summarized back into
  `docs/paper_sensys2027/sections/6evaluation.tex`.

Server handoff risk:
- The main Track D risk is not whether one baseline can run locally; it is
  whether baseline code, environment definition, project adapters, run scripts,
  and output schema are integrated into the repo before server training.
- Server training must run from a committed and pushed SHA, not from local
  uncommitted files, ad hoc downloads, or an undocumented conda state.
- Before server deployment, Track D must provide:
  `baselines/` scaffold, environment file, unified data loader, label mapping,
  noisy evaluation protocol, output schema, and local smoke-test receipt.
- Any full baseline training follows the server/local protocol:
  commit SHA, tmux session name, `WEEKLY_TAG=drone_2026w19`, output directory
  under `weeklyresult/weekly_drone_2026w19/offline_baselines/<name>/`,
  startup receipt with first 30 lines, and completion receipt with last 50
  lines, checkpoints, and result tree.
- If an official baseline repo requires old or incompatible dependencies,
  prefer a minimal project-local reimplementation of the architecture over
  making the server environment depend on the full old upstream repo.

Recommended execution order:
1. Create a Track D branch for repo integration.
2. Add baseline scaffold, environment file, adapters, and run scripts.
3. Run local import/shape/tiny-subset smoke tests only.
4. Commit and push the branch to create a reproducible SHA.
5. Deploy the dedicated conda environment on the server from the committed
   environment file.
6. Launch full baseline training in tmux and write all outputs to
   `weeklyresult/`.
7. After result handoff, update `6evaluation.tex` and paper tables.

## Track C Receipt: Framing And Contribution Rewrite Validation
Receipt time: 2026-05-13 20:08 CDT.

Scope:
- Paper-writing task only.
- No model changes.
- No experiments.
- No ESP32 firmware changes.
- No server dispatch.
- `docs/weekly_todo/2026/2026w18/todo.md` and
  `docs/weekly_todo/handoff_log.md` were already dirty before this PM sync and
  were not touched by the writing agent.

Writing-agent changed files:
- `docs/paper_sensys2027/main.tex`
- `docs/paper_sensys2027/WRITING_OUTLINE.md`
- `docs/paper_sensys2027/sections/1introduction.tex`
- `docs/paper_sensys2027/sections/2motivation.tex`
- `docs/paper_sensys2027/sections/3architecture.tex`
- `docs/paper_sensys2027/sections/4recognizer.tex`
- `docs/paper_sensys2027/sections/5prototype.tex`
- `docs/paper_sensys2027/sections/8conclusion.tex`

Manager validation:
- [x] Framing is now further centered on voice-driven UAV safety mechanism /
  UAV safety interaction layer.
- [x] Introduction contains the four intended named contributions:
  Safety Interaction Layer, Intent-State Modeling, ESP32 On-Device Deployment,
  and Baseline and Deployment Comparison.
- [ ] Full contribution rewrite is not accepted yet, but the three extra items
  should not be treated as simple deletion items. They came from advisor
  discussion and should be rewritten as pending contribution candidates if the
  required validation can be completed:
  `open source artifacts / future extension`,
  `different users / different language intent`, and `overcome the noise`.
- [ ] `git diff --check -- docs/paper_sensys2027` currently fails due to
  trailing whitespace at
  `docs/paper_sensys2027/sections/1introduction.tex:26`.

Revised Track C writing direction:
- Do not simply delete the three extra items.
- Rewrite them into formal paper language and decide where they belong in the
  contribution structure:
  1. `overcome the noise` -> rotor-noise robust intent recognition / noise
     robustness evidence.
  2. `different users / different language intent` -> speaker and language
     generalization, conditional on validated evaluation.
  3. `open source artifacts / future extension` -> reproducible artifacts,
     scripts, protocols, and extension path, conditional on a real artifact
     package.
- Update related sections, not only the contribution list:
  `1introduction.tex`, `2motivation.tex`, `4recognizer.tex`,
  `6evaluation.tex`, `7relatedwork.tex`, and `8conclusion.tex` as needed.
- Remove the trailing whitespace and rerun
  `git diff --check -- docs/paper_sensys2027`.
- Keep the same no-overclaim boundaries: ESP32 runtime is runtime feasibility
  only; Track B dry-run is plumbing evidence only; Track A gate/buffer remains
  preliminary; baseline comparisons, user/language generalization, and
  open-source artifact claims need actual evidence before final wording.

## Track D Receipt: Baseline Repo-Integrated Training Lane Plan
Receipt time: 2026-05-13 20:17 CDT.

Scope:
- Read-only planning only.
- No file changes by Track D agent.
- No dependency installation.
- No external repo download.
- No training.
- No commit or push.

Manager interpretation:
- Track D baseline comparison must become a reproducible repo-integrated
  training lane before any server run.
- Server training cannot be launched from the current dirty workspace or from
  local ad hoc downloads.

Proposed repo layout:
- `baselines/README.md`
- `baselines/environment.yml`
- `baselines/configs/{common_offline.yaml,bcresnet1_logmel.yaml,tcresnet8_logmel.yaml,tcresnet8_mfcc40.yaml,dscnn_s_logmel.yaml,dscnn_s_mfcc40.yaml}`
- `baselines/common/{data_loader.py,audio_io.py,frontends.py,noise.py,augmentation.py,metrics.py,runner.py,receipts.py}`
- `baselines/{bc_resnet,tc_resnet,ds_cnn}/{model.py,adapter.py,UPSTREAM.md}`
- `scripts/run_trackd_offline_baseline.py`

Implementation policy:
- Do not vendor full external repositories by default.
- Prefer minimal project-local reimplementation of BC-ResNet, TC-ResNet8, and
  DS-CNN-S in the project stack.
- If any upstream code is copied later, preserve upstream license, source URL,
  source commit, and local modification note.

Environment plan:
- Proposed isolated conda env: `drone-trackd-baselines`.
- Do not contaminate current `drone` env.
- Draft dependency stack: Python 3.10, TensorFlow/Keras 2.14, `numpy<2.0`,
  `scipy`, `scikit-learn`, `matplotlib`, `pandas`, `pyyaml`, `joblib`,
  `librosa`, `soundfile`, `tqdm`.
- Dependency risk:
  - BC-ResNet official repo uses PyTorch; avoid pulling PyTorch into the first
    Track D env unless explicitly approved.
  - TC-ResNet official repo uses TensorFlow 1.13.1; reimplement in TF2/Keras.
  - Arm DS-CNN code is old TF/CMSIS-oriented; reimplement DS-CNN-S locally.

Fairness and frontend rules:
- Same split: `dataset/processed/data_paths.npz`.
- Same labels and encoder:
  `emergency / movement / unknown`, `saved_models/label_encoder.joblib`.
- Same noise source and protocol:
  `dataset/raw/tellonoise`, train SNR uniform `[-15, -5]`,
  `noise_mix_prob=1.0`, eval SNR `-10.0`.
- Same audio contract: `1 s`, `16 kHz`.
- Same output schema:
  `run_config.json`, `classification_report_noisy.txt`, `metrics.json`,
  confusion matrix, macro F1, per-class precision/recall/F1.
- Primary offline baseline table should use `*_logmel` rows.
- MFCC rows are `model+frontend` rows; move them to frontend ablation if the
  paper needs strict architecture-only comparison.

First-pass configs proposed:
- `bcresnet1_logmel`: BC-ResNet tau=1, project log-mel `(256,32,1)`.
- `tcresnet8_logmel`: TCResNet8 width multiplier 1.0, project log-mel.
- `tcresnet8_mfcc40`: TCResNet8 with project MFCC40; optional MFCC row.
- `dscnn_s_logmel`: DS-CNN-S with project log-mel.
- `dscnn_s_mfcc40`: DS-CNN-S with project MFCC40; optional MFCC row.
- Common training budget: batch 32, max 50 epochs, early stop 10, seed 42,
  cross entropy only, Adam learning rate `1e-4`.
- If no learning is observed in smoke or first run, a separate
  official-recipe tuning lane requires manager approval.

Server handoff plan:
- Before server run:
  1. Manager approves implementation.
  2. Create Track D integration branch.
  3. Add `baselines/`, env file, configs, adapters, shared loader/eval utils.
  4. Run local smoke tests only: import, frontend shape, synthetic forward,
     tiny loader, optional one-batch train smoke only if approved.
  5. Commit and push branch.
- Server settings:
  - `WEEKLY_TAG=drone_2026w19`
  - tmux session: `weekly_drone_2026w19_baseline_<baseline_name>`
  - output root:
    `weeklyresult/weekly_drone_2026w19/offline_baselines/<baseline_name>/`
- Startup receipt must include first 30 log lines with commit SHA, branch,
  conda env, Python/TensorFlow versions, GPU visibility, baseline config, input
  paths, output path, and first model summary line.
- Completion receipt must include last 50 log lines, checkpoint path, and result
  tree.

Recommended first training batch after implementation approval:
- `bcresnet1_logmel`
- `tcresnet8_logmel`
- `dscnn_s_logmel`

Manager decision:
- [x] Exact run plan received.
- [x] Server handoff gate accepted.
- [ ] Implementation branch/scaffold not yet approved.
- [ ] Dependency installation not yet approved.
- [ ] External repo download or vendoring not approved.
- [ ] Full baseline training not approved.

## 2026-05-04 Remaining Checklist
- [x] Track C: finish paper outline audit and rewrite plan.
- [x] Track C: core writing objective / claim / draft review memo accepted.
- [x] Track C: first structural rewrite received and validated with
  `git diff --check`.
- [x] Track C: revise paper voice from staged-evidence framing to design-first
  target-system framing.
- [x] Track C: accept talk-to-the-drone framing revision and 7-layer evaluation
  stack.
- [x] Track C: accept current framing convergence toward voice-driven UAV safety
  mechanism.
- [ ] Track C: rewrite advisor-suggested contribution candidates into formal
  paper contributions or conditional evaluation-backed claims.
- [ ] Track C: fix `git diff --check` for paper sources.
- [x] Track D: initialize evaluation track plan bound to
  `sections/6evaluation.tex`.
- [x] Track D: baseline literature/model shortlist.
- [ ] Track D: decide MFCC fairness rule for baseline table vs frontend
  ablation.
- [ ] Track D: decide 3-row vs 5-row baseline table for the first-round draft.
- [x] Track D: decide local vs server/tmux execution for offline baselines.
- [x] Track D: approve isolated conda environment plan before installing
  dependencies.
- [x] Track D: approve project-local baseline code layout before importing or
  copying external baseline code.
- [x] Track D: receive exact run plan before baseline implementation/training.
- [x] Track D: integrate baseline code/env/adapters/run scripts into repo before
  any server training dispatch.
- [x] Track D: commit and push Track D integration branch before server env
  deployment.
- [x] Track D: run first-batch log-mel baseline training on server.
- [x] Track D: receive complete server handoff with per-class metrics,
  startup/completion receipts, and tarball path.
- [x] Track D: update `main` with current paper draft before result-branch
  synchronization.
- [x] Track D: server-created local result commit
  `91153291ef3ead3ea75c7e7cb273150b549ce899`.
- [x] Track D: server-created and verified Git bundle for result commit.
- [x] Track D: import server result commit to local by Git bundle because
  server cannot push to GitHub.
- [x] Track D: inspect per-class baseline reports before paper integration.
- [ ] Track D: decide whether to merge result branch into `main` or keep as
  evidence branch.
- [ ] Track D: add verified citations to `references.bib` after approval.
- [x] Track B: dry command dispatch receipt accepted and synced.
- [x] Track A: design/prep receipt accepted with board validation blocker.
- [x] Track C: writing audit receipt accepted; paper files intentionally unchanged.
- [x] Track C: dispatch actual paper rewrite pass.
- [ ] Track B: prepare Tuesday ground/no-prop/dry command bridge prompt.
- [x] PM decision recorded: pause Track A for W18 pre-meeting execution.
- [ ] Track A: artifact consolidation deferred until after the 2026-05-07
  meeting unless explicitly reopened.
- [ ] Track A: heuristic calibration patch deferred until after the 2026-05-07
  meeting unless explicitly reopened.
- [x] Notion weekly management page updated with Track A receipt.
- [x] Notion weekly management page updated with Track A pause decision.
- [x] Append Track B receipt to `docs/weekly_todo/handoff_log.md`.
- [x] Append Track A receipt to `docs/weekly_todo/handoff_log.md`.
- [x] Append Track C receipt to `docs/weekly_todo/handoff_log.md`.
- [x] Append Track C writing review memo to `docs/weekly_todo/handoff_log.md`.
- [x] Append Track C first structural rewrite receipt and PM correction to
  `docs/weekly_todo/handoff_log.md`.
- [x] Append Track C talk-to-the-drone framing revision receipt to
  `docs/weekly_todo/handoff_log.md`.
- [x] Append Track C framing/contribution validation receipt to
  `docs/weekly_todo/handoff_log.md`.
- [x] Append Track D evaluation initialization plan to
  `docs/weekly_todo/handoff_log.md`.
- [x] Append Track D baseline literature/model shortlist receipt to
  `docs/weekly_todo/handoff_log.md`.
- [x] Append Track D result-commit push-blocker receipt to
  `docs/weekly_todo/handoff_log.md`.

## Track D Git Result Handoff Status
Update time: 2026-05-14 03:01 CDT.

Current local state:
- local branch: `main`
- local/remote `main`: `54fb1654e8fb5bd914f281d89c087bb560f529b8`
- local workspace: clean before this PM sync.
- latest local weekly result directory remains `weekly_drone_2026w18`; W19
  result artifacts are not yet present locally.

Server result commit:
- branch: `codex/track-d-baseline-results-20260514`
- commit: `91153291ef3ead3ea75c7e7cb273150b549ce899`
- parent/source commit:
  `420c4e4bc0bb00f5fe900195d9a9790d4d69e9c1`
- commit message: `Add W19 Track D first-batch baseline results`
- diff: `34 files changed, 745 insertions(+)`
- server status after commit: clean.

Server push blocker:
- `git push origin codex/track-d-baseline-results-20260514` failed because the
  server has no GitHub HTTPS credentials:
  `fatal: could not read Username for 'https://github.com': No such device or
  address`.
- SSH push is also unavailable:
  `git@github.com: Permission denied (publickey)`.

Committed artifact scope:
- `weeklyresult/weekly_drone_2026w19/offline_baselines/`
- `weeklyresult/weekly_drone_2026w19/offline_baselines_trackd_firstbatch_20260514.tar.gz`
- No code, paper, or weekly todo files were changed on the server result
  branch.

Result summary:

| baseline | accuracy | macro_f1 | checkpoint |
| --- | ---: | ---: | --- |
| `tcresnet8_logmel` | `0.840927` | `0.840687` | `weeklyresult/weekly_drone_2026w19/offline_baselines/tcresnet8_logmel/checkpoints/best.weights.h5` |
| `bcresnet1_logmel` | `0.796962` | `0.793465` | `weeklyresult/weekly_drone_2026w19/offline_baselines/bcresnet1_logmel/checkpoints/best.weights.h5` |
| `dscnn_s_logmel` | `0.606615` | `0.600723` | `weeklyresult/weekly_drone_2026w19/offline_baselines/dscnn_s_logmel/checkpoints/best.weights.h5` |

Per-class notes:
- `tcresnet8_logmel` is strongest overall by accuracy and macro F1.
- `bcresnet1_logmel` has the highest emergency recall (`0.8969`) but weaker
  movement recall (`0.6472`).
- `dscnn_s_logmel` is substantially weaker in this first-batch configuration.

Next synchronization method:
- Use `git bundle` from the server result branch, then import the bundle
  locally.
- This preserves the server-created commit SHA without requiring GitHub
  credentials on the server.
- Do not merge into `main` until the local bundle import is audited.

## Track D Server Git Auth Diagnosis
Update time: 2026-05-14 03:07 CDT.

Server diagnosis:
- Checked-out server branch during diagnosis: `main`
- Server HEAD: `f9740f00b79f8e5966510a8936767024e7e7b310`
- Server `main` status: clean but `[origin/main: behind 8]`
- Result branch exists locally:
  `codex/track-d-baseline-results-20260514`
- Result branch commit:
  `91153291ef3ead3ea75c7e7cb273150b549ce899`
- Remote:
  `origin https://github.com/z1L0Ng/Drone.git` for fetch and push.

Auth/config findings:
- No `remote.origin.pushurl`.
- No `remote.pushDefault`.
- No `branch.main.pushRemote`.
- No `branch.codex/track-d-baseline-results-20260514.pushRemote`.
- No `credential.helper`.
- `SSH_AUTH_SOCK` is empty.
- `gh` is not installed.
- `ssh -T git@github.com` fails with `Permission denied (publickey)`.
- `git push --dry-run origin codex/track-d-baseline-results-20260514` fails
  with:
  `fatal: could not read Username for 'https://github.com': No such device or address`.

Manager interpretation:
- This is an authentication/session issue, not a `codex/` branch permission
  issue.
- If the same server user/repo previously pushed successfully, that push must
  have used a different available auth path at the time: an interactive
  credential prompt/cache, a different clone/session, a temporary credential,
  or an ssh-agent/key that is not available now.
- The current server session has no usable GitHub auth through HTTPS, SSH, or
  GitHub CLI.
- Since result commit `91153291...` already exists locally on the server, the
  cleanest provenance-preserving path remains `git bundle` import on the local
  machine.

Next action:
- Ask server to create a bundle containing
  `codex/track-d-baseline-results-20260514`, verify it, and provide the bundle
  file for local import.

## Track D Git Bundle Ready
Update time: 2026-05-14 03:09 CDT.

Server bundle status:
- server branch: `codex/track-d-baseline-results-20260514`
- server branch HEAD:
  `91153291ef3ead3ea75c7e7cb273150b549ce899`
- server `git status --short`: clean
- bundle path: `/tmp/trackd_results_20260514.bundle`
- bundle size: `5.4M`

Bundle verification:
- `/tmp/trackd_results_20260514.bundle is okay`
- contains:
  `91153291ef3ead3ea75c7e7cb273150b549ce899 refs/heads/codex/track-d-baseline-results-20260514`
- requires:
  `420c4e4bc0bb00f5fe900195d9a9790d4d69e9c1`

Manager interpretation:
- The server-created Git commit is now packaged as a verified bundle.
- This preserves the result commit SHA and parent/source commit without relying
  on server GitHub credentials.
- Local result sync is still pending until the bundle is copied to the local
  machine and fetched into a local branch.

Next local import target:
- Copy `/tmp/trackd_results_20260514.bundle` from the server to a local path,
  e.g. `/Users/zilongzeng/Research/Drone/.handoff/trackd_results_20260514.bundle`.
- Fetch the bundle into local branch
  `codex/track-d-baseline-results-20260514`.
- Audit result tree before any merge into `main`.

## Track D Local Bundle Import And Audit
Update time: 2026-05-14 03:16 CDT.

Local import:
- local bundle path:
  `.handoff/trackd_results_20260514.bundle`
- local bundle size: `5.4M`
- `git bundle verify`: passed.
- fetched local branch:
  `codex/track-d-baseline-results-20260514`
- fetched branch HEAD:
  `91153291ef3ead3ea75c7e7cb273150b549ce899`

Commit/file-scope audit:
- `git show --stat` confirms result commit:
  `91153291 Add W19 Track D first-batch baseline results`
- diff vs source commit `420c4e4...` contains only
  `weeklyresult/weekly_drone_2026w19/`.
- Result commit contains 34 files, including:
  - three `checkpoints/best.weights.h5`
  - three `classification_report_noisy.txt`
  - three `metrics.json`
  - three confusion matrix `.npy/.png` pairs
  - three `history/train_history.csv`
  - three `run_config.json`
  - three `source_manifest.json`
  - startup/completion/result-tree receipts
  - `offline_baselines_trackd_firstbatch_20260514.tar.gz`
- No code, paper, or weekly todo files are in the result commit.

Size audit:
- tarball blob size: `2821746` bytes.
- `tcresnet8_logmel` checkpoint: `1421792` bytes.
- `bcresnet1_logmel` checkpoint: `1553776` bytes.
- `dscnn_s_logmel` checkpoint: `340824` bytes.

Metric audit from imported Git objects:

| model | accuracy | macro F1 | emergency F1 | movement F1 | unknown F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `w14 preprocess_ext` anchor | `0.88` | `0.88` | `0.87` | `0.88` | `0.90` |
| `B_small_teacher_student` deployment candidate | `0.87` | `0.87` | `0.86` | `0.87` | `0.88` |
| `tcresnet8_logmel` | `0.8409` | `0.8407` | `0.8638` | `0.8136` | `0.8446` |
| `bcresnet1_logmel` | `0.7970` | `0.7935` | `0.8269` | `0.7381` | `0.8154` |
| `dscnn_s_logmel` | `0.6066` | `0.6007` | `0.6658` | `0.5162` | `0.6201` |

Interpretation:
- None of the first-batch baselines beats `w14 preprocess_ext` on overall
  accuracy or macro F1.
- `tcresnet8_logmel` is the strongest first-batch baseline overall.
- `bcresnet1_logmel` has the highest emergency recall among the baselines
  (`0.8969`) but lower emergency precision and substantially lower movement
  recall than `tcresnet8_logmel`.
- `dscnn_s_logmel` is weak under this exact protocol.
- Paper claim should be: the project model anchor remains stronger than the
  first-batch compact KWS baselines under the same noisy-eval protocol.
- Do not claim deployment feasibility or safety validation from these offline
  baseline results.

Receipt caveat:
- The committed Git tree contains `completion_last50.txt` and
  `result_tree.txt` for each baseline.
- The text inside `completion_last50.txt` has an internal `result_tree:` list
  that does not include `completion_last50.txt` / `result_tree.txt` themselves.
  Treat this as a receipt-generation-order limitation, not as missing files.

Merge consideration:
- Do not merge immediately during this audit step.
- Merging `codex/track-d-baseline-results-20260514` into `main` will bring both
  the Track D baseline scaffold lineage and W19 result artifacts, because the
  result branch is based on `420c4e4...`.
- Recommended next decision: either merge the result branch into `main` after
  accepting scaffold+results together, or keep it as an evidence branch and
  manually curate paper-facing tables.

## Local/Server Branch Sync Closeout
Update time: 2026-05-14 03:26 CDT.

Local cleanup:
- Local branch: `main`
- Local `git status --short`: clean.
- `.handoff/` is retained locally and excluded via `.git/info/exclude`.

Local and GitHub branch state:
- `main` / `origin/main`:
  `b6c42e565a89c939a6d550924732e532d8a685c2`
- `codex/track-d-baseline-integration-20260513` / remote:
  `420c4e4bc0bb00f5fe900195d9a9790d4d69e9c1`
- `codex/track-d-baseline-results-20260514` / remote:
  `91153291ef3ead3ea75c7e7cb273150b549ce899`

Server sync confirmation:
- Server path: `/files1/Zilong/Drone`
- Server branch after sync: `main`
- Server `git status --short`: clean.
- Server `main`:
  `b6c42e565a89c939a6d550924732e532d8a685c2`
- Server `origin/main`:
  `b6c42e565a89c939a6d550924732e532d8a685c2`
- Server retained local result branch:
  `codex/track-d-baseline-results-20260514`
  at `91153291ef3ead3ea75c7e7cb273150b549ce899`.

Closeout decision:
- `main` is synchronized between local, GitHub, and server.
- Track D integration and result branches are synchronized between local and
  GitHub, and the result branch still exists on the server.
- No merge of Track D result branch into `main` has been performed.

## Risks
- Track B and Track A output files are ignored by `.gitignore`; final
  preservation needs an explicit policy for whether to force-add selected
  realworld artifacts or keep them as runtime-only evidence.
- Track A artifacts are split across main workspace and Track A worktree; this
  must be consolidated before commit or handoff.
- Track A current raw-energy heuristic fails quiet-background suppression, so it
  is paused for the remainder of the W18 pre-meeting execution window.
- Flight testing is blocked until live dry-run coverage includes emergency and
  movement cases.
- Movement intent currently lacks direction, so direct drone movement remains
  unsafe without manual override or a separate direction parser.
- Track A gate may false-trigger on non-speech noise and is not a safety
  mechanism.
- Track A should be discussed as initial demo feasibility only in the 2026-05-07
  meeting; it should not consume the remaining pre-meeting execution time unless
  explicitly reopened.
- Paper writing risk is now structural: `main.tex` does not include the more
  current `3overview/4implementation` files, and several included sections still
  contain stale claims or unsupported generalization language.
- Paper voice risk: if the draft keeps saying "staged evidence" as the central
  frame, it will read like a progress report. The next pass should write the
  target system/design first, then mark missing evaluations explicitly.
- Paper compile risk: local LaTeX toolchain is unavailable, so structural
  validation is limited to `git diff --check`, grep checks, and source review
  until a PDF can be compiled elsewhere.
- Evaluation scope risk: the new 7-layer evaluation plan is stronger and more
  paper-like, but several layers still require new experiments before the
  submission draft can make final claims.
- Baseline-selection risk: a model that is strong in keyword spotting or general
  speech intent may be unfair or unhelpful if it cannot be adapted cleanly to
  movement / emergency / unknown under the same rotor-noise protocol.
- Baseline-comparison risk: MFCC baselines may confound the offline model
  comparison with the planned frontend ablation unless the table explicitly
  separates model family from frontend.
- Upper-bound risk: Direct SLU / FSC-style systems use pretraining and a
  different task formulation, so they should not be mixed into the fair main
  comparison table without a clear upper-bound label.
