# Weekly TODO (CDT, Thursday-cycle 2026w27)

Meeting source: 2026-06-25 meeting, 12:35 CDT.

Current date at planning: 2026-06-30.

Immediate target: IEEE Pervasive Computing special issue on `Embodied
Pervasive Computing`.

Submission mode: short magazine trial paper, not the long-term MobiCom /
SenSys / TMC systems paper.

## Current Repo Audit

Audit time: 2026-06-30 15:32 CDT.

- Branch: `main`.
- HEAD: `48fdd747274938fbd391d17393e97758a9312da3`.
- Worktree dirty files:
  - `.DS_Store`
  - `docs/.DS_Store`
  - `docs/README.md`
  - `docs/weekly_todo/handoff_log.md`
  - `docs/ieee_pervasive/`
  - `docs/ieee_pervasive_magazine_template.zip`
  - `docs/weekly_todo/2026/2026w25/`
- Latest result directory: `weeklyresult/weekly_drone_2026w23`.
- Current IEEE scaffold:
  - `docs/ieee_pervasive/main.tex`
  - `docs/ieee_pervasive/sections/1introduction.tex`
  - `docs/ieee_pervasive/sections/2system.tex`
  - `docs/ieee_pervasive/sections/3demo.tex`
  - `docs/ieee_pervasive/sections/4realworld.tex`
  - `docs/ieee_pervasive/sections/5conclusion.tex`
  - `docs/ieee_pervasive/references.bib`
- Current IEEE scaffold is only a bullet skeleton, about 438 words total across
  TeX/Bib files, with no references yet.

## Meeting Decisions

- [x] Use IEEE Pervasive Computing as a short-term magazine-paper trial.
- [x] Keep the paper concise:
      fewer than 6000 words, fewer than about 20 references, limited
      figures/tables, no equations.
- [x] Focus on drone-side speech intent recognition and embodied interaction.
- [x] Include safety only as a light `safety net` concept.
- [x] Stop the system story at intent output / intent interface where useful.
- [x] Reserve detailed safety mechanisms, stronger evaluation, and new
      technical novelty for future MobiCom / SenSys / TMC work.
- [x] Avoid making the magazine paper a compressed version of the long systems
      paper.

## This Week Goal

Prepare and register the IEEE Pervasive Computing magazine submission, then
produce a reviewable first draft.

Hard date:

- 2026-07-01: title and abstract registration due.

Next hard date:

- 2026-07-08: full manuscript due.

## Paper Scope For This Trial Submission

Recommended title direction:

- `Toward On-Device Speech Intent Recognition for Small Drones`
- or `A Lightweight Speech-to-Intent Layer for Embodied Drone Interaction`
- or `Drone-Side Speech Intent Recognition for Embodied Pervasive Interaction`

Recommended paper identity:

- This is a lightweight framework / experience / feasibility article.
- It introduces why speech-to-intent is useful for drones, why it should run
  near or on the drone, and how a compact intent layer can support future
  embodied interaction.
- It should not claim complete drone safety validation.
- It should not present the model architecture as the main novelty.
- It should not expose all future safety-state policy ideas.

Core message:

- Drones are embodied systems operating near people.
- Existing controller/app/network interfaces can be slow or unavailable for
  nearby human communication.
- Speech can provide a hands-free interaction channel, but direct speech-to-
  command is too strong for this first paper.
- A drone-side speech-to-intent layer is a lightweight intermediate interface.
- Safety can be mentioned as a future-facing safety net, but detailed safety
  mechanisms remain future work.

## Writing Plan

### 2026-06-30 Tue: registration preparation and scope freeze

- [ ] Confirm submission site / registration form.
- [ ] Confirm authorship and author order.
- [ ] Confirm title, short abstract, keywords, and target special issue.
- [ ] Freeze paper scope:
      generic framework + basic evaluation; no deep safety mechanism.
- [ ] Review current `docs/ieee_pervasive` scaffold and identify missing
      sections.
- [ ] Prepare registration abstract draft.
- [ ] Decide whether the Overleaf project is the source of truth for this trial
      paper, with repo as backup/reference only.

### 2026-07-01 Wed: registration and first structure pass

- [ ] Submit title and abstract registration.
- [ ] Save registration receipt / confirmation.
- [ ] Build Overleaf structure:
      introduction, framework/design goals, prototype/demo, basic evaluation,
      applications/vision, limitations/future work.
- [ ] Add figure/table placeholders.
- [ ] Build a reference shortlist with fewer than 20 citations.

### 2026-07-02 Thu: team-review skeleton

