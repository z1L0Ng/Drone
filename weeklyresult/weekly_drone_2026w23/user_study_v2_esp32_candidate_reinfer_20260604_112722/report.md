# user_study_v2 ESP32 Candidate Re-Inference

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

- exact command: `env MPLCONFIGDIR=/tmp/matplotlib NUMBA_CACHE_DIR=/tmp/numba_cache TF_CPP_MIN_LOG_LEVEL=2 /opt/anaconda3/envs/drone/bin/python weeklyresult/weekly_drone_2026w23/user_study_v1_esp32_candidate_reinfer_20260604_025517/run_user_study_v1_reinfer.py --dataset-name user_study_v2 --input-root /Users/zilongzeng/Research/DroneControl/user_study_v2 --mode full --output-dir weeklyresult/weekly_drone_2026w23/user_study_v2_esp32_candidate_reinfer_20260604_112722`
- input data path: `/Users/zilongzeng/Research/DroneControl/user_study_v2`
- output path: `/Users/zilongzeng/Research/Drone/weeklyresult/weekly_drone_2026w23/user_study_v2_esp32_candidate_reinfer_20260604_112722`

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

- observed structure: `participant/Intent/index.wav`
- participant/user id: first-level directory name
- intent: second-level directory name, normalized to `emergency`, `movement`, `unknown`
- keyword: unavailable in the supplied SD path; keyword-plan inference was not used
- repeat/index: WAV filename stem, recorded as `repeat_idx`
- audio file format counts: {"channels": 1, "sample_rate_hz": 16000, "sample_width_bytes": 2}: 1462
- participants: 11 (`Hongjun, Junxi, Muyuan, Shujun, Weiqian, Weisi, Yueyuan, Yunfei, Zhejia, Zhuoran, Zilong`)
- valid trials: 1462
- skipped/invalid files: 0
- expected full intent grid if every participant had 3 intents x 50 files: 1650
- missing against that full grid: 188
- keyword encoded in SD path: False
- board logs inside input root: False
- external board event logs found: 24
- external board event logs with timing/log fields: 21
- board log join: External host logs exist outside the SD input root, but the provided SD tree is flattened as participant/intent/index.wav and does not preserve board keyword/capture-id paths. No board prediction is joined without an explicit path mapping.

## Final Metrics

- total trials: 1462
- overall accuracy: 0.7955
- macro F1: 0.7957
- emergency precision / recall / F1: 0.9323 / 0.6863 / 0.7906
- movement recall / F1: 0.8596 / 0.7947
- unknown false event rate: 0.1400

## Participant Summary

| participant | trials | accuracy | emergency recall | movement recall | unknown false event rate | macro F1 |
|---|---:|---:|---:|---:|---:|---:|
| Hongjun | 150 | 0.7533 | 0.5000 | 0.9000 | 0.1400 | 0.7436 |
| Junxi | 100 | 0.7500 | 0.5400 | 0.9600 | NA | 0.5096 |
| Muyuan | 150 | 0.7400 | 0.5000 | 0.8400 | 0.1200 | 0.7354 |
| Shujun | 150 | 0.8067 | 0.7200 | 0.8200 | 0.1200 | 0.8073 |
| Weiqian | 150 | 0.8133 | 0.7400 | 0.9600 | 0.2600 | 0.8117 |
| Weisi | 62 | 0.7742 | 0.7857 | 0.7500 | NA | 0.5372 |
| Yueyuan | 100 | 0.8700 | 0.7800 | 0.9600 | NA | 0.5994 |
| Yunfei | 150 | 0.8667 | 0.8800 | 0.8200 | 0.1000 | 0.8677 |
| Zhejia | 150 | 0.7867 | 0.7200 | 0.7600 | 0.1200 | 0.7886 |
| Zhuoran | 150 | 0.7000 | 0.7000 | 0.6400 | 0.2400 | 0.7023 |
| Zilong | 150 | 0.8867 | 0.7000 | 0.9800 | 0.0200 | 0.8820 |

## Intent Summary

| intent | support | precision | recall | F1 |
|---|---:|---:|---:|---:|
| emergency | 542 | 0.9323 | 0.6863 | 0.7906 |
| movement | 520 | 0.7388 | 0.8596 | 0.7947 |
| unknown | 400 | 0.7511 | 0.8600 | 0.8019 |

## Keyword Summary

Keyword-level metrics are not available from the supplied SD tree because keyword is not encoded in the path and keyword-plan inference was explicitly not used.

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
