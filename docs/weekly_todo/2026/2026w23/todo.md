# Weekly TODO (CDT, Thursday-cycle 2026w23)

Meeting checkpoint: Thursday 2026-06-04.

Planning cycle: Thursday 2026-06-04 -> submission weekend.

Project target: SenSys 2027 first-round submission.

## Current Repo Audit

Audit time: 2026-06-05 12:19 CDT.

- Branch: `main`
- HEAD: `9f73717bf176cb5adc7eb0072d3e26076c18eae7`
- Worktree status: clean.
- Latest result directory: `weeklyresult/weekly_drone_2026w23`.
- Related Work status correction: current
  `docs/paper_sensys2027/sections/2relatedwork.tex` already contains
  `tab:related_work_comparison`; the remaining action is to polish/expand it,
  not to add a table from scratch.

## Priority Update

Current submission focus:

1. Rewrite the paper framing around:
   naive approaches fail -> Akouo insight -> system realization -> evaluation
   proves the contrast.
2. Defer demo video work unless needed as optional presentation support.
3. Prioritize missing baseline/evaluation support, especially approaches that
   the new framing criticizes.

## Writing-Agent Framing Diagnosis Receipt

Status:
- Writing agent completed a read-only framing diagnosis.
- No TeX edits, figure edits, experiments, model changes, or firmware changes.

New thesis direction:
- Akouo targets hands-free UAV safety interaction under rotor self-noise.
- The core problem is not just speech recognition near a drone, but how noisy
  human speech should enter a physical control system.
- Akouo should be framed as constrained safety-relevant intent events mediated
  by a safety-state boundary, not as transcripts, keyword triggers, or direct
  flight commands.

Argument structure:

```text
Goal X:
Hands-free UAV safety interaction under rotor noise.

Naive Y:
ASR/STT + command parsing, keyword spotting / speech-command classifiers,
or direct speech-to-command mapping.

Problems:
Rotor-noise brittleness, transcript ambiguity, embedded latency/memory mismatch,
lack of conservative fallback, and unsafe direct action binding.

Insight W:
Represent nearby speech as constrained safety-relevant intent events.

System A:
Akouo realizes this event abstraction through onboard recognition and a
safety-state boundary.
```

Revised contribution targets:
- Safety-state voice interaction abstraction.
- Constrained intent-event contract.
- Onboard rotor-noisy event recognizer.
- Naive-approach comparison and system evaluation.

Sections needing rewrite:
- Abstract: name the transcript-first/direct-trigger alternatives and the event
  mediation contrast.
- Introduction: reorganize around X -> Y failures -> W insight -> Akouo -> evidence.
- Related Work: organize around ASR/speech interfaces, KWS/command classifiers,
  embedded speech/TinyML, and UAV safety mechanisms.
- Motivation: become the failure-analysis section.
- Architecture: strengthen why unknown/logged events/bridge avoid naive failures.
- Recognizer: frame as producing the event contract, not model novelty alone.
- Prototype: present safety-state boundary as a core design, not convenience.
- Evaluation: add naive-approach comparison.
- Conclusion: close on safer speech admission into UAV control.

Required evaluation additions:
- ASR + command parser baseline.
- Keyword spotting / direct-trigger baseline.
- Direct command classifier or direct-command mapping baseline.
- No-unknown fallback ablation.
- No-bridge/direct-action ablation.
- Keep TC-ResNet, BC-ResNet, and DS-CNN as recognizer architecture baselines,
  not full system alternatives.
- Add runtime/deployability comparison where possible.

## Current Risks

- If the paper criticizes ASR/STT or direct command mapping but does not compare
  against them, the evaluation will look incomplete.
- If evaluation protocols are vague, reviewers may doubt whether metrics reflect
  a real deployment.
- If the rewrite happens without preserving current figures/tables/page budget,
  the final submission may regress in presentation quality.

## Next Actions

- [x] Ask evaluation agent for a minimum feasible ASR/STT + parser baseline plan.
- [x] Ask evaluation agent for no-unknown and no-bridge ablation plans that can
      be produced quickly.
- [x] Ask writing agent to prepare concrete section rewrite patches only after
      baseline feasibility is known.
- [x] Keep figure work limited to supporting the new framing.

## Evaluation-Agent Baseline Feasibility Receipt

Status:
- Evaluation agent completed baseline/evaluation feasibility planning.
- No experiments were run and no files were edited by the agent.

Core conclusion:
- Existing BC-ResNet, TC-ResNet, and DS-CNN results can only support compact
  speech-command classifier baselines.
- They do not by themselves support the new framing claim that naive approaches
  fail.
- The paper needs at least one transcript-first ASR/STT + rule-parser baseline,
  and preferably one direct-command mapping strawman.

Recommended baseline list:

1. Transcript-first ASR/STT + rule parser.
   - Primary paper-facing candidate: Whisper `tiny.en` or `base.en`.
   - Faster/lightweight candidate: Vosk small English model.
   - Optional deployability caveat: `whisper.cpp` quantized tiny/base.
2. Compact speech-command classifier baselines.
   - Keep TC-ResNet8, BC-ResNet1, DS-CNN-S.
   - Rename them as speech-command classifier baselines, not safety baselines.
3. Direct command mapping baseline.
   - No new model needed.
   - Use existing recognizer or parser predictions and map events directly to
     actions, removing the safety-state boundary.

Minimum feasible experiment before submission:
- Run one ASR/STT baseline at the fixed noisy condition.
- Output root:
  `weeklyresult/weekly_drone_2026w23/asr_stt_baseline_<system>_fixed_noisy_20260604/`
- Required outputs:
  - `run_manifest.json`
  - `transcripts.csv`
  - `parsed_intents.csv`
  - `metrics.json`
  - `classification_report_intent_parse.txt`
  - `confusion_matrix_intent_parse.csv`
  - `latency_summary.json`
  - `report.md`

Recommended protocol:
- Input: same test split from `dataset/processed/data_paths.npz`.
- Noise: reuse the W23 fixed noisy condition matching current paper table.
- Parser: normalize transcript, apply deterministic dictionaries, precedence
  `emergency > movement > unknown`.
- Metrics: transcript non-empty rate, keyword hit rate, intent parse accuracy,
  macro F1, emergency recall, unknown false action rate, parse failure rate,
  median/p95 latency, and deployment caveat.

Execution split:
- Local only for this submission-week ASR baseline:
  - parser/eval harness
  - parser tests
  - 50-200 sample smoke
  - full fixed-noisy ASR transcription over the test split
  - optional direct-command simulator
- Do not dispatch this ASR baseline to the server unless the user explicitly
  reverses this decision.

Paper guidance:
- Do not claim ASR fails until numeric results exist.
- Current KWS rows should be renamed as compact speech-command classifier
  baselines.
- Direct-command mapping can enter as a strawman/ablation if numbers are
  produced; otherwise keep it as motivation or discussion.

Risk:
- If only planning/discussion is added and no ASR+parser result appears,
  reviewers may still see the “naive approach fails” claim as unsupported.

## Local-Only ASR Baseline Decision

Decision time: 2026-06-04 17:04 CDT.

- The W23 ASR/STT baseline smoke and full run should both run locally.
- This is an evaluation run, not model training, so the server/tmux training
  handoff protocol does not apply unless the work is later moved to server.
- The implementation still needs a committed code state before results are
  treated as final paper evidence.

Required local outputs:
- Smoke:
  `weeklyresult/weekly_drone_2026w23/asr_stt_baseline_<system>_fixed_noisy_20260604_smoke/`
- Full:
  `weeklyresult/weekly_drone_2026w23/asr_stt_baseline_<system>_fixed_noisy_20260604/`

Required receipts:
- Local startup receipt: command, commit SHA, Python/env, ASR system/model,
  input split, noise condition, output directory.
- Local completion receipt: runtime summary, transcript count, parsed count,
  metric summary, result tree, and any skipped/failed files.

## ASR/STT Baseline Result Receipt

Receipt time: 2026-06-04 18:56 CDT.

Status:
- Evaluation agent completed the local ASR/STT + rule-parser baseline.
- No paper edits, no model training, no model-training-code edits, and no
  server/tmux execution.