- [ ] Produce a 4-5 page skeleton draft.
- [ ] Add the conceptual safety-net figure placeholder.
- [ ] Add setup/demo figure placeholder.
- [ ] Add a compact basic-evaluation table placeholder.
- [ ] Send skeleton to team for early framing feedback.

### 2026-07-03 Fri: first prose draft

- [ ] Convert bullets into readable magazine-style prose.
- [ ] Keep safety discussion short and explicitly future-facing.
- [ ] Keep evaluation lightweight.
- [ ] Keep references under 20.
- [ ] Check that no deep MobiCom/SenSys novelty is overexposed.

### 2026-07-04 to 2026-07-05 Weekend: draft completion

- [ ] Complete first full draft.
- [ ] Add final figure/table drafts.
- [ ] Check word count against 6000-word limit.
- [ ] Check no equations.
- [ ] Mark claims that need softer language.

### 2026-07-06 Mon: revision after team feedback

- [ ] Integrate comments from coauthors.
- [ ] Tighten title/abstract/introduction.
- [ ] Improve figure captions.
- [ ] Trim repeated or overly technical content.

### 2026-07-07 Tue: final preparation

- [ ] Final proofread.
- [ ] Verify references and citations.
- [ ] Confirm PDF formatting.
- [ ] Confirm final author metadata.
- [ ] Upload a near-final PDF if the system permits checking before the
      deadline.

### 2026-07-08 Wed: full submission

- [ ] Submit final manuscript.
- [ ] Save submission receipt.
- [ ] Archive final Overleaf source/PDF pointers in the project-management page.

## Evaluation / Evidence Plan

Use only light evidence that supports feasibility:

- Basic offline intent-recognition result, if already available and easy to
  explain.
- On-device/runtime feasibility, if it can be summarized without internal run
  names.
- Simple demo workflow:
  microphone/ESP32 captures speech, outputs intent, logs result.
- Optional ASR contrast:
  transcript-first systems struggle under rotor-noisy one-second clips, but do
  not overclaim that all ASR fails.

Do not include:

- Full control-loop safety validation.
- Large user-study claims.
- Detailed safety-state policy or action-admission mechanisms.
- Full baseline leaderboard.
- All W23 action-pressure and no-unknown ablation details unless needed.

## Figure / Table Plan

Limit to 3-4 visual items total.

Recommended:

- [ ] Figure 1: scenario / motivation:
      person near drone, speech as hands-free communication.
- [ ] Figure 2: lightweight speech-to-intent framework:
      audio capture -> on-device recognition -> intent output -> future
      application/safety net.
- [ ] Figure 3: prototype/demo setup:
      drone, ESP32/microphone, host/logging path.
- [ ] Table 1: compact feasibility summary:
      intent classes, runtime/evidence type, demo/evaluation takeaway.

Optional:

- [ ] Small conceptual safety-net inset, only if it does not make the paper
      look like a full safety paper.

## Registration Checklist

- [ ] Final title.
- [ ] Short abstract.
- [ ] Author list and order.
- [ ] Corresponding author.
- [ ] Keywords.
- [ ] Special issue selection:
      `Embodied Pervasive Computing`.
- [ ] Conflict / metadata if requested.
- [ ] Confirmation receipt saved.

## Risks

- Registration due date is tomorrow: 2026-07-01.
- The current IEEE scaffold is only a bullet skeleton.
- The paper can become too broad if safety is overdeveloped.
- The paper can become too weak if novelty is framed only as
  `speech recognition on drones`.
- The paper should not consume the stronger novelty reserved for future
  MobiCom / SenSys / TMC work.
- Existing dirty files may include work from the writing thread; do not revert
  without review.

## Commands / Prompts To Dispatch

### Writing Agent

Use the current `docs/ieee_pervasive` scaffold and Overleaf project as context.
Do not edit the old SenSys paper. First produce a registration package:
three title options, one 150-250 word abstract, 5-8 keywords, and a 4-5 page
magazine-paper outline. Keep the paper under 6000 words, fewer than about 20
references, limited figures/tables, and no equations. Focus on generic
speech-to-intent framework and basic feasibility evidence. Keep detailed safety
mechanism, control-loop evaluation, and stronger novelty for future work.

### Figure Agent

Do not create final art yet. Produce a figure plan for 3-4 visual items:
scenario, speech-to-intent framework, prototype/demo setup, and compact
evaluation summary. Prefer simple, readable magazine-style visuals and real
setup photos where possible.

### Evaluation Agent

Do not run new experiments unless explicitly approved. Audit existing results
and propose the smallest basic-evaluation table that can support feasibility
without overclaiming safety or full deployment.
