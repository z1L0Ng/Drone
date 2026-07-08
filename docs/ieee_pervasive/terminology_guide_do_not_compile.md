# Terminology Guide for the IEEE Pervasive Draft

This file is a writing guide only. It is not included by `main.tex` and should not be compiled in Overleaf.

## Length Target

Target body length: about 4000 words, excluding title, abstract, keywords, references, figure captions, and tables.

Current local body estimate from the five section files: about 2700 words.

Suggested final allocation:

- Introduction: 600-700 words
- System Frame: 750-850 words
- Implementation and Evaluation: 850-950 words
- Real-World Applications and Vision: 900-1000 words
- Limitations and Future Work: 700-800 words

The main expansion should come from `Real-World Applications and Vision`, `System Frame`, and `Limitations and Future Work`. Avoid expanding the paper by adding low-level model or firmware details, because this article should remain magazine-style rather than becoming a shortened SenSys-style systems paper.

## Core Framing Sentence

Preferred high-level framing:

> Spoken drone interaction should follow a three-part path: speech, speech-to-text or speech processing, and a safety net before any drone-facing behavior.

This is the central design frame for the article. It lets us discuss speech interfaces for drones without claiming that the current prototype solves full intent understanding or complete drone safety.

## Term Glossary

### Drone / UAV

Meaning: The physical aerial robot platform. On first mention in the full manuscript, use `Unmanned Aerial Vehicles (UAVs, or drones)`. After that, use `drone` or `drones`.

Use when: Referring to the concrete platform, local sensing, rotor noise, microphone placement, or physical operation.

Avoid: Repeating `UAV` throughout the article or switching to `aerial agent`. Also avoid treating `drone` as only a software agent. The point of the article is that it is a physical system sharing space with people.

### Aerial agent

Meaning: Do not use this as a manuscript label. Use `drone` instead.

Use when: Only in internal notes if discussing why a previous title or draft used this wording.

Avoid: `aerial agent`, `aerial agents`, and `embodied aerial agent(s)` in the manuscript.

### Spoken drone interaction

Meaning: Interaction in which a nearby person uses speech as an input channel around a drone.

Use when: Describing the application problem at article level.

Avoid: Equating spoken interaction with direct voice command. The article argues against treating speech as immediate command by default.

### Nearby speech

Meaning: Speech produced in the same physical space as the drone. It may be directed at the drone, near the drone, or simply present in the shared environment.

Use when: Emphasizing ambiguity, bystander speech, rotor noise, and shared-space interaction.

Avoid: Assuming every utterance is addressed to the drone.

### Speech

Meaning: The human audio input before software interpretation.

Use when: Discussing the start of the pipeline.

Avoid: Treating speech itself as a command or intent. Speech is raw human input in a noisy physical setting.

### Speech-to-text

Meaning: A front-end option that converts speech into a transcript.

Use when: Comparing possible speech front ends or explaining why a transcript-first interface can be fragile under short, noisy drone audio.

Avoid: Making speech-to-text the only possible front end. The article's framework allows either speech-to-text or direct speech processing.

### Speech processing

Meaning: A broader front-end term for extracting a useful speech-derived signal from audio. This can include keyword recognition, command recognition, emergency-speech detection, or compact category output.

Use when: Referring to the current prototype and the broader pipeline without claiming full intent recognition.

Avoid: Calling the current prototype `intent recognition` as the main contribution. Stronger intent recognition is future work.

### Speech front end

Meaning: The module that receives audio and produces the first software output: transcript, keyword, category, or other speech-derived signal.

Use when: Explaining that the safety net starts after speech has been processed.

Avoid: Describing the front end as the safety net itself. The front end produces input to the safety net.

### Speech-derived signal

Meaning: The output of the speech front end. It may be a transcript, keyword, category, score, or compact label.

Use when: Keeping the framework general across speech-to-text and direct speech-processing designs.

Avoid: Treating the signal as already safe, correct, or action-ready.

### Safety net

Meaning: The article's central concept. A safety net is the design boundary between speech-derived output and drone-facing behavior. It prevents speech output from being treated as immediate vehicle behavior.

Use when: Arguing why spoken drone interaction needs extra care compared with phones, smart speakers, or cloud assistants.

Avoid: Defining it as a complete safety controller, full control loop, or formal safety proof. The current paper does not validate complete safety.

### Drone interaction stack

Meaning: The later software/human-facing system that may use speech-derived information. This may include operator display, awareness, confirmation, task logic, or future policy logic.

Use when: Referring to what comes after the safety net in high-level diagrams.

Avoid: Giving detailed control-loop or safety-state design. That novelty should be reserved for future systems papers.

### Drone-facing behavior / vehicle-facing behavior

Meaning: Any downstream behavior that could matter to the drone as a physical system, such as movement, task state, operator alerting, or later autonomy decisions.

Use when: Explaining why speech should not be treated as an immediate command.

Avoid: Overusing this phrase in every paragraph. Use it where the physical consequence matters.

### Safety-net category

Meaning: The compact category produced by the current prototype for the safety-net framing: `emergency`, `movement`, or `unknown`.

Use when: Describing the prototype output in Section 3.

Avoid: Calling these categories complete intents. They are simple speech-processing outputs for the magazine article's safety-net demonstration.

