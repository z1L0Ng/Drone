# Weekly TODO (CDT, Thursday-cycle 2026w25)

Meeting checkpoint: Thursday 2026-06-18.

Restart source: 2026-06-11 meeting, 14:38 CDT.

Project status: restarted after the W23 no-submit freeze.

Current near-term goal: formulate the next paper/system/evaluation plan before
the Thursday meeting. Do not restart training, firmware changes, or large
experiments until the plan is reviewed.

## Current Repo Audit

Audit time: 2026-06-16 23:51 CDT.

- Branch: `main`
- HEAD: `48fdd747274938fbd391d17393e97758a9312da3`
- Worktree status: only `docs/.DS_Store` is modified.
- Latest result directory: `weeklyresult/weekly_drone_2026w23`.
- Server/local protocol: still valid for future training handoff, but the
  week-specific section is stale and still points to W19/SenSys.
- ESP32 profile handoff: still useful for deployment history, but the latest
  active planning question is not model dispatch; it is venue, system
  formulation, and evaluation design.

## Restart Decisions

- [x] Restart project planning after the no-submit freeze.
- [x] Treat SenSys 2027 first-round artifacts as frozen evidence, not as the
      immediate submission target.
- [x] Consider IEEE Pervasive Computing special issue as a promising near-term
      venue, pending authorship/guest-editor eligibility confirmation.
- [x] Keep top-conference paths open only as longer-horizon targets:
      INFOCOM needs more mathematical/algorithmic rigor; MobiCom needs stronger
      system building and broader evaluation.
- [ ] Confirm whether a guest editor can be an author for the IEEE Pervasive
      Computing special issue.
- [ ] Collect the exact CFP, deadline, page limit, article type, and ethics /
      human-subjects requirements for the selected venue.

## Work Plan Before Thursday

### Track A: Venue and Submission Strategy

- [ ] Confirm IEEE Pervasive Computing special issue eligibility, including
      whether guest editors can be authors.
- [ ] Record venue constraints: deadline, length, article style, anonymization,
      review process, data/video expectations, and ethics language.
- [ ] Prepare a venue decision memo with three paths:
      IEEE Pervasive Computing, MobiCom-style systems paper, and
      INFOCOM-style algorithm/systems paper.

### Track B: Paper Reading and Positioning

- [ ] Read and summarize UAV speech-interface papers.
- [ ] Read and summarize drone ego-noise / UAV audition papers.
- [ ] Read and summarize human-drone interaction and safety-mechanism papers.
- [ ] Read and summarize embedded speech / TinyML papers that affect the
      onboard-real-time claim.
- [ ] Produce a paper map that answers:
      what each line of work solves, what it does not solve, and where Akouo's
      safety-net framing fits.

Initial reading queue:

- `Kite: Automatic Speech Recognition for UAVs`.
- `Unmanned Aerial Vehicle Control Through Domain-based Automatic Speech Recognition`.
- `Evaluating Voice Command Pipelines for Drone Control: From STT and LLM to Direct Classification and Siamese Networks`.
- `HoverAI: An Embodied Aerial Agent for Natural Human-Drone Interaction`.
- `Vocalics in Human-Drone Interaction`.
- `Speech enhancement using ego-noise references with a microphone array embedded in a UAV`.
- `DroneAudioset: An Audio Dataset for Drone-based Search and Rescue`.
- Recent lightweight UAV/drone speech-enhancement papers, if they are relevant
  to microphone placement and rotor-noise evaluation.

### Track C: System Formulation

- [ ] Define the key terms in paper-facing language:
      `safety net`, `safety-state boundary`, `structured safety-state event`,
      `event-state contract`, `emergency intent`, `movement intent`,
      `unknown/fallback`, `onboard real-time`, and `vehicle-facing action`.
- [ ] Decide whether `safety net` should replace or wrap the current
      `safety-state boundary` terminology.
- [ ] Draw the revised system module list:
      audio capture, rotor-noisy recognizer, event generator,
      safety-state boundary, host/vehicle interface, logging, and fallback.
