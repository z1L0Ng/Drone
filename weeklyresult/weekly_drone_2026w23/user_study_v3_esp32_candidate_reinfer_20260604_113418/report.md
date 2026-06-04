# user_study_v3 ESP32 Candidate Re-Inference

Claim boundary: this is controlled user-study SD audio reinference with the local ESP32 candidate recognizer. It is not live-flight validation and not semantic safety validation.

## Run Context

- branch: `main`
- HEAD: `b98af4af0b30f46d1aef5e8dc1e2b2309ba0ad8a`
- dirty status:

```text
## main...origin/main
 M .DS_Store
 M docs/.DS_Store
 D docs/paper_sensys2027/figures/acc_original_vs_finetuned.png
 M docs/paper_sensys2027/figures/figure1.png
 D docs/paper_sensys2027/figures/prototype_pipeline.tex
 M docs/paper_sensys2027/figures/recognizer_architecture.pdf
 D docs/paper_sensys2027/figures/recognizer_architecture.tex
 M docs/paper_sensys2027/figures/response_time_breakdown.pdf
 D docs/paper_sensys2027/figures/response_time_breakdown.tex
 M docs/paper_sensys2027/figures/safety_state_flow.tex
 D docs/paper_sensys2027/figures/source/recognizer_architecture.drawio
 D docs/paper_sensys2027/figures/source/system_architecture.drawio
 D docs/paper_sensys2027/figures/source/user_study_evidence.pptx
 M docs/paper_sensys2027/figures/system_architecture.pdf
 D docs/paper_sensys2027/figures/system_architecture.tex
 D docs/paper_sensys2027/figures/user_study_evidence.pdf
 D docs/paper_sensys2027/figures/user_study_evidence.tex
 M docs/paper_sensys2027/main.tex
 M docs/paper_sensys2027/sections/1introduction.tex
 M docs/paper_sensys2027/sections/3motivation.tex
 M docs/paper_sensys2027/sections/4architecture.tex
 M docs/paper_sensys2027/sections/5recognizer.tex
 M docs/paper_sensys2027/sections/6prototype.tex
 M docs/paper_sensys2027/sections/7evaluation.tex
 M docs/paper_sensys2027/sections/8conclusion.tex
 M scripts/paper_figures/plot_response_time_breakdown.py
?? docs/paper_sensys2027/figures/emergency_stop_sequence.pdf
?? scripts/eval_rotor_noise_snr_matrix.py
?? scripts/paper_figures/build_emergency_stop_sequence.py
?? scripts/paper_figures/render_figure1_opening_scenario.py
?? scripts/paper_figures/render_recognizer_architecture_graphviz.sh
?? scripts/paper_figures/render_system_architecture_plantuml.sh
?? weeklyresult/weekly_drone_2026w23/
```

- exact command: `env MPLCONFIGDIR=/tmp/matplotlib NUMBA_CACHE_DIR=/tmp/numba_cache TF_CPP_MIN_LOG_LEVEL=2 /opt/anaconda3/envs/drone/bin/python weeklyresult/weekly_drone_2026w23/user_study_v1_esp32_candidate_reinfer_20260604_025517/run_user_study_v1_reinfer.py --dataset-name user_study_v3 --input-root /Users/zilongzeng/Research/DroneControl/user_study_v3 --mode full --output-dir weeklyresult/weekly_drone_2026w23/user_study_v3_esp32_candidate_reinfer_20260604_113418`
- input data path: `/Users/zilongzeng/Research/DroneControl/user_study_v3`
- output path: `/Users/zilongzeng/Research/Drone/weeklyresult/weekly_drone_2026w23/user_study_v3_esp32_candidate_reinfer_20260604_113418`

## Model And Frontend

- selected model: `xiao_rt1s_c32_b256_samearch_ts`
- selection rationale: Current ESP32 user-study CDC+SD firmware config and host capture script name xiao_rt1s_c32_b256_samearch_ts as runtime candidate.
- other candidate considered: `B_small_teacher_student` exists as a frozen deployment artifact, but it is not the runtime candidate named by the current CDC+SD firmware.
- model path: `/Users/zilongzeng/Research/Drone/weeklyresult/weekly_drone_2026w19/realworld/esp32_rt1s_c32_validation/xiao_rt1s_c32_b256_samearch_ts_full_integer.tflite`
- model sha256: `e43cc3f7b7f7e2413bdc35765bca5d45473b5b1b63fdee1a0a28d3e9de0d2ab8`
- model metadata: `/Users/zilongzeng/Research/Drone/weeklyresult/weekly_drone_2026w19/realworld/esp32_rt1s_c32_validation/MODEL_TEST_INFO.json`
- run config: `/Users/zilongzeng/Research/Drone/weeklyresult/weekly_drone_2026w19/xiao_rt1s_c32_b256_samearch_ts/run_config.json`
- frontend config: `/Users/zilongzeng/Research/Drone/src/model_config.py`
- frontend shared implementation: `/Users/zilongzeng/Research/Drone/src/logmel_frontend_shared.py`
- ESP32 frontend constants: `/Users/zilongzeng/Research/Drone/realworld/esp32/firmware/esp32_local_cdc/frontend_constants.h`
- label mapping: `/Users/zilongzeng/Research/Drone/saved_models/label_encoder.joblib` -> `emergency, movement, unknown`
- frontend parameters: sample_rate=16000 Hz, window=16000 samples, n_fft=1024, hop=512, center=False, n_mels=256, fmin=50 Hz, fmax=None, top_db=80, max_frames=32
- quantization: input `[0.3137255012989044, 127]`, output `[0.00390625, -128]`

