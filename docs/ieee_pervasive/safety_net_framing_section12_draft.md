# Safety-Net Framing and First-Section Draft

Date: 2026-06-30

Purpose: advisory draft for the IEEE Pervasive Computing article. This does not replace the Overleaf source. It updates the earlier speech-to-intent framing after the meeting decision that `safety net` can remain the core paper idea, while audio intent recognition becomes one component inside that safety net.

## Core Framing

The article should not be framed as:

- a speech recognition paper for drones;
- a demo paper;
- a compressed version of the long Akouo/SenSys safety-state/control-loop paper;
- a claim that the current prototype fully validates autonomous safe flight.

The article should be framed as:

- a magazine-style article about a `safety net` for embodied drone interaction;
- a system-facing argument that speech around an embodied drone should not become direct action;
- an instantiation of the first sensing component of that safety net: drone-side audio intent recognition under rotor noise;
- a readable bridge between ubiquitous/embodied computing and practical drone interaction.

One-sentence thesis:

> Small drones need a safety net between nearby human speech and vehicle-facing behavior; drone-side audio intent recognition is a practical first component of that safety net because it turns noisy, ambiguous speech into bounded events that can be logged, inspected, and later mediated before action.

## What "Safety Net" Means Here

Use `safety net` as a high-level paper-facing concept, not as a detailed control-policy disclosure.

Definition for this article:

> A safety net is an intermediate layer that keeps human input to an embodied drone bounded, inspectable, and deferrable before it can influence physical behavior.

In this article, the safety net has three visible parts:

1. Sensing input: nearby speech is captured near the drone.
2. Intent event: the audio layer maps short speech windows into a small set of intent states, such as emergency, movement, and unknown.
3. Mediation point: those intent events are logged and exposed to future policy or operator logic, rather than being treated as immediate flight commands.

Keep hidden or future-facing:

- detailed safety-state machine;
- admission-control policy;
- action-selection logic;
- repeated live-flight validation;
- broad multilingual or long-horizon interaction mechanisms.

## Revised Section Structure

Recommended 4-5 page magazine structure:

1. `Introduction`
   - Problem: drones are embodied physical systems, so speech near them is different from speech to a phone or smart speaker.
   - Thesis: we need a safety net between speech and behavior.
   - Component: audio intent recognition is the first practical piece.

2. `A Safety Net for Spoken Drone Interaction`
   - Define safety net.
   - Explain why direct speech-to-command is too strong.
   - Explain why compact intent events are a better interface.
   - Place the audio component inside the safety net.

3. Rename current `Demo`
   - Current name `Demo` is too weak and makes the article sound like a project demonstration.
   - Better options:
     - `Prototype and Feasibility Evidence`
     - `An Embodied Prototype`
     - `Building the First Audio Layer`
     - `From Speech to Intent Events on a Drone`
   - Recommended: `Prototype and Feasibility Evidence`
   - Reason: it lets us discuss setup, rotor-noise evidence, embedded runtime, and ASR contrast without claiming full deployment or safety validation.

4. `Applications and Design Lessons`
   - Shared-space drone interaction.
   - Why local sensing and bounded intent matter.
   - Lessons for embodied pervasive systems.

5. `Limitations and Future Work`
   - Safety net is a framing and first-step prototype, not complete safety certification.
   - Future work: richer policy, continuous interaction, microphone placement, larger deployment, multilingual interaction, stronger safety evaluation.

## Updated Abstract Draft

Small drones increasingly operate near people in laboratories, classrooms, inspection sites, and other shared spaces. Voice is a natural way for nearby people to communicate with such systems, but speech around a drone is not the same as speech to a phone or smart speaker: the drone is an embodied system with rotor noise, limited onboard computation, and physical consequences after interpretation. This article argues that embodied drone interaction needs a safety net between nearby speech and vehicle-facing behavior. We frame this safety net as an intermediate layer that keeps human input bounded, inspectable, and deferrable before it can influence action. As a first component, we study drone-side audio intent recognition, which converts short speech windows into compact intent events such as emergency, movement, and unknown rather than open-ended transcripts or direct commands. We outline a prototype path using an embedded microphone and microcontroller-class inference pipeline, and summarize basic feasibility evidence from rotor-noisy recognition, embedded runtime, and contrast with transcript-first ASR. The goal is not to claim complete flight-control validation, but to show how a constrained audio intent layer can provide a practical foundation for safer and more accountable voice interaction with embodied drones.

Word count: 194.

## Section 1 Draft: Introduction

Small drones are moving from isolated flight demonstrations into spaces where people work, learn, and move around them. In a lab, a classroom, a warehouse aisle, or an inspection site, the person closest to a drone may not be holding a controller. They may need to warn the drone, redirect attention, or communicate a simple intent while their hands and eyes are occupied. Voice is therefore an appealing interface: it is fast, natural, and already used by people to coordinate activity in shared physical spaces.

But voice near a drone is not the same interface as voice to a phone, a smart speaker, or a cloud assistant. A drone is an embodied system. It produces its own acoustic noise, senses from a moving physical platform, and may eventually connect perception to behavior in the real world. This makes direct speech-to-command mappings risky and incomplete as a design pattern. A misheard phrase, background conversation, or uncertain transcript should not become a vehicle-facing action simply because an audio model produced text or a keyword.