- [ ] Identify which modules are already implemented, which are prototype-only,
      and which are still conceptual.
- [ ] Prepare a figure/photo checklist:
      physical setup, microphone positions, drone/host path, pipeline overview,
      safety-state boundary, and evaluation setup.

### Track D: Evaluation Redesign

- [ ] Redesign evaluation around the restarted target venue.
- [ ] Separate evaluation evidence into:
      recognition quality, onboard runtime, safety-net behavior,
      control-loop behavior, user/participant study, and physical setup /
      microphone placement.
- [ ] Decide what can be measured before the next meeting and what needs a
      longer experiment campaign.
- [ ] Revisit existing baselines:
      ASR/STT + parser, compact speech-command model families, direct mapping,
      no-unknown fallback, and existing UAV speech interface baselines.
- [ ] Draft a table of metrics:
      accuracy, emergency recall, unknown false action, action pressure,
      response time, event cadence, drop rate, user-level variability,
      noise condition, and deployment footprint.
- [ ] Decide whether new experiments are needed before any next submission:
      microphone placement, rotor-noise levels, shield/placement study,
      stronger ASR baseline, repeated control-loop trials, or additional users.

## Deliverables By Thursday Morning

- [ ] One-page venue strategy memo.
- [ ] Paper reading map with 8-12 relevant papers and explicit positioning.
- [ ] System terminology table.
- [ ] Revised system module/evidence matrix.
- [ ] Evaluation redesign matrix.
- [ ] Figure/photo checklist for the next draft.
- [ ] Agent dispatch prompts for writing, evaluation, deployment/photo audit,
      and literature review.

## Today Plan

- [x] Audit repo / weekly todo / technical specs / latest results.
- [x] Create W25 restart plan.
- [x] Record restart in handoff log.
- [x] Sync W25 restart plan into Notion:
      `https://app.notion.com/p/382309efda298124bf04fa136df47def`.
- [x] Move the W25 restart plan into the `Drone Weekly Management` database
      under `Drone Project Management`.
- [x] Create advisor-facing research report in `Research Report` database:
      `https://app.notion.com/p/383309efda298132aeafc1f1cfc969e5`.
- [ ] Review whether any immediate venue/authorship rule can be verified from
      official sources.
- [ ] Prepare prompts for the active agents, but do not dispatch until approved.

## 2026-06-19 Meeting Prep

Goal: make the next-plan discussion clear, not to start implementation.

### Submission Targets

Option 1: IEEE Pervasive Computing special issue on `Embodied Pervasive Computing`.

- Source: IEEE Computer Society calls-for-papers page.
- Current public deadline:
  - Title and abstract due: 2026-07-01.
  - Full manuscript due: 2026-07-08.
  - Publication window: Apr-Jun 2027.
- Fit:
  - Strong fit if Akouo is framed as an embodied pervasive system for
    human-drone safety interaction.
  - Requires accessible systems narrative, clear terms, strong visuals, and
    real-world deployment/evaluation story.
- Open issue:
  - Guest-editor authorship eligibility is still not confirmed from the public
    page and must be checked directly.

Option 2: MobiCom-style systems paper.

- Source: MobiCom 2025 CFP as the most recent verified public guideline.
- Current public guideline from recent MobiCom cycle:
  - Full paper, double-blind review.
  - Up to 12 single-spaced pages including figures/tables, followed by
    references.
  - Requires practical working systems, rigorous analysis, system design, and
    real-world measurement/deployment.
- Fit:
  - Long-term target if we can make Akouo a stronger mobile/robotic systems
    contribution.
  - Needs broader evaluation, repeatable deployment, stronger baselines, and a
    clear technical contribution beyond speech classification.
- Open issue:
  - Not an immediate target unless the team commits to a larger system/eval
    campaign.

INFOCOM note:

- Do not make INFOCOM the immediate second option. Current work lacks the
  mathematical/algorithmic framing that INFOCOM would likely need.