### Emergency

Meaning: Speech that may indicate danger, interruption, stop, or urgent need around the drone.

Use when: Explaining the central safety motivation.

Avoid: Claiming that emergency detection alone makes drone behavior safe.

### Movement

Meaning: Speech that may relate to ordinary drone movement or direction.

Use when: Showing that the prototype separates urgent speech from ordinary movement-related speech.

Avoid: Presenting movement as a direct flight command. It is a category before later safety handling.

### Unknown

Meaning: Speech or sound that should not be treated as emergency or movement-related speech.

Use when: Explaining that unsupported input should not be forced into drone-relevant meaning.

Avoid: Making `unknown` the conceptual center of the paper. The safety argument should stay centered on emergency-related speech and safe handling of speech-derived outputs.

### Emergency-related speech

Meaning: A safer prose term than `emergency intent` for the current article.

Use when: Talking about the current prototype and evaluation.

Avoid: Replacing every instance with `intent`. Use `intent recognition` only as future work.

### Movement-related speech

Meaning: Speech that appears related to movement, direction, or ordinary drone motion.

Use when: Describing the category in a way that avoids direct-command framing.

Avoid: Saying that the drone executes movement from this category.

### Unsupported input

Meaning: Input that the speech-processing module should not treat as either emergency-related or movement-related speech.

Use when: Explaining why the system should not force uncertain speech into action-oriented meaning.

Avoid: Overclaiming robustness. `Unsupported` is a design category, not proof that all ambiguous speech is handled correctly.

### On-device / onboard / local processing

Meaning: Speech processing that runs on or near the drone rather than depending on a phone, cloud service, or network connection.

Use when: Explaining real-time interaction, network independence, and acoustic proximity to the drone.

Avoid: Claiming privacy, security, or safety benefits beyond what is supported. Local processing helps the first speech step happen near the drone, but it is not complete system safety.

### Rotor-noisy conditions

Meaning: Acoustic conditions shaped by drone rotor noise, often represented in evaluation by different SNR levels.

Use when: Discussing why spoken drone interaction is harder than speech to a phone or smart speaker.

Avoid: Treating the tested SNR conditions as exhaustive real-world validation.

### Microphone placement

Meaning: Where the microphone is placed relative to the drone, speaker, rotor noise, and surrounding environment.

Use when: Discussing the microphone-placement schematic and limitations.

Avoid: Assuming placement is a solved detail. It should be part of future deployment study.

### Real-time

Meaning: The local pipeline can process one-second audio windows at approximately the pace needed for the prototype interaction.

Use when: Reporting the embedded timing result.

Avoid: Claiming hard real-time control guarantees. The prototype timing supports first-step speech processing, not full flight-control validation.

### Context-aware safety policy

Meaning: Future logic that interprets speech-derived signals differently depending on drone state, environment, task, proximity to people, battery, or operating area.

Use when: Writing Limitations and Future Work.

Avoid: Describing this as implemented in the current prototype.

### Multimodal sensing

Meaning: Future use of audio together with visual cues, gesture, localization, flight state, or environmental sensing.

Use when: Explaining why speech alone may not be enough in real deployments.

Avoid: Claiming current multimodal validation.

### Full control-loop validation

Meaning: Future testing of how speech-derived safety signals interact with planning, control, fail-safe behavior, and human oversight across complete drone missions.

Use when: Stating limitations.

Avoid: Claiming the current article has performed this validation.

### Stronger intent recognition

Meaning: Future conference-level work on richer semantic parsing or intent vocabularies beyond the current safety-net categories.

Use when: Naming future work clearly.

Avoid: Making it the current magazine article's core contribution.

## Terms to Prefer

- `safety net`
- `speech front end`
- `speech-to-text or speech processing`
- `speech-derived signal`
- `emergency-related speech`
- `movement-related speech`
- `unsupported input`
- `drone-side speech processing`
- `local / onboard processing`
- `drone`

## Terms to Avoid or Use Only Carefully

- `intent-aware safety net`: too close to the earlier title and makes the article intent-heavy.
- `speech-to-intent`: reserve for future technical work.
- `intent event`: too systems-paper-like for this magazine framing.
- `bounded intent`: too abstract and may sound like an algorithmic claim.
- `safety layer`: avoid because `safety net` is the chosen concept.
- `mediation`: use sparingly; it implies later logic we have not implemented.
- `control loop`: use only in future-work limitations.
- `safety-state`: do not use in this magazine article.
- `complete safety`: only use in negated limitation statements.

## Recommended Figure Terminology

High-level framework:

`Nearby speech` -> `Speech-to-text / speech processing` -> `Safety net` -> `Drone interaction stack`

Module-level prototype:

`Nearby speaker` -> `Microphone capture` -> `Feature preprocessing` -> `On-device speech module` -> `Safety-net category`

Microphone placement:

`Nearby speaker`, `Drone`, `Onboard / near-drone microphone`, `Rotor noise`, `Speech path`, `Distance and angle`

## One-Sentence Boundary for the Paper

This article frames spoken drone interaction around a safety net between speech processing and drone-facing behavior, and uses an onboard speech-processing prototype to make that framing concrete without claiming complete safety validation or full intent understanding.