Dependency/execution:
- ASR system: Whisper `tiny.en`.
- Python package: `openai-whisper==20250625`.
- Runtime dependency: `torch==2.12.0`.
- Device: CPU.
- Local model cache:
  `weeklyresult/weekly_drone_2026w23/asr_stt_model_cache/whisper`.
- Local environment required `KMP_DUPLICATE_LIB_OK=TRUE` to avoid an OpenMP
  runtime conflict in the conda environment.
- Vosk fallback was not used.

Full result:
- Condition: W23 manifest `snr_m10db = -10.0 dB`.
- Samples: `10008/10008`.
- Failed/skipped: `0`.
- Transcript non-empty rate: `0.4253`.
- Keyword hit rate: `0.1225`.
- Intent parse accuracy: `0.4294`.
- Macro F1: `0.3503`.
- Emergency recall: `0.2209`.
- Unknown false action rate: `0.0204`.
- Median/p95 ASR latency: `0.0618 / 0.0861 s`.
- Model cache size: `75,571,315 bytes`.

Confusion matrix:

```text
true\pred,emergency,movement,unknown
emergency,737,95,2504
movement,34,292,3010
unknown,34,34,3268
```

Artifacts:
- Smoke:
  `weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604_smoke/`
- Full:
  `weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604/`
- Key files: `run_manifest.json`, `startup_receipt.md`, `transcripts.csv`,
  `parsed_intents.csv`, `metrics.json`,
  `classification_report_intent_parse.txt`,
  `confusion_matrix_intent_parse.csv`, `latency_summary.json`, `report.md`,
  `result_tree.txt`.

Paper usability:
- Paper-usable as a transcript-first ASR baseline with conservative wording.
- Safe wording: Whisper `tiny.en` plus deterministic parsing has limited
  command/intent coverage on fixed rotor-noisy 1s clips, especially for
  emergency recall.
- Do not write “all ASR fails.”
- Align any condition-label/value mismatch in the current paper table before
  inserting this ASR row.

Commit caution:
- Do not commit the local Whisper model cache unless explicitly approved.
- Prefer committing the script, result summaries, and lightweight artifacts only.

## Naive-Solution Framing and Baseline Expansion Plan

Decision time: 2026-06-04 19:18 CDT.

Current decision:
- Hold the completed Whisper `tiny.en` + parser result as an evidence
  candidate.
- Do not immediately make it the only naive-approach comparison in the paper.
- First map the likely reviewer-suggested solutions, decide how each should be
  framed, and then choose which additional baselines can be run in the remaining
  time.

Reviewer-obvious solution families:

1. Transcript-first ASR/STT + parser.
   - Why reviewers may expect it: the most natural way to process speech is to
     transcribe words and parse commands.
   - Paper framing: transcript-first systems are flexible but expose Akouo to
     rotor-noise transcript loss, parser ambiguity, and non-MCU deployment
     constraints.
   - Existing evidence: Whisper `tiny.en` + deterministic parser at `-10 dB`.
   - Additional possible baseline: Vosk small English as a lightweight offline
     STT contrast, if time permits.

2. Keyword spotting / direct trigger.
   - Why reviewers may expect it: small KWS models are common in embedded audio.
   - Paper framing: keyword-trigger designs can be lightweight, but they do not
     by themselves provide the safety-state boundary or explicit containment of
     unsupported audio.
   - Existing evidence: TC-ResNet, BC-ResNet, DS-CNN as compact
     speech-command classifier baselines.
   - Additional possible baseline: dictionary keyword trigger over transcripts
     or audio labels, reporting missed emergency and unknown false trigger rate.

3. Direct speech-command classifier.
   - Why reviewers may expect it: train a classifier and map the class directly
     to commands.
   - Paper framing: direct classifiers conflate recognition with action binding;
     errors become command pressure unless a separate boundary blocks them.
   - Possible baseline: use Akouo/reference predictions or classifier baseline
     predictions, then simulate direct action mapping without the safety-state
     boundary.

4. No-unknown fallback ablation.
   - Why reviewers may expect it: a simpler classifier may only predict
     actionable command classes.
   - Paper framing: unknown/fallback is not just another label; it is a safety
     containment mechanism.
   - Possible baseline: collapse unknown examples into the nearest actionable
     class or measure forced-action rate without explicit unknown.

5. No-bridge/direct-action ablation.
   - Why reviewers may expect it: after recognition, dispatch actions directly.
   - Paper framing: Akouo's bridge is the mechanism that prevents speech output
     from becoming physical action without policy checks.
   - Possible baseline: replay event logs without boundary rules and report how
     many events would become unauthorized or blocked actions.

6. Cloud/phone ASR or stronger ASR.
   - Why reviewers may expect it: high-quality speech systems exist off-device.
   - Paper framing: this can be a performance upper-bound or discussion point,
     but it may not satisfy onboard/low-power/safety-boundary requirements.
   - Possible baseline: defer unless a fast API/offline model is already
     available; avoid spending submission time on a moving target.

Minimum useful additional baselines:
- [x] Direct command mapping simulator from existing predictions/logs.
- [x] No-unknown fallback ablation from existing confusion outputs.
- [ ] Optional Vosk small English STT baseline only if Whisper result is judged
      insufficient or too narrow.

Paper-writing plan:
- Use the completed Whisper result to support a narrow claim:
  transcript-first ASR+parser has limited intent coverage in our fixed
  rotor-noisy 1s setup.
- Use KWS baselines to support model-family comparison, not system safety.
- Use direct-mapping/no-unknown/no-bridge ablations to support the safety-state
  abstraction claim.
- Avoid broad universal statements such as “ASR fails” or “KWS is unsafe.”

## Safety Ablation / Direct Mapping Result Receipt

Receipt time: 2026-06-04 19:30 CDT.

Status:
- Evaluation agent completed the direct command mapping simulator and
  no-unknown fallback ablation.
- No paper edits, no model training, no server/tmux execution.

Artifact directory:
- `weeklyresult/weekly_drone_2026w23/safety_ablation_direct_mapping_20260604/`

New script:
- `scripts/eval_safety_ablation_direct_mapping.py`

Key files:
- `action_pressure_table.csv`
- `direct_mapping_metrics.json`
- `no_unknown_ablation_metrics.json`
- `input_sources.json`
- `report.md`
- `result_tree.txt`
- `run_manifest.json`

Core results:
- Akouo/reference fixed noisy `-10 dB`:
  - direct mapping action pressure: `67.57 / 100 windows`
  - unknown false action rate: `0.1634`
  - missed emergency action rate: `0.1469`
- ASR Whisper tiny parser:
  - action pressure: `12.25 / 100 windows`
  - unknown false action rate: `0.0204`
  - missed emergency action rate: `0.7791`
  - paper role: transcript-first baseline failure evidence candidate.
- Embedded user-study v4 candidate:
  - action pressure: `68.81 / 100 windows`
  - unknown false action rate: `0.1625`
  - missed emergency action rate: `0.3782`

No-unknown ablation:
- Akouo/reference and ASR are label/confusion-only bounds.
- Removing unknown forces all true unknown samples into actionable classes.
- Akouo/reference additional action pressure: `+32.43 / 100 windows`.
- ASR additional action pressure: `+87.75 / 100 windows`.
- Embedded v4 has probabilities:
  - true unknown forced to emergency: `82.25%`
  - true unknown forced to movement: `17.75%`
  - additional action pressure: `+31.19 / 100 windows`.

Paper usability:
- Paper-usable as an offline action-pressure simulator.
- Required boundary wording:
  “This is not a flight test or safety validation; it measures how often
  recognizer outputs would become actionable if the bridge and unknown fallback
  were removed.”
- Highest-priority numbers for Evaluation:
  1. Akouo/reference direct mapping action pressure `67.57 / 100 windows` and
     unknown false action rate `0.1634`.
  2. No-unknown Akouo/reference additional action pressure
     `+32.43 / 100 windows`.
  3. Embedded v4 probability no-unknown result:
     `82.25%` true unknown forced emergency and `17.75%` forced movement.

