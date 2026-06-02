# Weekly TODO (CDT, Thursday-cycle 2026w20)

Meeting checkpoint: Thursday 2026-05-28.

Planning cycle: Friday 2026-05-22 -> Thursday morning 2026-05-28.

Project target: SenSys 2027 first-round submission.

## Current Repo Audit

Audit time: 2026-05-28 CDT.

- Branch: `main`
- HEAD: `7485d630e6ffa8a9d7657d1a5b5150389dcfda70`
- Worktree status: dirty, mainly `docs/paper_sensys2027/` writing and figure
  updates plus `.DS_Store` noise.
- Local W20 weekly todo did not exist before this receipt; this file starts the
  repo-side W20 management surface.

## Weekly Goal

This week is the submission-prep week before the SenSys 2027 first-round paper
deadline. The main objective is to turn the Akouo draft from a progress report
into a full-paper shaped systems draft:

1. Freeze story and contribution framing around Akouo as a voice-driven UAV
   safety interaction layer under rotor noise.
2. Expand the paper to an 11-12 page body with natural system-paper prose,
   figures, tables, and `XXX` placeholders for not-yet-finalized metrics.
3. Replace project-management/run-name language with paper-facing language.
4. Complete the minimum evaluation evidence needed before the June 1 result
   freeze: participant-level user study, rotor robustness, bridge response time,
   and repeated control-boundary trials.

## SenSys 2027 Timing

- Abstract registration: Friday 2026-05-29 AoE.
- Paper submission: Friday 2026-06-05 AoE.
- Full paper target: up to 12 pages body, with references/appendix outside the
  body page budget per the current CFP note from the writing agent receipt.
- Double-blind submission; human participants require a generic ethics
  statement.

## Track C / Paper Writing Receipt

Scope:
- SenSys paper writing and structure only.
- No model training, no ESP32 firmware work, no server job.

Main paper framing:
- System name is unified as `Akouo`.
- Title/abstract now frame the paper as voice-driven UAV safety interaction
  under rotor noise.
- The story has shifted away from speech classification / KWS toward:
  human speech -> constrained intent events -> conservative safety-state
  boundary, not direct flight commands.

Completed writing changes:
- Introduction was revised around hands-free natural interaction, additional UAV
  safety layer, and the distinction from ASR/KWS/direct flight control.
- Section order is now:
  `Introduction -> Related Work -> Motivation -> Architecture -> Recognizer -> Prototype -> Evaluation -> Conclusion`.
- Related Work was moved immediately after Introduction.
- Sections 4-8 were rewritten from technical-report style into a system-paper
  narrative.
- Architecture now emphasizes intent events, safety meanings for
  emergency/movement/unknown, and the control boundary.
- Prototype keeps the proposed paper-facing pipeline at the system level and no
  longer exposes internal implementation/run labels.
- Prototype subsection title was changed from `Host Bridge` to
  `Safety-State Bridge`.
- Recognizer section is organized around the system target rather than as an
  isolated model paper.
- Internal run names do not appear in the body.

Paper-facing pipeline rule:
- The paper should describe the proposed full pipeline:
  ESP32 onboard capture -> onboard log-mel/integer inference -> event reporting
  -> safety-state bridge -> Tello command boundary.
- Internal bring-up language such as `USB CDC`, `serial`, `weeklyresult`, run
  names, branches, `xiao_*`, `RT1S`, `C32`, and `flight_validation` should not
  appear in the paper body or compiled figures.

Evaluation structure:
- Evaluation uses traditional subsections, not RQ style:
  - Offline Recognition Quality
  - Robustness Under Rotor Noise
  - Embedded Inference and Event Reporting
  - Baseline Comparison
  - Control Bridge and Grounded SDK Behavior
  - User Study
  - Propeller Noise Shielding Study

Current filled evidence:
- Offline reference: accuracy `0.88`, macro F1 `0.88`, emergency P/R/F1
  `0.96/0.79/0.87`.
