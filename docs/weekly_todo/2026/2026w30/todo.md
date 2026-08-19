# Weekly TODO (CDT, Thursday-cycle 2026w30)

Meeting source: 2026-07-10 meeting record.

Next meeting: 2026-07-23.

Current planning date: 2026-07-22.

Project state: post-magazine-submission / next-stage evaluation planning.

## Current Repo Audit

Audit time: 2026-07-22 17:03 CDT.

- Branch: `main`.
- HEAD: `495d94fee3f53b6c192a2c28f03524319d11fa2f`.
- Dirty files:
  - `docs/ieee_pervasive/main.tex`
  - `docs/ieee_pervasive/references.bib`
  - `docs/ieee_pervasive/sections/3demo.tex`
- Latest result directory: `weeklyresult/weekly_drone_2026w23`.
- Current IEEE Pervasive draft evidence:
  - `docs/ieee_pervasive/main.tex`
  - `docs/ieee_pervasive/sections/1introduction.tex`
  - `docs/ieee_pervasive/sections/2system.tex`
  - `docs/ieee_pervasive/sections/3demo.tex`
  - `docs/ieee_pervasive/sections/4realworld.tex`
  - `docs/ieee_pervasive/sections/5conclusion.tex`
  - `docs/ieee_pervasive/references.bib`
  - local word count across TeX/Bib files: about `4680` words.
  - current visible title: `Speech as a Safety Net for Drone Operation`.

## Meeting Decisions From 2026-07-10

- [x] The immediate bottleneck is no longer only model accuracy; the next stage
      needs a complete evaluation framework.
- [x] Evaluation should cover algorithm performance, physical speech factors,
      hardware/platform design, deployment behavior, and real test workflow.
- [x] Hardware contribution must be clarified:
      commodity off-the-shelf setup vs drone-specific miniaturized/optimized
      hardware design.
- [x] Multi-platform validation is valuable if feasible, because different
      drones and propellers create different rotor-noise profiles.
- [x] Rotor/propeller noise should become a first-class experimental axis.
- [x] Real-world factors should include SNR, speech volume, and user-drone
      distance.
- [x] Use standardized recorded speech playback for controlled tests before
      large user studies, so volume/distance/noise variables can be isolated.
- [x] Do not rush full formal user study before the workflow is validated.
- [x] First run a small pilot with 2-3 nearby testers and record the whole
      process on video for advisor/Stephen feedback.

## Goal Before 2026-07-23 Meeting

Produce short, concrete, reportable planning artifacts rather than trying to
finish broad experiments.

Tomorrow's report should say:

- We translated the July 10 discussion into an evaluation framework.
- We separated immediate pilot validation from full formal experiments.
- We identified hardware contribution questions that need advisor approval.
- We proposed a standardized playback protocol for volume/distance/SNR tests.
- We defined the next two-week experiment path.

## Short-Term Deliverables

### 1. Evaluation Framework v0

- [x] Prepare a compact evaluation matrix with axes, metrics, controls, and
      expected evidence.
- [x] Include these axes:
      model quality, rotor noise, volume, distance, SNR, hardware placement,
      deployment latency, multi-drone/propeller variation, pilot video.
- [x] Mark which experiments can be done immediately and which require hardware
      or user-study preparation.

### 2. Hardware Contribution Memo

- [x] Decide whether current hardware is only commodity assembly or has
      drone-specific design contributions.
- [x] Audit possible hardware contribution claims:
      miniaturization, microphone placement, downward-facing capture,
      structural mounting, isolation from rotor/propeller noise, onboard
      compute placement, weight/size constraints.
- [x] Prepare advisor questions:
      what counts as enough hardware novelty for this paper line?

### 3. Controlled Playback Protocol v0

- [x] Define standardized recorded-speech playback workflow:
      same speech clip, same playback device, controlled volume settings,
      controlled distance settings, and fixed drone/microphone state.
- [x] Candidate variables:
      volume level, distance, rotor on/off, drone platform, propeller type,
      language.
- [x] Candidate outputs:
      recognition accuracy, emergency recall, false positives, SNR estimate,
      latency, failed/missed command rate.

