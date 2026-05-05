# SenSys 2027 Design-First Draft Outline

This folder is the local working draft for a SenSys 2027 first-round submission. The compiled paper should read as a system-design paper for a drone-side emergency voice safety component, not as a weekly evidence report. Incomplete validation should be tracked with LaTeX source comments until it is ready to appear in the compiled document.

## Format Checklist

- Use `acmart` with `\documentclass[sigconf,anonymous]{acmart}`.
- Keep the paper in ACM two-column `sigconf` format.
- Maintain strict anonymization.
- Treat the body budget as `12` pages for the main paper; references can spill past the limit.
- Do not add custom formatting that shrinks margins, changes font size, or suppresses anonymity cues.

## Core Thesis

A drone-side voice safety component can make small UAVs more interruptible under severe self-noise when it is framed as emergency-oriented intent recognition first, deployment-constrained local event generation second, and conservative control-bridge integration third.

The system architecture is:

`voice input -> log-mel frontend -> emergency intent recognizer -> event guardrail -> embedded inference -> control bridge -> safety event log`

The paper should present this as the intended system contract. Repo evidence is tracked in source comments and used only where the compiled claim is already defensible:

- Main model anchor: `w14 preprocess_ext`, because it is the reproducible noisy-set anchor.
- Deployment candidate: `B_small_teacher_student`, because it is the current small-student TFLM candidate.
- Runtime prototype: XIAO ESP32-S3 local inference over USB CDC.
- Open validation: labeled real-world semantic accuracy, gate false-trigger behavior, and safe control bridge behavior.

## Accepted Claim Map

| Claim | Evidence path | Paper wording |
| --- | --- | --- |
| System architecture is an emergency voice safety component for nearby drones. | System design text in this draft; no single result file needed. | Present as the design contribution and evaluation object. |
| `w14 preprocess_ext` is the main noisy-set anchor. | `weeklyresult/weekly_drone_2026w14/preprocess_ext/classification_report_noisy.txt`; `run_config.json` | Use as the model-quality anchor for the recognizer. |
| `B_small_teacher_student` is the deployment candidate. | `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/*`; `tflm_candidate_precheck.json` | Use as the embedded candidate; do not call it the winner. |
| ESP32 local inference is feasible as a runtime path. | `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_report.md` | Runtime stability and latency evidence only. |
| Track B is dry-run control plumbing. | `weeklyresult/weekly_drone_2026w18/realworld/tello_dryrun/20260504_local_cdc_replay_report.md` | Dry command dispatch only; no flight evidence. |
| Track A is preliminary gate/buffer feasibility. | `docs/weekly_todo/2026/2026w18/todo.md`; `weeklyresult/weekly_drone_2026w18/realworld/gate_buffer_e2e/*` | Meeting discussion only; not a validated safety mechanism. |

## Section Plan

1. `Introduction`
   State the systems problem and emergency-interruption design. Avoid opening with evidence staging. End with design-first contributions.

2. `Background and Motivation`
   Motivate rotor self-noise and emergency-oriented narrow intent recognition. Cross-language and cross-platform material belongs only as future context.

3. `System Architecture`
   Present the full architecture: voice input, emergency intent recognizer, event guardrail, embedded inference, control bridge, and safety event logging.

4. `Emergency Intent Recognizer`
   Define the recognizer contract, explain the high-level model architecture, name `w14 preprocess_ext` as the anchor, and keep `B_small_teacher_student` as the deployment candidate.

5. `Prototype and Real-World Setup`
   Describe how the prototype instantiates the architecture on XIAO ESP32-S3. Keep incomplete bridge and acoustic validation as source TODOs until evidence is ready.

6. `Evaluation`
   Separate existing evidence, missing evidence, and planned validation. Keep the evidence table, but do not let it drive the paper narrative.

7. `Related Work`
   Keep UAV speech interfaces, direct spoken intent modeling, robust transfer, and embedded deployment constraints separate.

8. `Conclusion`
   End with the system idea and next validation steps, not a weekly-progress summary.

## Non-Claims

- Do not claim labeled real-world semantic accuracy for ESP32 runtime logs.
- Do not treat `B_small_teacher_student` as a mainline winner over `w14 preprocess_ext`.
- Do not write Track B dry-run as flight or live drone-control evidence.
- Do not write Track A gate/buffer as a validated safety mechanism.
- Do not present cross-language or cross-platform generalization as a completed contribution.

## Figure/Table Plan

- System architecture figure: voice input -> log-mel frontend -> emergency intent recognizer -> event guardrail -> control bridge -> safety event log.
- Recognizer architecture figure: w14 anchor recognizer and B_small deployed student as compact blocks, not a full Keras layer list.
- Prototype dataflow figure: XIAO microphone -> audio window -> log-mel features -> int8 TFLM inference -> USB CDC event -> bridge record.
- Recognizer design table: three-way intent contract and reject behavior.
- Deployment candidate table: w14 anchor vs B_small deployment candidate.
- Runtime table: ESP32 local event path success/drop/timing summary.
- Validation matrix: existing evidence, missing evidence, and planned validation for recognizer, runtime, control bridge, and gate/buffer.
- Control-log schema table: predicted label, confidence, latency, state transition, command selection, send event, ack/timeout.

## Thursday 2026-05-07 Meeting Questions

- Should the paper use the phrase "voice safety component" or the more conservative "safety-oriented interrupt interface"?
- Is current ESP32 inference latency acceptable for an interrupt/hold interface, or should emergency handling require a faster pre-gate?
- What evidence is required for first-round submission: live dry-run, no-prop bench, or low-risk flight?
- Should Track A appear in the paper at all, or stay as meeting-only feasibility material until false triggers are controlled?
- Should all multi-platform wording be removed until another drone platform is tested?
- Where should we cite prior evidence that emergency speech can differ in pitch or vocal intensity from neutral commands, if we use that motivation outside Section 4?
