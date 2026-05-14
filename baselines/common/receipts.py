"""Output schema and receipt helpers."""

from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Any


def git_head(cwd: str | Path = ".") -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(cwd), text=True).strip()
    except Exception:
        return "unknown"


def git_branch(cwd: str | Path = ".") -> str:
    try:
        return subprocess.check_output(["git", "branch", "--show-current"], cwd=str(cwd), text=True).strip()
    except Exception:
        return "unknown"


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def source_manifest(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "git_branch": git_branch(),
        "git_head": git_head(),
        "python_version": platform.python_version(),
        "scaffold": "project-local minimal reimplementation",
    }
    try:
        import tensorflow as tf

        manifest["tensorflow_version"] = str(tf.__version__)
    except Exception as exc:
        manifest["tensorflow_version"] = f"unavailable: {exc}"
    try:
        import keras

        manifest["keras_version"] = str(keras.__version__)
    except Exception as exc:
        manifest["keras_version"] = f"unavailable: {exc}"
    if extra:
        manifest.update(extra)
    return manifest


def result_tree(root: str | Path) -> str:
    base = Path(root)
    if not base.exists():
        return f"{base} (missing)"
    lines: list[str] = []
    for dirpath, _, filenames in os.walk(base):
        rel_dir = Path(dirpath).relative_to(base)
        prefix = "." if str(rel_dir) == "." else str(rel_dir)
        for filename in sorted(filenames):
            lines.append(f"{prefix}/{filename}")
    return "\n".join(lines)


def write_output_schema_stubs(output_dir: str | Path, config: dict[str, Any]) -> None:
    """Create non-training schema stubs for future server runs.

    This is not called by default smoke checks because the current task forbids
    launching training, not writing code. Future approved setup can call it when
    preparing a run directory.
    """
    out = Path(output_dir)
    (out / "history").mkdir(parents=True, exist_ok=True)
    (out / "checkpoints").mkdir(parents=True, exist_ok=True)
    (out / "receipts").mkdir(parents=True, exist_ok=True)
    write_json(out / "run_config.json", config)
    write_json(out / "source_manifest.json", source_manifest())


def write_text(path: str | Path, text: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
