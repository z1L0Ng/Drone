# IEEE Pervasive 注册材料中文版

目标：IEEE Pervasive Computing 特刊 Embodied Pervasive Computing。

CFP 约束（2026-06-30 已核对 IEEE Computer Society CFP 页面）：

- 标题和摘要截止：2026-07-01。
- 完整稿件截止：2026-07-08。
- 预计出版时间：2027 年 4-6 月。
- CFP 匹配点：embodied pervasive computing 和 pervasive agents 的理论基础、系统架构、真实部署。
- 本文匹配点：具身系统在物理世界中的感知与行动、边缘智能、机器人、人类监督、安全且社会感知的运行、真实系统部署经验。

已检查本地 scaffold：

- `docs/ieee_pervasive/main.tex`
- `docs/ieee_pervasive/sections/1introduction.tex`
- `docs/ieee_pervasive/sections/2system.tex`
- `docs/ieee_pervasive/sections/3demo.tex`
- `docs/ieee_pervasive/sections/4realworld.tex`
- `docs/ieee_pervasive/sections/5conclusion.tex`

## 标题选项

1. Drone-Side Speech Intent Recognition for Embodied Pervasive Interaction
2. Toward On-Device Speech-to-Intent Interfaces for Small Drones
3. A Lightweight Speech-to-Intent Layer for Human-Drone Interaction

推荐注册标题：Drone-Side Speech Intent Recognition for Embodied Pervasive Interaction。

## 摘要

小型无人机正越来越多地出现在实验室、教室、巡检现场和其他人与机器共享的空间中。在这些场景里，免手持的语音交流往往比手机应用、遥控器或云端服务更加自然。然而，无人机周围的语音并不等同于面向智能音箱的语音：无人机是一个具身系统，存在机载噪声、受限算力，以及语音解释之后可能带来的物理后果。本文将无人机侧 speech-to-intent recognition 定位为一种面向具身普适交互的轻量接口。不同于把周围语音直接处理成开放式转录文本或飞行命令，该接口将短语音窗口转换为紧凑的意图类别，并在靠近无人机的位置完成识别，再以结构化事件的形式暴露给未来的应用逻辑。我们介绍为什么无人机交互需要 on-device intent recognition，概述一个由嵌入式麦克风和微控制器级推理管线构成的原型路径，并总结来自旋翼噪声识别、嵌入式运行时间和 transcript-first ASR 对比的基础可行性证据。本文目标不是声称完成了自主控制或安全验证，而是说明一个受约束的语音意图层为什么是迈向更丰富、更可审计的具身无人机语音交互的实际第一步。

英文版摘要词数：185。

## 关键词

- Embodied pervasive computing
- Human-drone interaction
- On-device speech recognition
- Spoken intent recognition
- Edge intelligence
- UAV interfaces
- Rotor-noisy sensing
- TinyML

## 4-5 页 magazine-style 大纲

### 第 1 页：开场场景与问题

对应章节：Introduction

目标：让读者先理解为什么无人机附近的语音交互重要，而不是一开始进入模型架构。

内容：

- 以共享空间中的具体场景开头：一个人在小型无人机附近，需要在双手被占用、控制器不可用或手机应用打开太慢时快速表达意图。
- 解释为什么常规语音接口不能直接套用到无人机上：旋翼噪声、短语音片段、嵌入式算力限制，以及无人机作为物理系统的后果。
- 明确文章主张：drone-side speech-to-intent layer 是具身无人机交互的一个实际且受约束的第一步。
- 避免说系统已经实现端到端安全控制无人机。

图：

- Figure 1：场景照片或插图，展示人在无人机附近说话，以及无人机侧或近无人机侧的麦克风感知路径。

### 第 2 页：Speech-to-Intent 作为接口

对应章节：System Frame

目标：用读者容易理解的方式定义这个轻量抽象。

内容：