### 4. Pilot Video Protocol

- [x] Prepare a 2-3 tester pilot script before formal user study.
- [x] Record full setup/process, not just final success.
- [x] Show microphone placement, drone/platform, playback or spoken prompt,
      output/log behavior, and any failure case.
- [ ] Send video to advisor/Stephen for protocol feedback before scaling.

### 5. Writing / Paper Update

- [ ] Keep the IEEE Pervasive draft as the current short paper artifact.
- [ ] Start a separate next-stage evaluation section outline for the longer
      systems paper.
- [ ] Do not overclaim safety validation from current evidence.
- [ ] Use tomorrow's meeting to decide whether hardware contribution and
      rotor-noise evaluation become the main next-story angle.
- [x] Prepare a Chinese meeting-discussion draft for 2026-07-23 and sync it to
      the W30 Notion management page for review.
- [x] Rewrite the Chinese draft report after adding evaluation redesign and
      cross-language dataset/mapping strategy.
- [x] Add a full-paper contribution/readiness section: where the next systems
      paper's contribution could land and what is still missing for top-tier
      systems submission.
- [x] Rewrite the report around the updated control-loop plan:
      remove `embedded event generation` as a standalone evaluation layer,
      add complete speech-to-drone control-loop evaluation, add multi-platform
      evaluation, and introduce a finer-grained intent taxonomy.
- [x] Review the updated Chinese draft for flow and create the same-date English
      final report without changing the intended meaning.

### 6. Meeting Report Database Workflow

- [x] Create a dedicated Chinese draft meeting-report database under
      `Drone Project Management`.
- [x] Create a dedicated English final meeting-report database under
      `Drone Project Management`.
- [x] Seed the Chinese draft database with the first date-named page:
      `2026-07-23`.
- [x] Document the rule:
      Chinese draft pages are for user discussion; after approval, write the
      English version into the final report database.
- [x] Use meeting date as page title in both databases, e.g. `YYYY-MM-DD`.

Notion database URLs:

- Chinese drafts:
  `https://app.notion.com/p/ad1b23cbdacb4387b15e208e6f90dd8c`
- English finals:
  `https://app.notion.com/p/15961b8948524d838e4e063c7c0d949b`
- First Chinese draft:
  `https://app.notion.com/p/3a6309efda2981959ba3fb5058bee71c`
- First English final report:
  `https://app.notion.com/p/3a6309efda29815eb14fe1723ec2b276`

### 7. Paper Search Thread

- [x] Prepare a bootstrap prompt for a new SOTA / related-work paper-search
      thread.
- [x] User manually opens a new Codex thread and pastes the prompt, because
      `create_thread` is not exposed in this session.
- [x] Sync the paper-search thread's receipt back into this W30 page after it
      finishes.

Thread title suggestion:

`Drone SOTA Paper Search - Safety-Net / Rotor-Noise / On-Device Speech`

Bootstrap prompt:

```text
你是 Drone 项目的 paper-search agent，只负责只读文献检索和论文定位分析，不做实现、不改 repo、不跑实验、不启动服务器任务。

工作目标：
为 Drone 完整版 systems paper 做一轮最新 SOTA / related-work 检索，回答：
1. 最新 speech / audio / intent / ASR / KWS / noisy speech 方法能给我们的完整论文提供什么；
2. 哪些方法适合作为 baseline、对照、related work、failure mode，或者 future direction；
3. 哪些方向能帮助我们重新强化 novelty、system design、evaluation design 和 paper framing。

项目背景：
- 当前短文是 IEEE Pervasive-style spoken safety-net / drone operation framework。
- 长期目标是更强的 SenSys / MobiCom-style systems paper。
- 当前下一阶段重点不是单纯提升模型 accuracy，而是设计完整 evaluation framework。
- 重点场景是 drone-side / near-drone voice interaction under rotor / propeller noise。
- 当前系统方向包括：on-device recognition, rotor-noise robustness, microphone / hardware placement, controlled playback, SNR / volume / distance evaluation, pilot workflow, possible multi-drone / propeller variation。
- 当前 evidence 边界：已有 ESP32 runtime / deployment prototype evidence，但不能写成 flight safety validation；硬件目前只能保守称为 drone-side embedded audio prototype。

请先搜索并阅读近期和经典论文，优先使用 primary sources：
- ACM / IEEE / USENIX / ISCA / Interspeech / ICASSP / SenSys / MobiSys / MobiCom / UbiComp / IMWUT / TinyML / embedded ML / robotics / HRI 相关来源；
- arXiv 可以作为补充，但要标明是否 peer-reviewed；
- 优先 2021-2026，必要时包含经典 baseline。

检索方向至少包括：
1. noisy speech recognition / noise-robust ASR / enhancement under non-stationary noise；
2. keyword spotting / speech command recognition / spoken language intent under noise；
3. tiny / on-device / MCU speech recognition and embedded audio inference；
4. drone / UAV acoustic noise, rotor-noise cancellation, microphone placement, audio sensing on drones；
5. human-drone interaction and voice control of drones；
6. safety layer / safety monitor / runtime assurance / human-in-the-loop safety for drones or robots；
7. evaluation methods for real-world speech interaction: SNR, distance, volume, playback protocol, user study design。

输出格式：

1. Status
- branch / local repo audit if you inspect repo;
- what you searched;
- no files changed unless explicitly approved.

2. Paper Map
Table columns:
- Category
- Paper / year / venue
- Main idea
- Why relevant to Drone
- Can be baseline / related work / motivation / future work
- What claim it supports or challenges
- Link / DOI

3. SOTA Lessons For Our Full Paper
Organize by:
- Story framing
- Novelty opportunities
- System design
- Evaluation design
- Baselines and comparisons
- Hardware / microphone / rotor-noise angle

4. Recommended Additions To Paper
- 5-8 concrete papers that should be cited;
- which section each belongs to;
- one-sentence reason per paper.

5. Possible New Baselines / Ablations
For each candidate:
- what it tests;
- implementation cost: low / medium / high;
- whether it is necessary for the next paper;
- whether it can be done with current dataset/logs or needs new experiments.

6. Risks
- overclaim risks;
- papers that are adjacent but not directly comparable;
- areas where SOTA is too large / cloud-based / unfair as baseline.

7. Next Questions For Advisor
- concise questions we should ask in the next meeting.

Boundary:
Do not say our system is safer than existing mechanisms unless evidence supports it.
Do not turn cloud ASR / large foundation models into unfair baseline rows without discussing deployment mismatch.
Do not propose experiments before explaining which paper claim they would support.
```

Paper-search receipt sync time: 2026-07-23 00:36 CDT.

Scope:

- [x] Read-only paper search completed.
- [x] No files changed by paper-search thread.
- [x] No experiments, training, firmware changes, live drone tests, or server
      dispatch.
- [x] Search covered noisy ASR/enhancement, KWS/SLU, TinyML/MCU speech,
      UAV ego-noise, human-drone interaction, runtime assurance, and
      SNR/playback/HRI evaluation protocol.

Must-fix evidence issues before any full-paper claim:

- [ ] 1462-trial result audit:
      current receipt says desktop TFLite re-inference from SD audio, with
      `trials with board prediction = 0`; do not write this as live onboard
      participant inference until board-native logs exist.
- [ ] SNR table audit:
      paper-search thread found a possible 5 dB label mismatch between W23
      receipt labels and the paper table; verify before reusing the table.
- [ ] Terminology audit:
      replace `onboard rotor-noise canceller` style wording with
      `rotor-noise-aware embedded recognizer` unless an explicit enhancement or
      cancellation module is actually implemented.

Main strategic conclusion:

- [x] Strongest full-paper direction:
      `drone-side embedded spoken-intent recognition under rotor noise, with
      conservative policy mediation`.
- [x] Avoid stronger claim:
      do not frame current evidence as flight-safety validation, proven risk
      reduction, or formal runtime assurance.

Most useful novelty opportunities:

- Physical-condition-aware evaluation:
  SNR, distance, speech volume, rotor state, microphone placement, and
  drone/propeller variation in one protocol.
- Deployment-matched conservative intent recognition:
  compare within MCU/resource constraints, not against unconstrained cloud ASR.