This article argues for a safety net between nearby human speech and embodied drone behavior. By safety net, we mean an intermediate layer that keeps speech-derived input bounded, inspectable, and deferrable before it can influence physical behavior. The safety net does not require the first prototype to solve full autonomy or complete flight safety. Instead, it asks a narrower systems question: what should a drone expose from nearby speech so that later policies, operators, or applications can reason about it responsibly?

Our answer starts with audio intent recognition. Rather than transcribing arbitrary speech or mapping words directly to commands, the drone-side audio layer converts short speech windows into compact intent events, such as emergency, movement, or unknown. These events are intentionally limited. They are easier to inspect, easier to log, and better aligned with future mediation than open-ended transcripts. They also reflect the acoustic reality of small drones, where rotor noise and embedded computation constrain what can be recognized reliably near the vehicle.

We present this direction as a lightweight embodied pervasive computing article, not as a complete drone-control system. The contribution is the framing and first prototype step: a speech-aware safety net in which drone-side audio intent recognition provides bounded events for future interaction logic. We discuss why this framing matters, how the first audio layer can be built on embedded hardware, and what current feasibility evidence can and cannot support.

### Section 1 goals

- Establish the human-drone interaction scenario.
- Make `safety net` the core paper idea.
- Explain why audio intent is a component, not the whole paper.
- Set a conservative claim boundary: no full autonomous control or complete safety validation.

### Section 1 figure placeholder

Figure 1: a person speaks near a drone in a shared space; speech enters a safety-net layer before any vehicle-facing behavior. The visual should show the safety net as a mediation layer, not as a direct command arrow.

## Section 2 Draft: A Safety Net for Spoken Drone Interaction

The central design choice is to avoid treating speech as a direct command channel. In everyday conversation, people speak casually, repeat themselves, hesitate, and talk to others nearby. Around a drone, this ambiguity is amplified by rotor noise, distance, microphone placement, and the limited compute budget of onboard devices. A direct speech-to-command interface hides these uncertainties behind a simple action mapping. For embodied systems, that mapping is too strong.

A safety-net interface changes the role of speech. Instead of asking the audio layer to decide what the drone should do, the audio layer reports what kind of human intent may be present. This distinction is important. An emergency-like utterance, a movement-related utterance, and an unknown or ambiguous sound should have different meanings to the rest of the system, but none of them needs to be treated as an immediate flight command in this article. They are structured events that can be logged, inspected, confirmed, ignored, or passed to future policy logic.

This motivates a compact intent vocabulary. The initial interface uses three coarse categories: `emergency`, `movement`, and `unknown`. The emergency class captures urgent stop-like or danger-like speech. The movement class captures speech that may relate to motion or direction. The unknown class is not merely a leftover label; it is part of the safety net because it gives the system a way to represent uncertainty without forcing action. This is deliberately smaller than open-ended natural language understanding. The point is not to cover every possible command, but to create a bounded event interface that is plausible on embedded hardware and meaningful for later mediation.

Running this layer near or on the drone also matters. Drone-side recognition keeps sensing close to the physical acoustic environment, including rotor noise and placement effects. It reduces dependence on networked speech services and lets the system produce local evidence: an audio window, an intent label, confidence, timing, and a log entry. These are the kinds of artifacts a safety net needs before richer policy or operator logic can be added.

In the current prototype path, audio intent recognition is therefore the first implemented component of the safety net. A microphone captures a short speech window near the drone, an embedded pipeline computes acoustic features and predicts an intent event, and the result is reported for logging or future mediation. The prototype stops at this event boundary. That boundary is intentional: it lets the article focus on how speech should enter an embodied drone system without claiming that the present implementation solves the complete action policy.

### Section 2 goals

- Define safety net in concrete system terms.
- Justify why direct speech-to-command is the wrong abstraction.
- Explain the three intent categories as an interface.
- Make `unknown` a positive design element.
- Preserve future novelty by stopping at the event boundary.

### Section 2 figure placeholder

Figure 2: Safety-net architecture. Suggested flow: nearby speech -> audio sensing -> intent recognition -> bounded event (`emergency`, `movement`, `unknown`) -> log / future mediation. Avoid showing a direct arrow from speech to drone action.

## Notes for Later Sections

### Replace `Demo`

Recommended section title:

> Prototype and Feasibility Evidence

Why:

- `Demo` sounds too informal and undersells the article.
- `Evaluation` sounds too strong if evidence is lightweight.
- `Prototype and Feasibility Evidence` supports a magazine-style article and keeps claims scoped.

This section should include:

- physical setup;
- embedded audio pipeline;
- rotor-noisy recognition summary;
- runtime / event reporting feasibility;
- ASR contrast as motivation, not as a broad ASR failure claim.

### Overclaim guardrail

Safe phrasing:

- "first component of a safety net"
- "bounded intent events"
- "future mediation"
- "prototype path"
- "basic feasibility evidence"
- "does not validate complete flight safety"

Avoid:

- "the drone safely executes voice commands"
- "we solve voice-driven UAV safety"
- "audio intent guarantees safe behavior"
- "full safety-state/control-loop design"
- "complete deployment validation"
