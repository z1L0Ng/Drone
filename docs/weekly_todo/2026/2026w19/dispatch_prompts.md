# Dispatch Prompts (Thursday-cycle 2026w19)

Project target: SenSys 2027 first-round submission.

Do not use planning track labels in execution prompts. Address the active agent
role directly and keep the scope explicit.

## Prompt 0: Writing Agent - Read-Only Overleaf Draft Audit

```text
你是 Drone 项目的论文写作agent。

任务目标：
用户刚把 `docs/paper_sensys2027/` 更新为 Overleaf 上的最新版，其中包含老师修改过的地方和强调的细节。请先做只读审计，梳理当前 paper writing direction、section structure、advisor edits 对后续写作和 evaluation 设计的影响。这个任务只审计和规划，不直接改文稿。

职责范围：
- 只审计 `docs/paper_sensys2027/` 当前 dirty draft。
- 重点关注 main story、title/abstract、section order、related work 位置、motivation、architecture、recognizer、evaluation、conclusion。
- 对照 2026-05-14 meeting 决策：additional voice-command UAV safety layer、response time comparison、real-time onboard constraint、demo video、user-study / testing-condition expansion、VP intro first pass。
- 产出给项目管理agent和 evaluation agent 使用的写作方向审计，不做正文修改。

禁止事项：
- 不改任何文件。
- 不训练模型。
- 不启动服务器任务。
- 不改 ESP32 / Tello 代码。
- 不新增 citation 到 `references.bib`。
- 不把当前 draft 中的 TODO 或 planned evaluation 写成已完成结果。
- 不 merge W19 baseline result branch。

必须先审计：
- git branch / HEAD / git status。
- `docs/paper_sensys2027/main.tex`。
- `docs/paper_sensys2027/sections/1introduction.tex`。
- `docs/paper_sensys2027/sections/2motivation.tex`。
- `docs/paper_sensys2027/sections/3architecture.tex`。
- `docs/paper_sensys2027/sections/4recognizer.tex`。
- `docs/paper_sensys2027/sections/5prototype.tex`。
- `docs/paper_sensys2027/sections/6evaluation.tex`。
- `docs/paper_sensys2027/sections/7relatedwork.tex`。
- `docs/paper_sensys2027/sections/8conclusion.tex`。
- `docs/paper_sensys2027/references.bib`。
- `docs/paper_sensys2027/WRITING_OUTLINE.md` if present。
- `docs/weekly_todo/2026/2026w19/todo.md`。

需要回答的问题：
1. 当前 Overleaf 版 draft 的主线是什么？它和之前的 safety-state mediated framing 有哪些变化？
2. 老师修改后，paper 应该更强调哪些贡献：additional safety layer、on-device real-time intent recognition、response-time/safety behavior、user study/demo，还是 baseline quality？
3. 当前 section order 是否已经符合 “related work after introduction” 的要求？如果没有，后续重写应如何调整？
4. `6evaluation.tex` 当前是否足够支撑 evaluation agent 去设计 protocol？哪些 evaluation 方向应优先进入 Prompt 3？
5. 哪些措辞存在 overclaim 风险，尤其是 real-time、onboard、safety mechanism、live control、user/language robustness？
6. 哪些内容应等 VP introduction first pass 后再改，哪些可以先作为 evaluation protocol 设计依据？

输出格式：
- Branch / HEAD / dirty status。
- Current draft structure summary。
- Advisor-edit / Overleaf-draft implications。
- Writing direction adjustments。
- Evaluation-design implications for evaluation agent。
- High-risk wording / overclaim list。
- Recommended next writing actions。
- Explicit note: no files changed.

验收标准：
- 只读审计。
- 能直接指导 evaluation agent 执行下一步 protocol 设计。
- 明确哪些内容是已有证据，哪些是 planned / missing evidence。
```

## Prompt 1: ESP32 Deployment Agent - Latency Audit And <=1s Feasibility