- 对比 transcript-first ASR、直接命令映射和紧凑意图识别。
- 高层解释三类意图接口：emergency、movement、unknown/fallback。
- 强调 intent 是给未来应用逻辑使用的结构化信号，不是直接飞行命令。
- 解释为什么 on-device 或 drone-side processing 重要：更接近真实声学环境、减少网络依赖、支持本地事件上报。
- 模型细节保持简短；这是一篇 magazine article，不是 recognizer architecture paper。

图：

- Figure 2：简洁管线图：microphone/audio window -> on-device speech-to-intent recognizer -> intent event -> logging/future application logic。

### 第 3 页：原型和 Demo 证据

对应章节：Prototype / Demo

目标：说明这个接口已经在具体的无人机侧原型路径中被验证过，而不是停留在概念层。

内容：

- 描述基本设置：ESP32/XIAO 级别开发板或麦克风靠近无人机，16 kHz 一秒语音窗口，log-mel frontend，紧凑 full-integer inference，intent logging。
- 谨慎总结已有可行性证据：
  - 板端本地管线已经存在：麦克风采集、log-mel frontend、full-integer TFLM inference、USB CDC result reporting。
  - 之前的稳定性证据显示，重复板端触发可以完成且无失败；当前 ESP32-S3 原型大约是 3.1 s trigger-to-result。
  - 离线旋翼噪声评估支持“该意图任务在加入旋翼噪声后仍然可测”这一说法，但它不是飞行验证。
- ASR 对比只作为动机：transcript-first ASR 在短、带旋翼噪声的片段上可能较脆弱，并且不具备同样的 MCU 部署形态。

图/表：

- Figure 3：真实 setup 照片或带标注的设置图：drone、microphone/ESP32、host/logging path。
- Table 1：紧凑可行性总结表，行包括 rotor-noisy recognition、embedded runtime、ASR contrast。

### 第 4 页：应用、经验和边界

对应章节：Real-World Applications and Vision

目标：把原型和 Embodied Pervasive Computing 特刊主题连接起来。

内容：

- 应用场景：实验室、教室、仓库、巡检现场、现场支持等无人机与人近距离共处的环境。
- 设计经验 1：具身语音接口应该先使用受约束的 intent events，而不是直接进入开放语言理解或动作策略。
- 设计经验 2：本地声学上下文很重要，因为无人机本身会改变感知环境。
- 设计经验 3：unknown/fallback 是接口的一部分，不是事后补丁。
- 简短提到 safety-net 概念：未来系统可以把 intent events 作为 safety net 或 application policy 的输入，但本文不提出完整的 safety-state/control-loop mechanism。

可选图：

- 如果版面允许，可加入一个小 inset：intent events 输入未来监督/应用逻辑。保持概念性，避免展开成完整安全系统。

### 第 5 页：局限与未来工作

对应章节：Limitations and Future Work

目标：保留未来 systems paper 的 novelty，同时给出清楚的研究方向。

内容：

- 当前范围：speech-to-intent recognition 和 prototype feasibility，不是完整飞行控制验证。
- 意图空间有限：三类接口是有意保持简单，未来扩展需要更强交互证据。
- 部署限制：麦克风位置、真实旋翼条件、距离、说话人变化和连续交互都需要更大规模研究。
- Safety future work：未来无人机系统应将 intent events 连接到明确的监督、confidence handling 和 action policies，但这些机制不属于这篇短文的范围。
- 收束信息：on-device speech-to-intent recognition 是具身普适无人机交互的实际入口，因为它让语音保持本地、受约束、可检查。

## Overclaim 检查

可以使用：

- “speech-to-intent layer”
- “drone-side voice interface”
- “basic feasibility evidence”
- “prototype path”
- “future safety net”
- “structured intent event”

避免使用：

- “safe autonomous drone control”
- “validated safety mechanism”
- “complete control loop”
- “robust to all rotor noise”
- “general natural-language drone command”
- “Akouo system contribution”，除非明确重新打开完整长篇 systems paper。

## 注册建议

建议使用标题选项 1 注册，除非作者团队希望用更保守的 “Toward” 标题。摘要已经在 150-250 词范围内，并且把文章中心放在 embodied drone interaction 上，同时没有暴露详细 safety-state 或 action-policy novelty。