- Boundary-aware operating curves:
  report emergency recall, unknown false admission, confidence/abstention, and
  latency together instead of only argmax accuracy.

Recommended paper additions / citation targets:

- UAV ego-noise and microphone-array background:
  Wang & Cavallaro 2017; Manamperi et al. 2022; Clayton et al. 2023.
- UAV speech / human-drone interaction:
  KITE / Oneata & Cucu 2019/2021; Tezza & Andujar 2019.
- Noisy speech and KWS:
  FullSubNet 2021, DeepFilterNet 2022, Sato et al. 2021,
  Yang et al. 2023, PCEN 2017.
- TinyML / MCU evaluation:
  TFLM / David et al. 2021; MLPerf Tiny / Banbury et al. 2021.
- Runtime assurance / safety boundary:
  SOTER / Desai et al. 2019; Schierman et al. 2020;
  Mehmood et al. 2022.
- Evaluation / user-study methods:
  DNS Challenge protocol and HRI metrics-methods survey.

Priority ablations / baselines suggested by paper search:

1. Fix evidence/receipt mismatches before adding new claims.
2. Confidence / abstention operating curves and calibration.
3. `unknown` / action-pressure analysis under realistic priors.
4. Log-mel vs PCEN as low-cost frontend robustness comparison.
5. Clean-only vs generic-noise vs rotor-noise vs paired-alignment training.
6. Matched-size TC/BC/DS-CNN int8 baseline and resource table.
7. Raw vs enhancement-preprocessed audio only if we claim noise suppression.
8. Board-native participant replay/logging if participant metrics stay in the
   full paper.

New advisor questions from paper-search receipt:

- Should the full paper center on rotor-noise-aware embedded speech, or on
  policy-gated safety interaction?
- Should `safety layer/boundary` be softened to `policy gate` or
  `mediated intent interface` until flight/HIL safety evidence exists?
- Is microphone placement and physical-condition evaluation more valuable than
  continuing to chase recognizer accuracy?
- Do we need to rerun participant trials with board-native predictions and
  firmware/version receipts?
- Should confidence-threshold operating curves become a required main result?
- What end-to-end response time target is acceptable for emergency interaction?

## Evaluation Framework v0

| Layer | Main Question | Variables | Metrics / Evidence | Immediate Status |
| --- | --- | --- | --- | --- |
| Model quality | Does the recognizer work under drone noise? | clean/noisy, language, intent class | accuracy, macro F1, emergency recall, false positives | existing evidence + needs expansion |
| Rotor noise | How much does propeller/drone noise hurt speech recognition? | drone type, propeller type, rotor on/off, playback noise | SNR, per-class accuracy, degradation curve | high priority next |
| Volume/distance | How far can a user be and still be understood? | speaker volume, distance from drone/mic | success rate vs distance/volume, SNR | protocol first, then test |
| Hardware design | Is the platform a contribution or only a commodity stack? | mic placement, orientation, mounting, size/weight | design rationale, photos/diagrams, repeatability | needs advisor decision |
| Deployment | Can the system run near/on the drone? | onboard compute, streaming/reporting mode | latency, throughput, drop rate, power/size if available | partial evidence exists |
| Multi-platform | Does the setup generalize beyond one drone? | drone model, propeller size/noise profile | accuracy/SNR/runtime by platform | later, after pilot |
| Pilot workflow | Is the experimental procedure valid before formal study? | 2-3 testers, recorded video, full process | qualitative feedback, protocol issues | immediate, short-term |

## Evaluation Agent Receipt (Read-Only)

Receipt time: 2026-07-22.

Scope:

- [x] Read-only evaluation planning completed.
- [x] No experiments started.
- [x] No file edits by evaluation agent.
- [x] No training, server work, firmware changes, or live drone tests.

Returned planning upgrades:

- [x] Acceptance gates added for rotor noise, volume, distance, SNR,
      multi-drone/propeller variation, deployment latency, and pilot video.
- [x] First-pilot protocol defined:
      standardized playback first, one primary setup, small grid, full video,
      one log bundle per run, no threshold tuning during pilot, advisor/Stephen
      review before scaling.
