# Drone Pre-Meeting Report Draft (2026-07-23, 中文讨论稿)

Source meetings:

- 2026-07-10 Drone project meeting.
- 2026-07-23 pre-meeting planning and paper-search follow-up.

Prepared: 2026-07-23 CDT.

Purpose:

- This is the Chinese discussion draft for the 2026-07-23 meeting.
- After user review, the English final report should be written into the
  `Drone Meeting Final Reports (English)` Notion database.
- This report is planning-oriented. It does not claim new experiment results.

## 1. 本周要讨论的核心变化

我现在觉得下一篇完整论文不能继续停留在 “drone-side speech recognizer”
这个层面。更强的系统论文应该回答一个更完整的问题：

> 当无人机已经起飞并处在 rotor-noisy operating condition 下，人通过语音给出不同类型的指令，
> 系统能否从 speech input 到 intent recognition，再到 policy gate，再到 drone response，
> 形成一条可复现、可测量、可解释的 control loop？

因此，新版 evaluation 不再把 `embedded event generation` 单独作为一层主评估。
板端事件生成仍然是实现前提，但它更适合放在 control-loop evidence 里作为内部日志和
版本可追溯性，而不是作为论文的独立 evaluation layer。

下一阶段更关键的是：

- 完整 control loop 是否能跑通；
- drone 起飞后接到不同 speech-derived command 是否能做出正确 response；
- response 是否可记录、可复现、可安全中断；
- 不同 drone / propeller / microphone placement 是否改变系统表现；
- intent 类别是否需要从当前三类变成更细粒度的可控 taxonomy。

## 2. 为什么不能只沿用已有 evaluation 结果

已有 W19/W23 结果仍然有价值，但它们主要回答的是模型、板端 runtime 或局部 pipeline
是否可行。下一篇完整 systems paper 需要证明的是系统级能力：

- 输入端：speech 在 rotor noise、距离、音量变化下是否可靠；
- 识别端：不同 intent 类别是否能稳定区分；
- 控制端：识别结果是否能经过 policy gate 触发正确 drone response；
- 实验端：同样流程是否能在不同平台和不同条件下重复。

因此旧结果应该先进入 evidence audit，不能直接作为下一篇论文的主线。
我们应该从下一篇 paper 的 claim 重新设计 evaluation，再决定哪些旧结果可保留、哪些需要重跑。

## 3. 新版 evaluation framework

我建议下一阶段 evaluation 改为六层，每一层对应一个更清楚的 systems-paper claim。

| Layer | 需要回答的问题 | 需要收集的证据 | 备注 |
| --- | --- | --- | --- |
| Physical acoustic operating range | 系统在什么真实物理条件下能听清 speech | rotor on/off, SNR, speech volume, distance, mic placement, clipping rate | 这是 drone 场景区别于普通 speech recognition 的基础 |
| Fine-grained intent recognition | 重新划分后的 intent 类别能否被稳定识别 | per-intent accuracy/recall, confusion matrix, confidence, unknown false admission | 不再只做 emergency/movement/unknown 三类 |
| Complete control loop behavior | drone 起飞或进入 grounded/no-prop state 后，接到指令能否做出对应 response | command issued, policy decision, drone ack, observed response, video/log alignment, latency | 替代原来的 embedded event generation layer |
| Safety-net mediation | 错误识别或低置信度时是否会被 policy gate 拦住 | reject rate, unknown handling, direct-mapping comparison, no-unknown ablation, unsafe-action suppression | 不 claim flight safety，只评估 mediation behavior |
| Multi-platform robustness | 不同 drone / propeller / hardware placement 是否影响系统 | drone model, propeller type, rotor spectrum, SNR, recognition/control-loop metrics | 新增主评估轴 |
| Protocol repeatability | 实验流程能否被复现和扩展 | prompt list, setup photos, metadata template, firmware/model hash, pilot video, log bundle | 正式 user study 和多平台实验前的 gate |