- Embedded recognizer: accuracy `0.848`, macro F1 `0.850`, emergency R/F1
  `0.70/0.81`.
- Board-side integer invocation: `627 ms`.
- First-window board event latency: `1606 ms`.
- Steady-state event reporting p95: `1005 ms`.
- Continuous event reporting: `30/30`, p50/p95 `990/1021 ms`.
- Grounded SDK reachability: `0/1 ack`, `3002 ms timeout`.
- Control-boundary fixture: emergency `1/1`, movement blocked `1/1`, unknown
  rejected `3/3`.

Baseline evidence integrated as preliminary offline comparison:
- TC-ResNet8: accuracy `0.841`, macro F1 `0.841`, emergency R/F1 `0.84/0.86`.
- BC-ResNet1: accuracy `0.797`, macro F1 `0.793`, emergency R/F1 `0.90/0.83`.
- DS-CNN-S: accuracy `0.607`, macro F1 `0.601`, emergency R/F1 `0.78/0.67`.
- Baseline support parity still needs final audit before writing this as a fully
  matched leaderboard.

User-study protocol added:
- Use isolated participant identifiers.
- Three intent categories: emergency, movement, unknown.
- Each trial saves both ESP32 embedded prediction and saved-audio offline
  reference prediction.
- Offline reference is not treated as ground truth; it is an embedded/reference
  comparison point.
- User-aware fine-tuning is optional personalization and separate from the base
  system claim.
- Current decision: no geometry, direction, angle, distance, speaker-position,
  or direction-level accuracy variables in this submission-cycle user study.

Validation / hygiene checks reported:
- `git diff --check -- docs/paper_sensys2027` passed.
- Body/figures search found no compiled internal terms:
  `BLE`, `Mac`, `host`, `Tello AP`, `USB`, `CDC`, `serial`, `weeklyresult`,
  `xiao_`, `RT1S`, `C32`, `flight_validation`.
- Final full LaTeX compile is still pending.

## Missing Evidence

- [ ] Rotor-noise robustness curve.
- [ ] Real participant-level user-study data.
- [ ] Safety-state bridge response-time numbers.
- [ ] Repeated control-boundary trials beyond the current small fixture.
- [ ] Propeller shielding / microphone placement result; downgrade to
  discussion if not completed.
- [ ] Baseline support-parity audit before final leaderboard language.
- [ ] Abstract with final core numbers after the June 1 result freeze.
- [ ] Full LaTeX compile and page-count check.

## Submission Plan

- 2026-05-28 Thu:
  - Freeze paper story and contribution framing.
  - Prepare HotCRP abstract registration.
  - Confirm user-study, rotor robustness, and bridge timing protocols.
- 2026-05-29 Fri:
  - Submit abstract registration.
  - Freeze figure/table list.
  - Start minimum user-study data collection.
- 2026-05-30 to 2026-05-31:
  - Complete initial user study.
  - Complete rotor-noise robustness curve.
  - Expand control-boundary trials.
  - Prepare demo storyboard / synchronized logs.
- 2026-06-01 Mon:
  - Freeze all paper results.
  - Update evaluation tables and result paragraphs.
  - Rewrite abstract with final numbers.
- 2026-06-02 Tue:
  - Integrate Architecture / Prototype / Evaluation narrative.
  - Run claim-boundary audit.
  - Confirm baseline parity wording.
- 2026-06-03 Wed:
  - Produce advisor-readable full draft.
  - Check page count, target 11-12 body pages.
  - Send title/abstract/contributions/evaluation tables to advisors.
- 2026-06-04 Thu:
  - Remove all `XXX`, visible TODOs, and draft comments.
  - Finish anonymity, references, figures/tables, and LaTeX compile check.
  - Upload to HotCRP for processing check.