Baseline expansion decision:
- Vosk or stronger ASR is not required for the current submission if the paper
  only claims that transcript-first ASR+parser is fragile in this setup.
- If the paper wants a formal ASR/STT comparison claim, add Vosk or Whisper
  small/base; otherwise prioritize paper rewrite.

## Writing-Agent Evaluation Integration Receipt

Receipt time: 2026-06-05 01:49 CDT.

Status:
- Writing agent integrated ASR baseline, compact speech-command classifier
  baselines, direct mapping, and no-unknown ablations into Evaluation.
- Modified file:
  `docs/paper_sensys2027/sections/7evaluation.tex`.
- No experiment, model, firmware, or figure changes.

Completed Evaluation changes:
- Added `Transcript-First ASR Baseline` subsection.
  - Whisper `tiny.en` + deterministic parser:
    accuracy `0.4294`, macro F1 `0.3503`, emergency recall `0.2209`,
    transcript non-empty `0.4253`, keyword hit `0.1225`.
  - Boundary: fixed rotor-noisy 1s clips, transcript-first baseline only; not
    evidence that all ASR systems fail.
- Renamed the old baseline comparison framing to
  `Compact Speech-Command Classifier Baselines`.
  - TC-ResNet, BC-ResNet, and DS-CNN are scoped as compact speech-command
    classifier baselines, not full safety-system baselines.
- Added `Safety-State Boundary Ablations` subsection.
  - Direct mapping: `67.57` action requests / 100 windows; unknown false action
    rate `0.1634`.
  - No-unknown reference ablation: `+32.43` action requests / 100 windows.
  - Embedded v4 no-unknown: true unknown forced emergency `82.25%`, forced
    movement `17.75%`.
  - Boundary: offline action-pressure simulation, not flight test, measured
    actuation, or safety validation.
- Evaluation opening was updated while preserving traditional systems-paper
  subsection style; no Q&A/RQ headings were introduced.

Validation:
- `git diff --check -- docs/paper_sensys2027` passed.
- LaTeX compile is still pending.

## Writing-Agent Motivation Rewrite Receipt

Receipt time: 2026-06-05 01:57 CDT.

Status:
- Writing agent completed Motivation-only rewrite.
- Modified file:
  `docs/paper_sensys2027/sections/3motivation.tex`.
- No Introduction, Evaluation, experiment, model, firmware, or figure-asset
  changes.

Completed Motivation structure:
- `Voice Input Creates Physical Action Risk`
- `Failure Modes of Common Speech Interfaces`
- `Constrained Safety-State Events`

Covered design hazards:
- Transcript-first ASR/STT + parser may have limited coverage in short
  rotor-noisy clips.
- KWS / compact speech-command classifier does not provide safety-state
  mediation by itself.
- Direct speech-to-command mapping can turn recognition errors into action
  pressure.
- No-unknown fallback can force unsupported audio into actionable classes.
- Embedded/deployment constraints require local event streams and boundary
  checks.

Boundary:
- Motivation no longer previews Evaluation tables.
- Clean/noisy figure caption was adjusted to serve motivation.
- The section does not claim all ASR fails.
- The section does not claim flight safety validation.

Validation:
- `git diff --check -- docs/paper_sensys2027` passed.
- LaTeX compile is still pending.

## Writing-Agent Architecture Consistency Receipt

Receipt time: 2026-06-05 02:05 CDT.

Status:
- Writing agent completed Architecture consistency pass.
- Modified file:
  `docs/paper_sensys2027/sections/4architecture.tex`.
- No Introduction, Evaluation, experiment, model, firmware, or figure-asset
  changes.

Completed changes:
- Tightened terminology from `intent event / control boundary / bridge` to
  `structured safety-state event / safety-state boundary / event-state contract`.
- Reframed `movement` as ordinary control-oriented intent without direction,
  distance, velocity, or permission; it should not read as a direct navigation
  command.
- Reframed `unknown` as a containment mechanism, not a normal third class.
- Removed `Tello SDK` / engineering bridge tone from Architecture and replaced
  it with `gated vehicle-facing action`.
- Made the safety-state boundary a core design element that considers vehicle
  state, policy, authority, and recent history before forwarding anything.
- Did not repeat Motivation failure analysis and did not add Evaluation numbers
  or Q&A/RQ headings.

Validation:
- Architecture search found no inconsistent terms reported by writing agent:
  `bridge`, `Tello`, `SDK`, `control boundary`, `all ASR`,
  `flight safety validation`.
- `git diff --check -- docs/paper_sensys2027` passed.
- LaTeX compile is still pending.

## Writing-Agent Evaluation Tone Check Receipt

Receipt time: 2026-06-05 02:22 CDT.

Status:
- Writing agent completed Evaluation tone check.
- Modified file:
  `docs/paper_sensys2027/sections/7evaluation.tex`.
- No experiments, model, firmware, or figure changes.

Completed changes:
- Unified terminology to `structured safety-state event`,
  `safety-state boundary`, and `event-state contract`.
- Removed old `control bridge / control boundary / direct command` tone.
- Kept ASR baseline narrowly scoped to fixed rotor-noisy 1s clips and did not
  generalize to all ASR.
- Clarified compact speech-command classifier baselines are not complete
  safety-system baselines.
- Preserved direct mapping / no-unknown as offline action-pressure simulations,
  not flight tests or measured UAV actuation.
- Shifted Evaluation tone from offline model leaderboard toward layered system
  evidence.
- No new experiment numbers and no table structure changes.

Validation:
- Grep reported no hits for old/forbidden terms:
  `bridge`, `control boundary`, `Tello`, `SDK`, `direct command`,
  `flight safety validation`, `safety validation`, `RQ`.
- `git diff --check -- docs/paper_sensys2027` passed.
- LaTeX compile is still pending.

## Writing-Agent Discussion Boundary Receipt

Receipt time: 2026-06-05 02:28 CDT.

Status:
- Writing agent completed Discussion boundary pass.
- Modified file:
  `docs/paper_sensys2027/sections/8conclusion.tex`.
- No Introduction, Evaluation, experiment, model, firmware, or figure changes.

Completed changes:
- Split the old `Discussion and Conclusion` into separate `Discussion` and
  short `Conclusion` sections.
- Discussion now scopes Akouo as an additional safety interaction layer, not a
  replacement for obstacle avoidance, geofencing, failsafe behavior, manual
  override, or flight-controller safeguards.
- Clarified Akouo is not full navigation or a complete speech-to-control system.
- Clarified `movement` does not encode direction, distance, velocity, or flight
  permission.
- Clarified ASR baseline scope: Whisper `tiny.en` + parser on fixed
  rotor-noisy 1s clips, not all ASR systems.
- Clarified direct-mapping and no-unknown results are offline action-pressure
  simulations, not flight tests or flight-safety validation.
- Clarified user study does not cover geometry, direction, angle, or distance.
- Clarified embedded/runtime evidence supports local event generation and
  steady cadence, not semantic safety or full vehicle integration.
- Conclusion now closes on constrained safety-state events as safer speech
  admission into UAV control.

Validation:
- `git diff --check -- docs/paper_sensys2027` passed.
- Local grep reported no hits for:
  `bridge`, `control boundary`, `Tello`, `SDK`, `RQ`, `Question`,
  `Discussion and Conclusion`.
- LaTeX compile is still pending.

## Writing-Agent Abstract/Intro Framing Receipt

Receipt time: 2026-06-05 11:56 CDT.

Status:
- Writing agent completed a scoped wording fix for the paper-facing framing.
- Modified files:
  - `docs/paper_sensys2027/main.tex`
  - `docs/paper_sensys2027/sections/1introduction.tex`
  - `docs/paper_sensys2027/sections/2relatedwork.tex`
  - `docs/paper_sensys2027/sections/4architecture.tex`
  - `docs/paper_sensys2027/sections/5recognizer.tex`
  - `docs/paper_sensys2027/sections/6prototype.tex`
- No experiments, figure assets, model code, or firmware were changed.

Completed changes:
- Abstract now follows the intended argument chain:
  goal -> naive approaches -> failure modes -> insight -> Akouo -> evaluation
  contrast.