### Paper Revision Scope To Discuss

Story framework:

- [ ] Decide whether the paper identity should be `embodied pervasive
      safety-interaction system` or `mobile systems paper`.
- [ ] Define `safety net` concretely:
      what it observes, what state it maintains, what actions it can block or
      admit, and how it differs from direct speech command.
- [ ] Keep the central insight:
      speech should be admitted as structured safety-state updates, not
      transcripts, keywords, or direct vehicle commands.

System design:

- [ ] Redraw module boundary:
      microphone/audio capture, onboard recognizer, event generator,
      safety-state boundary, host/vehicle interface, logging, fallback.
- [ ] Add real setup pictures:
      drone, ESP32/microphone, host, microphone placement, and control path.
- [ ] Mark what is implemented, what is prototype-only, and what remains
      conceptual.

Evaluation:

- [ ] Reorganize around deployment questions rather than model leaderboard:
      recognition under rotor noise, runtime/event cadence, safety-net behavior,
      user/participant trials, physical setup/microphone placement, and
      control-loop behavior.
- [ ] Decide which new evidence is essential for the selected target:
      mic placement/noise study, repeated safety-state trials, stronger ASR
      baseline, participant expansion, or live/grounded control-chain tests.
- [ ] Keep existing W23 numbers as evidence candidates, not final claims.

Figures/tables:

- [ ] Replace abstract diagrams with real setup photos and clean pipeline
      visuals.
- [ ] Add a system setup figure showing microphone position and host/drone
      connection.
- [ ] Keep table/figure count venue-appropriate:
      Pervasive Computing favors clarity and visual explanation; MobiCom needs
      denser evidence tables and reproducibility details.

Discussion items for advisor:

- [ ] Which venue path should we optimize for first?
- [ ] Can Alex / guest editor be an author for the Pervasive Computing special
      issue?
- [ ] Should `safety net` be the top-level term, or should we keep
      `safety-state boundary` as the precise technical term?
- [ ] What minimum experiments are required before we rewrite the paper?
- [ ] Should we aim for a readable magazine-style article first, then develop a
      longer MobiCom-style paper later?

## Two-Path Paper Planning Framework

This section is for discussion only. Do not treat it as an implementation or
experiment dispatch.

### Path 1: IEEE Pervasive Computing

Target:

- IEEE Pervasive Computing special issue on `Embodied Pervasive Computing`.
- Public CFP currently says:
  - Title and abstract due: 2026-07-01.
  - Full manuscript due: 2026-07-08.
  - Publication: Apr-Jun 2027.
- IEEE Computer Society author guidance says magazines publish both
  peer-reviewed and editorial content and should appeal to both experts and
  non-experts. Specific word/reference limits vary by magazine and must be
  checked on the Pervasive Computing Author Information / submission page.

How to frame Akouo:

- Frame Akouo as an embodied pervasive safety-net system for small UAVs.
- The core story should be:
  humans naturally use voice near a drone, but a drone is an embodied physical
  system, so speech must not be admitted as direct command; Akouo converts
  rotor-noisy speech into constrained safety-state updates and exposes them to
  a safety net before vehicle-facing behavior is considered.
- Tone should be readable and system-oriented, not a model leaderboard paper.

Possible novelty:

- A safety-net framing for voice-driven UAV interaction.
- A concrete event-state contract between speech recognition and drone policy.
- An embodied prototype showing local audio capture, real-time embedded
  inference, event reporting, and conservative admission into the vehicle side.
- Real-world setup and evaluation around rotor-noisy speech, user interaction,
  and physical placement rather than only offline classification accuracy.

Current draft weak points for this path:

- Too much of the current draft still reads like a conference model/evaluation
  paper instead of a broad pervasive computing article.
- `safety net` is not yet a precise paper-facing term.
- Figures are too abstract; the Pervasive version needs real setup pictures,
  microphone placement, drone/host/control path, and a clean system overview.
- Evaluation is too fragmented across old weekly evidence and needs to be
  reorganized into a readable embodied-system evidence story.
