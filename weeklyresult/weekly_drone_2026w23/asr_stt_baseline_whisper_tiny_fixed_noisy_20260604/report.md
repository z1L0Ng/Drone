# ASR/STT Intent Parser Baseline

Status: FULL local evaluation.

## Runtime Summary

- ASR system/model: `whisper` / `tiny.en`
- Device: `cpu`
- Condition: `snr_m10db` (`-10.0` dB)
- Total samples requested: `10008`
- Transcript count: `10008`
- Parsed count: `10008`
- Skipped/failed files: `0`
- Total run time: `805.58` s
- Median/p95 ASR latency: `0.0618` / `0.0861` s
- Model cache size: `75571315` bytes

## Metric Summary

- transcript non-empty rate: `0.4253`
- keyword hit rate: `0.1225`
- intent parse accuracy: `0.4294`
- intent parse macro F1: `0.3503`
- emergency recall: `0.2209`
- unknown false action rate: `0.0204`
- parse failure rate: `0.0000`

## Deployment Caveat

Whisper tiny.en is a transcript-first ASR baseline; it is not an MCU-deployable intent-event recognizer and requires PyTorch-class runtime.

## Result Tree

```text
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604/classification_report_intent_parse.txt	380 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604/confusion_matrix_intent_parse.csv	103 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604/latency_summary.json	453 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604/metrics.json	1827 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604/parsed_intents.csv	463781 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604/report.md	867 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604/run_manifest.json	4698 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604/startup_receipt.md	1097 bytes
weeklyresult/weekly_drone_2026w23/asr_stt_baseline_whisper_tiny_fixed_noisy_20260604/transcripts.csv	1759916 bytes
```