- Introduction now names transcript-first ASR, keyword/speech-command
  classifiers, and direct mapping as natural-but-problematic alternatives.
- Contributions now use the paper-facing terms:
  `structured safety-state event`, `event-state contract`, and
  `safety-state boundary`.
- Related Work transition now emphasizes the remaining systems problem:
  how speech enters UAV control as a constrained event-state contract.
- Figure/table captions touched in Architecture, Recognizer, and Prototype were
  aligned to the safety-state boundary framing.

Remaining consistency tasks:
- `3motivation.tex` still has `control boundary` / `bridge` wording that should
  be replaced or justified.
- `5recognizer.tex` still has `control boundary` / `bridge` wording in body
  text.
- `6prototype.tex` still has multiple `bridge/control-boundary` body terms; it
  needs a Prototype consistency pass unless `bridge` is deliberately defined as
  the implementation component.
- `1introduction.tex` has one `bridge` in a LaTeX comment only; it does not
  compile into the PDF but can be cleaned before final submission.

Validation:
- `git diff --check -- docs/paper_sensys2027` passed.
- `RQ|Question|Q&A` check reported no hits.
- LaTeX compile is still pending.

## Writing-Agent Terminology Consistency Receipt

Receipt time: 2026-06-05 12:05 CDT.

Status:
- Writing agent completed the scoped terminology consistency pass.
- Modified files:
  - `docs/paper_sensys2027/sections/3motivation.tex`
  - `docs/paper_sensys2027/sections/5recognizer.tex`
  - `docs/paper_sensys2027/sections/6prototype.tex`
  - `docs/paper_sensys2027/figures/safety_state_flow.tex`
- No experiments, figure assets, model code, firmware, or evaluation numbers
  were changed.

Completed changes:
- Replaced remaining `control boundary`, `control-boundary`, and
  `safety boundary` wording with `safety-state boundary`.
- Tightened `intent event` wording to `structured safety-state event` or
  `event-state contract` where appropriate.
- Retained one `bridge` in Prototype, but explicitly defined it as a
  lightweight implementation component that implements the safety-state
  boundary, not as a separate paper concept.
- Updated `safety_state_flow.tex` caption to describe an event-state contract
  and structured updates to the safety-state boundary.

Validation:
- `git diff --check -- docs/paper_sensys2027` passed.
- Scoped `RQ|Question|Q&A` check reported no hits.
- Scoped `control boundary|control-boundary|safety boundary` check reported no
  hits.
- Scoped `bridge` check reported only the intentionally defined Prototype
  implementation component.
- LaTeX compile is still pending.

## Paper Rewrite TODO

Goal:
- Convert the draft from a module-building story into a systems-paper argument:
  naive approaches fail -> Akouo insight -> system realization -> evaluation
  proves the contrast.

Global rewrite rules:
- Do not frame the paper as “we wanted voice interaction, so we built model,
  deployment, and control modules.”
- Do frame it as “transcript-first, keyword-trigger, and direct-command designs
  are natural but problematic; Akouo instead admits speech into UAV control as
  constrained safety-state events.”
- Do not rewrite Evaluation or other sections into Q&A/RQ-style subsections.
  Preserve a traditional systems-paper subsection structure and adjust by
  adding/removing subsections and rewriting internal narrative.
- Do not overclaim ASR/STT failure until ASR+parser numeric results exist.
- Keep `XXX` placeholders where final ASR/user/evaluation results are pending.
- Existing TC-ResNet, BC-ResNet, and DS-CNN rows must be called compact
  speech-command classifier baselines, not full safety-system baselines.

Section-level tasks:

- [x] Abstract:
  - Add explicit contrast against transcript-first ASR/STT and direct-trigger
    speech-command designs.
  - State the Akouo insight in one sentence: speech becomes mediated
    safety-relevant intent events, not transcripts or commands.
  - Add only final frozen numbers; keep placeholders until ASR/user results are
    available.
  - 2026-06-05 scoped pass completed in `main.tex`; final numeric polish and
    compile check remain pending.

- [x] Introduction:
  - Temporarily pause additional edits until Motivation, Architecture, and
    Evaluation narrative are stable.
  - Reorder around X -> naive Y -> failures -> insight W -> Akouo A.
  - Compress broad UAV policy/adoption background.
  - Name the three naive approaches early:
    ASR/STT + parser, KWS/speech-command classifier, direct speech-to-command.
  - Explain why each is problematic under rotor noise and safety-boundary needs.
  - Rewrite contribution bullets to match:
    safety-state voice abstraction, constrained intent-event contract,
    onboard rotor-noisy event recognizer, and naive-approach/system evaluation.
  - Ensure Figure 1 supports the opening scenario and does not become the full
    architecture figure.
  - 2026-06-05 scoped pass completed in `1introduction.tex`; later final polish
    can still adjust prose rhythm, but the framing target is now represented.

- [x] Related Work:
  - Reorganize around the approaches Akouo contrasts with:
    ASR/STT speech interfaces, KWS/speech-command classifiers, embedded
    speech/TinyML, and UAV safety mechanisms.
  - Add/polish a related-work comparison table if space allows.
  - Each subsection should close with why the prior family does not provide
    rotor-noisy, onboard, safety-state-mediated voice events.
  - 2026-06-05 scoped transition pass completed in `2relatedwork.tex`; the
    related-work comparison table was simplified on 2026-06-06. Final page-fit
    and prose rhythm can still be reviewed after compile.

- [x] Motivation:
  - Treat this as the next active rewrite target before Introduction.
  - Convert into a concrete failure-analysis section.
  - Include examples for:
    transcript ambiguity under rotor noise, keyword false trigger or missed
    emergency, direct classifier forcing unknown audio into commands, and
    embedded ASR deployability mismatch.
  - Do not present these as proven empirical failures until corresponding
    results exist; use them as design hazards, then let Evaluation quantify.
  - Use the new ASR/direct-mapping/no-unknown evidence as background support,
    but do not turn Motivation into an Evaluation results preview.

- [x] Architecture:
  - Strengthen why the event abstraction avoids naive failures.
  - Make the event contract central:
    `emergency -> safety-critical event`,
    `movement -> pending interaction requiring downstream policy`,
    `unknown -> fallback/no action`.
  - Explain logging/auditability and safety-state boundary as design mechanisms.
  - Make clear speech is never directly bound to UAV motion.

- [x] Recognizer:
  - Open with “the recognizer exists to produce the event contract.”
  - Reduce model-report language unless it supports rotor-noisy event generation
    or embedded deployment constraints.
  - Connect compact speech-command baselines to this section, not to safety
    mechanism comparison.
  - 2026-06-05 terminology pass completed.
  - 2026-06-06 scoped recognizer naming pass completed: paper-facing
    `CBranchformer` removed; section and figure now use compact
    Branchformer-style temporal encoder wording.

- [ ] Prototype:
  - Present the prototype as realizing onboard event generation plus
    safety-state mediation.
  - Avoid debug/transport language and internal run names.
  - Keep the safety-state boundary as a core mechanism, not implementation
    convenience.
  - 2026-06-05 terminology pass completed; one `bridge` remains intentionally
    defined as an implementation component of the safety-state boundary.

- [x] Evaluation:
  - Add or revise conventional subsections for naive-approach comparison;
    do not use “Why not X?” headings or RQ-style structure.
  - Add ASR/STT + rule-parser baseline results when local run completes.
  - Rename current baseline table/section as compact speech-command classifier
    baselines.
  - Add no-unknown fallback and no-bridge/direct-action ablation if results can
    be produced quickly.
  - Use safety-facing metrics:
    emergency recall, unknown false action/event rate, parse failure rate,
    runtime/deployability, and mediated control behavior.
  - Make every metric traceable to a real input set, noise condition, and
    deployment path.

Suggested Evaluation subsection shape:
- Recognition Quality Under Rotor Noise.
- Transcript-First ASR Baseline.
- Compact Speech-Command Classifier Baselines.
- Safety-State Boundary Ablations.
- Embedded Runtime and Event Reporting.
- Participant-Level Evaluation.
- Discussion of Deployment Boundaries.