## Input Data Audit

- observed structures: `participant/intent/keyword/*.wav`
- participant/user id: first-level directory name
- intent: second-level intent directory when present; for early flat keyword directories, intent is assigned only by the documented legacy keyword mapping below
- keyword: third-level directory for intent-structured trials; second-level directory for early flat trials
- repeat/index: WAV filename stem, recorded as `repeat_idx`
- label source counts: intent_directory: 1462
- legacy flat keyword mapping used: false
- audio file format counts: {"channels": 1, "sample_rate_hz": 16000, "sample_width_bytes": 2}: 1462
- participants: 11 (`Hongjun, Junxi, Muyuan, Shujun, Weiqian, Weisi, Yueyuan, Yunfei, Zhejia, Zhuoran, Zilong`)
- valid trials: 1462
- skipped/invalid files: 0
- expected full intent grid if every participant had 3 intents x 50 files: 1650
- missing files against modern 3x50-per-participant reference grid: 188
- extra files against modern 3x50-per-participant reference grid: 0
- keyword encoded in SD path: True
- board logs inside input root: False
- input results.csv count: 0
- input board log rows: 0
- input board log rows with timing/log fields: 0
- external board event logs found: 24
- board log join: Input-root results.csv files are joined by participant, intent, keyword, and WAV filename. Flat legacy participant/keyword directories have no input results.csv rows and therefore keep empty board fields.
- trials with board prediction: 0
- recomputed-board agreement rate: NA
- recomputed-board mismatch count: 0

## Final Metrics

- total trials: 1462
- overall accuracy: 0.7264
- macro F1: 0.7268
- emergency precision / recall / F1: 0.8466 / 0.5904 / 0.6957
- movement recall / F1: 0.8173 / 0.7309
- unknown false event rate: 0.2075

## Board Consistency

| trials with board prediction | agreement rate | mismatch count |
|---:|---:|---:|
| 0 | NA | 0 |

## Participant Summary

| participant | trials | accuracy | emergency recall | movement recall | unknown false event rate | macro F1 |
|---|---:|---:|---:|---:|---:|---:|
| Hongjun | 150 | 0.7533 | 0.4800 | 0.9200 | 0.1400 | 0.7445 |
| Junxi | 100 | 0.6700 | 0.4400 | 0.9000 | NA | 0.4482 |
| Muyuan | 150 | 0.7467 | 0.4400 | 0.8800 | 0.0800 | 0.7365 |
| Shujun | 150 | 0.7467 | 0.6000 | 0.8200 | 0.1800 | 0.7451 |
| Weiqian | 150 | 0.5733 | 0.1200 | 0.8400 | 0.2400 | 0.5097 |
| Weisi | 62 | 0.8226 | 0.8333 | 0.8000 | NA | 0.5531 |
| Yueyuan | 100 | 0.9200 | 0.8600 | 0.9800 | NA | 0.6317 |
| Yunfei | 150 | 0.8467 | 0.8000 | 0.8000 | 0.0600 | 0.8463 |
| Zhejia | 150 | 0.7933 | 0.7800 | 0.7600 | 0.1600 | 0.7960 |
| Zhuoran | 150 | 0.7133 | 0.7400 | 0.7800 | 0.3800 | 0.7126 |
| Zilong | 150 | 0.5067 | 0.4400 | 0.5000 | 0.4200 | 0.5110 |

## Intent Summary

| intent | support | precision | recall | F1 |
|---|---:|---:|---:|---:|
| emergency | 542 | 0.8466 | 0.5904 | 0.6957 |
| movement | 520 | 0.6610 | 0.8173 | 0.7309 |
| unknown | 400 | 0.7188 | 0.7925 | 0.7539 |

## Keyword Summary

| intent | keyword | support | accuracy | most common wrong prediction |
|---|---|---:|---:|---|
| emergency | abort | 20 | 0.2000 | movement |
| emergency | freeze | 20 | 0.1500 | unknown |
| emergency | help | 20 | 0.3000 | movement |
| emergency | hold | 20 | 0.1500 | movement |
| emergency | stop | 20 | 0.6000 | movement |
| emergency | unavailable_in_sd_path | 442 | 0.6606 | movement |
| movement | forward | 20 | 0.3000 | emergency |
| movement | go | 20 | 0.7500 | emergency |
| movement | left | 20 | 0.8000 | emergency |
| movement | right | 20 | 0.7000 | unknown |
| movement | unavailable_in_sd_path | 420 | 0.8524 | unknown |
| movement | up | 20 | 0.8000 | emergency |
| unknown | bed | 20 | 0.3000 | movement |
| unknown | bird | 20 | 0.7500 | movement |
| unknown | cat | 20 | 0.8500 | movement |
| unknown | dog | 20 | 0.5000 | movement |
| unknown | happy | 20 | 0.9500 | movement |
| unknown | unavailable_in_sd_path | 300 | 0.8333 | movement |

## Skipped Or Invalid Files

No invalid WAV files were skipped.

## Artifact Paths

- `trial_predictions.csv`
- `participant_summary.csv`
- `intent_summary.csv`
- `keyword_summary.csv`
- `confusion_matrix.csv`
- `run_manifest.json`
- `latex_tables.md`
- `missing_expected_trials.csv`
- `skipped_invalid.csv`
- `legacy_keyword_mapping.json`
- `board_consistency.csv`
- `board_mismatch_examples.csv`
