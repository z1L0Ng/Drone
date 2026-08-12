from __future__ import annotations

import tempfile
import unittest
from collections import Counter
from pathlib import Path

import numpy as np

from src.multilingual_retraining.config import load_config
from src.multilingual_retraining.contracts import LABELS
from src.multilingual_retraining.frontend import extract_logmel_input, load_exact_mono_pcm, tensor_sha256
from src.multilingual_retraining.metrics import compute_metrics, fit_temperature, temperature_scale
from src.multilingual_retraining.sampler import balanced_epoch_indices

from tests.multilingual_retraining.fixture_factory import create_fixture


REPO_ROOT = Path(__file__).resolve().parents[2]


class SamplerMetricsFrontendTest(unittest.TestCase):
    def test_balanced_sampler_equalizes_language_class_cells(self) -> None:
        records = []
        for language in ("en", "es", "de"):
            for label in LABELS:
                for speaker in range(1 + (language == "en")):
                    records.append(
                        {
                            "language": language,
                            "label": label,
                            "source_word": f"word-{label}-{speaker % 2}",
                            "speaker_id": f"speaker-{language}-{label}-{speaker}",
                            "voice_id": "",
                        }
                    )
        indices = balanced_epoch_indices(records, ("en", "es", "de"), LABELS, 90, 1234)
        counts = Counter((records[index]["language"], records[index]["label"]) for index in indices)
        self.assertEqual(set(counts.values()), {10})
        self.assertEqual(indices, balanced_epoch_indices(records, ("en", "es", "de"), LABELS, 90, 1234))

    def test_frontend_matches_explicit_256x32_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = create_fixture(Path(temporary))
            audio_path = next(fixture["audio_root"].rglob("*.wav"))
            waveform = load_exact_mono_pcm(audio_path)
            config = load_config(
                REPO_ROOT / "config/multilingual_2026w33/en_only_anchor_v0.json"
            ).effective
            first = extract_logmel_input(waveform, config["frontend"])
            second = extract_logmel_input(waveform, config["frontend"])
            self.assertEqual(first.shape, (256, 32, 1))
            self.assertEqual(first.dtype, np.float32)
            self.assertEqual(tensor_sha256(first), tensor_sha256(second))
            self.assertTrue(np.array_equal(first, second))

    def test_metrics_and_validation_only_temperature(self) -> None:
        truth = np.asarray([0, 1, 2, 0, 1, 2])
        probabilities = np.asarray(
            [
                [0.8, 0.1, 0.1],
                [0.1, 0.7, 0.2],
                [0.2, 0.2, 0.6],
                [0.4, 0.5, 0.1],
                [0.6, 0.3, 0.1],
                [0.7, 0.1, 0.2],
            ]
        )
        languages = ["en", "en", "es", "es", "de", "de"]
        metrics = compute_metrics(truth, probabilities, languages, ece_bins=5)
        self.assertEqual(metrics["support"], 6)
        self.assertIn("de|movement", metrics["per_language_class"])
        self.assertEqual(metrics["unknown_false_emergency"]["count"], 1)
        calibration = fit_temperature(probabilities, truth)
        calibrated = temperature_scale(probabilities, calibration["temperature"])
        self.assertTrue(np.allclose(np.sum(calibrated, axis=1), 1.0))


if __name__ == "__main__":
    unittest.main()