- [x] Discussion:
  - Separate Discussion from Conclusion.
  - Discuss what Akouo is and is not:
    an additional safety interaction layer, not a replacement for existing UAV
    safety systems; not full navigation; not generic ASR.
  - Include limitations: ASR baseline scope, user-study scope, no geometry in
    current study, real-flight boundary, IRB status if needed.
  - Use this section to absorb weak/incomplete studies instead of overclaiming.

- [x] Conclusion:
  - Keep short.
  - Close on the insight: safer admission of speech into UAV control through
    constrained safety-state events.

- [ ] Final paper hygiene:
  - Remove all visible TODOs and unresolved `XXX` unless explicitly accepted.
  - Run forbidden-term check.
  - Run no-geometry user-study check.
  - Run LaTeX compile, page-count check, figure/table orphan check, and
    anonymity check.

## Motivation-First Rewrite Decision

Decision time: 2026-06-05 01:51 CDT.

- Temporarily pause additional Introduction edits.
- Start the next concrete rewrite pass from Motivation.
- Motivation should become the failure-analysis section that naturally explains
  why Akouo uses constrained safety-state events.
- The section should use ASR/direct-mapping/no-unknown evidence as design
  support, but should not read like an Evaluation subsection.

Motivation should cover:
- Transcript-first ASR/STT + parser:
  limited intent coverage under fixed rotor-noisy 1s clips; do not generalize to
  all ASR.
- KWS / compact speech-command classifier:
  useful as recognizers, but ordinary classifier outputs do not define
  safety-state mediation by themselves.
- Direct action mapping:
  recognizer outputs can create action pressure without a boundary.
- No-unknown fallback:
  unknown/fallback is a safety containment mechanism, not merely a third label.
- Embedded/deployment constraints:
  the system needs local event generation and explicit boundary checks.

Writing order:
1. Motivation.
2. Architecture consistency pass.
3. Evaluation tone check.
4. Discussion boundary.
5. Introduction only after the above are stable.

## Figure/Table Revision TODO

Global figure/table rules:
- Figures must support the new argument chain, not merely decorate sections.
- Prefer external editable assets plus PDF/PNG exports; LaTeX should only wrap
  figures with `includegraphics`, captions, and labels.
- Avoid over-compressing important figures into one column; use `figure*` when
  the figure carries a main claim.
- No internal terms: USB CDC, serial, weeklyresult, run name, xiao, RT1S, C32.
- No user-study geometry terms: geometry, direction, angle, distance,
  speaker-position, direction-level accuracy.

Figure tasks:

- [x] Figure 1 / opening scenario:
  - Purpose: motivate talk-to-the-drone under rotor noise.
  - Show person speech, rotor-noisy UAV, onboard Akouo event generation, and
    conservative boundary before response.
  - Reduce decorative controller/map/background content.
  - Do not show full architecture or too many pipeline blocks.
  - Caption should say this is a hands-free interaction scenario, not a proven
    safety outcome.
  - 2026-06-05 user completed Figure 1 polish; no further action unless final
    compile/page-fit shows a problem.

- [x] System architecture:
  - Use `figure*` if possible.
  - Separate physical context, onboard event recognizer, safety-state bridge,
    and gated UAV response.
  - Make naive direct speech-to-command path visibly absent or blocked.
  - Avoid duplicating Figure 1; this figure should explain mechanism, not scene.
  - 2026-06-05 audit decision: keep as `figure*`, keep asset unchanged, keep
    `width=\textwidth`; single-column would over-compress the wide asset.
  - 2026-06-05 caption patch completed: caption now foregrounds rotor-noisy
    speech, structured safety-state event, UAV policy, and separation between
    recognition and vehicle-facing action.
  - Completed minimal patch: update caption to foreground rotor-noisy speech,
    structured safety-state event, UAV policy, and separation between
    recognition and vehicle-facing action.

- [x] Safety-state flow:
  - Decide whether to keep as a standalone figure or merge into system
    architecture.
  - If kept, show only emergency/movement/unknown -> boundary handling.
  - Movement must remain pending / policy-required, not direct navigation.
  - 2026-06-05 audit decision: keep as `table*`, do not merge into
    `fig:system_architecture`, do not resize to one column; table defines event
    semantics while the architecture figure shows pipeline separation.
  - 2026-06-05 minimal patch completed: caption now says each recognizer output
    is a structured safety-state update with boundary handling semantics, not a
    direct flight command.
  - Completed minimal patch: caption should say each recognizer output is a
    structured safety-state update with boundary handling semantics, not a
    direct flight command. Header `Boundary action` may become
    `Safety-state boundary handling`.

- [ ] Recognizer architecture:
  - Single-column is acceptable only if readable.
  - Show offline reference path and embedded path sharing the same intent-event
    contract.
  - Do not include run names or internal profile labels.

- [ ] Prototype pipeline:
  - Decide whether it is still necessary after system architecture.
  - If kept, show paper-facing pipeline only:
    onboard capture -> frontend -> integer inference -> event reporting ->
    safety-state bridge.
  - Avoid debug transport details.

- [ ] Response-time breakdown:
  - Use `figure*` if it carries the real-time claim.
  - Separate first-event latency from steady-state cadence.
  - Mark safety-state boundary / vehicle-facing timing values as final numbers
    or placeholders consistently.
  - Do not imply first-window subsecond latency if only steady-state 1s
    throughput is validated.

- [ ] User-study evidence:
  - Use `figure*`.
  - Replace any user-geometry protocol table.
  - Show participant/session pipeline, prompt matrix, result summary, and
    optional log/demo strip.
  - No direction, angle, distance, or speaker-position content.

- [ ] Clean/noisy signal visualization:
  - Keep only if it clearly helps explain rotor-noise difficulty.
  - If kept, make it visually clean and large enough to read.
  - Drop if it competes with higher-priority figures.

Table tasks:

- [ ] Related-work comparison table:
  - Add or revise a compact table comparing ASR/STT interfaces,
    KWS/speech-command classifiers, embedded speech/TinyML, UAV safety
    mechanisms, and Akouo.
  - Suggested columns:
    rotor-noise focus, MCU/onboard feasibility, constrained intent events,
    safety-state boundary, deployment/evaluation link.
  - 2026-06-05 audit result: current `2relatedwork.tex` has no comparison
    table. Add a qualitative comparison table only, without invented numbers.
  - Recommended rows: `ASR/STT + parser`, `KWS/speech-command classifiers`,
    `embedded speech/TinyML`, `UAV safety mechanisms`, `Akouo`.
  - Recommended columns: `Approach family`, `Rotor-noisy UAV setting`,
    `Onboard/MCU feasibility`, `Constrained event output`,
    `Safety-state boundary / paper role`.
  - If page budget is tight, let this table absorb or replace
    `tab:safety_components` rather than adding another overlapping Motivation
    table.

- [ ] Baseline comparison table:
  - Rename TC-ResNet, BC-ResNet, DS-CNN rows as compact speech-command
    classifier baselines.
  - Add ASR+parser row only after numeric local results exist.
  - Avoid implying KWS baselines are complete safety mechanisms.

- [ ] Safety/evaluation metrics table:
  - Consider a table that maps each evaluation to the claim it supports:
    recognition quality, transcript-first comparison, event containment,
    runtime/deployability, and user-study evidence.

- [ ] Table 3 decision:
  - Audit current Table 3 after the rewrite.
  - Decide: keep and rename, resize, merge into another table, or delete.
  - Table 3 must justify page space by supporting a core claim.

- [ ] User-study protocol table:
  - Prefer replacing with `fig:user_study_evidence`.
  - If kept, rename away from geometry and include only participant, intent,
    keyword, repeat, embedded/reference prediction, and logs.

- [ ] Rotor robustness / shielding tables:
  - Keep only if final values are available and support a main claim.
  - Otherwise move to Discussion or remove.

## Figure/Table Polish Plan

Planning time: 2026-06-05 12:19 CDT.

Decision:
- Figure 1 is done by the user.
- Remaining work should polish the figures/tables that carry paper claims.
- Demo video work remains deferred; focus on paper figures/tables and baseline
  presentation.