这一版 evaluation 的核心变化是：我们不再只证明“板子能输出 label”，而是证明
speech-derived signal 如何进入真实 drone interaction workflow。

## 4. 完整 control loop 应该怎么测

完整 control loop 不应该一开始就直接上危险飞行动作。建议分成三个安全层级：

1. Grounded / no-prop bench：
   - 验证 speech input -> recognition -> policy gate -> command decision -> SDK/host log。
   - 不让 drone 起飞，不执行真实移动。
   - 目标是验证软件链路、日志和 policy gate。

2. Takeoff / hover response test：
   - drone 起飞后保持 hover。
   - 测试最小闭环：takeoff、hover/hold、land、emergency stop/land。
   - 只测低风险、可观察、可中断的 response。

3. Constrained movement test：
   - 在安全空间内测试 forward/back/left/right/up/down/yaw 等细粒度 movement。
   - 每次只执行小幅、短时、限速动作。
   - 必须有 manual override、timeout、emergency fallback 和视频记录。

每个 trial 至少记录：

- spoken prompt / playback prompt；
- predicted intent；
- confidence；
- policy gate decision；
- command sent or rejected；
- drone ack / timeout；
- observed physical response；
- latency from speech-window end to command decision and drone response；
- video timestamp；
- failure reason。

可报告指标包括：

- response success rate；
- command correctness；
- unsafe / rejected / timeout counts；
- emergency response time；
- movement direction correctness；
- false action rate；
- missed emergency rate；
- recovery after wrong or unknown input。

## 5. Intent 类别需要重新划分

当前 `emergency / movement / unknown` 三类适合作为早期 prototype，但如果下一篇论文要讲完整
control loop，这个粒度太粗。特别是 `movement` 现在只能说明“用户想让 drone 动”，
但无法判断 direction、distance、speed 或 action type。

我建议把 intent taxonomy 分阶段细化。

### Stage 0: 当前三类保留为历史 baseline

- `emergency`
- `movement`
- `unknown`

用途：

- 保留与旧模型和旧结果的可比性；
- 作为 coarse safety-net proof-of-concept；
- 不作为完整 control-loop 的最终类别。

### Stage 1: 可测试 control-loop taxonomy

第一版完整闭环可以先用以下类别：

| Intent group | Example commands | Drone-side meaning | 是否适合第一轮闭环 |
| --- | --- | --- | --- |
| Emergency / stop | stop, emergency, abort | 立即进入 hold / land / emergency handling | 是 |
| Takeoff / landing | take off, land | 切换飞行状态 | 是，但必须低风险测试 |
| Hover / hold | hold, stay, pause | 保持或停止当前动作 | 是 |
| Directional movement | forward, back, left, right, up, down | 小幅方向动作 | 可以放第二阶段 |
| Yaw / orientation | turn left, turn right | 姿态/朝向变化 | 可以放第二阶段 |
| Status / query | battery, status | 非运动 response，可用于低风险闭环 | 是，适合早期测试 |
| Unknown / unsupported | unrelated speech, unsupported phrase | no action / reject | 必须保留 |

这比三分类更有系统价值，因为它能直接对应 control-loop response。

### Stage 2: 更长期的 intent expansion

后续如果要做更强论文，可以再扩展：

- distance-aware command: move forward 50 cm；
- speed-aware command: slowly move left；
- mission-level command: follow me, return home；
- multimodal command: voice + gesture / position；
- cross-language equivalents of the same command set。

但这些不应该进入第一轮 control-loop evaluation，否则 scope 会失控。

## 6. Multi-platform evaluation

下一篇完整 systems paper 需要考虑多平台，因为不同 drone 的 propeller size、rotor speed、
airframe geometry、motor noise 和 mounting location 都会影响 speech capture。

多平台 evaluation 可以设计成两层：

1. Primary platform deep evaluation：
   - 在当前主 drone 上做完整 physical matrix 和 control loop。
   - 这是主结果。

