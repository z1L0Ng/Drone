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

## 2026-05-04 Remaining Checklist
- [x] Track C: finish paper outline audit and rewrite plan.
- [x] Track C: core writing objective / claim / draft review memo accepted.
- [x] Track C: first structural rewrite received and validated with
  `git diff --check`.
- [ ] Track C: revise paper voice from staged-evidence framing to design-first
  target-system framing.
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