- 2026-06-05 Fri:
  - Final proofread in the morning.
  - Submit final PDF before noon local time.
  - Use afternoon only for HotCRP metadata / processing / conflicts.

## Risks

- The paper story is now mostly aligned, but evaluation density is still the
  largest submission risk.
- If June 1 data freeze lacks user-study and rotor robustness evidence, the
  first-round submission may still be possible but will be vulnerable to
  evidence-sufficiency criticism.
- Baseline support parity must be audited before strong comparison claims.
- Internal implementation language must stay out of the compiled paper body.
- Full compile, page count, references, and anonymity still need a final gate.

## 2026-06-01 Figure Integration Receipt

Status:
- Writing agent completed the figure-integration text pass; no figure drawing,
  no experiments, and no model/firmware changes.
- Modified paper files are limited to the draft tree:
  `sections/1introduction.tex`, `sections/4architecture.tex`,
  `sections/5recognizer.tex`, `sections/6prototype.tex`,
  `sections/7evaluation.tex`, `sections/8conclusion.tex`, and
  `figures/prototype_pipeline.tex`.
- Checks reported by the writing agent:
  - `git diff --check -- docs/paper_sensys2027` passed.
  - Internal implementation terms were not found in the paper-facing text.
  - User-study geometry residue was not found.

Decisions:
- Complex figures will be produced as external editable assets plus PDF/PNG
  exports. LaTeX should only provide lightweight `includegraphics` wrappers.
- `fig:user_study_evidence` replaces `tab:user_geometry_protocol`.
- `fig:demo_storyboard` should be merged into the user-study evidence figure or
  dropped.
- `fig:safety_layer_overview` is currently orphaned; either delete it or
  formally connect it as an intro/architecture overview.

Next:
- Figure/table agent should create final external visual assets for system
  architecture, recognizer architecture, response-time breakdown, and
  user-study evidence.
- Writing agent should only coordinate captions, labels, references, and
  placement once final assets exist.

## 2026-06-01 Figure Asset Delivery Receipt

Status:
- Figure/table agent delivered external editable visual assets and PDF exports.
- No LaTeX/TikZ complex figure drawing was used.
- No paper prose, experiment, model, or firmware changes were made in this
  delivery.

Delivered assets:
- `docs/paper_sensys2027/figures/source/system_architecture.drawio` ->
  `docs/paper_sensys2027/figures/system_architecture.pdf`
- `docs/paper_sensys2027/figures/source/recognizer_architecture.drawio` ->
  `docs/paper_sensys2027/figures/recognizer_architecture.pdf`
- `docs/paper_sensys2027/figures/source/user_study_evidence.pptx` ->
  `docs/paper_sensys2027/figures/user_study_evidence.pdf`
- `scripts/paper_figures/plot_response_time_breakdown.py` ->
  `docs/paper_sensys2027/figures/response_time_breakdown.pdf`
- Helper scripts:
  `scripts/paper_figures/render_diagram_exports.py` and
  `scripts/paper_figures/build_user_study_evidence_pptx.mjs`

Figure placement decisions:
- `fig:system_architecture`: `figure*` preferred.
- `fig:recognizer_architecture`: one-column.
- `fig:response_time_breakdown`: `figure*` preferred.
- `fig:user_study_evidence`: `figure*`.

Writing integration required:
- Replace old LaTeX placeholders with lightweight `includegraphics` wrappers.
- Use `fig:user_study_evidence` instead of `tab:user_geometry_protocol`.
- Merge/drop old `fig:demo_storyboard`; user-study Panel D can absorb it.
- Keep no-geometry rule: no geometry, direction, angle, distance,
  speaker-position, or direction-level accuracy content.

Reported checks:
- `git diff --check -- docs/paper_sensys2027 scripts/paper_figures` passed.
- PDF visible text and editable source text scans did not hit forbidden
  study/internal terms.
- Four PDFs are one-page vector PDFs and were visually checked through PNG
  conversion.