- [x] Reporting boundary defined:
      this supports evaluation readiness and controlled robustness claims, not
      flight safety validation or proof of superiority over existing drone
      safety mechanisms.

Key gate candidates from the evaluation agent:

- Rotor-noise scale-up only if target condition keeps emergency recall `>=0.80`
  and unknown false action `<=0.20`, with same command set and measured SNR.
- Distance supported range should be the farthest tested distance meeting
  emergency recall `>=0.80` and unknown false action `<=0.20`.
- SNR curves are valid only if the same samples are used across bins, no
  clipping artifacts appear, and the SNR method is documented before results.
- Pilot video passes only if it shows setup, microphone placement, prompts,
  output/log behavior, and failures, with logs linked to video segments.

## Hardware / Deployment Agent Receipt (Read-Only)

Receipt time: 2026-07-22.

Scope:

- [x] Read-only hardware contribution audit completed.
- [x] No firmware modification.
- [x] No live drone test.
- [x] No training, server work, or experiment launch.

Bottom-line decision:

- [x] Current setup supports a `drone-side embedded audio prototype` claim.
- [x] Current evidence does not support a strong `custom drone hardware design`
      claim.

Defensible wording:

> We built a drone-side audio prototype using a XIAO ESP32-S3 Sense module
> placed on or near the drone. The module captures one-second 16 kHz audio
> windows in the drone acoustic field, runs local feature extraction and int8
> inference, and reports compact safety-net categories for downstream control
> logic.

Avoid:

- `custom drone hardware`
- `optimized microphone mount`
- `payload-neutral design`
- `vibration-isolated acoustic front end`
- `flight-validated safety system`
- `robust onboard acoustic enclosure`

Claimable components:

- Onboard compute path:
  local capture, logmel feature extraction, int8 TFLM inference, compact
  label/confidence reporting.
- Real-time steady-state pipeline:
  about one inference opportunity per one-second window, not first-window
  subsecond end-to-end latency.
- Rotor-noise exposure as a design/evaluation condition.
- Compact BLE event interface as integration evidence.

Commodity / weak components:

- XIAO ESP32-S3 Sense board and onboard microphone.
- Tello as flight endpoint.
- BLE/USB/SD as commodity transports.
- Tape/strap/ad hoc placement unless documented as a repeatable mount.
- Default Tello takeoff/hover behavior if not measured as controlled height.

Missing evidence:

- Exact microphone orientation.
- Mounting method close-up.
- Size/weight and center-of-mass impact.
- Mic-port exposure to prop wash / rotor noise.
- Hardware comparison against phone/offboard mic, external mic, or alternate
  mounting points.

Minimum photos/diagrams for advisor discussion:

- Full top-down photo of drone with ESP32 mounted.
- Close-up of ESP32 board with microphone port marked.
- Side-view photo showing board height, cable routing, prop clearance, and mic
  direction.
- Ruler/caliper photo for size and scale/weight photo for board + mount.
- Top-view geometry diagram:
  speaker, drone body, rotors, mic location, speech path, rotor-noise paths,
  distance, orientation.
- Mounting diagram/photo:
  tape/strap/bracket, attachment point, and whether the board can shift.
- Compute diagram:
  core 0 capture, core 1 frontend/TFLM/BLE, 3-buffer queue, one label/confidence
  per window.
- Acoustic evidence figure:
  prop-off vs hover rotor-noise waveform or spectrogram at onboard mic.

## Writing Agent Receipt (Read-Only)

Receipt time: 2026-07-22.

Scope:

- [x] Meeting-ready writing bullets completed.
- [x] No paper file edits by writing agent.
- [x] No experiment, model, firmware, or server work.

Reusable report bullets:

- Evaluation should connect algorithm performance, rotor-noise conditions,
  hardware placement, runtime behavior, and repeatable test workflow.
- Rotor/propeller noise should become a first-class experimental axis because
  it distinguishes the work from ordinary speech recognition.
- Controlled playback should precede formal user study because it isolates
  speech content, playback device, volume, distance, and drone/microphone state.
