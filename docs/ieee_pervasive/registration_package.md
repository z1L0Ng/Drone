# IEEE Pervasive Registration Package

Target: IEEE Pervasive Computing special issue on Embodied Pervasive Computing.

CFP constraints checked on 2026-06-30 from the IEEE Computer Society CFP page:

- Title and abstract due: 2026-07-01.
- Full manuscript due: 2026-07-08.
- Publication window: Apr-Jun 2027.
- CFP fit: theoretical foundations, system architectures, and real-world deployments of embodied pervasive computing and pervasive agents.
- Topic fit for this article: embodied systems that sense and act in the physical world, edge intelligence, robotics, human oversight, safe and socially aware operation, and real-world deployment lessons.

Local scaffold checked:

- `docs/ieee_pervasive/main.tex`
- `docs/ieee_pervasive/sections/1introduction.tex`
- `docs/ieee_pervasive/sections/2system.tex`
- `docs/ieee_pervasive/sections/3demo.tex`
- `docs/ieee_pervasive/sections/4realworld.tex`
- `docs/ieee_pervasive/sections/5conclusion.tex`

## Title Options

1. Drone-Side Speech Intent Recognition for Embodied Pervasive Interaction
2. Toward On-Device Speech-to-Intent Interfaces for Small Drones
3. A Lightweight Speech-to-Intent Layer for Human-Drone Interaction

Preferred registration title: Drone-Side Speech Intent Recognition for Embodied Pervasive Interaction.

## Abstract

Small drones increasingly operate near people in labs, classrooms, inspection sites, and other shared spaces where hands-free communication can be more natural than phone apps, controllers, or cloud services. Yet speech around a drone is not the same as speech to a smart speaker: the vehicle is an embodied system with onboard noise, constrained compute, and physical consequences after interpretation. This article frames drone-side speech-to-intent recognition as a lightweight interface for embodied pervasive interaction. Instead of treating nearby utterances as open-ended transcripts or direct flight commands, the proposed layer converts short speech windows into compact intent categories that can be recognized close to the vehicle and exposed to future application logic as structured events. We describe the motivation for on-device intent recognition, outline a prototype path using an embedded microphone and microcontroller-class inference pipeline, and summarize basic feasibility evidence from rotor-noisy recognition, embedded runtime, and contrast with transcript-first ASR. The goal is not to claim complete autonomous control or safety validation, but to show why a constrained speech intent layer is a practical first step toward richer, more accountable voice interaction with embodied drones.

Word count: 185.

## Keywords

- Embodied pervasive computing
- Human-drone interaction
- On-device speech recognition
- Spoken intent recognition
- Edge intelligence
- UAV interfaces
- Rotor-noisy sensing
- TinyML

## 4-5 Page Magazine-Style Outline

### Page 1: Opening Scenario and Problem

Section: Introduction

Goal: Make the reader see why voice matters for nearby drones, without starting from model architecture.

Content:

- Open with a shared-space scenario: a person near a small drone wants to communicate quickly while hands are busy or a controller/app is unavailable.
- Explain why standard voice interfaces do not transfer directly: rotor noise, short utterances, embedded compute limits, and the physical nature of the drone.
- State the article thesis: a drone-side speech-to-intent layer is a practical, constrained first step for embodied drone interaction.
- Avoid saying the system safely controls drones end to end.

Visual:

- Figure 1: scenario photo or illustration showing a person speaking near a drone and an onboard/near-drone microphone path.

### Page 2: Speech-to-Intent as the Interface

Section: System Frame

Goal: Define the lightweight abstraction in reader-facing terms.

Content:

- Contrast transcript-first ASR, direct command mapping, and compact intent recognition.
- Explain the three-category interface at a high level: emergency, movement, unknown/fallback.
- Frame intent as a structured signal for future application logic, not as a direct command.
- Explain why on-device or drone-side processing matters: proximity to the acoustic environment, reduced network dependence, and local event reporting.
- Keep model details minimal; this is a magazine article, not a recognizer architecture paper.

Visual:

- Figure 2: simple pipeline: microphone/audio window -> on-device speech-to-intent recognizer -> intent event -> logging/future application logic.

### Page 3: Prototype and Demo Evidence

Section: Prototype / Demo

Goal: Show that the interface has been exercised in a concrete drone-side prototype path.

Content:

- Describe the basic setup: ESP32/XIAO-class board or microphone near the drone, 16 kHz one-second audio windows, log-mel frontend, compact full-integer inference, and intent logging.
- Summarize existing feasibility evidence carefully:
  - Board-side local pipeline exists: microphone capture, log-mel frontend, full-integer TFLM inference, USB CDC result reporting.
  - Prior stability evidence shows repeated board-side triggers completing without failures, with roughly 3.1 s trigger-to-result cost in the current ESP32-S3 prototype.
  - Rotor-noisy offline evaluation supports the claim that the intent task remains measurable under added rotor noise, but it is not flight validation.
- Mention ASR contrast only as motivation: transcript-first ASR can be brittle on short rotor-noisy clips and is not MCU deployable in the same way.

Visual/table:

- Figure 3: real setup photo or labeled setup diagram: drone, microphone/ESP32, host/logging path.
- Table 1: compact feasibility summary with rows for rotor-noisy recognition, embedded runtime, and ASR contrast.

### Page 4: Applications, Lessons, and Boundaries

Section: Real-World Applications and Vision

Goal: Connect the prototype to the special issue theme of embodied pervasive systems.

Content:

- Application settings: labs, classrooms, warehouses, inspection sites, and field-support contexts where drones work near people.
- Design lesson 1: embodied voice interfaces should prefer constrained intent events before richer language or action policies.
- Design lesson 2: local acoustic context matters because the drone itself changes the sensing environment.
- Design lesson 3: unknown/fallback is part of the interface, not an afterthought.
- Brief safety-net concept: future systems can use intent events as inputs to a safety net or application policy, but this article does not present a complete safety-state/control-loop mechanism.

Optional visual:

- Small inset only if space permits: intent events feeding future oversight/application logic. Keep it conceptual and short.

### Page 5: Limitations and Future Work

Section: Limitations and Future Work

Goal: Preserve future systems-paper novelty while still ending with a concrete research direction.

Content:

- Current scope: speech-to-intent recognition and prototype feasibility, not full flight-control validation.
- Limited intent space: the three-category interface is intentionally small and should expand only with stronger interaction evidence.
- Deployment limits: microphone placement, real rotor conditions, distance, speaker variability, and continuous interaction need broader study.
- Safety future work: future drone systems should connect intent events to explicit oversight, confidence handling, and action policies, but those mechanisms are outside this short article.
- Closing message: on-device speech-to-intent recognition is a practical entry point for embodied pervasive drone interaction because it keeps voice local, constrained, and inspectable.

## Overclaim Checks

Use:

- "speech-to-intent layer"
- "drone-side voice interface"
- "basic feasibility evidence"
- "prototype path"
- "future safety net"
- "structured intent event"

Avoid:

- "safe autonomous drone control"
- "validated safety mechanism"
- "complete control loop"
- "robust to all rotor noise"
- "general natural-language drone command"
- "Akouo system contribution" unless the full long-form systems paper is intentionally reopened.

## Registration Recommendation

Register with title option 1 unless the author team wants a softer "Toward" title. The abstract is already within the requested 150-250 word range and keeps the article centered on embodied drone interaction without exposing detailed safety-state or action-policy novelty.