2. Secondary platform transfer check：
   - 选 1-2 个不同 drone 或不同 propeller/mounting configuration。
   - 不一定做完整矩阵，但至少测同一 prompt set、同一距离/音量、同一 mic placement rule。
   - 目标是证明问题和方法不是只针对单一硬件偶然成立。

建议指标：

- rotor-noise spectrum / SNR difference；
- recognition accuracy / emergency recall / unknown false admission；
- control-loop response success；
- latency / ack / timeout；
- platform-specific failure cases；
- microphone placement sensitivity。

报告边界：

- 如果只测两个平台，不能 claim universal generalization；
- 可以 claim “we observe platform-dependent rotor-noise effects and evaluate whether the same protocol transfers.”

## 7. Hardware contribution 的边界

当前硬件部分仍然应该保守写成：

> drone-side embedded audio prototype

而不是：

> custom drone hardware design

可以 claim 的部分：

- ESP32-S3 Sense 放在无人机附近或机身上，直接暴露在 drone acoustic field 中；
- 本地完成 1 s / 16 kHz audio capture、feature extraction、int8 inference；
- 输出 compact speech-derived signal 给后续 policy/control logic；
- drone-specific 部分来自 sensing location、rotor-noise exposure、onboard compute constraint、
  mounting and microphone placement。

如果要让 hardware 变成更强 contribution，需要补：

- top-down setup photo；
- mic-port close-up；
- side-view showing mic direction / clearance / cable routing；
- size and weight evidence；
- speaker / drone / rotor / microphone geometry diagram；
- prop-off vs hover waveform or spectrogram；
- microphone placement ablation。

## 8. Cross-language 作为 generalization 轴

Cross-language 仍然值得保留，但它应该服务于新的 intent taxonomy 和 control-loop story。
它不应该只是“模型能不能识别另一种语言”，而应该是：

> 同一套 drone intent taxonomy 和 policy mapping 是否可以跨语言表达和测试？

候选数据源：

| Dataset | 用途 | 风险 | 初步判断 |
| --- | --- | --- | --- |
| MLCommons Multilingual Spoken Words Corpus | keyword-level multilingual command / KWS-style 测试 | isolated word，不是完整 drone command | 适合方向词、stop/help 等 keyword |
| Mozilla Common Voice | transcript filtering、phrase-level speech、unknown/general speech | clip 长度和语义不固定，需要筛选和切窗 | 适合 phrase 和 unknown |
| FLEURS | 102-language general speech / language robustness reference | 不是 command/intent 数据集 | 可作为 unknown/general speech reference |
| MInDS-14 | multilingual spoken intent benchmark | banking domain，不自然映射 drone labels | 只适合 related work / sanity check |
| W14 Quechua/Polish strict benchmark | 本地已有 emergency/normal cross-language 资产 | MT gloss；2-class；不是 control-loop taxonomy | 只作为历史参考 |

Mapping 策略要跟新 taxonomy 对齐：

- 每个 command group 有 canonical English prompt；
- 每种语言需要 translation / back-translation；
- 每条样本记录 source text、English gloss、intent group、mapping rationale、review status；
- unknown 需要主动构造；
- 第一批语言只选 3-5 种，优先选择能人工 audit 的语言。

## 9. 下一篇完整 systems paper 的 contribution 落点

我现在的判断是：如果只做 ESP32 prototype + accuracy / F1 + demo + 少量 multilingual，
仍然不够支撑完整 systems top venue。更强的 contribution 应该落在完整系统评估与交互闭环上。

更有希望的主线可以改成：

> A reproducible evaluation and control-loop framework for drone-side spoken command interfaces under rotor noise.

这条主线比单纯 recognizer 更强，因为它包括：

1. Physical-condition-aware evaluation：
   系统刻画 rotor noise、SNR、distance、volume、mic placement 如何影响 speech-to-drone interaction。

