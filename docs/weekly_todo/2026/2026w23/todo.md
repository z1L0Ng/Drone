# Weekly TODO (CDT, Thursday-cycle 2026w23)

Meeting checkpoint: Thursday 2026-06-04.

Planning cycle: Thursday 2026-06-04 -> submission weekend.

Project target: SenSys 2027 first-round submission.

## Current Repo Audit

Audit time: 2026-06-04 16:58 CDT.

- Branch: `main`
- HEAD: `0f3da223f64689cfa5103b6dfdf5cd5f137f313f`
- Worktree status: clean.
- Latest result directory: `weeklyresult/weekly_drone_2026w23`.

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
- [ ] Keep figure work limited to supporting the new framing.

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

- [ ] Related Work:
  - Reorganize around the approaches Akouo contrasts with:
    ASR/STT speech interfaces, KWS/speech-command classifiers, embedded
    speech/TinyML, and UAV safety mechanisms.
  - Add a related-work comparison table if space allows.
  - Each subsection should close with why the prior family does not provide
    rotor-noisy, onboard, safety-state-mediated voice events.
  - 2026-06-05 scoped transition pass completed in `2relatedwork.tex`; the
    related-work comparison table is still open, so this item remains unchecked.

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

- [ ] Recognizer:
  - Open with “the recognizer exists to produce the event contract.”
  - Reduce model-report language unless it supports rotor-noisy event generation
    or embedded deployment constraints.
  - Connect compact speech-command baselines to this section, not to safety
    mechanism comparison.
  - 2026-06-05 terminology pass completed; full prose flow and table/figure
    integration review remains unchecked.

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

- [ ] Figure 1 / opening scenario:
  - Purpose: motivate talk-to-the-drone under rotor noise.
  - Show person speech, rotor-noisy UAV, onboard Akouo event generation, and
    conservative boundary before response.
  - Reduce decorative controller/map/background content.
  - Do not show full architecture or too many pipeline blocks.
  - Caption should say this is a hands-free interaction scenario, not a proven
    safety outcome.

- [ ] System architecture:
  - Use `figure*` if possible.
  - Separate physical context, onboard event recognizer, safety-state bridge,
    and gated UAV response.
  - Make naive direct speech-to-command path visibly absent or blocked.
  - Avoid duplicating Figure 1; this figure should explain mechanism, not scene.

- [ ] Safety-state flow:
  - Decide whether to keep as a standalone figure or merge into system
    architecture.
  - If kept, show only emergency/movement/unknown -> boundary handling.
  - Movement must remain pending / policy-required, not direct navigation.

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
