# Startup Receipt

- timestamp: `2026-06-04T17:12:17`
- commit_sha: `0f3da223f64689cfa5103b6dfdf5cd5f137f313f`
- git_branch: `main`
- exact_command: `MPLCONFIGDIR=/tmp/matplotlib NUMBA_CACHE_DIR=/tmp/numba_cache NUMBA_DISABLE_JIT=1 KMP_DUPLICATE_LIB_OK=TRUE conda run -n drone python scripts/eval_asr_stt_intent_baseline.py --asr-system whisper --model-name tiny.en --condition-slug snr_m10db --limit 100 --progress-every 10 --output-dir weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604_smoke`
- python_executable: `/opt/anaconda3/envs/drone/bin/python`
- python_version: `3.11.13`
- asr_system: `whisper`
- asr_model: `tiny.en`
- asr_device: `cpu`
- model_cache_dir: `weeklyresult/weekly_drone_2026w23/asr_stt_model_cache/whisper`
- input_split: `dataset/processed/data_paths.npz`
- noise_manifest: `weeklyresult/weekly_drone_2026w23/rotor_noise_snr_matrix_20260603/run_manifest.json`
- noise_source: `dataset/raw/tellonoise`
- noise_condition: `snr_m10db` / `-10.0` dB
- output_directory: `weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604_smoke`
