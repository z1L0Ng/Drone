# initial_data ESP32 Candidate Re-Inference

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

- exact command: `env MPLCONFIGDIR=/tmp/matplotlib NUMBA_CACHE_DIR=/tmp/numba_cache TF_CPP_MIN_LOG_LEVEL=2 /opt/anaconda3/envs/drone/bin/python weeklyresult/weekly_drone_2026w23/user_study_v1_esp32_candidate_reinfer_20260604_025517/run_user_study_v1_reinfer.py --dataset-name initial_data --input-root /Users/zilongzeng/Documents/data --mode full --output-dir weeklyresult/weekly_drone_2026w23/initial_data_esp32_candidate_reinfer_20260604_114111`
- input data path: `/Users/zilongzeng/Documents/data`
- output path: `/Users/zilongzeng/Research/Drone/weeklyresult/weekly_drone_2026w23/initial_data_esp32_candidate_reinfer_20260604_114111`

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

- observed structures: `participant/intent/keyword/*.wav, participant/keyword/*.wav`
- participant/user id: first-level directory name
- intent: second-level intent directory when present; for early flat keyword directories, intent is assigned only by the documented legacy keyword mapping below
- keyword: third-level directory for intent-structured trials; second-level directory for early flat trials
- repeat/index: WAV filename stem, recorded as `repeat_idx`
- label source counts: intent_directory: 637, legacy_keyword_mapping: 575
- legacy flat keyword mapping used: true
- legacy mapping emergency keywords: `abort, freeze, help, hold, stop`
- legacy mapping movement keywords: `down, follow, forward, go, left, right, up`
- legacy mapping unknown keywords: `bed, bird, cat, dog, happy, no, one, two, wow, yes`
- audio file format counts: {"channels": 1, "sample_rate_hz": 16000, "sample_width_bytes": 2}: 1212
- participants: 8 (`Shujun, Weiqian, Zhejia, Zhuoran, hongjun, junxi, weisi, yueyuan`)
- valid trials: 1212
- skipped/invalid files: 0
- expected full intent grid if every participant had 3 intents x 50 files: 1200
- missing files against modern 3x50-per-participant reference grid: 152
- extra files against modern 3x50-per-participant reference grid: 164
- keyword encoded in SD path: True
- board logs inside input root: True
- input results.csv count: 5
- input board log rows: 637
- input board log rows with timing/log fields: 637
- external board event logs found: 24
- board log join: Input-root results.csv files are joined by participant, intent, keyword, and WAV filename. Flat legacy participant/keyword directories have no input results.csv rows and therefore keep empty board fields.
- trials with board prediction: 637
- recomputed-board agreement rate: 0.9733
- recomputed-board mismatch count: 17

## Final Metrics

- total trials: 1212
- overall accuracy: 0.4282
- macro F1: 0.4247
- emergency precision / recall / F1: 0.2861 / 0.3205 / 0.3023
- movement recall / F1: 0.5515 / 0.5028
- unknown false event rate: 0.5968

## Board Consistency

| trials with board prediction | agreement rate | mismatch count |
|---:|---:|---:|
| 637 | 0.9733 | 17 |

Mismatch examples are written to `board_mismatch_examples.csv`; first examples:
- Shujun/emergency/stop/1.wav: recomputed=movement, board=emergency, gt=emergency
- Weiqian/emergency/abort/36.wav: recomputed=movement, board=emergency, gt=emergency
- Weiqian/movement/left/74.wav: recomputed=movement, board=emergency, gt=movement
- Weiqian/unknown/happy/146.wav: recomputed=emergency, board=movement, gt=unknown
- weisi/emergency/freeze/24.wav: recomputed=unknown, board=emergency, gt=emergency

## Participant Summary

| participant | trials | accuracy | emergency recall | movement recall | unknown false event rate | macro F1 |
|---|---:|---:|---:|---:|---:|---:|
| Shujun | 150 | 0.5733 | 0.1200 | 0.8400 | 0.2400 | 0.5097 |
| Weiqian | 150 | 0.2200 | 0.3600 | 0.2200 | 0.9200 | 0.2033 |
| Zhejia | 150 | 0.5067 | 0.4400 | 0.5000 | 0.4200 | 0.5110 |
| Zhuoran | 150 | 0.6200 | 0.0600 | 0.9200 | 0.1200 | 0.5249 |
| hongjun | 117 | 0.3419 | 0.1000 | 0.5400 | 0.7660 | 0.3003 |
| junxi | 279 | 0.3405 | 0.3125 | 0.4423 | 0.7387 | 0.3353 |
| weisi | 37 | 0.8108 | 0.8108 | 0.0000 | NA | 0.2985 |
| yueyuan | 179 | 0.3687 | 0.3636 | 0.5185 | 0.7284 | 0.3682 |

## Intent Summary

| intent | support | precision | recall | F1 |
|---|---:|---:|---:|---:|
| emergency | 365 | 0.2861 | 0.3205 | 0.3023 |
| movement | 408 | 0.4620 | 0.5515 | 0.5028 |
| unknown | 439 | 0.5601 | 0.4032 | 0.4689 |

## Keyword Summary

| intent | keyword | support | accuracy | most common wrong prediction |
|---|---|---:|---:|---|
| emergency | abort | 47 | 0.2128 | movement |
| emergency | freeze | 116 | 0.2672 | unknown |
| emergency | help | 40 | 0.2250 | movement |
| emergency | hold | 50 | 0.3400 | movement |
| emergency | stop | 112 | 0.4464 | movement |
| movement | down | 40 | 0.5750 | emergency |
| movement | follow | 40 | 0.4750 | emergency |
| movement | forward | 40 | 0.3750 | emergency |
| movement | go | 80 | 0.4500 | emergency |
| movement | left | 88 | 0.4545 | emergency |
| movement | right | 80 | 0.7625 | unknown |
| movement | up | 40 | 0.7750 | emergency |
| unknown | bed | 40 | 0.3500 | movement |
| unknown | bird | 40 | 0.6500 | emergency |
| unknown | cat | 40 | 0.7250 | emergency |
| unknown | dog | 40 | 0.4250 | movement |
| unknown | happy | 40 | 0.7250 | emergency |
| unknown | no | 64 | 0.1094 | movement |
| unknown | one | 30 | 0.5000 | emergency |
| unknown | two | 18 | 0.3333 | emergency |
| unknown | wow | 64 | 0.2031 | emergency |
| unknown | yes | 63 | 0.3333 | emergency |

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
