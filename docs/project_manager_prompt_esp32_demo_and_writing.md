# Project Manager Prompt: ESP32 Demo And SenSys Writing Plan

Use this prompt to hand the current state to the project management agent.

```text
你是 Drone 项目的项目管理 agent。请根据当前 ESP32 realworld 进展，重新规划下一阶段工作，目标是服务 SenSys 2027 first-round submission。

核心背景：
- 本周 ESP32/XIAO realworld 线已经从 host-backed 推理推进到板端完整推理。
- 当前稳定 baseline 是 XIAO ESP32-S3 Sense 本地流程：
  ESP32 onboard mic capture -> logmel frontend -> full-integer TFLM inference -> USB CDC result reporting.
- 固件路径：
  realworld/esp32/firmware/esp32_local_cdc_fast/esp32_local_cdc_fast.ino
- 当前模型候选：
  realworld/esp32/models/B_small_teacher_student/student_kd_best.weights.h5
  realworld/esp32/phase2_artifacts/B_small_teacher_student_full_integer.tflite
- 当前稳定性报告：
  weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_report.md
- 关键实测结果：
  total_triggers=30
  success_rate=1.0000
  drop_rate=0.0000
  capture_p50_ms=926
  frontend_p50_ms=55
  infer_p50_ms=2094
  total_p50_ms=3075
  raw_uniform_count=0
  gate_pass=1
- 我和实验室学长讨论后认为：ESP32-S3 上约 2 秒推理开销对当前 prototype 是正常且可接受的，不再把它作为当前阶段主阻塞。

本周核心结论：
- ESP32 板端音频采集、logmel、int8 TFLM 推理已经功能稳定。
- 目前不要继续把主要精力放在模型压缩或进一步降低板端推理时间。
- 下一阶段重点改为：打通 ESP32 推理结果到 drone 控制链路，形成可展示 demo，并把系统证据写进 SenSys 2027 投稿计划。

请你做以下规划：
1. 更新项目状态判断：
   - Phase 1 USB CDC host inference：已通过并收尾。
   - Phase 2 ESP32 本地推理：已通过功能稳定性 gate。
   - 当前未完成主线：ESP32-to-drone 控制链路、demo protocol、论文系统证据。
2. 给出下一阶段 1-2 周执行计划，优先级必须是：
   - 安全控制链路设计
   - dry-run / no-propeller bench loop
   - Tello 或 drone command bridge
   - demo 日志与视频/图示素材
   - SenSys paper section update
3. 明确不要默认派发新的模型训练任务，除非 demo 证明当前 2s 推理延迟不可接受。
4. 规划时必须包含安全状态机，至少覆盖：
   - IDLE
   - LISTENING
   - INTENT_PENDING
   - CONFIRMED_EMERGENCY
   - CONFIRMED_MOVEMENT
   - SAFE_HOLD
   - ERROR_HOLD
5. 规划 demo 验收指标，至少包含：
   - end-to-end command latency
   - successful command ack rate
   - false-trigger rate
   - emergency stop/hold success rate
   - complete event log coverage
6. 写作规划必须落到：
   - docs/paper_sensys2027/
   - Prototype / Real-World Setup
   - Evaluation
   - System Design
   - Figure plan: system path, state machine, prototype photo/schematic, timing breakdown.
7. 证据路径必须引用：
   - docs/realworld_esp32_weekly_project_report_handoff.md
   - weeklyresult/weekly_drone_2026w17/realworld/esp32_bench/local_cdc_fast_v4_stability30_report.md
   - realworld/esp32/PHASE2_OPTIMIZATION_ATTEMPTS.md
   - realworld/deployment_plan_xiaoesp32s3_tello_2026w16.md
   - docs/paper_sensys2027/WRITING_OUTLINE.md

输出格式：
1. 当前项目状态
2. 本周可汇报成果
3. 下一阶段目标
4. 1-2 周任务拆解
5. 各 agent 分工
6. Demo gate
7. Paper writing gate
8. 风险与 fallback
9. 需要用户批准的事项
```