Meeting-driven requirements:
- Rename unclear figures/tables so the caption says the claim, not the internal
  artifact name.
- Resize important figures; use `figure*` or `table*` when single-column
  layout makes the claim unreadable.
- Add a Related Work comparison table.
- Improve reference clarity and make each visual align with the new framing.
- Separate Discussion/Conclusion is already handled; the figure/table pass
  should now reinforce that story rather than add new claims.

### Priority 0: claim-bearing visuals/tables

- [x] `fig:system_architecture`
  - Role: main mechanism figure, not a scenario illustration.
  - Required message: speech becomes a structured safety-state event before the
    safety-state boundary considers any gated vehicle-facing response.
  - Layout: keep/convert to `figure*`; make boundary visually dominant.
  - Must show: onboard event recognizer, event-state contract, safety-state
    boundary, existing UAV safety mechanisms/policy inputs, gated response.
  - Must avoid: direct speech-to-command path as a valid route; decorative map
    clutter; internal transport/debug labels.
  - Audit result: keep; asset does not need modification; caption-only polish
    recommended.
  - Caption patch completed with:
    `\sys{} system architecture. Rotor-noisy nearby speech is converted into a
    structured safety-state event and admitted to UAV policy only through the
    safety-state boundary, separating recognition from vehicle-facing action.`

- [x] `tab:intent_state_contract` / safety-state flow
  - Role: explain the event-state contract.
  - Decision needed: keep as a table, convert to a clean visual flow, or merge
    into `fig:system_architecture`.
  - If kept, caption should foreground the claim:
    emergency/movement/unknown are structured updates to the safety-state
    boundary, not commands.
  - Movement must remain pending/policy-required.
  - Audit result: keep as `table*`, keep separate from architecture, do not
    resize to one column.
  - Patch completed: caption-only polish plus header change from
    `Boundary action` to `Safety-state boundary handling`.

- [ ] Related Work comparison table
  - Role: answer the reviewer question "why not ASR/KWS/other UAV safety?"
    before Evaluation.
  - Suggested columns: Approach family, rotor-noise setting, onboard MCU
    feasibility, constrained event output, safety-state boundary, paper role.
  - Suggested rows: ASR/STT + parser, KWS/speech-command classifiers,
    embedded speech/TinyML, UAV safety mechanisms, Akouo.
  - Keep wording careful: prior work is not "wrong"; it leaves a different
    systems gap.
  - Audit result: current Related Work has no comparison table; implement a
    qualitative table with the recommended rows/columns and no experimental
    numbers.
  - Page-budget rule: prefer replacing/absorbing `tab:safety_components` over
    adding a redundant table.

### Priority 1: evaluation visuals/tables

- [ ] `fig:response_time_breakdown`
  - Role: support real-time event-source claim.
  - Layout: consider `figure*` if the current one-column figure is compressed.
  - Must separate first-event latency from steady-state event cadence.
  - Must not imply first-window subsecond latency.
  - Highlight measured pieces: capture window, frontend, integer inference,
    steady event period, first event latency.

- [ ] `tab:baseline_comparison` and `tab:asr_baseline`
  - Role: compare natural speech-interface alternatives.
  - Decision needed: keep as separate tables or combine into one baseline table.
  - If combined, separate rows by family:
    transcript-first ASR baseline vs compact speech-command classifier baselines.
  - Caption must make scope clear: fixed rotor-noisy one-second clips and
    offline/parser comparison, not universal ASR failure.

- [ ] `tab:safety_ablation`
  - Role: quantify why the safety-state boundary and unknown fallback matter.
  - Keep as a small, high-impact table if space allows.
  - Caption must retain boundary: offline action-pressure simulation, not
    vehicle actuation or flight safety validation.

- [ ] `tab:user_study_participant_variability`
  - Role: show participant variability and user-study evidence.
  - Meeting/use-case: occupy meaningful paper space with real participant data
    rather than a protocol-only table.
  - Consider converting to a figure or mixed figure/table:
    participant-level bars for emergency recall and unknown false event rate,
    with trial counts visible.
  - No geometry, direction, angle, distance, or speaker-position content.

### Priority 2: optional / drop candidates

- [ ] `fig:recognizer_architecture`
  - Role: show offline reference and embedded recognizer share the same event
    contract.
  - Check whether `figure*` is needed for readability.
  - Avoid run/profile/internal labels; make the output contract visually clear.

- [ ] `fig:clean_vs_noisy`
  - Role: motivate rotor-noise difficulty.
  - Keep only if visually legible and clearly useful.
  - If weak or redundant, drop or replace with a cleaner signal visualization.

- [ ] `tab:safety_components`
  - Role: complement existing UAV safety mechanisms.
  - Possible merge with Related Work comparison table.
  - Drop if it repeats prose without adding a claim.

- [ ] `tab:prototype_interfaces`
  - Role: explain prototype evidence path.
  - Drop or compress if `fig:system_architecture` and Prototype prose already
    cover the same pipeline.

- [ ] `fig:emergency_stop_sequence`
  - Role: controlled demonstration visual.
  - Keep only if the figure is clear and does not imply broad flight validation.
  - Demo video link remains deferred.

Validation required after figure/table agent:
- [ ] `git diff --check -- docs/paper_sensys2027`.
- [ ] Forbidden internal-term check.
- [ ] No-geometry user-study check.
- [ ] LaTeX compile and page-count check.
- [ ] Orphan figure/table/reference check.

## Figure/Table Receipt - System Architecture Caption and Event-State Contract Audit

Receipt time: 2026-06-05 12:40 CDT.

Status:
- Figure/table agent applied the caption-only patch for
  `fig:system_architecture`.
- `figure*` and `width=\textwidth` are unchanged.
- Figure/table agent completed a read-only audit for
  `tab:intent_state_contract` / `safety_state_flow`.

Completed:
- `fig:system_architecture` caption now states:
  rotor-noisy speech -> structured safety-state event -> UAV policy through
  safety-state boundary -> separation between recognition and vehicle-facing
  action.
- Validation reported: `git diff --check -- docs/paper_sensys2027` passed.

Event-state contract audit:
- Decision: keep as `table*`.
- Do not merge into `fig:system_architecture`; the figure shows pipeline
  separation, while the table defines event semantics.
- Do not resize to one column because the three columns need full width.
- Intended message: Emergency, Movement, Unknown, and Low confidence are
  structured safety-state updates with distinct boundary handling, not commands.
- Claim supported: Akouo's novelty is the event-state contract; speech becomes
  constrained safety-state events and the safety-state boundary determines how
  each event may affect UAV behavior.

Recommended next patch:
- Caption:
  `Event-state contract exposed by \sys{}. Each recognizer output is treated as
  a structured safety-state update with boundary handling semantics, not as a
  direct flight command.`
- Optional header:
  `Boundary action` -> `Safety-state boundary handling`.

Risk:
- Low overclaim risk. Rows are conservative because they use policy, pending,
  fallback/no action, and threshold handling language.

## Figure/Table Receipt - Event-State Contract Patch and Related Work Table Audit

Receipt time: 2026-06-05 12:45 CDT.

Status:
- Figure/table agent completed the minimal patch for
  `docs/paper_sensys2027/figures/safety_state_flow.tex`.
- Figure/table agent completed a read-only audit for the Related Work
  comparison table.

Completed event-state contract patch:
- Caption replaced with:
  `Event-state contract exposed by \sys{}. Each recognizer output is treated as
  a structured safety-state update with boundary handling semantics, not as a
  direct flight command.`
- Header changed:
  `Boundary action` -> `Safety-state boundary handling`.
- Kept `table*`.
- Did not merge with `fig:system_architecture`.
- Did not resize to one column.
- Validation reported: `git diff --check -- docs/paper_sensys2027` passed.

Related Work comparison table audit:
- Current `docs/paper_sensys2027/sections/2relatedwork.tex` has no comparison
  table.
- Recommended table type: qualitative comparison table, no experimental
  numbers.
- Recommended rows:
  - `ASR/STT + parser`
  - `KWS/speech-command classifiers`
  - `embedded speech/TinyML`
  - `UAV safety mechanisms`
  - `Akouo`