- Related work needs to connect to embodied agents, pervasive computing, and
  human-drone interaction, not only KWS/ASR.

Evaluation to add or redesign:

- Physical setup evidence: microphone position, drone/ESP32/host placement,
  rotor state, and logging path.
- User-facing evidence: participant prompts, event logs, emergency/movement/
  unknown behavior, and failure cases.
- Safety-net behavior: what gets admitted, blocked, logged, or deferred.
- Runtime evidence: embedded inference and event cadence, but framed as
  supporting embodied interaction rather than as the only contribution.
- Baselines: use ASR/KWS/direct mapping as contrastive alternatives, but avoid
  making the article look like a pure benchmark paper.

Main open questions:

- Can the guest editor be an author?
- What is the exact Pervasive Computing word/reference/figure limit from the
  submission system?
- Is July 8 realistic if we need new photos and a cleaned evaluation story?

### Path 2: MobiCom-Style Systems Paper

Target:

- MobiCom-style mobile/robotic systems paper as a longer-cycle target.
- Recent MobiCom CFP guidance emphasizes practical working systems, rigorous
  analysis, system design, and real-world measurement/deployment.
- Recent MobiCom submission format:
  - Double blind.
  - Up to 12 single-spaced pages including figures/tables, references extra.
  - PDF submission; strict formatting; no author identity leakage.
- Exact next-cycle dates must be checked when we decide to target it.

How to frame Akouo:

- Frame Akouo as a mobile robotic edge system that admits human speech into a
  physical UAV control process through a safety-state boundary.
- The paper must answer why this is a systems contribution, not just
  "voice classifier on a drone."
- The story should emphasize the interaction between acoustic sensing,
  embedded real-time constraints, event-state abstraction, safety policy, and
  deployment under rotor noise.

Possible novelty:

- A formal or at least precise safety-state boundary for speech admission into
  mobile robotic control.
- A real-time embedded speech-event pipeline with measured end-to-end behavior.
- A deployable control-loop design that separates recognition, admission,
  fallback, and vehicle-facing action.
- A measurement-driven characterization of rotor-noisy speech interaction on a
  physical UAV platform.

Current draft weak points for this path:

- Technical novelty is not yet strong enough for MobiCom.
- The safety-state boundary is described conceptually but not yet evaluated as
  a systems mechanism.
- Current control-loop evidence is limited and not enough for a strong mobile
  systems claim.
- Evaluation is not yet broad enough: limited users, limited physical
  conditions, limited repeated control behavior, and limited comparison to
  alternative system designs.
- The recognizer/model story alone will not carry the paper.

Evaluation to add or redesign:

- Repeated grounded/no-prop or controlled flight-adjacent control-loop trials.
- Safety-state transition logs with response time, block/admit/defer decisions,
  fallback behavior, and false-action pressure.
- Microphone placement and rotor-noise characterization.
- More participant/user variation and failure analysis.
- Stronger baselines:
  ASR + parser, direct mapping, no-unknown fallback, compact classifier
  families, and ideally an existing UAV voice-control pipeline if reproducible.
- System ablations:
  without safety-state boundary, without unknown/fallback, with/without
  calibration or confidence policy, and potentially different event policies.
- Reproducibility package plan: code, logs, datasets where allowed, and hardware
  setup documentation.

Main open questions:

- What is the concrete technical insight that would make this a MobiCom paper?
- Do we need a formal state machine / policy model?
- How many users, environments, microphone placements, and control-loop trials
  are enough?
- Is the current hardware platform sufficiently convincing, or do we need a
  stronger drone/control setup?

### Suggested Position For The Meeting

- Do not rush promotion or broad dissemination.
- Use the next meeting to choose the first target path.
- If the target is IEEE Pervasive Computing:
  prioritize readable framing, terminology, photos, system narrative, and
  cleaned evaluation.
- If the target is MobiCom-style:
  plan a longer evidence campaign and do not promise near-term submission.
- Keep existing W23 results as a starting evidence bank, not as final claims.

