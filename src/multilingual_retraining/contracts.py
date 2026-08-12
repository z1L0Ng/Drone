"""Frozen code-level contracts for the W33 multilingual preparation lane."""

LABELS = ("emergency", "movement", "unknown")
LABEL_TO_INDEX = {label: index for index, label in enumerate(LABELS)}
LANGUAGES = ("en", "es", "de")
SPLITS = ("train", "validation_selection", "validation_calibration", "test")

MANIFEST_SCHEMA = "drone.multilingual_audio_manifest.v0"
VALIDATION_RECEIPT_SCHEMA = "drone.multilingual_manifest_validation_receipt.v0"
CONFIG_SCHEMA = "drone.multilingual_retraining_config.v0"
START_RECEIPT_SCHEMA = "drone.multilingual_run_start_receipt.v0"
COMPLETION_RECEIPT_SCHEMA = "drone.multilingual_run_completion_receipt.v0"
ABORT_RECEIPT_SCHEMA = "drone.multilingual_run_abort_receipt.v0"
PREDICTION_SCHEMA = "drone.multilingual_prediction.v0"
METRICS_SCHEMA = "drone.multilingual_metrics.v0"

WEEKLY_OUTPUT_PREFIX = "weeklyresult/weekly_drone_2026w33"