- The IEEE magazine paper remains a readable short artifact; the next systems
  paper should deepen the evidence around rotor-noise robustness, hardware
  setup, controlled test protocol, deployment behavior, and repeatable real-world
  workflow.

Advisor questions added:

- Should rotor/propeller-noise robustness be the central next contribution?
- Which hardware aspects are paper-worthy:
  mic placement, mounting, miniaturization, or onboard compute integration?
- What distance and volume ranges should define the first controlled playback
  study?
- What is the gate before formal user study:
  pilot video, stable logs, or minimum recognition threshold?
- Should multi-drone or multi-propeller testing wait until the single-platform
  protocol is stable?

## Tomorrow Meeting Talking Points

- [ ] We should not run a large user study yet; first freeze the evaluation
      protocol with a 2-3 tester pilot video.
- [ ] The highest-value next experiment axis is rotor/propeller noise, because
      it can connect model performance, hardware design, and drone-specific
      system contribution.
- [ ] Controlled playback should come before informal repeated human speech,
      because it isolates volume/distance/SNR variables.
- [ ] Hardware contribution needs a decision: if current hardware is
      drone-specific enough, we should document miniaturization, mic placement,
      and mounting; if not, present it as a prototype and avoid overclaiming.
- [ ] Multi-drone tests are valuable but should wait until the single-platform
      protocol is stable.

## Questions For Advisor / Stephen

- [ ] Which evaluation axis should define the main contribution:
      rotor-noise robustness, hardware design, or complete deployed workflow?
- [ ] What drone platforms are realistically available for multi-platform tests?
- [ ] What distance and volume ranges are acceptable for the first controlled
      playback study?
- [ ] Should microphone placement be treated as a design contribution or only
      an implementation detail?
- [ ] How many language samples are enough for a first generalization claim?
- [ ] What should be the gate before formal user study:
      successful pilot video, stable logs, or a minimum accuracy threshold?

## This Week / Next Week Timeline

### 2026-07-22 Wed Night

- [x] Convert 2026-07-10 meeting notes into W30 management plan.
- [x] Prepare evaluation framework v0.
- [x] Prepare tomorrow meeting talking points.
- [x] Sync Notion page.
- [ ] Send writing/evaluation prompt to the relevant agents if user approves.

### 2026-07-23 Thu Meeting

- [ ] Present evaluation framework v0.
- [ ] Ask for approval on pilot-video-first strategy.
- [ ] Ask for hardware contribution decision.
- [ ] Ask for controlled playback variable ranges.
- [ ] Confirm whether multi-drone/propeller-noise tests are next priority.

### 2026-07-24 to 2026-07-27

- [ ] Prepare pilot script and standardized audio clips.
- [ ] Prepare logging template.
- [ ] Prepare microphone placement photos/diagrams.
- [ ] Recruit 2-3 pilot testers.
- [ ] Run one small pilot only after protocol is approved.

### 2026-07-28 to 2026-07-30

- [ ] Review pilot video with advisor/Stephen.
- [ ] Revise protocol.
- [ ] Decide formal experiment scope.

## Risks

- Running experiments before the protocol is stable can force repeated data
  collection.
- Hardware contribution may be weak if the current setup is only an
  off-the-shelf assembly; avoid overclaiming until audited.
- Multi-drone testing can expand scope quickly; keep it secondary until the
  first platform protocol is stable.
- SNR/volume/distance metrics need clear measurement definitions; otherwise
  results will be hard to defend.
- Formal user study should wait until pilot workflow and logging are stable.

## Evaluation Redesign From Scratch

Decision on 2026-07-23:

- [x] Temporarily ignore existing evaluation numbers when designing the next
      full-paper evaluation framework.
- [x] Rebuild evaluation from paper claims, not from what results already exist.
- [x] Treat previous W23/W19 results as candidate evidence that must be audited
      later, not as the default backbone of the next systems-paper story.

### Claim-Driven Evaluation Layers

