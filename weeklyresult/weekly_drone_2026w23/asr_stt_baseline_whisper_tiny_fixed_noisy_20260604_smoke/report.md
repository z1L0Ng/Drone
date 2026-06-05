# ASR/STT Intent Parser Baseline

Status: SMOKE local evaluation.

## Runtime Summary

- ASR system/model: `whisper` / `tiny.en`
- Device: `cpu`
- Condition: `snr_m10db` (`-10.0` dB)
- Total samples requested: `100`
- Transcript count: `100`
- Parsed count: `100`
- Skipped/failed files: `0`
- Total run time: `9.33` s
- Median/p95 ASR latency: `0.0610` / `0.1839` s
- Model cache size: `75571315` bytes

## Metric Summary

- transcript non-empty rate: `0.4700`
- keyword hit rate: `0.0900`
- intent parse accuracy: `0.3600`
- intent parse macro F1: `0.2791`
- emergency recall: `0.1471`
- unknown false action rate: `0.0000`
- parse failure rate: `0.0000`

## Deployment Caveat

Whisper tiny.en is a transcript-first ASR baseline; it is not an MCU-deployable intent-event recognizer and requires PyTorch-class runtime.

## Result Tree

```text
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604_smoke/classification_report_intent_parse.txt	380 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604_smoke/confusion_matrix_intent_parse.csv	89 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604_smoke/latency_summary.json	456 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604_smoke/metrics.json	1642 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604_smoke/parsed_intents.csv	4557 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604_smoke/report.md	860 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604_smoke/result_tree.txt	1103 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604_smoke/run_manifest.json	4423 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604_smoke/startup_receipt.md	1120 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604_smoke/transcripts.csv	21358 bytes
```
