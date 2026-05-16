# Paper Integration Plan For Evaluation Rewrite

Date: 2026-05-16

Scope: planning only. No paper tex, `references.bib`, ESP32 firmware, Tello control code, training code, or server tasks were changed by this evaluation-agent pass.

## Audit Status

Git audit at start of this pass:

| Item | Value |
| --- | --- |
| Branch | `main` |
| HEAD | `3d5eba17ade035f030020db283897f0765916b7a` |
| Dirty/untracked state | existing modifications in `.DS_Store`, `docs/paper_sensys2027/*`, `docs/weekly_todo/handoff_log.md`, and untracked `docs/weekly_todo/2026/2026w19/` |

Files audited read-only:

- `docs/paper_sensys2027/main.tex`
- `docs/paper_sensys2027/sections/1introduction.tex`
- `docs/paper_sensys2027/sections/2motivation.tex`
- `docs/paper_sensys2027/sections/3architecture.tex`
- `docs/paper_sensys2027/sections/4recognizer.tex`
- `docs/paper_sensys2027/sections/5prototype.tex`
- `docs/paper_sensys2027/sections/6evaluation.tex`
- `docs/paper_sensys2027/WRITING_OUTLINE.md`
- `docs/weekly_todo/2026/2026w19/todo.md`
- `docs/weekly_todo/2026/2026w19/dispatch_prompts.md`
- W19 first-batch baseline artifacts on branch `codex/track-d-baseline-results-20260514`, read through `git show` only

The current draft already frames the system as an additional voice-command UAV safety interaction layer. The evaluation rewrite should preserve that framing and should not collapse the paper into a generic recognizer benchmark.

## Proposed `6evaluation.tex` Structure

1. Evaluation overview and evidence boundaries.
   State that the evaluation has four evidence classes: recognizer quality, latency/runtime, safety-state/bridge behavior, and user-study/demo evidence.

2. Recognizer quality under matched conditions.
   Report anchor/student and verified offline baselines under matched split/support and noise condition. Include confusion matrix and class-specific emergency/unknown metrics.

3. Testing-condition robustness.
   Report SNR/noise-source/distance/angle/background condition results only where result files exist. Keep uncollected live conditions as protocol text or TODO comments.

4. Deployment and runtime.
   Report TFLite compatibility, model size, op mix, runtime stability, and timing breakdown. Explicitly say current `2094 ms` pure inference p50 and `3075 ms` total p50 are runtime evidence under audit, not semantic accuracy and not a `<=1s` real-time result.

5. Safety-state and bridge behavior.
   Report event-to-state logs: emergency handling, movement pending path, unknown fallback, manual override, ack/timeout, and unsafe command attempt count. Existing W18 dry-run replay can support plumbing only because it lacks emergency/live/no-prop coverage.

6. User-study and demo protocol.
   Describe the planned approved collection: participants, utterances, metadata, conditions, timing annotation, and demo evidence. Only move this into results after data exists.

7. Mechanism-level comparison to existing UAV safety modules.
   Explain why geofencing, obstacle avoidance, return-to-home, RC failsafe, manual stop, and controller actions are not classifier baselines. Compare them in a mechanism matrix over trigger source, response path, latency definition, coverage, fail-safe behavior, and evidence type.

8. Artifact and reproducibility plan.
   List result manifests, run configs, TFLite/export metadata, timing logs, bridge schemas, study manifests, and figure-generation scripts that exist.

## Evidence Map For Paper Claims

