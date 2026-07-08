# Section 1 Introduction Plan

Purpose: focused planning and draft text for Section 1 of the IEEE Pervasive Computing article. The manuscript will be written in Overleaf; this file is a local writing guide.

Current framing:

- Core concept: `safety net`.
- Technical entry point: `audio intent recognition`.
- Paper identity: magazine-style embodied pervasive computing article, not a full safety-control systems paper.
- Likely title direction: `Intent-Aware Safety Net` or `From Speech to Intent`.

## Section 1 Job

Section 1 should do four things:

1. Open with a concrete human-drone interaction scene.
2. Explain why speech near a drone is different from speech to a phone, smart speaker, or controller app.
3. Introduce the paper's central idea: a safety net between nearby speech and vehicle-facing behavior.
4. Position audio intent recognition as the first concrete component of that safety net.

It should not:

- start from model architecture;
- sound like a speech-recognition benchmark paper;
- claim complete safe drone control;
- reveal detailed safety-state or control-loop novelty reserved for future systems papers.

## Paragraph Flow

### Paragraph 1: Scenario

Function: bring the reader into the shared-space drone setting.

Message:

- Small drones are entering labs, classrooms, warehouses, inspection sites, and other shared physical spaces.
- A nearby person may need to communicate quickly without a controller or app.
- Voice is natural because it is hands-free and already used for human coordination.

Tone:

- Magazine-style and accessible.
- Avoid starting with "UAVs are widely used" generic boilerplate.

### Paragraph 2: Why Existing Voice Interfaces Are Not Enough

Function: create the technical problem.

Message:

- Speech around a drone is not the same as speech to consumer voice assistants.
- Drones are embodied systems with rotor noise, onboard compute constraints, physical movement, and consequences after interpretation.
- Direct speech-to-command is too strong because uncertain speech, background conversation, or ASR errors should not directly become vehicle-facing behavior.

Key phrase:

> Speech near a drone needs mediation before action.

### Paragraph 3: Introduce Safety Net

Function: name the central paper idea.

Message:

- The paper argues for a `safety net` between nearby speech and drone behavior.
- Define safety net as an intermediate layer that keeps speech-derived input bounded, inspectable, and deferrable.
- Do not describe this as a complete safety controller.

Key phrase:

> The safety net is not a promise that every action is safe; it is a design boundary that prevents speech from being treated as immediate action.

### Paragraph 4: Audio Intent as First Component

Function: connect the central idea to what we actually built and can discuss.

Message:

- The first implemented component is drone-side audio intent recognition.
- It maps short speech windows to compact events: `emergency`, `movement`, and `unknown`.
- These are intent events, not commands.
- `unknown` is part of the safety net because it gives uncertainty a place to go.

Key phrase:

> Intent is the interface between noisy speech and later mediation.

### Paragraph 5: Article Scope and Contributions

Function: tell the reader what the article will and will not do.

Message:

- This is a lightweight embodied pervasive computing article.
- It presents the safety-net framing, the audio-intent component, and basic prototype/feasibility evidence.
- It does not claim full flight-control validation or complete autonomous safety.

Possible contribution wording:

- A safety-net framing for spoken interaction with embodied drones.
- A compact intent-event interface for speech entering that safety net.
- A prototype path and feasibility evidence for drone-side audio intent recognition under rotor-noisy, embedded constraints.

## Recommended Figure for Section 1

Figure 1 should appear near the end of Section 1 or at the start of Section 2.

Suggested caption idea:

> Spoken interaction with a small drone should pass through a safety net before it can influence vehicle-facing behavior. In this article, drone-side audio intent recognition provides the first bounded event layer of that safety net.

Visual content:

- Left: nearby person speaking near drone.
- Middle: safety-net layer.
- Inside safety net: audio intent recognition -> bounded intent events.
- Right: future mediation / logging / application logic.

Avoid:

- a direct arrow from speech to drone action;
- detailed state machine;
- live-flight command sequence.

## Section 1 Draft v2

Small drones are beginning to share everyday spaces with people. In laboratories, classrooms, warehouse aisles, and inspection sites, a drone may fly or hover close to someone who is not holding a controller. That person may need to warn the drone, request attention, or express a simple intent while their hands and eyes are occupied. Voice is a natural channel in these moments because it is immediate, hands-free, and already used by people to coordinate activity in physical spaces.

However, speech near a drone is not the same as speech to a phone, smart speaker, or cloud assistant. A drone is an embodied computing system: it produces rotor noise, senses from a physical platform, operates with limited onboard resources, and may eventually connect perception to behavior in the world. These properties make direct speech-to-command interaction a poor default abstraction. Background conversation, a partial utterance, or an uncertain transcript should not become vehicle-facing behavior simply because an audio system produced text, a keyword, or a high-confidence label.

This article argues that spoken drone interaction needs a safety net between nearby speech and vehicle-facing behavior. We use `safety net` to mean an intermediate layer that keeps speech-derived input bounded, inspectable, and deferrable before it can influence action. This is not a claim that the current prototype solves complete drone safety. Rather, it is a design boundary: speech should first become a structured signal that can be logged, checked, ignored, confirmed, or passed to later policy logic.

Our first concrete component of this safety net is drone-side audio intent recognition. Instead of treating speech as open-ended transcripts or direct commands, the audio layer maps short speech windows into compact intent events such as `emergency`, `movement`, and `unknown`. This vocabulary is intentionally small. It gives urgent speech, motion-related speech, and uncertainty different representations while avoiding the stronger claim that the drone understands arbitrary language. In this framing, intent is the interface between noisy nearby speech and later mediation.

We present this direction as a magazine-style embodied pervasive computing article. The focus is not a new flight controller or a complete safety validation. The focus is a practical framing and first prototype path: an intent-aware safety net in which drone-side audio recognition provides bounded events for future interaction logic. We discuss why this boundary matters for embodied drones, how the first audio layer can be built on embedded hardware, and what basic feasibility evidence can and cannot support.

## Chinese Reading Notes

这一节的主线应该是：

1. 无人机进入 shared physical spaces，所以附近的人需要一种自然、快速、免手持的交互方式。
2. 但无人机不是手机/音箱，speech cannot directly become action。
3. 因此文章提出 `safety net`，它是 speech 和 vehicle-facing behavior 之间的中间层。
4. 我们现在实现和展示的是 safety net 的第一个组成部分：audio intent recognition。
5. 文章承诺的是 bounded intent events + prototype feasibility，不是完整 autonomous safety。

最重要的句子可以是：

> Intent is the interface between noisy nearby speech and later mediation.

这个句子能把 `intent` 和 `safety net` 连起来，适合作为 Introduction 或 Section 2 的核心转折句。
