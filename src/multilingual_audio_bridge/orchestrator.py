"""Resumable S0-S3 server orchestration with fail-closed stage receipts."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, Mapping

from src.multilingual_three_class_intake import (
    load_json_yaml,
    run_feasibility,
    validate_config,
    validate_config_artifacts,
)

from .acquisition import APPROVAL_ENV, acquire, load_plan, plan_summary
from .contracts import (
    ABORT_RECEIPT_SCHEMA,
    STAGE_RECEIPT_SCHEMA,
    BridgeError,
    atomic_json,
    sha256_file,
)
from .manifest import produce_frozen_manifest
from .materialize import (
    SPLIT_FREEZE_APPROVAL_ENV,
    freeze_metadata_proposal,
    load_frozen_proposal,
    materialize,
)
from .metadata_bootstrap import bootstrap_metadata


STAGES = ("S0", "S1", "S2", "S3")
AUDIO_TRANSFORM_APPROVAL_ENV = "DRONE_W33_AUDIO_TRANSFORM_APPROVED"
MANIFEST_FREEZE_APPROVAL_ENV = "DRONE_W33_MANIFEST_FREEZE_APPROVED"


def _stage_path(root: Path, stage: str) -> Path:
    return root / "receipts" / "stages" / f"{stage}.json"


def _load_json(path: Path) -> Dict[str, Any]:
    import json

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BridgeError(f"cannot load stage receipt {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BridgeError(f"stage receipt must be a JSON object: {path}")
    return value


def _require_previous(root: Path, stage: str) -> None:
    index = STAGES.index(stage)
    if index == 0:
        return
    previous = STAGES[index - 1]
    path = _stage_path(root, previous)
    if not path.is_file():
        raise BridgeError(f"{stage} requires passing {previous} receipt")
    receipt = _load_json(path)
    if receipt.get("schema_version") != STAGE_RECEIPT_SCHEMA or receipt.get("status") != "pass":
        raise BridgeError(f"{stage} requires passing {previous} receipt")
    for artifact_path, expected_sha in receipt.get("result", {}).get("artifacts", {}).items():
        artifact = Path(artifact_path)
        if not artifact.is_file() or sha256_file(artifact) != expected_sha:
            raise BridgeError(
                f"{stage} previous-stage artifact no longer verifies: {artifact}"
            )


def _previous_stage_sha256(root: Path, stage: str) -> str:
    _require_previous(root, stage)
    return sha256_file(_stage_path(root, STAGES[STAGES.index(stage) - 1]))


def _nearest_existing_path(path: Path) -> Path:
    candidate = path.resolve()
    while not candidate.exists():
        if candidate.parent == candidate:
            raise BridgeError(f"cannot find an existing path for space probe: {path}")
        candidate = candidate.parent
    return candidate


def _run_stage(
    root: Path,
    stage: str,
    input_hashes: Mapping[str, str],
    action: Callable[[], Mapping[str, Any]],
) -> Dict[str, Any]:
    _require_previous(root, stage)
    path = _stage_path(root, stage)
    if path.is_file():
        previous = _load_json(path)
        if (
            previous.get("schema_version") == STAGE_RECEIPT_SCHEMA
            and previous.get("status") == "pass"
            and previous.get("input_hashes") == dict(input_hashes)
        ):
            for artifact_path, artifact_sha in previous.get("result", {}).get("artifacts", {}).items():
                candidate = Path(artifact_path)
                if not candidate.is_file() or sha256_file(candidate) != artifact_sha:
                    raise BridgeError(f"existing {stage} artifact receipt no longer verifies: {candidate}")
            return {**previous, "resumed": True}
        raise BridgeError(f"existing {stage} receipt does not match current inputs")
    result = dict(action())
    result.pop("manifest_records", None)
    receipt = {
        "schema_version": STAGE_RECEIPT_SCHEMA,
        "stage": stage,
        "status": "pass",
        "input_hashes": dict(input_hashes),
        "result": result,
        "resumed": False,
    }
    atomic_json(path, receipt)
    return receipt


def dry_run_summary(
    plan_path: str | Path,
    intake_config_path: str | Path,
    root: str | Path,
) -> Dict[str, Any]:
    plan = load_plan(plan_path)
    return {
        "mode": "dry-run",
        "writes_performed": False,
        "network_performed": False,
        "audio_materialized": False,
        "canonical_manifest_created": False,
        "stages": list(STAGES),
        "root": str(Path(root).resolve()),
        "inputs": {
            "plan": str(Path(plan_path).resolve()),
            "intake_config": str(Path(intake_config_path).resolve()),
        },
        "generated_s1_artifacts": {
            "metadata_index": str(Path(root).resolve() / "intake" / "metadata_index.json"),
            "proposal": str(Path(root).resolve() / "intake" / "metadata_split_proposal.csv"),
            "proposal_receipt": str(
                Path(root).resolve() / "intake" / "metadata_split_proposal.receipt.json"
            ),
        },
        "acquisition": plan_summary(plan),
        "execution_guard": {
            "S0": ["--execute", f"{APPROVAL_ENV}=YES"],
            "S1": [
                "--execute",
                f"{APPROVAL_ENV}=YES",
                f"{SPLIT_FREEZE_APPROVAL_ENV}=YES",
            ],
            "S2": [
                "--execute",
                f"{APPROVAL_ENV}=YES",
                f"{AUDIO_TRANSFORM_APPROVAL_ENV}=YES",
            ],
            "S3": [
                "--execute",
                f"{APPROVAL_ENV}=YES",
                f"{MANIFEST_FREEZE_APPROVAL_ENV}=YES",
            ],
        },
    }


def run_orchestrator(
    plan_path: str | Path,
    intake_config_path: str | Path,
    root: str | Path,
    manifest_version: str,
    stage: str = "all",
    execute: bool = False,
    fixture_only: bool = False,
) -> Dict[str, Any]:
    if stage not in {*STAGES, "all"}:
        raise BridgeError(f"unknown stage {stage!r}")
    if not execute:
        return dry_run_summary(plan_path, intake_config_path, root)
    if os.environ.get(APPROVAL_ENV) != "YES":
        raise BridgeError(f"execution requires --execute and {APPROVAL_ENV}=YES")
    output_root = Path(root).resolve()
    base_input_hashes = {
        "plan_sha256": sha256_file(plan_path),
        "intake_config_sha256": sha256_file(intake_config_path),
    }
    intake_root = output_root / "intake"
    metadata_index_path = intake_root / "metadata_index.json"
    proposal_path = intake_root / "metadata_split_proposal.csv"
    feasibility_report_path = intake_root / "feasibility_report.json"
    proposal_receipt_path = intake_root / "metadata_split_proposal.receipt.json"
    acquisition_receipt = output_root / "receipts" / "S1_acquisition.json"
    bootstrap_receipt = output_root / "receipts" / "S1_metadata_bootstrap.json"
    requested = list(STAGES) if stage == "all" else [stage]
    completed: Dict[str, Any] = {}
    current_input_hashes = dict(base_input_hashes)
    try:
        for current in requested:
            if current == "S0":
                def s0() -> Mapping[str, Any]:
                    plan = load_plan(plan_path)
                    config = load_json_yaml(Path(intake_config_path))
                    unresolved = validate_config(config)
                    unknown_receipt = validate_config_artifacts(
                        Path(intake_config_path), config
                    )
                    if unresolved:
                        raise BridgeError(f"S0 unresolved immutable receipts: {unresolved}")
                    summary = plan_summary(plan)
                    probe = _nearest_existing_path(output_root)
                    free_bytes = shutil.disk_usage(probe).free
                    if free_bytes < summary["minimum_working_space_bytes"]:
                        raise BridgeError(
                            f"insufficient server space: free={free_bytes}, "
                            f"minimum={summary['minimum_working_space_bytes']}"
                        )
                    return {
                        "stage_name": "plan_and_contract_validation",
                        "plan": summary,
                        "free_space_bytes": free_bytes,
                        "space_gate": "pass",
                        "config_unresolved_receipts": unresolved,
                        "approved_unknown_inventory_sha256": unknown_receipt["file_sha256"],
                        "proposal_required_before_s1": False,
                    }

                current_input_hashes = dict(base_input_hashes)
                completed[current] = _run_stage(
                    output_root, current, current_input_hashes, s0
                )
            elif current == "S1":
                if os.environ.get(SPLIT_FREEZE_APPROVAL_ENV) != "YES":
                    raise BridgeError(
                        f"S1 proposal freeze requires {SPLIT_FREEZE_APPROVAL_ENV}=YES"
                    )

                def s1() -> Mapping[str, Any]:
                    acquisition = acquire(plan_path, output_root, execute=True)
                    bootstrap = bootstrap_metadata(
                        plan_path,
                        intake_config_path,
                        acquisition_receipt,
                        output_root,
                        execute=True,
                        fixture_only=fixture_only,
                    )
                    report = run_feasibility(
                        config_path=Path(intake_config_path),
                        metadata_index_path=metadata_index_path,
                        output_dir=intake_root,
                        write_proposal=True,
                    )
                    frozen = freeze_metadata_proposal(
                        intake_config_path,
                        proposal_path,
                        feasibility_report_path,
                        proposal_receipt_path,
                        execute=True,
                    )
                    artifacts = {
                        str(acquisition_receipt): sha256_file(acquisition_receipt),
                        str(bootstrap_receipt): sha256_file(bootstrap_receipt),
                        str(metadata_index_path): sha256_file(metadata_index_path),
                        str(proposal_path): sha256_file(proposal_path),
                        str(feasibility_report_path): sha256_file(feasibility_report_path),
                        str(proposal_receipt_path): sha256_file(proposal_receipt_path),
                    }
                    artifacts.update(bootstrap.get("artifacts", {}))
                    for asset in acquisition.get("assets", []):
                        archive_path = Path(asset["download"]["path"])
                        artifacts[str(archive_path)] = asset["download"]["archive_sha256"]
                    return {
                        "stage_name": "acquire_bootstrap_and_freeze_metadata_proposal",
                        "acquisition": acquisition,
                        "metadata_bootstrap": bootstrap,
                        "feasibility": {
                            "admission_status": report["admission_status"],
                            "proposal_sha256": report["hashes"]["proposal_manifest_sha256"],
                            "overlap_assertions": report["overlap_assertions"],
                        },
                        "proposal_freeze": frozen,
                        "artifacts": dict(sorted(artifacts.items())),
                    }

                current_input_hashes = {
                    **base_input_hashes,
                    "S0_receipt_sha256": _previous_stage_sha256(output_root, "S1"),
                }
                completed[current] = _run_stage(
                    output_root,
                    current,
                    current_input_hashes,
                    s1,
                )
            elif current == "S2":
                if os.environ.get(AUDIO_TRANSFORM_APPROVAL_ENV) != "YES":
                    raise BridgeError(
                        f"S2 materialization requires {AUDIO_TRANSFORM_APPROVAL_ENV}=YES"
                    )

                def s2() -> Mapping[str, Any]:
                    acquisition_validation = acquire(
                        plan_path, output_root, execute=True
                    )
                    if acquisition_validation.get("resumed") is not True:
                        raise BridgeError("S2 must consume a resumed, revalidated S1 acquisition")
                    _, proposal_receipt = load_frozen_proposal(
                        proposal_path, proposal_receipt_path
                    )
                    if proposal_receipt["config_sha256"] != base_input_hashes["intake_config_sha256"]:
                        raise BridgeError("proposal config SHA does not match intake config")
                    result = materialize(
                        proposal_path,
                        proposal_receipt_path,
                        acquisition_receipt,
                        output_root / "materialized",
                        manifest_version,
                    )
                    return {
                        **result,
                        "source_tree_revalidation": "pass",
                        "artifacts": {
                            str(result["materialization_index"]): result["materialization_index_sha256"],
                            str(result["lineage"]): result["lineage_sha256"],
                        },
                    }

                current_input_hashes = {
                    **base_input_hashes,
                    "S1_receipt_sha256": _previous_stage_sha256(output_root, "S2"),
                    "acquisition_receipt_sha256": sha256_file(acquisition_receipt),
                    "metadata_bootstrap_receipt_sha256": sha256_file(bootstrap_receipt),
                    "metadata_index_sha256": sha256_file(metadata_index_path),
                    "proposal_sha256": sha256_file(proposal_path),
                    "proposal_receipt_sha256": sha256_file(proposal_receipt_path),
                }
                completed[current] = _run_stage(
                    output_root,
                    current,
                    current_input_hashes,
                    s2,
                )
            else:
                if os.environ.get(MANIFEST_FREEZE_APPROVAL_ENV) != "YES":
                    raise BridgeError(
                        f"S3 manifest freeze requires {MANIFEST_FREEZE_APPROVAL_ENV}=YES"
                    )
                materialized = output_root / "materialized"
                def s3() -> Mapping[str, Any]:
                    result = produce_frozen_manifest(
                        materialized / "materialization_index.jsonl",
                        materialized / "audio_lineage.jsonl",
                        acquisition_receipt,
                        materialized / "audio",
                        output_root / "frozen",
                        config_sha256=base_input_hashes["intake_config_sha256"],
                        proposal_sha256=sha256_file(proposal_path),
                        fixture_only=fixture_only,
                    )
                    return {
                        **result,
                        "artifacts": {
                            str(result["manifest"]): result["manifest_sha256"],
                            str(result["validation_receipt"]): result["validation_receipt_sha256"],
                        },
                    }

                current_input_hashes = {
                    **base_input_hashes,
                    "S2_receipt_sha256": _previous_stage_sha256(output_root, "S3"),
                    "acquisition_receipt_sha256": sha256_file(acquisition_receipt),
                    "proposal_sha256": sha256_file(proposal_path),
                    "materialization_index_sha256": sha256_file(
                        materialized / "materialization_index.jsonl"
                    ),
                    "lineage_sha256": sha256_file(materialized / "audio_lineage.jsonl"),
                }
                completed[current] = _run_stage(
                    output_root,
                    current,
                    current_input_hashes,
                    s3,
                )
    except Exception as exc:
        abort = {
            "schema_version": ABORT_RECEIPT_SCHEMA,
            "status": "abort",
            "requested_stage": stage,
            "failed_after": sorted(completed),
            "input_hashes": current_input_hashes,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        atomic_json(output_root / "receipts" / "abort.json", abort)
        raise
    return {
        "status": "pass",
        "requested_stage": stage,
        "completed": completed,
        "base_input_hashes": base_input_hashes,
    }