```text
你是 Drone 项目的 esp32部署agent。

任务目标：
审计当前 ESP32 on-device inference path 的 latency，判断是否存在把端侧推理时间压到 <=1s 的可行路径。这里的 <=1s 是为了支持 paper 中的 real-time onboard story，至少应接近或小于 1s audio capture 的时间尺度。

职责范围：
- 只做 ESP32 deployment / runtime / timing 审计和必要的低风险 instrumentation 计划。
- 可以阅读 firmware、host runner、既有 timing logs、TFLM precheck、ESP32 handoff 文档。
- 可以提出优化方案或最小代码修改建议，但不要直接训练新模型。

禁止事项：
- 不训练模型。
- 不启动服务器任务。
- 不改 paper 正文。
- 不接 Tello 飞行控制。
- 不把 runtime stability 写成 semantic accuracy 或 safety validation。
- 不 merge W19 baseline result branch。

必须先审计：
- git branch / HEAD / git status。
- `docs/realworld_esp32_tflm_profile_handoff.md`。
- `weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_report.md`。
- `realworld/esp32/firmware/esp32_local_cdc_fast/`。
- `realworld/esp32/models/B_small_teacher_student/` and related TFLM artifacts if present。

关键问题：
1. 当前约 2094 ms inference p50 是纯 TFLM Invoke 时间，还是包含 frontend / serialization / host overhead？
2. capture、frontend、TFLM invoke、USB/Bluetooth serialization、host receive 分别占多少？
3. bottleneck 是模型结构、TFLM op implementation、arena/memory layout、frontend 计算、CPU frequency/compiler flags，还是测量方式？
4. 是否存在不用重训模型的低风险优化？
5. 如果必须新训练 tiny deployment student，给出训练需求，但不要启动训练。

输出产物：
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/latency_audit.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/timing_breakdown.csv`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/one_second_feasibility_decision.md`
- 如果需要训练新模型，额外输出 `training_handoff_plan.md`，必须包含所需 commit SHA、tmux session name、WEEKLY_TAG、weeklyresult output dir、startup/completion receipt要求。

验收标准：
- 明确当前 bottleneck。
- 明确 <=1s 是否可能通过工程优化达成。
- 明确是否需要新模型训练。
- 所有结论都必须引用本地文件或新生成日志。
```

## Prompt 2: ESP32 Deployment Agent - Bluetooth Host-Mediated Tello Chain

```text
你是 Drone 项目的 esp32部署agent。

任务目标：
推进 ESP32 -> Bluetooth -> Mac host -> Tello SDK 的 host-mediated control chain。当前目标是 dry-run / no-prop / grounded 证据，不做飞行测试，不绕过 safety state machine。

职责范围：
- 设计或实现 ESP32-S3 到 Mac 的 Bluetooth event transport。
- 如果 Bluetooth 不稳定，保留 USB CDC fallback。
- Host 端负责接收事件、进入 safety state machine、输出 dry/no-prop/grounded command decision。
- 保持现有 safety event schema 的字段语义。

禁止事项：
- 不发无约束 Tello movement command。
- 不上飞机。
- 不把 coarse `movement` 直接映射为 forward/back/left/right。
- 不绕过 `manual_override`。
- 不改模型训练。
- 不改 paper 正文。

必须先审计：
- git branch / HEAD / git status。
- `realworld/shared/control_event_schema.json`。
- `realworld/tello/label_command_mapping.json`。
- `realworld/tello/dry_command_dispatch.py`。
- `weeklyresult/weekly_drone_2026w18/realworld/tello_dryrun/`。
- 当前 ESP32 serial / Bluetooth device availability。

设计要求：
- event 字段至少保留：timestamp, label/intent, confidence, safety_state, safety_hold, manual_override, command_result, result_detail, ack/timeout, fallback_reason。
- `emergency` 进入 safe-hold / emergency handling。
- `movement` 只能进入 pending interaction / manual override path。
- `unknown` 进入 no-action / safe-hold fallback。
- 明确 dry-run、no-prop、grounded、flight evidence 的区别。

输出产物：
- `weeklyresult/weekly_drone_2026w19/realworld/tello_control_chain/control_chain_design.md`
- `weeklyresult/weekly_drone_2026w19/realworld/tello_control_chain/event_schema_delta.md`
- `weeklyresult/weekly_drone_2026w19/realworld/tello_control_chain/dry_or_grounded_run_log.csv` if a run is possible
- `weeklyresult/weekly_drone_2026w19/realworld/tello_control_chain/go_no_go_report.md`

验收标准：
- 不出现 unsafe direct command path。
- emergency / movement / unknown 三类路径都有清楚设计；如果无法 live 覆盖，需要写明 blocker。
- manual_override 是一等字段。
- 输出能支持 paper 中 safety-state behavior evaluation，但不能写成 flight validation。
```

