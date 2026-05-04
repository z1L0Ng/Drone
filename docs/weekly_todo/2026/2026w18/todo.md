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

## 2026-05-04 Remaining Checklist
- [x] Track C: finish paper outline audit and rewrite plan.
- [x] Track B: dry command dispatch receipt accepted and synced.
- [x] Track A: design/prep receipt accepted with board validation blocker.
- [x] Track C: writing audit receipt accepted; paper files intentionally unchanged.
- [ ] Track B: prepare Tuesday ground/no-prop/dry command bridge prompt.
- [ ] Track A: consolidate artifact set into one branch/worktree before commit.
- [x] Notion weekly management page updated with Track A receipt.
- [x] Append Track B receipt to `docs/weekly_todo/handoff_log.md`.
- [x] Append Track A receipt to `docs/weekly_todo/handoff_log.md`.
- [x] Append Track C receipt to `docs/weekly_todo/handoff_log.md`.

## Risks
- Track B and Track A output files are ignored by `.gitignore`; final
  preservation needs an explicit policy for whether to force-add selected
  realworld artifacts or keep them as runtime-only evidence.
- Track A artifacts are split across main workspace and Track A worktree; this
  must be consolidated before commit or handoff.
- Flight testing is blocked until live dry-run coverage includes emergency and
  movement cases.
- Movement intent currently lacks direction, so direct drone movement remains
  unsafe without manual override or a separate direction parser.
- Track A gate may false-trigger on non-speech noise and is not a safety
  mechanism.
- Paper writing risk is now structural: `main.tex` does not include the more
  current `3overview/4implementation` files, and several included sections still
  contain stale claims or unsupported generalization language.
