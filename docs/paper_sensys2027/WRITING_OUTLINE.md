# SenSys 2027 Design-First Draft Outline

This folder is the local working draft for a SenSys 2027 first-round submission. The compiled paper should read as a system-design paper for a voice-driven UAV safety interaction mechanism under rotor noise, with intent recognition as the mechanism that converts voice into auditable intent/state events. It should not read as generic speech classification, noisy keyword spotting, ASR, an emergency-only safety interface, or a weekly evidence report. Incomplete validation should be tracked with LaTeX source comments until it is ready to appear in the compiled document.

## Format Checklist

- Use `acmart` with `\documentclass[sigconf,anonymous]{acmart}`.
- Keep the paper in ACM two-column `sigconf` format.
- Maintain strict anonymization.
- Treat the body budget as `12` pages for the main paper; references can spill past the limit.
- Do not add custom formatting that shrinks margins, changes font size, or suppresses anonymity cues.

## Core Thesis

A drone-side UAV safety interaction layer can make talking to small UAVs more natural and controllable under severe self-noise when it uses narrow on-device intent-state recognition as the safety mechanism, deployment-constrained local event generation as the runtime path, and a conservative control bridge as the action boundary.

The system architecture is:

`voice input -> log-mel frontend -> on-device intent-state recognizer -> fallback guardrail -> embedded inference -> control bridge -> interaction/state log`

The paper should present this as the intended system contract. Repo evidence is tracked in source comments and used only where the compiled claim is already defensible:

- Main model anchor: `w14 preprocess_ext`, because it is the reproducible noisy-set anchor.
- Deployment candidate: `B_small_teacher_student`, because it is the current small-student TFLM candidate.
- Runtime prototype: XIAO ESP32-S3 local inference over USB CDC.
- Open validation: labeled real-world semantic accuracy, gate false-trigger behavior, and safe control bridge behavior.

## Accepted Claim Map

| Claim | Evidence path | Paper wording |
| --- | --- | --- |
| System architecture is a voice-driven UAV safety interaction layer for nearby drones. | System design text in this draft; no single result file needed. | Present as the design contribution and evaluation object. |
| `w14 preprocess_ext` is the main noisy-set anchor. | `weeklyresult/weekly_drone_2026w14/preprocess_ext/classification_report_noisy.txt`; `run_config.json` | Use as the model-quality anchor for the recognizer. |
| `B_small_teacher_student` is the deployment candidate. | `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/*`; `tflm_candidate_precheck.json` | Use as the embedded candidate; do not call it the winner. |
| ESP32 local inference is feasible as a runtime path. | `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_report.md` | Runtime stability and latency evidence only. |
| Track B is dry-run control plumbing. | `weeklyresult/weekly_drone_2026w18/realworld/tello_dryrun/20260504_local_cdc_replay_report.md` | Dry command dispatch only; no flight evidence. |
| Track A is preliminary gate/buffer feasibility. | `docs/weekly_todo/2026/2026w18/todo.md`; `weeklyresult/weekly_drone_2026w18/realworld/gate_buffer_e2e/*` | Meeting discussion only; not a validated safety mechanism. |

## Section Plan

1. `Introduction`
   State the systems problem and talk-to-the-drone safety interaction design. Avoid opening with evidence staging. End with exactly four contributions: Safety Interaction Layer, Intent-State Modeling, Rotor-Noise Robust On-Device Recognition, and Evaluation and Reproducibility Plan.

2. `Background and Motivation`
   Motivate rotor self-noise and narrow intent-state recognition for voice-driven UAV safety interaction. Cross-language and cross-platform material belongs only as future context.

3. `System Architecture`
   Present the full architecture: voice input, on-device intent-state recognizer, fallback guardrail, embedded inference, control bridge, and interaction/state logging.

4. `On-Device Intent Recognizer`
   Define the recognizer contract, explain the high-level model architecture, name `w14 preprocess_ext` as the anchor, and keep `B_small_teacher_student` as the deployment candidate.

5. `Prototype and Real-World Setup`
   Describe how the prototype instantiates the architecture on XIAO ESP32-S3. Keep incomplete bridge and acoustic validation as source TODOs until evidence is ready.

6. `Evaluation`
   Organize the evaluation as a recognition-to-interaction stack: offline baselines, frontend ablation, noise robustness, embedded deployment comparison, board runtime and quantization fidelity, speaker/distance/language robustness, drone interaction behavior, and artifact-release protocol. Keep missing measurements in LaTeX comments until result files exist.

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

- System architecture figure: voice input -> log-mel frontend -> on-device intent recognizer -> event guardrail -> control bridge -> interaction event log.
- Recognizer architecture figure: w14 anchor recognizer and B_small deployed student as compact blocks, not a full Keras layer list.
- Prototype dataflow figure: XIAO microphone -> audio window -> log-mel features -> int8 TFLM inference -> USB CDC event -> bridge record.
- Offline recognition table: anchor recognizer and verified baseline rows on the same noisy-set split.
- Frontend ablation table: log-mel, MFCC, and other compact representations under matched training/evaluation settings.
- Noise robustness figure: accuracy, emergency F1, movement F1, and unknown false accept rate across SNR or rotor-noise conditions.
- Deployment candidate table: anchor recognizer, embedded student, and compact baselines with TFLite size, operator mix, memory estimate, and compatibility gate.
- Runtime and quantization table: ESP32 success/drop/timing plus float/int8/board output agreement.
- Speaker/distance/language robustness figure: per-condition accuracy, emergency recall, unknown false accepts, and missed-event rate.
- Drone interaction figure: speech input -> ESP32 event -> bridge decision -> command/state log -> drone-side response.
- Control-log schema table: predicted label, confidence, latency, state transition, command selection, send event, ack/timeout.
- Artifact-release checklist: result manifests, run configurations, model/export artifacts, evaluation scripts, and bridge-log schemas that are actually included in the release package.

## Thursday 2026-05-07 Meeting Questions

- Should the paper use "voice interaction layer", "talk-to-the-drone interface", or another publishable system name?
- Is current ESP32 inference latency acceptable for a voice-interaction event source, or should safety-critical intents require a faster pre-gate?
- What evidence is required for first-round submission: live dry-run, no-prop bench, or low-risk flight?
- Should Track A appear in the paper at all, or stay as meeting-only feasibility material until false triggers are controlled?
- Should all multi-platform wording be removed until another drone platform is tested?
- Where should we cite prior evidence that emergency speech can differ in pitch or vocal intensity from neutral commands, if we use that motivation outside Section 4?