## Detailed Meeting Report Draft

### Current Judgment

The current Akouo work should not be presented as a finished top-conference
systems paper yet. However, it is not blocked as a project. The current evidence
is enough to support a more accessible IEEE Pervasive Computing style article if
we are willing to:

1. rewrite the paper around an embodied UAV safety-net narrative,
2. add real setup figures/photos and a clearer system diagram,
3. reorganize existing evaluation evidence into a deployment story, and
4. add a small number of targeted evaluation checks rather than launching a new
   training campaign.

The MobiCom-style path should be treated as a follow-up research campaign. For
that route, the current work needs a sharper technical novelty beyond "voice
recognition on a drone" and stronger system/evaluation evidence.

### Recommended Near-Term Strategy

Near-term plan:

- Use the IEEE Pervasive Computing special issue as the immediate target if
  authorship eligibility and exact manuscript limits are acceptable.
- Treat the paper as an embodied pervasive computing article:
  explain the problem, system design, safety-net abstraction, deployment
  constraints, and practical lessons.
- Avoid overinvesting in new model architecture claims before the deadline.
- Small-supplement evaluation/figures are acceptable and useful.

Follow-up plan:

- After the IEEE path is decided or completed, use the next cycle to develop a
  stronger MobiCom-style contribution.
- The follow-up should focus on new technical novelty:
  safety-state policy design, online confidence/admission control, microphone
  placement/noise adaptation, formalized event-state boundary, or broader
  control-loop deployment.

### IEEE Pervasive Computing Path

Submission timing and requirements:

- Target issue: IEEE Pervasive Computing special issue on `Embodied Pervasive
  Computing`.
- Public CFP:
  - Title and abstract due: 2026-07-01.
  - Full manuscript due: 2026-07-08.
  - Publication window: Apr-Jun 2027.
- Public author guidance:
  - IEEE Computer Society magazines publish peer-reviewed and editorial
    content.
  - Magazine articles should be understandable to a broader technical audience,
    not only narrow conference specialists.
  - Exact word/reference/figure limits for IEEE Pervasive Computing must still
    be confirmed from the Author Information or submission system.

Possible paper framing:

- Working identity:
  `Akouo: a voice safety net for embodied UAV interaction`.
- Key argument:
  A drone is not a passive speech-recognition endpoint. It is an embodied
  physical system. Therefore, nearby human speech should not directly become a
  flight command. It should first become a structured safety-state update, then
  be mediated by a safety net before any vehicle-facing behavior is considered.
- Narrative emphasis:
  hands-free human-drone interaction, rotor-noisy sensing, onboard real-time
  constraints, safety-state boundary, and practical deployment lessons.

Novelty for IEEE path:

- Safety-net abstraction:
  voice is treated as a safety-relevant signal entering an embodied system, not
  as generic speech command.
- Event-state contract:
  emergency / movement / unknown are not direct commands; they are structured
  updates with different safety meanings.
- Embodied prototype:
  local microphone capture, embedded inference, event reporting, and a host /
  vehicle-facing boundary can be shown as a concrete system pipeline.
- Practical evidence:
  rotor-noisy recognition, real-time embedded behavior, baseline contrasts, and
  user-facing interaction evidence can be organized as lessons for embodied
  pervasive systems.

Current draft weaknesses for IEEE path:

- The current draft is still shaped like a systems-conference paper with many
  result fragments, not like a cohesive magazine article.
- The term `safety net` is not yet precisely defined.
- The system contribution is spread across model, ESP32, BLE/host, and
  evaluation details; it needs a simpler reader-facing story.
- Current figures are too abstract; the paper needs real setup photos and a
  clear physical pipeline.
- Evaluation currently reads like multiple weekly receipts; it needs to be
  reorganized into a small set of claims and evidence.

Small evaluation / figure supplements for IEEE:

- Figure supplement:
  - real photo of drone + ESP32/microphone + host setup,
  - microphone placement close-up,
  - simplified safety-net pipeline,
  - event-state contract graphic or table,
  - one compact evaluation summary figure/table.