## Prompt 3: Evaluation Agent - User Study, Testing Conditions, Response Time

```text
你是 Drone 项目的 evaluation agent。

任务目标：
设计下一阶段 evaluation protocol，使 paper 不只报告 offline accuracy/F1，而是能支撑 voice-command UAV safety layer 的系统评价。

前置条件：
- 先等待论文写作agent完成 “Read-Only Overleaf Draft Audit” 回执。
- 执行本任务时必须结合该写作审计结果，尤其是当前 Overleaf 版 draft 的 writing direction、advisor edits、evaluation-design implications 和 overclaim 风险。

职责范围：
- 只做 evaluation design / protocol / metric planning。
- 绑定当前 SenSys draft 的 evaluation 章节方向。
- 可以引用 W19 baseline result branch 的摘要，但不要 merge branch。
- 不采集新数据，除非 manager 后续明确批准。

禁止事项：
- 不训练模型。
- 不启动服务器任务。
- 不改 ESP32 firmware。
- 不改 Tello control code。
- 不新增 references.bib，除非 manager 明确批准。
- 不把 geofencing / obstacle avoidance / return-to-home 当作 classifier baseline。

必须先审计：
- git branch / HEAD / git status。
- `docs/paper_sensys2027/main.tex`。
- `docs/paper_sensys2027/sections/1introduction.tex`。
- `docs/paper_sensys2027/sections/2motivation.tex`。
- `docs/paper_sensys2027/sections/3architecture.tex`。
- `docs/paper_sensys2027/sections/4recognizer.tex`。
- `docs/paper_sensys2027/sections/5prototype.tex`。
- `docs/paper_sensys2027/sections/6evaluation.tex`。
- `docs/paper_sensys2027/WRITING_OUTLINE.md`。
- `docs/weekly_todo/2026/2026w19/todo.md`。
- W19 first-batch baseline summary if available from prior manager notes。

最新版 writing context：
- 当前 Overleaf draft 主线是 **additional voice-command UAV safety interaction
  layer**，不是 generic recognizer benchmark。
- Evaluation protocol 必须分成四类证据：recognizer quality、
  latency/runtime、safety-state/bridge behavior、user-study/demo evidence。
- 不要假设 ESP32 已满足 `<=1s` real-time；当前 paper 中已有 p50 inference
  `2094 ms`、total `3075 ms`，只能作为待审计 runtime evidence。
- 当前术语：anchor recognizer = `w14 preprocess_ext`；embedded student =
  `B_small_teacher_student` deployment candidate；`movement` = pending
  interaction；`emergency` = safety-critical handling；`unknown` =
  fallback/no-action。
- `paper_integration_plan.md` 必须标明哪些内容已有 repo evidence，哪些只能写成
  protocol/planned evaluation。

需要回答的问题：
1. Baseline comparisons 应该扩展到哪些 testing conditions？
2. User study 需要多少人、哪些 utterance、哪些 metadata、哪些环境条件？
3. Response time 怎么定义：speech onset -> model event, model event -> host command, command -> drone response？
4. 如何和 manual stop / controller action / existing UAV safety module 做公平的 response-time 或 mechanism-level comparison？
5. Paper 中如何解释没有统一 quantitative benchmark 的原因？
6. 哪些结果必须真实采集，哪些只能作为 protocol / planned evaluation？

输出产物：
- `weeklyresult/weekly_drone_2026w19/evaluation_protocol/testing_condition_matrix.md`
- `weeklyresult/weekly_drone_2026w19/evaluation_protocol/user_study_protocol.md`
- `weeklyresult/weekly_drone_2026w19/evaluation_protocol/response_time_metric_plan.md`
- `weeklyresult/weekly_drone_2026w19/evaluation_protocol/safety_state_metrics.md`
- `weeklyresult/weekly_drone_2026w19/evaluation_protocol/paper_integration_plan.md`

验收标准：
- 明确区分 recognizer accuracy、latency/runtime、safety-state behavior、user-study/demo evidence。
- 明确哪些评价是可量化的，哪些只能用 mechanism matrix 解释。
- 输出能直接指导后续 `6evaluation.tex` 重写。
```