| Layer | Question | Evidence Needed | Notes |
| --- | --- | --- | --- |
| Physical acoustic operating range | Under what rotor-noise, volume, distance, and microphone-placement conditions can drone-side speech be used? | controlled playback grid, measured SNR/SPL if possible, rotor on/off, distance curve, clipping rate | This should be the first real evaluation layer because it makes the drone setting concrete. |
| Recognition robustness | How does the recognizer behave under drone-specific noise and across speech variation? | per-intent accuracy, emergency recall, unknown false admission, confidence distribution, language/speaker breakdown | Accuracy alone is not enough; unknown false admission and emergency miss rate matter more. |
| Embedded event generation | Can the onboard system produce stable events in a repeatable runtime path? | board-native logs, latency p50/p95/p99, drop rate, event completeness, firmware/model hash | Must distinguish desktop re-inference from board-native prediction. |
| Safety-net mediation | What does the downstream policy gate do with speech-derived events? | reject/unknown handling, confidence threshold curve, action-pressure simulation, no-unknown ablation | This is not flight safety validation; it shows why direct mapping is risky. |
| Protocol repeatability | Can the experiment be repeated by another person without ad hoc retuning? | fixed prompt list, playback files, setup photos, metadata template, pilot video | This should gate formal user study and multi-drone expansion. |

### Recommended Immediate Priority

- [ ] First freeze a controlled playback protocol with metadata fields:
      language, prompt_id, intended_class, speaker/source, volume setting,
      measured SPL if available, distance, rotor state, drone/platform,
      propeller type, mic placement, model/firmware hash, prediction,
      confidence, latency, and notes.
- [ ] Then run a tiny pilot only to validate logs and workflow.
- [ ] Only after that decide whether to reuse, rerun, or discard existing W23
      user-study / ASR / safety-ablation numbers.
- [ ] Do not start full user study or cross-language training until mapping,
      labels, and evidence boundaries are approved.

## Cross-Language Dataset And Mapping Plan

Purpose:

- Cross-language should be framed as a generalization/evaluation axis, not as
  the main proof of safety.
- The core question is whether the drone-side speech interface can preserve the
  same `emergency / movement / unknown` event contract across languages under
  rotor noise.
- The first milestone should be a small, auditable dataset-selection and
  mapping protocol, not immediate model training.

### Candidate Dataset Pool

| Dataset | Role | Why Useful | Main Limitation | Initial Decision |
| --- | --- | --- | --- | --- |
| MLCommons Multilingual Spoken Words Corpus (MSWC) | keyword-level cross-language command/evaluation pool | 1-second spoken-word examples in many languages; close to current speech-command input length | isolated words only; command semantics must be manually mapped | first choice for keyword-level multilingual evaluation |
| Mozilla Common Voice | sentence/phrase-level multilingual speech pool | broad language and speaker coverage; transcripts available; CC0 releases | clips are variable length and not command-specific; requires transcript filtering | good for phrase/unknown/background speech and language diversity |
| FLEURS | controlled multilingual ASR/representation reference | 102-language parallel speech benchmark; useful for language coverage and non-command speech | not a command/intent dataset; weak match to drone control semantics | use as auxiliary unknown/general speech or language-robustness reference |
| MInDS-14 | multilingual spoken intent benchmark | true spoken intent labels across 14 language varieties | banking-domain intents do not map naturally to drone emergency/movement | useful as related-work/method sanity, not main drone evaluation |
| CoVoST / CVSS / MASSIVE-style resources | translation or text-intent resources | useful for multilingual phrase design and translation checks | not directly aligned with 1-second onboard spoken command evaluation | support prompt design, not primary audio evaluation |
| Existing W14 Quechua/Polish strict benchmark | local legacy emergency/normal reference | already packaged with strict rows and gloss mapping | MT-derived glosses, acted/domain-shifted speech, not current 3-class contract | audit only; do not reuse as main claim without revalidation |

### Mapping Strategy

Use a three-level mapping rule before any model or evaluation run:

1. Lexical command mapping:
   - `emergency`: words/phrases equivalent to stop, emergency, help, abort,
     land-now, danger.
   - `movement`: words/phrases equivalent to go, move, up, down, left, right,
     forward, follow, take off, return.
   - `unknown`: non-command words or ordinary speech that should not request
     drone action.
   - Every selected item needs language, source text, English gloss, mapping
     rationale, and reviewer/native-speaker check status.