- Evaluation supplement:
  - repackage W23 evidence into an evidence matrix,
  - add repeated safety-net decision trials if they are quick and low-risk,
  - add a small microphone placement / rotor-noise setup check if feasible,
  - summarize existing ASR/parser and direct-mapping baselines as contrastive
    evidence,
  - avoid new full training unless a specific missing claim requires it.
- Writing supplement:
  - rewrite introduction/motivation for embodied safety net,
  - simplify model details,
  - move weekly/run-specific details out,
  - add a lessons/discussion section that is useful for a pervasive computing
    audience.

Minimum IEEE go/no-go questions:

- Can a guest editor be an author?
- What are the exact word/reference/figure limits?
- Can we produce real setup photos and a coherent evaluation summary within the
  remaining time?
- Does the team accept a more explanatory article rather than a top-conference
  claim of strong technical novelty?

### MobiCom-Style Follow-Up Path

Submission timing and requirements:

- Treat this as a longer-horizon target, not the next immediate submission.
- Recent MobiCom guidance emphasizes practical working systems, rigorous
  analysis, system design, and real-world measurement/deployment.
- Recent format is 12 pages for non-reference content, double blind, strict
  formatting and anonymity.
- Exact future deadline must be checked when this becomes the active target.

How to frame for MobiCom:

- Akouo must become a stronger mobile robotic systems contribution.
- The framing should not be:
  "we built a classifier and put it on a drone."
- The framing should be:
  "we design and evaluate a speech-admission layer that controls how noisy
  human speech enters a physical UAV control process."
- The core system question should be:
  how to safely admit acoustic human intent into an embodied mobile system under
  noise, latency, and uncertainty constraints.

Novelty needed for MobiCom:

- A precise safety-state boundary or policy model, not only a narrative term.
- An online admission mechanism:
  confidence, timing, unknown handling, refractory behavior, and action gating.
- A deployment-aware acoustic design:
  microphone placement, rotor-noise characterization, and possibly adaptive
  calibration.
- A control-loop evaluation:
  repeated trials showing how recognizer uncertainty affects block/admit/defer
  decisions and vehicle-facing outcomes.
- A stronger comparison:
  transcript-first ASR, direct command mapping, no-unknown fallback, compact
  model families, and ideally a reproducible existing UAV voice-control
  pipeline.

Current draft weaknesses for MobiCom:

- Technical novelty is still underdeveloped.
- The model design is not enough by itself.
- The safety-state boundary is not yet evaluated as a mechanism.
- The control-loop evidence is too limited.
- User/physical-environment coverage is too small.
- There is no full experimental campaign showing robustness across placement,
  rotor conditions, users, and policy settings.

Evaluation campaign needed for MobiCom:

- Physical setup:
  multiple microphone placements, rotor states, distances, and environmental
  conditions.
- Recognition:
  noisy speech accuracy, emergency recall, unknown containment, per-user
  variation, failure-case analysis.
- Runtime:
  inference latency, event cadence, drop rate, host/vehicle round-trip, command
  decision latency.
- Safety-state mechanism:
  block/admit/defer rates, false-action pressure, missed emergency handling,
  unknown fallback behavior, repeated state transition logs.
- Control-loop:
  grounded/no-prop repeated trials first; flight-adjacent or carefully
  controlled flight only if safety permits.
- Baselines/ablations:
  ASR+parser, direct mapping, no unknown, no safety-state boundary, compact
  speech-command models, confidence threshold variants, microphone placement
  variants.
- Reproducibility:
  documented hardware setup, logs, scripts, public/non-sensitive data where
  possible.

Suggested MobiCom follow-up research questions:

- What is the right safety-state abstraction for speech entering physical UAV
  control?
- How should confidence, timing, and unknown audio affect admission decisions?
- How does microphone placement and rotor-noise geometry change safety-event
  reliability?
- What evidence is needed to show a voice safety net improves interaction
  without increasing unsafe action pressure?