## Prompt 4: Model Design Agent - <=1s Tiny Student Architecture Analysis

```text
你是 Drone 项目的模型设计agent。

任务目标：
在不训练模型的前提下，分析如何把 ESP32/XIAO 端侧 TFLM Invoke 时间从当前 `2094 ms` 降到 `<=1000 ms`，同时尽量保持当前 recognizer accuracy 和 emergency recall。重点不是泛泛压缩模型，而是针对 latency audit 已定位的 early CNN stem Conv2D bottleneck 提出可训练、可部署、可验收的候选设计。

职责范围：
- 只做模型结构分析、profile 推导、训练方案设计和风险评估。
- 可以阅读当前模型代码、run_config、Keras summary、TFLite precheck、ESP32 op timing、W14/W17/W19 evidence。
- 可以提出 2-4 个候选 model profile 和推荐的 server training lane。
- 不直接改代码，除非 manager 后续明确批准。

禁止事项：
- 不训练模型。
- 不启动服务器任务。
- 不改 ESP32/Tello 固件或 host code。
- 不改 paper 正文。
- 不 merge W19 baseline result branch。
- 不把 proposed candidate 写成已验证结果。

必须先审计：
- git branch / HEAD / git status。
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/latency_audit.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/timing_breakdown.csv`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/one_second_feasibility_decision.md`
- `weeklyresult/weekly_drone_2026w19/realworld/esp32_latency/training_handoff_plan.md`
- `docs/realworld_esp32_tflm_profile_handoff.md`
- `weeklyresult/weekly_drone_2026w14/preprocess_ext/run_config.json`
- `weeklyresult/weekly_drone_2026w14/preprocess_ext/classification_report_noisy.txt`
- `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/run_config.json`
- `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/classification_report_noisy.txt`
- `weeklyresult/weekly_drone_2026w17/B_small_teacher_student/tflm_candidate_precheck.json`
- current model/profile code under `src/` that defines `xiao_bottleneck256_tflm` and related deployment profiles。

已知关键事实：
- 当前 `B_small_teacher_student / xiao_bottleneck256_tflm` 是 deployment candidate，不是新的 mainline accuracy winner。
- 当前 TFLM Invoke p50 `2094 ms` 是纯 Invoke，不含 capture/frontend/USB。
- capture p50 `926 ms`，frontend p50 `55 ms`，USB/host receive p50 about `5.5 ms`。
- Early CNN stem `CONV_2D` 是 bottleneck：Conv2D total about `1572.7 ms`，first three stem Conv2D calls about `1535.1 ms`，largest conv about `969.3 ms`。
- 当前 TFLite op mix：`CONV_2D=6`, `DEPTHWISE_CONV_2D=1`, `FULLY_CONNECTED=11`, `SOFTMAX=2`；不能回到 grouped temporal `CONV_2D`。
- Paper 需要的是 credible `<=1s` onboard story；如果做不到，必须明确写成 future optimization。

需要回答的问题：
1. 当前 early CNN stem 为什么这么慢？从 feature map shape、channels、kernel/stride、op type、PSRAM/internal memory 角度解释。
2. 哪些结构改动最可能把 Invoke p50 降到 `<=1000 ms`：减少 stem channels、提前 stride/pooling、depthwise-separable stem、smaller Branchformer entry、减少 FC/attention-like blocks 等？
3. 哪些改动可能严重伤害 accuracy / emergency recall？如何用 KD 或 teacher-student 设置降低风险？
4. 是否应保持 `(256,32,1)` logmel frontend，还是提出 frontend 变更？如果提出 frontend 变更，必须说明它会影响公平性和 paper claims。
5. 设计 2-4 个候选 profile，给出参数规模、预期 op mix、预期 latency 风险、accuracy 风险、TFLM compatibility 风险。
6. 推荐第一批 server training candidates，最多 2 个，说明为什么。

输出产物：
- `weeklyresult/weekly_drone_2026w19/model_design_rt1s/infer_bottleneck_analysis.md`
- `weeklyresult/weekly_drone_2026w19/model_design_rt1s/candidate_profiles.md`
- `weeklyresult/weekly_drone_2026w19/model_design_rt1s/training_recommendation.md`
- `weeklyresult/weekly_drone_2026w19/model_design_rt1s/server_handoff_draft.md`

`server_handoff_draft.md` 只写计划，不启动训练。若建议训练，必须包含：
- required commit SHA placeholder
- branch requirement
- tmux session name
- `WEEKLY_TAG=drone_2026w19`
- output directory under `weeklyresult/weekly_drone_2026w19/<candidate>/`
- startup first30 receipt requirements
- completion last50 + checkpoint + result tree requirements
- TFLite/TFLM export and ESP32 smoke gates

验收标准：
- 结论必须围绕 early CNN stem bottleneck，不是泛泛压缩。
- 至少一个候选应有合理机会达到 `<=1s` Invoke。
- 必须明确 accuracy/emergency recall 风险。
- 必须明确哪些建议需要代码改动，哪些需要服务器训练，哪些需要 ESP32 smoke 验证。
- 不产生训练结果声明。
```

