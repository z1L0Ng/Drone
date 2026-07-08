# Figure Text Drafts for July 2 Framing

## Figure A: High-Level Framework

Suggested diagram labels:

`Nearby speech` -> `Speech-to-text / speech processing` -> `Safety net` -> `Drone interaction stack`

Suggested caption:

High-level safety-net framework for spoken drone interaction. Nearby speech is first converted into a transcript, keyword, category, or other speech-derived signal. The safety net sits after this speech front end and before the drone interaction stack, preventing speech output from being treated as immediate vehicle behavior.

Suggested body text:

Figure A summarizes the article's main framing. Speech is useful because it is fast and hands-free, but it should not directly become drone behavior. The first module may be speech-to-text, keyword recognition, or a direct speech-processing model. The safety net receives that output and keeps the first speech-derived signal separate from later drone-facing decisions.

## Figure B: Module-Level Prototype Pipeline

Suggested diagram labels:

`Nearby speaker` -> `Microphone capture` -> `Feature preprocessing` -> `On-device speech module` -> `Safety-net category`

Output labels:

`Emergency`, `Movement`, `Unknown`

Suggested caption:

Module-level prototype pipeline on the XIAO ESP32-S3 Sense board. The onboard microphone captures one-second audio windows, the board preprocesses compact audio features, and the local speech module outputs a safety-net category for the interaction stack.

Suggested body text:

Figure B shows the prototype path used in the evaluation. The board stays near the drone's acoustic condition, including rotor noise and microphone placement. The pipeline runs locally, so the first speech-processing result does not depend on a phone application, cloud speech service, or network connection.

## Figure C: Microphone Placement Schematic

Suggested diagram labels:

`Nearby speaker`, `Drone`, `Onboard / near-drone microphone`, `Rotor noise`, `Speech path`, `Distance and angle`

Suggested caption:

Microphone-placement schematic for spoken drone interaction. The microphone is placed on or near the drone, so it captures both the nearby speaker and the drone's own acoustic footprint. Distance, orientation, rotor noise, and enclosure design affect what the speech-processing module receives.

Suggested body text:

Figure C makes the acoustic setting explicit. Unlike a phone or smart speaker, the drone hears speech from within the same physical space that it changes through motion and rotor noise. This placement is useful for local interaction, but it also makes microphone location, speaker geometry, and noise exposure part of the safety-net design.