- Can the safety-net mechanism generalize beyond the current Tello/ESP32
  prototype?

### Proposed Plan To Discuss With Advisor

Proposal:

- Short term:
  aim for IEEE Pervasive Computing if authorship/format constraints work.
  Use current progress, add small evaluation/figure supplements, and rewrite the
  paper around embodied safety net.
- Medium term:
  after IEEE submission or decision, start a MobiCom-style follow-up focused on
  new technical novelty and stronger system evaluation.

Advisor decisions needed:

- Is the IEEE Pervasive path worth prioritizing despite the short deadline?
- What exact claim should be the center of the IEEE article?
- Which small evaluation supplement is most valuable:
  physical setup/mic placement, safety-net repeated trials, stronger baseline,
  or user-facing evidence?
- For MobiCom, what should be the new technical novelty:
  state machine/policy, online admission control, acoustic deployment design, or
  control-loop evaluation?

## 2026-06-25 IEEE Pervasive Writing Thread Bootstrap

Meeting source: 2026-06-18 12:35 CDT publication strategy discussion.

Decision:

- [x] Open a separate writing thread for the IEEE Pervasive Computing magazine
      trial submission.
- [x] Keep this thread scoped away from the long-term MobiCom/SenSys/TMC
      research plan.
- [x] Thread task is framework support for the user's new Overleaf project, not
      direct repo paper editing.
- [x] Do not ask the thread to start writing full prose immediately.

Thread goal:

- Build a condensed magazine-paper outline for the IEEE Pervasive Computing
  special issue on `Embodied Pervasive Computing`.
- Respect the meeting constraints:
  fewer than 6000 words, about 20 citations, limited figures, no equations.
- Present a generic overview and basic evaluation.
- Preserve deeper evaluation and stronger novelty for future MobiCom/SenSys/TMC.

Thread boundary:

- No model changes.
- No experiments.
- No firmware/Tello/ESP32 tasks.
- No server training.
- No edits to `docs/paper_sensys2027` unless explicitly approved.
- No attempt to expose all existing work or all future ideas in this magazine
  trial paper.

Prompt location:

- Full bootstrap prompt is recorded in the Notion project-management page:
  `https://app.notion.com/p/382309efda298124bf04fa136df47def`.

### Refined Scope For The New Writing Thread

The first message to the new writing thread should be stricter than the initial
bootstrap. It should require the thread to inspect the local project first, then
inspect the IEEE Pervasive target, and only then propose a lightweight magazine
paper framework.

Key refinement:

- [x] The thread should scan the local Drone project to understand what Akouo is
      actually doing.
- [x] The thread should check the target CFP and writing constraints before
      proposing structure.
- [x] The thread should not assume we need to fully write or fully expose
      Akouo.
- [x] The IEEE article may be only a lightweight framework and basic evaluation
      article.
- [x] The thread must preserve deeper novelty, richer evaluation, and stronger
      system claims for later MobiCom/SenSys/TMC work.
- [x] The first output should be a decision memo / outline, not prose drafting.

Refined thread instruction:

```text
你是 Drone/Akouo 项目的 IEEE Pervasive Computing magazine 写作协作 agent。

你的第一阶段任务不是直接写正文，而是先做 scoped understanding 和 paper-planning：

1. 先扫一遍本地项目，理解我们到底在做什么：
   - 当前 repo: `/Users/zilongzeng/Research/Drone`
   - 重点看：
     - `docs/paper_sensys2027/`
     - `docs/weekly_todo/2026/2026w23/todo.md`
     - `docs/weekly_todo/2026/2026w25/todo.md`
     - `docs/weekly_todo/handoff_log.md`
     - `weeklyresult/weekly_drone_2026w23/`
     - 和 ESP32 / user-study / ASR baseline 相关的 summary 文件。
   - 目标是理解 Akouo 当前已有 evidence、边界、弱点和长期计划。

2. 再检查投稿目标要求：
   - Target: IEEE Pervasive Computing special issue on Embodied Pervasive Computing
   - CFP: https://www.computer.org/digital-library/magazines/pc/cfp-embodied-pervasive-computing-agents
   - Meeting constraints:
     - < 6000 words
     - about 20 citations
     - limited figures
     - no equations
     - magazine-style accessible writing
   - 你需要判断什么内容适合这个 venue，什么内容不适合。

3. 然后提出一个不干扰长期投稿计划的 magazine-paper framing：
   - 我们不一定要完整写 Akouo。
   - 这篇可以只是一个 lightweight framework + basic evaluation / experience article。
   - 不要完整暴露所有已有工作、所有系统细节、所有 future novelty。
   - 更深入的 technical novelty、control-loop evaluation、policy/state-machine design、
     larger user study、deployment campaign 留给后续 MobiCom/SenSys/TMC。

严禁事项：
- 不改 `docs/paper_sensys2027/`，除非我明确要求。
- 不跑实验、不训练模型、不改 ESP32/Tello 固件、不启服务器。
- 不把 magazine paper 写成 MobiCom/SenSys 的缩写版。
- 不把模型架构写成主要 novelty。
- 不声称完整 safety validation。
- 不把所有已有 result 都塞进去。

请先输出：
1. 你扫读本地项目后的理解：我们已有的系统、证据、边界是什么。
2. 你对 IEEE Pervasive CFP 和 meeting constraints 的理解。
3. 哪些 Akouo 内容适合放进 magazine paper，哪些应该保留给长期系统论文。
4. 一个 <6000 words、约 20 citations、limited figures、no equations 的 outline。
5. 建议的 2-4 张 figure/table placeholder。
6. basic evaluation 只应该包含哪些轻量证据。
7. 后续 MobiCom/SenSys/TMC 应该保留哪些 novelty 和 evaluation。
8. 我在 Overleaf 新项目里应该先建哪些 section。

输出语言：中文为主；section title、paper-facing phrase 可以用英文。
```

## Risks

- Venue risk: IEEE Pervasive Computing guest-editor authorship eligibility is
  not confirmed yet.
- Scope risk: top-conference framing requires substantially more technical
  depth than the frozen SenSys draft had.
- Evidence risk: current evaluation is strong as a prototype evidence stack but
  still weak for broad safety-mechanism claims.
- Terminology risk: `safety net` must be defined concretely or reviewers will
  read it as marketing language.
- Artifact risk: the repo currently has a `docs/.DS_Store` modification; ignore
  unless the user asks for cleanup.

## Commands / Prompts To Dispatch After Approval

### Literature Review Agent

Read the restarted Akouo project context and build a literature map. Focus on
UAV speech interfaces, drone ego-noise / UAV audition, human-drone interaction,
UAV safety mechanisms, and embedded speech / TinyML. Return a table with:
citation, venue/year, system goal, sensing/control setup, noise setting,
onboard feasibility, safety mechanism, evaluation metrics, what it solves, what
it leaves open for Akouo. Do not edit paper files or run experiments.

### Writing/Formulation Agent

Read the current draft and the June 11 restart meeting. Do not rewrite the
paper yet. Produce a formulation memo that defines `safety net`,
`safety-state boundary`, `structured safety-state event`, and `event-state
contract`, then propose how the paper should be reframed for IEEE Pervasive
Computing versus a MobiCom-style systems submission. No TeX edits unless
approved.

### Evaluation Planning Agent

Read current W23 results and the restarted venue strategy. Do not run new
experiments. Produce a revised evaluation matrix separating recognition,
onboard runtime, safety-net behavior, control-loop behavior, participant study,
and microphone/physical setup. Mark which metrics are already available, which
need short experiments, and which require a longer campaign.

### Deployment / Photo Audit Agent

Audit the current physical setup evidence needed for the next manuscript:
microphone positions, ESP32/drone/host arrangement, control path, logging path,
and safety-state boundary evidence. Do not change firmware or run live drone
tests. Return a photo/figure checklist and a minimal capture protocol.