## Prompt 5: Local Mac Training Agent - RT1S A/B Training

```text
你是 Drone 项目的本地训练 agent。本周 RT1S tiny-student 训练被用户明确批准为 Mac-local exception，目的是便于在 Codex app 中管理。默认 server-training policy 不变；这个例外只适用于 W19 RT1S A/B 两个候选。

任务目标：
在本地 Mac 上训练两个 RT1S tiny-student candidate，用来判断是否能在尽量保持 recognizer quality / emergency recall 的同时，把 ESP32 TFLM Invoke 推向 <=1s。

训练顺序：
1. `xiao_rt1s_c32_b256_tflm`
2. `xiao_rt1s_c24_b192_tflm`

禁止事项：
- 不改 paper。
- 不改 ESP32/Tello 代码。
- 不 merge W19 baseline result branch。
- 不覆盖 `B_small_teacher_student` 现有 artifact。
- 不把训练结果写成 ESP32 latency 已达标；board latency 必须由 deployment agent 后续实测。

必须先审计：
- git branch / HEAD / git status。
- 确认 training commit SHA。
- `src/model_config.py` 中两个 RT1S profile 是否存在。
- `docs/weekly_todo/2026/2026w19/todo.md` 的 W19 local training exception。
- teacher checkpoint 是否存在：
  `saved_models/weekly_drone_2026w17/B_small_teacher_student/teacher_clean_best.weights.h5`

统一运行设置：
- `WEEKLY_TAG=drone_2026w19`
- conda env: `drone`
- frontend: `(256,32,1)` logmel，不改 frontend。
- labels: `emergency`, `movement`, `unknown`
- `KD_USE_STATS_BRANCH=0`
- `KD_TEACHER_USE_STATS_BRANCH=0`
- `KD_TEACHER_MODEL_PROFILE=xiao_bottleneck256_tflm`
- `KD_REUSE_TEACHER=1`
- `KD_TEACHER_CKPT=saved_models/weekly_drone_2026w17/B_small_teacher_student/teacher_clean_best.weights.h5`
- `KD_DISTILL_VARIANT=embed_only`
- `KD_ENABLE_CLASS_PROSODY_AUG=1`
- `KD_STUDENT_ENABLE_PROSODY_AUG=1`
- `KD_TEACHER_ENABLE_PROSODY_AUG=0`

每个 candidate 的输出目录：
- `KD_MODEL_DIR=saved_models/weekly_drone_2026w19/<candidate>`
- `KD_RESULT_DIR=weeklyresult/weekly_drone_2026w19/<candidate>`
- `KD_HISTORY_DIR=weeklyresult/weekly_drone_2026w19/<candidate>/history`
- `KD_STUDENT_CKPT=saved_models/weekly_drone_2026w19/<candidate>/student_kd_best.weights.h5`

日志要求：
- 写入 `logs/weekly_drone_2026w19_<candidate>_local_<timestamp>.log`
- 启动回执必须包含 first 30 log lines。
- 完成回执必须包含 last 50 log lines、checkpoint path、result tree、key metrics。

建议命令模板：
```bash
export WEEKLY_TAG=drone_2026w19
export CANDIDATE=xiao_rt1s_c32_b256_tflm
export TS=$(date +"%Y%m%d_%H%M%S")
export LOG_FILE=logs/weekly_drone_2026w19_${CANDIDATE}_local_${TS}.log
mkdir -p logs weeklyresult/weekly_drone_2026w19/${CANDIDATE}/history saved_models/weekly_drone_2026w19/${CANDIDATE}