- Recommended columns:
  - `Approach family`
  - `Rotor-noisy UAV setting`
  - `Onboard/MCU feasibility`
  - `Constrained event output`
  - `Safety-state boundary / paper role`
- Page-budget recommendation: if space is tight, this table should absorb or
  replace `tab:safety_components` rather than adding another overlapping
  Motivation table.

Next:
- Implement Related Work comparison table or ask the figure/table agent for a
  proposed exact LaTeX table first.

## Current Repo Audit Refresh - 2026-06-06 00:13 CDT

- Branch: `main`
- HEAD: `055d62d1e0dcc2a214af969aa270577dd7a9da4c`
- Worktree status: dirty paper/figure draft.
- Dirty scope includes `docs/paper_sensys2027/main.tex`,
  `references.bib`, sections `1-8`, recognizer figure asset, figure source
  directory, and `archive/figure2.aup3`.
- Latest result directory: `weeklyresult/weekly_drone_2026w23`.

## Advisor Late Feedback - 2026-06-05 23:42 CDT

Status:
- Advisor reviewed the latest draft shortly before final submission.
- Main concern: current paper may still look under-novel because the technical
  design can read like a generic speech interface, standard model design, and
  noise augmentation pipeline.
- Submission is still worth pursuing, but the paper needs a more explicit
  novelty and technical-contribution pass.

Advisor feedback summary:
- Introduction needs a clearer answer to why this is new compared with existing
  UAV speech interfaces.
- The strongest differentiator should be real drone-side deployment under rotor
  noise, plus the safety-state framing.
- Branchformer-like recognizer must be explained better without introducing an
  unpublished model name as the paper-facing contribution.
- If possible, use existing or fast ablation evidence to show why the selected
  recognizer and training path are useful.
- Noise augmentation alone is not novel; do not frame it as the primary
  contribution.
- Style needs another human-polish pass to remove AI-generated phrasing.
- Remove or revise figures that do not add clear value.
- Final authorship order needs to be finalized: advisor last, VP second-to-last.
- Keep advisor updated until submission.

Manager interpretation:
- Do not start a new large training campaign before submission.
- Treat this as a paper rescue pass:
  1. tighten Introduction novelty against UAV speech-interface prior work;
  2. revise Recognizer to explain the Branchformer-like recognizer and
     clean/noisy embedding alignment as deployment-oriented design choices for
     rotor-noisy event generation;
  3. reuse existing compact baselines as the model-family comparison evidence
     where possible;
  4. only request additional ablation if it can be run from existing artifacts or
     a very short local harness;
  5. cut figures/tables that do not support novelty, model design, deployment,
     or evaluation contrast.

Immediate checklist:
- [x] Introduction: add a sharper paragraph on why prior UAV speech interfaces
      do not solve real-time rotor-noisy onboard safety-state interaction.
- [x] Introduction: make novelty read as `real drone deployment under rotor
      noise + constrained safety-state event mediation`, not just voice command
      classification.
- [ ] Related Work: ensure the qualitative comparison table explicitly separates
      prior UAV speech interfaces, generic ASR/STT, compact KWS/classifiers,
      embedded TinyML speech, UAV safety mechanisms, and Akouo.
- [x] Recognizer: replace paper-facing `CBranchformer` naming with
      `Branchformer-like` or `compact Branchformer-style temporal encoder`.
- [x] Recognizer: add a concise technical explanation of why this
      Branchformer-like structure is used: local rotor-noise/speech cues, global
      one-second window context, and embedded-friendly depthwise temporal path.
- [x] Recognizer: explain clean-view/noisy-view same-architecture training as a
      robustness method, but do not claim it is independently novel.
- [ ] Evaluation: verify that TC-ResNet, BC-ResNet, and DS-CNN rows can be read
      as model-family comparison evidence for the Branchformer-like recognizer.
- [ ] Evaluation: decide whether any additional lightweight ablation is feasible
      before submission. Default is no new large run.
- [ ] Style: run a pass from Motivation onward for direct, human systems-paper
      prose; remove generic AI-like phrasing.
- [ ] Figures/tables: delete, shrink, or demote any visual that does not support
      novelty, model design, deployment, or evaluation contrast.
- [ ] Authorship: finalize metadata order outside the anonymous paper; advisor
      last, VP second-to-last.
- [ ] Venue fallback: after submission, discuss alternative venues if rejected;
      do not spend submission-time energy on venue planning now.

Risk:
- If the recognizer section still reads as generic Branchformer plus noise
  augmentation, reviewers may see insufficient technical novelty.
- If Branchformer-like design advantages are asserted without comparison, use
  conservative wording and point to compact baseline comparison rather than
  claiming a full architectural ablation.
- If the introduction over-focuses on safety framing without model/deployment
  specificity, the paper may still look like a broad idea rather than a concrete
  systems contribution.

## Writing Agent Receipt - Recognizer Naming Pass - 2026-06-06 00:33 CDT

Status:
- Writing agent completed the scoped recognizer naming pass.
- No experiments, model code, firmware, or evaluation numbers were changed.

Changed files:
- `docs/paper_sensys2027/sections/5recognizer.tex`
- `docs/paper_sensys2027/figures/source/recognizer_architecture.dot`
- `docs/paper_sensys2027/figures/recognizer_architecture.pdf`

Completed:
- Removed paper-facing `CBranchformer`.
- Replaced visible paper wording with `compact Branchformer-style temporal
  encoder` / `Branchformer-style encoder`.
- Revised Section 5.2 to explain the design by purpose:
  local speech/rotor-noise cues, global one-second window context,
  embedded-friendly depthwise temporal path, and clean/noisy same-architecture
  embedding alignment.
- Avoided unsupported claims that the architecture is superior to all baselines.

Verification:
- `rg -n "CBranchformer" docs/paper_sensys2027`: no matches.
- `pdftotext docs/paper_sensys2027/figures/recognizer_architecture.pdf - |
  rg -n "CBranchformer"`: no matches.
- `git diff --check -- docs/paper_sensys2027`: passed.

Remaining:
- Figure/table agent is not required for this naming fix.
- Future visual polish can still adjust layout/readability of the recognizer
  figure if page fit demands it.
- Evaluation still needs a conservative statement that compact baselines are
  model-family comparisons, not proof of full architectural superiority.

## Writing Agent Receipt - Introduction Novelty Pass - 2026-06-06 00:48 CDT

Status:
- Writing agent completed the minimal Introduction novelty pass.
- No experiments, model code, firmware, figures, or evaluation numbers were
  changed.
- `main.tex` was checked and left unchanged in this pass.

Changed files:
- `docs/paper_sensys2027/sections/1introduction.tex`

Completed:
- Added a sharper systems-gap sentence after prior UAV speech-interface
  discussion: the gap is not only whether speech can be recognized near a drone,
  but whether short rotor-noisy speech can be converted locally, while the UAV
  is operating, into a constrained safety-state update before any vehicle-facing
  response is considered.
- Replaced the vague `some shortcomings` wording with a clearer systems-paper
  contrast:
  transcript-first parsing is brittle on short rotor-noisy clips;
  KWS/command classifiers provide labels without mediation semantics;
  direct mapping can turn recognition errors into vehicle-facing actions.
- Preserved the current Akouo definition, contribution list, advisor comment
  blocks, and overall Introduction structure.

Verification:
- `git diff --check -- docs/paper_sensys2027`: passed.

Remaining:
- The phrase `while the UAV is operating` should be watched during final
  proofread because it could be read as implying live safety validation.
  Current sentence is bounded by `before any vehicle-facing response is
  considered`, so it does not make a completed safety-validation claim.
- Related Work comparison-table polish is complete; final page-fit/prose check
  remains.
- Evaluation wording still needs to ensure compact baselines are model-family
  comparisons, not proof of full architectural superiority.

## Writing Agent Receipt - Related Work Table Polish - 2026-06-06 00:56 CDT

Status:
- Writing/figure-table pass simplified Table 1 in Related Work.
- No experiments, model code, firmware, figures outside the table, or evaluation
  numbers were changed.