2. Semantic prompt mapping:
   - Build a small canonical prompt table in English, then translate/back-translate
     into selected languages.
   - Keep one prompt id across languages so results can be compared by semantic
     intent, not only by word identity.
   - Use this for controlled playback and later human recording.

3. Rejection/unknown mapping:
   - Unknown must be deliberately sampled, not treated as leftover noise.
   - Unknown should include non-command words, unrelated speech, and possibly
     command-like but unsupported phrases.
   - Report unknown false admission per language.

### First-Batch Language Selection Rule

Start with 3-5 languages only. Recommended decision rule:

- [ ] At least one language with high public-data availability.
- [ ] At least one language we can get native-speaker or fluent-speaker review for.
- [ ] At least one non-English language with command words available in MSWC or
      transcript-filterable Common Voice clips.
- [ ] Do not include a language if emergency/movement/unknown mapping cannot be
      audited.

Candidate first batch for discussion:

- English: anchor and compatibility with current dataset.
- Spanish or French: strong public speech-data availability and easier review.
- Mandarin Chinese: important application language if native-speaker review is
  available, but public 1-second command coverage must be checked.
- German or Polish: useful if MSWC/Common Voice coverage and command mapping are
  easier than Chinese.

### Cross-Language Experiment Design Options

| Option | What It Tests | Cost | When To Use |
| --- | --- | --- | --- |
| Zero-shot English-to-X | train/design on English, evaluate selected non-English command words/phrases | medium | only if the model/interface is intended to claim language generalization |
| Multilingual pooled evaluation | train/evaluate with balanced samples across languages | medium-high | if the paper wants a multilingual recognizer claim |
| Few-shot language adaptation | add a small number of target-language samples | medium | if zero-shot is weak but cross-language deployment remains important |
| Controlled multilingual playback | same prompt semantics, recorded or played back in each language under rotor noise | low-medium | best first experiment because variables can be controlled |
| Public-data-only benchmark | use MSWC/Common Voice/FLEURS without new recordings | low-medium | useful for planning and offline robustness, but weaker for drone realism |

### Cross-Language Go/No-Go Gate

- GO only if:
  - license is usable;
  - audio is accessible and can be converted to 16 kHz / 1 s or a documented
    windowing rule;
  - each class has enough samples after filtering;
  - mapping is auditable at the word/prompt level;
  - unknown class is explicitly constructed;
  - rotor-noise mixing/evaluation protocol is identical across languages.
- NO-GO if:
  - mapping depends only on machine translation without human/sample audit;
  - classes are imbalanced beyond repair;
  - the dataset domain is too far from commands and cannot support the claim;
  - language coverage is chosen for convenience but cannot answer a paper claim.

## Commands / Prompts To Dispatch

### Evaluation Agent Prompt

You are the Drone project's evaluation-planning agent. Do not run experiments
yet. Read the 2026w30 management plan and propose a concrete evaluation
framework for the next-stage drone speech safety-net work. Focus on metrics,
variables, controls, and acceptance criteria for rotor noise, speech volume,
distance, SNR, multi-drone/propeller variation, deployment latency, and a
2-3 tester pilot video. Return a one-page matrix and a minimal first-pilot
protocol. Do not start user study or model training.

### Hardware / Deployment Agent Prompt

You are the Drone project's hardware/deployment planning agent. Do not modify
firmware or run live drone tests. Audit the current hardware setup conceptually:
microphone placement, orientation, mounting, size/weight, onboard compute, and
rotor/propeller noise exposure. Decide what could be claimed as drone-specific
hardware design versus commodity assembly. Return a hardware contribution memo
and the minimum photos/diagrams needed for tomorrow's meeting.

### Writing Agent Prompt

You are the Drone project's writing support agent. Do not rewrite the current
paper wholesale. Based on the 2026-07-10 meeting, prepare short text bullets for
the next-stage paper/evaluation plan: why evaluation matters, why rotor noise
and hardware setup are central, why controlled playback is needed before formal
user study, and how the IEEE magazine paper transitions into a stronger systems
paper. Keep wording conservative and meeting-ready.
