from __future__ import annotations

import os
import unittest
from pathlib import Path

import numpy as np

from src.multilingual_retraining.config import load_config


REPO_ROOT = Path(__file__).resolve().parents[2]


class ModelContractTest(unittest.TestCase):
    def test_current_project_model_accepts_shared_input_and_emits_three_class_softmax(self) -> None:
        os.environ.setdefault("MPLCONFIGDIR", "/tmp/drone_w33_matplotlib")
        os.environ.setdefault("XDG_CACHE_HOME", "/tmp/drone_w33_cache")
        import tensorflow as tf

        from src.model import build_model
        from src.model_config import get_model_kwargs

        config = load_config(
            REPO_ROOT / "config/multilingual_2026w33/en_only_anchor_v0.json"
        ).effective
        tf.keras.backend.clear_session()
        tf.keras.utils.set_random_seed(123)
        model = build_model(
            tuple(config["model"]["input_shape"]),
            config["model"]["num_classes"],
            **get_model_kwargs(config["model"]["profile"]),
        )
        output = model(np.zeros((1, 256, 32, 1), dtype=np.float32), training=False).numpy()
        self.assertEqual(model.input_shape, (None, 256, 32, 1))
        self.assertEqual(model.output_shape, (None, 3))
        self.assertEqual(output.shape, (1, 3))
        self.assertTrue(np.all(np.isfinite(output)))
        self.assertTrue(np.allclose(np.sum(output, axis=1), 1.0, atol=1e-6))


if __name__ == "__main__":
    unittest.main()
