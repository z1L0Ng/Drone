"""Immutable receipt helpers for clean-slate multilingual runs."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from .config import sha256_file


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: str | Path, value: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, target)


def write_jsonl(path: str | Path, rows: Iterable[Mapping[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    os.replace(temporary, target)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def git_identity(root: str | Path) -> Dict[str, Any]:
    repo = Path(root).resolve()
    return {
        "commit": _git(repo, "rev-parse", "HEAD"),
        "branch": _git(repo, "branch", "--show-current") or None,
        "status": _git(repo, "status", "--porcelain"),
    }


def runtime_environment(repo_root: str | Path) -> Dict[str, Any]:
    root = Path(repo_root).resolve()
    versions: Dict[str, Any] = {}
    for module_name in ("numpy", "scipy", "librosa", "soundfile"):
        try:
            module = __import__(module_name)
            versions[module_name] = getattr(module, "__version__", "unknown")
        except Exception as exc:  # environment evidence must preserve failures
            versions[module_name] = f"unavailable:{type(exc).__name__}"
    environment_file = root / "environment.yml"
    return {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "packages": versions,
        "environment_yml_sha256": sha256_file(environment_file) if environment_file.exists() else None,
    }


def hash_inventory(root: str | Path, exclude_names: Iterable[str] = ()) -> Dict[str, str]:
    directory = Path(root)
    excluded = set(exclude_names)
    result: Dict[str, str] = {}
    for path in sorted(candidate for candidate in directory.rglob("*") if candidate.is_file()):
        relative = path.relative_to(directory).as_posix()
        if relative in excluded or path.name.endswith(".tmp"):
            continue
        result[relative] = sha256_file(path)
    return result