MPLCONFIGDIR=/tmp/matplotlib \
NUMBA_CACHE_DIR=/tmp/numba_cache \
conda run --no-capture-output -n drone bash -lc '
  export KD_MODEL_DIR=saved_models/weekly_drone_2026w19/'"${CANDIDATE}"'
  export KD_RESULT_DIR=weeklyresult/weekly_drone_2026w19/'"${CANDIDATE}"'
  export KD_HISTORY_DIR=weeklyresult/weekly_drone_2026w19/'"${CANDIDATE}"'/history
  export KD_STUDENT_CKPT=saved_models/weekly_drone_2026w19/'"${CANDIDATE}"'/student_kd_best.weights.h5
  export KD_TEACHER_CKPT=saved_models/weekly_drone_2026w17/B_small_teacher_student/teacher_clean_best.weights.h5
  export KD_TEACHER_MODEL_PROFILE=xiao_bottleneck256_tflm
  export KD_STUDENT_MODEL_PROFILE='"${CANDIDATE}"'
  export KD_REUSE_TEACHER=1
  export KD_USE_STATS_BRANCH=0
  export KD_TEACHER_USE_STATS_BRANCH=0
  export KD_DISTILL_VARIANT=embed_only
  export KD_ENABLE_CLASS_PROSODY_AUG=1
  export KD_STUDENT_ENABLE_PROSODY_AUG=1
  export KD_TEACHER_ENABLE_PROSODY_AUG=0
  python src/train_logmel_kd.py
' 2>&1 | tee "${LOG_FILE}"
```

第二个 candidate 把 `CANDIDATE` 改为 `xiao_rt1s_c24_b192_tflm`。

训练完成后必须汇报：
- branch / commit SHA / dirty status。
- command。
- log path。
- output tree。
- `run_config.json`。
- `classification_report_noisy.txt`。
- `student_history.csv` or equivalent history。
- checkpoint path。
- clean/noisy accuracy。
- emergency precision/recall/F1。
- 是否出现异常、OOM、NaN、early stop。

后续不由本 agent 做：
- full-int TFLite export。
- ESP32 board Invoke latency validation。
- paper claim writing。
```