| Paper content | Existing repo evidence? | Evidence path | Can write as result now? | Boundary |
| --- | --- | --- | --- | --- |
| Anchor recognizer quality | Yes | `weeklyresult/weekly_drone_2026w14/preprocess_ext/classification_report_noisy.txt` | Yes | Offline noisy-set recognizer result only. |
| Embedded student recognizer quality | Yes | `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/classification_report_noisy.txt` | Yes | Deployment candidate, not main recognizer winner. |
| W19 first-batch baseline comparison | Branch evidence only | `codex/track-d-baseline-results-20260514:weeklyresult/weekly_drone_2026w19/offline_baselines/*` | Not as final mainline table yet | Unmerged branch; support differs from anchor/student and needs comparability audit. |
| TFLM export compatibility | Yes | `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/tflm_candidate_precheck.json` | Yes | Deployment feasibility, not board semantic accuracy. |
| ESP32 runtime stability | Yes | `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_report.md` | Yes | Runtime only; not semantic accuracy or safety validation. |
| ESP32 `<=1s` real-time | No | W19 latency audit says current checkpoint is not low-risk feasible for `<=1s` | No | Must not claim. |
| Speech onset to model event | No | needs annotated live audio/video and synchronized logs | Protocol only | Existing trigger-based runs do not include speech onset. |
| Model event to host command | Partial dry-run only | W18 dry-run replay logs | Limited | Dry-run plumbing; no emergency/no-prop/grounded proof. |
| Command to drone response | No | requires no-prop/grounded/flight logs | Protocol only | Do not infer from dry-run. |
| Safety-state behavior | Partial | W18 dry-run replay and schema fields | Limited | Movement/unknown dry replay only; emergency missing. |
| User study | No | protocol in this directory | Protocol only | Requires manager approval and data collection. |
| Demo evidence | No | storyboard/collection future | Protocol only | Demo is explanatory unless logged as study data. |
| Existing UAV safety mechanism comparison | Planning evidence | mechanism matrix in this directory and prior planning notes | Yes as framing/matrix | Not a unified quantitative classifier benchmark. |

## W19 First-Batch Baseline Summary

Read-only source: branch `codex/track-d-baseline-results-20260514`, commit `91153291`, with result provenance from `run_config.json` and `metrics.json`.

| Baseline | Frontend | Eval SNR | Support | Accuracy | Macro F1 | Emergency F1 | Notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| TCResNet8 | logmel | `-10 dB` | `10008` | `0.8409` | `0.8407` | `0.8638` | Best first-batch baseline among the three. |
| BC-ResNet1 | logmel | `-10 dB` | `10008` | `0.7970` | `0.7935` | `0.8269` | Higher emergency recall, weaker movement recall. |
| DS-CNN-S | logmel | `-10 dB` | `10008` | `0.6066` | `0.6007` | `0.6658` | Weak first-batch baseline. |

Paper usage:

- Acceptable: "A first-batch unmerged W19 baseline branch suggests TCResNet8 and BC-ResNet1 are useful recognizer baselines, while DS-CNN-S is substantially weaker under the current `-10 dB` setup."
- Not acceptable yet: a final paper leaderboard directly mixing these numbers with `w14 preprocess_ext` and `B_small_teacher_student` without split/support/run-config comparability verification.

## Direct Answers For Evaluation Rewrite

1. Baseline comparisons should expand to matched offline split parity, SNR sweep, noise-source conditions, distance/angle/user conditions where collected, deployment runtime, and bridge state behavior. Recognizer baselines and safety mechanisms must be separate tables.

2. User study target: `24` participants for paper-facing controlled study; `6` participant pilot; minimum `12` only if reported as small controlled evidence. Use emergency/movement/unknown scripts, participant metadata, distance/angle/background metadata, and silence/background trials.

3. Response time must be decomposed into speech onset -> model event, model event -> host bridge decision/command send, and command send -> ack/timeout or physical response. Current evidence only supports component timing after trigger, not speech-onset timing.

4. Manual stop/controller comparisons are fair only with shared cue and stop event definitions. Existing UAV safety modules should be compared at mechanism level because their triggers are position, obstacle, link/battery, or operator-action conditions, not speech labels.

5. The paper should explain the lack of a unified quantitative benchmark by pointing to different trigger sources, failure modes, action semantics, and evidence types. The defensible comparison is a mechanism matrix plus per-mechanism latency when logs exist.

6. Results that must be truly collected: live semantic accuracy, speech-onset timing, no-prop/grounded command response, emergency bridge path, participant study outcomes, and any flight claim. Protocol/planned only: user study until approval, mechanism comparison without logs, safety-state validation beyond dry-run, and `<=1s` onboard real-time until a new measured candidate exists.

## Non-Claims To Preserve

- Do not claim runtime stability proves semantic accuracy.
- Do not claim ESP32 runtime proves safety validation.
- Do not claim current `B_small_teacher_student` satisfies `<=1s`.
- Do not claim Track B dry-run is flight or physical drone-response evidence.
- Do not claim gate/buffer is validated until false-trigger and repeated-trigger logs exist.
- Do not treat geofencing, obstacle avoidance, return-to-home, or RC failsafe as classifier baselines.
- Do not present `movement` as a direct flight command.