2. Fine-grained intent-to-control taxonomy：
   从 coarse emergency/movement/unknown 发展到可执行、可拒绝、可审计的 control-loop command groups。

3. Complete control-loop evaluation：
   测试 drone 起飞/hover 后是否能根据 speech-derived command 做出正确 response，而不只是输出 label。

4. Multi-platform robustness：
   比较不同 drone / propeller / mounting condition 下的 acoustic 和 control-loop performance。

5. Policy-gated safety-net behavior：
   保留 unknown/reject/confidence threshold/manual override，说明为什么不能 direct speech-to-action。

6. Cross-language generalization：
   检查同一套 intent taxonomy 是否能跨语言表达和评估。

### 顶会强度判断

当前版本还不够强，但这条路线比之前更像完整 systems paper。

如果能补齐以下证据，才有可能支撑 SenSys / MobiCom / MobiSys-style 投稿：

- 完整 control loop demo and logs；
- 起飞/hover 状态下的 speech command response；
- 细粒度 intent taxonomy 的识别和控制结果；
- controlled playback physical matrix；
- multi-platform 或 multi-propeller comparison；
- policy gate / reject / emergency fallback evidence；
- 可复现 metadata schema、video、setup diagram、log bundle。

如果这些做不完，这个方向更适合先投 workshop / magazine / lower-risk systems venue。

## 10. 和 IEEE magazine paper 的关系

IEEE Pervasive 这篇仍然可以保持 lightweight：framework、vision、basic prototype、demo。
它不需要承担完整 systems paper 的全部 evaluation。

下一篇 systems paper 则可以从 magazine paper 往前推进：

- magazine paper：提出 spoken safety net / drone speech framework；
- systems paper：证明 speech input 如何在真实 rotor-noisy drone operation 中进入完整 control loop。

这样两篇论文不会冲突。Magazine paper 保持轻量，完整 systems paper 负责真正的实验深度。

## 11. 明天希望老师帮助决定的问题

- [ ] 下一篇完整论文是否应该从 speech recognizer 转成 speech-to-drone control loop？
- [ ] 是否同意去掉 embedded event generation 作为独立 evaluation layer，把它放进完整 control-loop evidence？
- [ ] 第一轮 intent taxonomy 应该包含哪些类别：emergency/stop、takeoff/land、hover/hold、directional movement、status/query、unknown？
- [ ] 哪些 intent 可以进入第一轮真实飞行/hover 测试，哪些必须先停留在 grounded/no-prop？
- [ ] 完整 control loop 的成功标准是什么：ack、physical response、video evidence、还是 log + response 一致？
- [ ] 多平台 evaluation 是否应该成为主 contribution 之一，还是作为 supporting robustness evidence？
- [ ] 是否优先测试第二种 drone，还是先测试同一 drone 的不同 propeller / mounting condition？
- [ ] Cross-language 应该对齐新的 fine-grained taxonomy，还是先只做 emergency/stop 与 unknown？
- [ ] 老师是否认为这个 contribution stack 足够支撑完整 systems top venue？

## 12. 会后可能的 next actions

如果老师认可这个方向，我建议会后按这个顺序推进：

1. Freeze first-round fine-grained intent taxonomy.
2. Define safe control-loop stages: grounded/no-prop, takeoff/hover, constrained movement.
3. Freeze metadata schema for control-loop trials.
4. Prepare a small controlled playback pilot with one platform.
5. Decide second platform / propeller / mounting condition.
6. Build multilingual mapping table against the new taxonomy.
7. Only after protocol approval, start formal data collection.

## 13. 当前边界

- 本 report 不引入新实验结果。
- 不 claim flight safety validation。
- 不 claim onboard rotor-noise cancellation。
- 不把 desktop TFLite re-inference 写成 board-native live prediction。
- 不把 cross-language 或 multi-platform 作为已经完成的 claim。
- 不把 full control loop 直接等同于 safe autonomous flight。
