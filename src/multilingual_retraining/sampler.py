"""Deterministic comparison-lane sampling policies."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np


class SamplerError(ValueError):
    """Raised when a lane cannot satisfy its declared sampling contract."""


def derive_seed(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int(hashlib.sha256(payload).hexdigest()[:8], 16)


class _Cycle:
    def __init__(self, values: Iterable[Any], rng: np.random.Generator):
        self.values = list(values)
        if not self.values:
            raise SamplerError("cannot construct an empty sampler cycle")
        self.rng = rng
        self.position = 0
        self.order: List[Any] = []

    def next(self) -> Any:
        if self.position >= len(self.order):
            permutation = self.rng.permutation(len(self.values))
            self.order = [self.values[int(index)] for index in permutation]
            self.position = 0
        value = self.order[self.position]
        self.position += 1
        return value


def uniform_epoch_indices(records: Sequence[Mapping[str, Any]], epoch_size: int, seed: int) -> List[int]:
    if not records or epoch_size <= 0:
        raise SamplerError("uniform sampler requires records and a positive epoch_size")
    rng = np.random.default_rng(seed)
    result: List[int] = []
    cycle = _Cycle(range(len(records)), rng)
    for _ in range(epoch_size):
        result.append(int(cycle.next()))
    return result


def balanced_epoch_indices(
    records: Sequence[Mapping[str, Any]],
    languages: Sequence[str],
    labels: Sequence[str],
    epoch_size: int,
    seed: int,
) -> List[int]:
    """Balance language/class first, then word and speaker within each cell.

    Sampling is with replacement across exhausted cycles. ``source_word`` and
    speaker/voice identity affect sampling only and never enter model features.
    """

    if not records or epoch_size <= 0:
        raise SamplerError("balanced sampler requires records and a positive epoch_size")
    rng = np.random.default_rng(seed)
    cell_records: Dict[Tuple[str, str], List[int]] = defaultdict(list)
    word_records: Dict[Tuple[str, str, str], List[int]] = defaultdict(list)
    speaker_records: Dict[Tuple[str, str, str, str], List[int]] = defaultdict(list)

    for index, record in enumerate(records):
        language = str(record["language"])
        label = str(record["label"])
        word = str(record["source_word"])
        speaker = str(record.get("speaker_id") or record.get("voice_id"))
        cell_records[(language, label)].append(index)
        word_records[(language, label, word)].append(index)
        speaker_records[(language, label, word, speaker)].append(index)

    required_cells = [(language, label) for language in languages for label in labels]
    missing = [cell for cell in required_cells if not cell_records.get(cell)]
    if missing:
        raise SamplerError(f"balanced lane is missing language/class cells: {missing}")

    cell_cycle = _Cycle(required_cells, rng)
    word_cycles: Dict[Tuple[str, str], _Cycle] = {}
    speaker_cycles: Dict[Tuple[str, str, str], _Cycle] = {}
    record_cycles: Dict[Tuple[str, str, str, str], _Cycle] = {}

    for language, label in required_cells:
        words = sorted({str(records[index]["source_word"]) for index in cell_records[(language, label)]})
        word_cycles[(language, label)] = _Cycle(words, rng)
        for word in words:
            indices = word_records[(language, label, word)]
            speakers = sorted(
                {str(records[index].get("speaker_id") or records[index].get("voice_id")) for index in indices}
            )
            speaker_cycles[(language, label, word)] = _Cycle(speakers, rng)
            for speaker in speakers:
                record_cycles[(language, label, word, speaker)] = _Cycle(
                    speaker_records[(language, label, word, speaker)], rng
                )

    result: List[int] = []
    for _ in range(epoch_size):
        language, label = cell_cycle.next()
        word = word_cycles[(language, label)].next()
        speaker = speaker_cycles[(language, label, word)].next()
        result.append(int(record_cycles[(language, label, word, speaker)].next()))
    return result


def epoch_indices(
    records: Sequence[Mapping[str, Any]],
    mode: str,
    languages: Sequence[str],
    labels: Sequence[str],
    epoch_size: int,
    seed: int,
) -> List[int]:
    if mode == "uniform_examples":
        return uniform_epoch_indices(records, epoch_size, seed)
    if mode == "language_class_word_speaker_balanced":
        return balanced_epoch_indices(records, languages, labels, epoch_size, seed)
    raise SamplerError(f"unsupported sampler mode: {mode}")