Changed files:
- `docs/paper_sensys2027/sections/2relatedwork.tex`

Completed:
- Simplified `tab:related_work_comparison` from a wider qualitative table to
  three columns.
- Table now compares two core setting constraints:
  `Rotor-noisy UAV speech` and `Onboard real-time inference`.
- Rows remain qualitative:
  UAV speech interfaces, ASR/STT + parser, KWS/speech-command classifiers,
  embedded speech/TinyML, UAV safety mechanisms, and Akouo.
- Caption changed to:
  `How related work addresses the two core constraints in our setting.`
- Kept `table*` because the qualitative rows are still too compressed for a
  single-column ACM layout.

Verification:
- `git diff --check -- docs/paper_sensys2027`: passed.

Remaining:
- Final page-fit check is still needed after LaTeX compile.
- Table no longer explicitly has a `safety-state boundary` column; surrounding
  prose must continue to state that this is the remaining systems gap.

## Writing/Evaluation Agent Receipt - Evaluation Model-Family Wording Audit - 2026-06-06 01:06 CDT

Status:
- Writing/evaluation agent completed the scoped Evaluation/model-family wording
  audit.
- No experiments, model code, firmware, figure assets, training, or server
  tasks were changed.

Changed files:
- `docs/paper_sensys2027/sections/7evaluation.tex`

Completed:
- Reframed the second evaluation as a recognizer/interface-level comparison:
  Akouo-Ref is compared with common speech-interface alternatives, not with
  complete safety systems.
- Renamed TC-ResNet, BC-ResNet, and DS-CNN rows as compact
  speech-command `model-family` baselines.
- Updated the baseline table caption to clarify:
  the ASR row is a transcript-first parser baseline, while compact rows are
  recognizer alternatives under the same three-intent rotor-noisy task.
- Changed table row names from `baseline` to `family` for TC-ResNet8,
  BC-ResNet1, and DS-CNN-S.
- Changed Akouo-Ref comparison wording to `At this fixed comparison point`
  so the paper does not imply unconditional Branchformer-style superiority.

Decision:
- No additional lightweight ablation is required for this wording pass.
- Current evaluation already has:
  transcript-first ASR + parser;
  compact speech-command model-family comparison;
  direct mapping / no-unknown action-pressure simulation.
- A threshold operating curve would strengthen the safety story, but it is not
  required before rewriting the contribution paragraph.

Verification:
- `git diff --check -- docs/paper_sensys2027`: passed.

Remaining:
- Rewrite the contribution list completely so it matches Stephen's requested
  framing:
  common/naive approaches fail under the target constraints;
  the paper insight is safety-state mediation;
  Akouo realizes that insight with constrained events, onboard recognition, and
  layered evaluation.
- Do not write the contribution list as a module checklist.
- Do not claim TC-ResNet/BC-ResNet/DS-CNN prove Branchformer-style encoder
  superiority.

## Writing Agent Receipt - Contribution Rewrite - 2026-06-06 01:34 CDT

Status:
- Writing agent completed the contribution rewrite pass.
- No experiments, model code, firmware, figure assets, training, or server
  tasks were changed.

Changed files:
- `docs/paper_sensys2027/sections/1introduction.tex`

Completed:
- Rewrote the contribution block from a module checklist into a systems
  abstraction story.
- Contribution 1 is now `A speech-admission abstraction for UAV safety
  interaction`, identifying the missing layer between speech recognition and UAV
  action.
- Contribution 2 is now `A constrained intent-state interface for noisy human
  input`, where emergency, movement, and unknown define safe-admission semantics
  rather than command execution.
- Contribution 3 is now `An onboard rotor-noisy recognizer for that interface`,
  tying the recognizer to one-second rotor-noisy speech, local feature
  extraction, embedded-compatible inference, clean/noisy alignment, and compact
  Branchformer-style temporal encoding.
- Contribution 4 is now `Evidence organized around the failure modes of naive
  designs`, aligning evaluation with ASR+parser, compact model-family baselines,
  direct mapping/no-unknown action-pressure simulations, embedded timing, and
  participant-level onboard recognition.

Manager read:
- This version matches Stephen's requested structure better than the previous
  contribution list: the novelty is now phrased as speech admission into a
  safety-state boundary, not as recognizer + ESP32 + evaluation modules.
- It is acceptable to continue from this version.

Verification:
- `git diff --check -- docs/paper_sensys2027`: passed by writing agent.
- Forbidden-term check reported only one acceptable hit:
  `all ASR` appears in Evaluation as a boundary sentence saying the result does
  not prove all ASR systems fail.

Remaining:
- Run a final style pass over Introduction after the rest of the manuscript is
  stable, especially to remove leftover advisor comment blocks and reduce
  AI-like phrasing.
- Keep Contribution 3 conservative: do not let the Branchformer-style encoder
  sentence become an unsupported architecture-superiority claim.
- Continue figure/table pruning and compile/page-count checks.

## Urgent Advisor Fixes - Table 1 Citations and Human Subjects Statement - 2026-06-06 02:06 CDT

Status:
- Completed two urgent paper fixes requested by advisor.
- No experiments, model code, firmware, figure assets, training, or server
  tasks were changed.

Changed files:
- `docs/paper_sensys2027/sections/2relatedwork.tex`
- `docs/paper_sensys2027/sections/7evaluation.tex`

Completed:
- Table 1 now includes citations for each of the first five approach-family
  rows:
  UAV speech interfaces;
  ASR/STT + parser;
  KWS / speech-command classifiers;
  embedded speech / TinyML;
  UAV safety mechanisms.
- The participant-level live recognition subsection now includes an anonymized
  human-subjects statement:
  the participant protocol was approved by the authors' institutional review
  board, with identifying approval details omitted for double-blind review.
- The statement does not reveal institution names, investigator names, or IRB
  identifiers.

Verification:
- `git diff --check -- docs/paper_sensys2027`: passed.
- All newly referenced citation keys exist in `references.bib`.
- Anonymity grep for institution names in the new IRB sentence found no
  exposed names.

Remaining:
- Final compile must confirm Table 1 still fits after citation insertion.
- Final ethics statement should be checked against submission instructions; if
  HotCRP or camera-ready requires exact IRB details later, add them only after
  anonymity constraints no longer apply.

## No-Submit Freeze - 2026-06-06 22:21 CDT

Status:
- User and advisor decided to drop the current submission round for now.
- Current paper/evaluation/deployment results are frozen until the next meeting.
- No new writing, evaluation, deployment, server training, figure polishing, or
  agent dispatch should be started before the next meeting unless the user
  explicitly reopens the work.

Current local audit:
- Branch: `main`
- HEAD: `d3033872657f3b3eb1a4adcd04b64ed5ee486a67`
- Latest weekly result directory: `weeklyresult/weekly_drone_2026w23`
- Dirty paper files remain in `docs/paper_sensys2027/`.
- `docs/.DS_Store` is dirty noise.
- `docs/paper_sensys2027/figures/source/recognizer_architecture.dot` is shown
  as deleted in the current worktree and should be reviewed before any future
  snapshot commit.

Frozen assets to preserve:
- Current Akouo draft after contribution/framing rewrite.
- Related Work Table 1 citation patch.
- Anonymized human-subjects/IRB statement.
- ASR + parser baseline result.
- Compact speech-command model-family baseline results.
- Direct mapping / no-unknown action-pressure ablations.
- Participant-level live recognition table.
- ESP32 runtime and event-reporting evidence.
- Current figure/table assets and editable source folder state.

Restart conditions after next meeting:
- Confirm new target venue / timeline.
- Decide whether to continue from the frozen Akouo draft or branch into a new
  paper direction.
- Review dirty files and decide whether to create a snapshot commit.
- Decide whether to keep, restore, or delete the missing
  `recognizer_architecture.dot` source file.
- Rebuild the next sprint around stronger novelty/evaluation rather than
  submission-deadline polishing.

Do not do before next meeting:
- Do not dispatch new writing/evaluation/deployment agents.
- Do not start new local or server training.
- Do not rewrite paper sections opportunistically.
- Do not delete or restore dirty files without explicit user approval.
