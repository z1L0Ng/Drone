"""Guarded official-source acquisition and safe archive extraction.

No network operation occurs unless the caller passes ``execute=True`` and the
independent environment guard is present.  The runner records HTTP and archive
receipts and refuses unresolved hashes, sizes, releases, or license terms.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Sequence, Tuple
from urllib.parse import quote, urlparse

from .contracts import (
    ACQUISITION_PLAN_SCHEMA,
    ACQUISITION_RECEIPT_SCHEMA,
    BridgeError,
    atomic_json,
    canonical_json_bytes,
    require_sha256,
    sha256_bytes,
    sha256_file,
)


APPROVAL_ENV = "DRONE_W33_DATA_DOWNLOAD_APPROVED"
ALLOWED_HOSTS = {
    "storage.googleapis.com",
    "huggingface.co",
    "www.tensorflow.org",
    "creativecommons.org",
    "mlcommons.org",
}
DOWNLOAD_CHUNK_BYTES = 1024 * 1024
MAX_ARCHIVE_MEMBERS = 2_000_000
MAX_EXPANSION_RATIO = 8
MSWC_MAX_WAV_SHARD_DECLARED_BYTES = 2_000_000_000


def load_plan(path: str | Path) -> Dict[str, Any]:
    plan_path = Path(path)
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BridgeError(f"cannot load acquisition plan {plan_path}: {exc}") from exc
    if not isinstance(plan, dict) or plan.get("schema_version") != ACQUISITION_PLAN_SCHEMA:
        raise BridgeError(f"acquisition plan schema must be {ACQUISITION_PLAN_SCHEMA}")
    if plan.get("default_mode") != "dry-run":
        raise BridgeError("acquisition plan default_mode must be dry-run")
    guard = plan.get("execution_guard", {})
    if guard != {"cli_flag": "--execute", "environment": f"{APPROVAL_ENV}=YES"}:
        raise BridgeError("acquisition execution guard is not frozen")
    if plan.get("no_reidentification") is not True:
        raise BridgeError("no_reidentification must be true")
    sources = plan.get("sources")
    if not isinstance(sources, list) or {source.get("dataset_key") for source in sources} != {
        "gsc_v2",
        "mswc",
    }:
        raise BridgeError("plan must contain only official gsc_v2 and mswc sources")
    for source in sources:
        _validate_source(source)
    return plan


def _validate_https(url: str, context: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise BridgeError(f"{context} must use an approved official HTTPS host")


def _validate_license(source: Mapping[str, Any]) -> None:
    license_receipt = source.get("license_receipt", {})
    if license_receipt.get("license_id") != "CC-BY-4.0":
        raise BridgeError(f"{source.get('dataset_key')}: license must be CC-BY-4.0")
    _validate_https(str(license_receipt.get("terms_url", "")), "license terms_url")
    if license_receipt.get("attribution_required") is not True:
        raise BridgeError("CC BY attribution requirement must be explicit")
    if source.get("dataset_key") == "mswc" and license_receipt.get("no_reidentification") is not True:
        raise BridgeError("MSWC no-reidentification condition must be explicit")


def _validate_source(source: Mapping[str, Any]) -> None:
    for key in ("dataset_key", "dataset_name", "release", "official_page", "mode"):
        if not str(source.get(key, "")).strip():
            raise BridgeError(f"source missing {key}")
    _validate_https(str(source["official_page"]), f"{source['dataset_key']}.official_page")
    _validate_license(source)
    if source["mode"] == "direct_archive":
        assets = source.get("assets")
        if not isinstance(assets, list) or not assets:
            raise BridgeError("direct_archive source requires assets")
        for asset in assets:
            _validate_asset(asset, source)
    elif source["mode"] == "pinned_hf_tree":
        if source.get("revision") != "0bc9df68e92fd6bb54176bf7eb29e2b9e97cb218":
            raise BridgeError("MSWC release revision changed")
        trees = source.get("trees")
        if not isinstance(trees, list) or {tree.get("language") for tree in trees} != {"es", "de"}:
            raise BridgeError("MSWC plan must pin Spanish and German trees")
        for tree in trees:
            _validate_https(str(tree.get("api_url", "")), "MSWC tree api_url")
            require_sha256(tree.get("asset_index_sha256"), "MSWC tree asset_index_sha256")
            if not isinstance(tree.get("archive_count"), int) or tree["archive_count"] <= 0:
                raise BridgeError("MSWC tree archive_count must be positive")
            if not isinstance(tree.get("archive_total_bytes"), int) or tree["archive_total_bytes"] <= 0:
                raise BridgeError("MSWC tree archive_total_bytes must be positive")
        metadata_assets = source.get("metadata_assets")
        if (
            not isinstance(metadata_assets, list)
            or len(metadata_assets) != 2
            or {asset.get("language") for asset in metadata_assets} != {"es", "de"}
        ):
            raise BridgeError("MSWC plan must pin Spanish and German split metadata archives")
        for asset in metadata_assets:
            if asset.get("asset_role") != "split_metadata":
                raise BridgeError("MSWC metadata assets must declare asset_role=split_metadata")
            _validate_asset(asset, source)
            expected = asset.get("expected_tree", {})
            if expected.get("kind") != "mswc_split_metadata":
                raise BridgeError("MSWC metadata assets require exact split-metadata tree receipts")
            hashes = expected.get("required_file_sha256", {})
            if set(hashes) != {"train.csv", "dev.csv", "test.csv", "version.txt"}:
                raise BridgeError("MSWC split metadata must pin train/dev/test/version files")
            for name, value in hashes.items():
                require_sha256(value, f"{asset['asset_id']}.{name}")
    else:
        raise BridgeError(f"unsupported acquisition mode {source['mode']!r}")


def _validate_asset(asset: Mapping[str, Any], source: Mapping[str, Any]) -> None:
    for key in ("asset_id", "url", "filename", "archive_sha256", "size_bytes", "extract_kind"):
        if key not in asset:
            raise BridgeError(f"{source['dataset_key']} asset missing {key}")
    _validate_https(str(asset["url"]), f"{source['dataset_key']}.asset.url")
    require_sha256(asset["archive_sha256"], f"{asset['asset_id']}.archive_sha256")
    if not isinstance(asset["size_bytes"], int) or asset["size_bytes"] <= 0:
        raise BridgeError(f"{asset['asset_id']}.size_bytes must be positive")
    if PurePosixPath(str(asset["filename"])).name != asset["filename"]:
        raise BridgeError(f"unsafe asset filename {asset['filename']!r}")
    if asset["extract_kind"] not in {"tar", "zip"}:
        raise BridgeError("extract_kind must be tar or zip")


def plan_summary(plan: Mapping[str, Any]) -> Dict[str, Any]:
    direct_assets = sum(
        len(source.get("assets", [])) + len(source.get("metadata_assets", []))
        for source in plan["sources"]
    )
    indexed_assets = sum(
        tree["archive_count"]
        for source in plan["sources"]
        if source["mode"] == "pinned_hf_tree"
        for tree in source["trees"]
    )
    download_bytes = sum(
        asset["size_bytes"]
        for source in plan["sources"]
        for asset in [*source.get("assets", []), *source.get("metadata_assets", [])]
    ) + sum(
        tree["archive_total_bytes"]
        for source in plan["sources"]
        for tree in source.get("trees", [])
    )
    multiplier = float(plan["space_estimate"]["temporary_and_extracted_multiplier"])
    return {
        "mode": "dry-run",
        "network_performed": False,
        "audio_downloaded": False,
        "direct_archive_count": direct_assets,
        "indexed_archive_count": indexed_assets,
        "expected_download_bytes": download_bytes,
        "minimum_working_space_bytes": int(download_bytes * multiplier),
        "execution_guard": plan["execution_guard"],
    }


def _canonical_hf_assets(payload: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    assets = []
    for row in payload:
        path = str(row.get("path", ""))
        if row.get("type") != "file" or not path.endswith(".tar.gz"):
            continue
        lfs = row.get("lfs")
        if not isinstance(lfs, Mapping):
            raise BridgeError(f"MSWC archive lacks immutable LFS receipt: {path}")
        assets.append(
            {
                "path": path,
                "size": int(lfs["size"]),
                "sha256": require_sha256(lfs["oid"], f"{path}.lfs.oid"),
            }
        )
    return sorted(assets, key=lambda item: item["path"])


def fetch_hf_tree_assets(source: Mapping[str, Any], tree: Mapping[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    request = urllib.request.Request(str(tree["api_url"]), headers={"User-Agent": "talk-to-me-drone-w33/1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        body = response.read()
        response_url = response.geturl()
        headers = {key.lower(): value for key, value in response.headers.items()}
    payload = json.loads(body)
    if not isinstance(payload, list):
        raise BridgeError("MSWC tree API did not return a list")
    canonical = _canonical_hf_assets(payload)
    index_sha = sha256_bytes(canonical_json_bytes(canonical))
    if index_sha != tree["asset_index_sha256"]:
        raise BridgeError(f"MSWC {tree['language']} asset index hash mismatch")
    if len(canonical) != tree["archive_count"]:
        raise BridgeError(f"MSWC {tree['language']} archive count mismatch")
    if sum(asset["size"] for asset in canonical) != tree["archive_total_bytes"]:
        raise BridgeError(f"MSWC {tree['language']} archive byte total mismatch")
    revision = source["revision"]
    assets = []
    for row in canonical:
        relative = row["path"]
        parts = PurePosixPath(relative).parts
        original_split = parts[3]
        shard = PurePosixPath(relative).name.removesuffix(".tar.gz")
        assets.append(
            {
                "asset_id": f"mswc-{tree['language']}-{original_split}-{shard}",
                "url": (
                    "https://huggingface.co/datasets/MLCommons/ml_spoken_words/resolve/"
                    f"{revision}/{quote(relative, safe='/')}?download=true"
                ),
                "filename": f"mswc-{tree['language']}-{original_split}-{shard}.tar.gz",
                "archive_sha256": row["sha256"],
                "size_bytes": row["size"],
                "extract_kind": "tar",
                "language": tree["language"],
                "original_split": original_split,
                "source_path": relative,
                "expected_tree": {
                    "kind": "mswc_wav_shard",
                    "minimum_wav_files": 1,
                    "maximum_declared_bytes": MSWC_MAX_WAV_SHARD_DECLARED_BYTES,
                },
            }
        )
    return assets, {
        "url": tree["api_url"],
        "response_url": response_url,
        "etag": headers.get("etag"),
        "last_modified": headers.get("last-modified"),
        "body_sha256": sha256_bytes(body),
        "asset_index_sha256": index_sha,
        "archive_count": len(assets),
        "archive_total_bytes": sum(asset["size_bytes"] for asset in assets),
    }


def _download_stream(asset: Mapping[str, Any], archive_dir: Path) -> Dict[str, Any]:
    archive_dir.mkdir(parents=True, exist_ok=True)
    destination = archive_dir / str(asset["filename"])
    partial = destination.with_suffix(destination.suffix + ".part")
    expected_size = int(asset["size_bytes"])
    expected_sha = str(asset["archive_sha256"])
    if destination.exists():
        if destination.stat().st_size == expected_size and sha256_file(destination) == expected_sha:
            return {
                "path": str(destination),
                "resumed": False,
                "reused_verified": True,
                "size_bytes": expected_size,
                "archive_sha256": expected_sha,
                "url": asset["url"],
                "response_url": asset["url"],
                "etag": None,
                "last_modified": None,
            }
        raise BridgeError(f"existing archive fails immutable receipt: {destination}")

    offset = partial.stat().st_size if partial.exists() else 0
    if offset > expected_size:
        raise BridgeError(f"partial archive exceeds expected size: {partial}")
    headers = {"User-Agent": "talk-to-me-drone-w33/1"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    request = urllib.request.Request(str(asset["url"]), headers=headers)
    with urllib.request.urlopen(request, timeout=300) as response:
        status = getattr(response, "status", response.getcode())
        response_headers = {key.lower(): value for key, value in response.headers.items()}
        response_url = response.geturl()
        actual_etag = response_headers.get("etag", "").strip('"')
        expected_etag = str(asset.get("expected_etag", "")).strip('"')
        if expected_etag and actual_etag != expected_etag:
            raise BridgeError(f"HTTP ETag mismatch for {asset['asset_id']}")
        expected_modified = str(asset.get("expected_last_modified", ""))
        if expected_modified and response_headers.get("last-modified") != expected_modified:
            raise BridgeError(f"HTTP Last-Modified mismatch for {asset['asset_id']}")
        if offset and status != 206:
            offset = 0
        elif offset:
            content_range = response_headers.get("content-range", "")
            if not content_range.startswith(f"bytes {offset}-"):
                raise BridgeError(f"invalid resume Content-Range for {asset['asset_id']}")
        mode = "ab" if offset else "wb"
        with partial.open(mode) as handle:
            while True:
                chunk = response.read(DOWNLOAD_CHUNK_BYTES)
                if not chunk:
                    break
                handle.write(chunk)
    if partial.stat().st_size != expected_size:
        raise BridgeError(
            f"download size mismatch for {asset['asset_id']}: {partial.stat().st_size} != {expected_size}"
        )
    actual_sha = sha256_file(partial)
    if actual_sha != expected_sha:
        raise BridgeError(f"archive SHA-256 mismatch for {asset['asset_id']}")
    partial.replace(destination)
    return {
        "path": str(destination),
        "resumed": bool(offset),
        "reused_verified": False,
        "size_bytes": expected_size,
        "archive_sha256": actual_sha,
        "url": asset["url"],
        "response_url": response_url,
        "etag": response_headers.get("etag"),
        "last_modified": response_headers.get("last-modified"),
        "content_length": response_headers.get("content-length"),
    }


def _safe_member_path(name: str) -> PurePosixPath:
    value = PurePosixPath(name)
    if (
        not name
        or "\\" in name
        or value.is_absolute()
        or ".." in value.parts
        or "." in value.parts
        or (value.parts and value.parts[0].endswith(":"))
    ):
        raise BridgeError(f"unsafe archive member path: {name!r}")
    return value


def _copy_stream(source: Any, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        shutil.copyfileobj(source, handle, length=DOWNLOAD_CHUNK_BYTES)


def _tree_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(path.stat().st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _tar_expansion_limit(archive_size_bytes: int, expected: Mapping[str, Any]) -> int:
    ratio_limit = max(archive_size_bytes * MAX_EXPANSION_RATIO, 1024**3)
    declared_limit = expected.get("maximum_declared_bytes")
    if declared_limit is None:
        return ratio_limit
    if (
        expected.get("kind") != "mswc_wav_shard"
        or declared_limit != MSWC_MAX_WAV_SHARD_DECLARED_BYTES
    ):
        raise BridgeError("unsupported archive declared-byte exception")
    return max(ratio_limit, MSWC_MAX_WAV_SHARD_DECLARED_BYTES)


def _extract_tar(archive_path: Path, destination: Path, expected: Mapping[str, Any]) -> None:
    with tarfile.open(archive_path, mode="r:*") as archive:
        members = archive.getmembers()
        if len(members) > MAX_ARCHIVE_MEMBERS:
            raise BridgeError("archive member count exceeds safety limit")
        declared_bytes = sum(member.size for member in members if member.isfile())
        expansion_limit = _tar_expansion_limit(archive_path.stat().st_size, expected)
        if declared_bytes > expansion_limit:
            raise BridgeError("archive declared size exceeds expansion safety limit")
        for member in members:
            # Some publisher tarballs begin with a root-directory entry named
            # ``./``.  ``tarfile`` normalizes that member name to an empty
            # string.  It is safe only when it is a directory representing the
            # extraction root; every file and non-root directory still passes
            # the strict path validation below.
            if not member.name and member.isdir():
                continue
            _safe_member_path(member.name)
            if member.issym() or member.islnk() or member.isdev():
                raise BridgeError(f"archive links/devices are forbidden: {member.name}")
        for member in members:
            if not member.name and member.isdir():
                continue
            relative = _safe_member_path(member.name)
            target = destination.joinpath(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                source = archive.extractfile(member)
                if source is None:
                    raise BridgeError(f"cannot read archive member {member.name}")
                with source:
                    _copy_stream(source, target)


def _extract_zip(archive_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_ARCHIVE_MEMBERS:
            raise BridgeError("archive member count exceeds safety limit")
        expansion_limit = max(archive_path.stat().st_size * MAX_EXPANSION_RATIO, 1024**3)
        if sum(info.file_size for info in infos) > expansion_limit:
            raise BridgeError("archive declared size exceeds expansion safety limit")
        for info in infos:
            relative = _safe_member_path(info.filename)
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise BridgeError(f"archive symlinks are forbidden: {info.filename}")
            target = destination.joinpath(*relative.parts)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                with archive.open(info) as source:
                    _copy_stream(source, target)


def validate_expected_tree(root: Path, expected: Mapping[str, Any]) -> Dict[str, Any]:
    if not root.is_dir():
        raise BridgeError(f"expected extracted tree is missing: {root}")
    links = [path for path in root.rglob("*") if path.is_symlink()]
    if links:
        raise BridgeError(f"extracted tree contains a forbidden symlink: {links[0]}")
    kind = expected.get("kind")
    if kind == "gsc_v2":
        required = ["validation_list.txt", "testing_list.txt"]
        missing = [name for name in required if not (root / name).is_file()]
        word_dirs = [path for path in root.iterdir() if path.is_dir() and path.name != "_background_noise_"]
        wav_count = sum(1 for _ in root.rglob("*.wav"))
        if missing or len(word_dirs) < int(expected.get("minimum_word_directories", 35)) or wav_count == 0:
            raise BridgeError(f"GSC expected tree failed: missing={missing}, words={len(word_dirs)}, wav={wav_count}")
        return {
            "kind": kind,
            "word_directories": len(word_dirs),
            "wav_files": wav_count,
            "tree_fingerprint_sha256": _tree_fingerprint(root),
        }
    if kind == "mswc_wav_shard":
        wav_count = sum(1 for _ in root.rglob("*.wav"))
        if wav_count < int(expected.get("minimum_wav_files", 1)):
            raise BridgeError("MSWC shard contains no WAV files")
        unexpected = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() != ".wav"]
        if unexpected:
            raise BridgeError(f"MSWC shard contains unexpected file: {unexpected[0]}")
        return {
            "kind": kind,
            "wav_files": wav_count,
            "tree_fingerprint_sha256": _tree_fingerprint(root),
        }
    if kind == "mswc_split_metadata":
        expected_hashes = expected.get("required_file_sha256", {})
        actual_files = sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        )
        if actual_files != sorted(expected_hashes):
            raise BridgeError(
                f"MSWC split metadata tree mismatch: expected={sorted(expected_hashes)}, "
                f"actual={actual_files}"
            )
        actual_hashes = {name: sha256_file(root / name) for name in sorted(expected_hashes)}
        if actual_hashes != dict(sorted(expected_hashes.items())):
            raise BridgeError("MSWC split metadata file SHA-256 mismatch")
        return {
            "kind": kind,
            "file_sha256": actual_hashes,
            "tree_fingerprint_sha256": _tree_fingerprint(root),
        }
    raise BridgeError(f"unknown expected tree kind {kind!r}")


def safe_extract(archive_path: Path, destination: Path, extract_kind: str, expected: Mapping[str, Any]) -> Dict[str, Any]:
    if destination.exists():
        tree = validate_expected_tree(destination, expected)
        return {"destination": str(destination), "reused_verified": True, "tree": tree}
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        if extract_kind == "tar":
            _extract_tar(archive_path, temporary, expected)
        elif extract_kind == "zip":
            _extract_zip(archive_path, temporary)
        else:
            raise BridgeError(f"unsupported extract kind {extract_kind!r}")
        tree = validate_expected_tree(temporary, expected)
        temporary.replace(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {"destination": str(destination), "reused_verified": False, "tree": tree}


def _asset_destination(source: Mapping[str, Any], asset: Mapping[str, Any], root: Path) -> Path:
    if source["dataset_key"] == "gsc_v2":
        return root / "sources" / "gsc_v2" / str(source["release"])
    if asset.get("asset_role") == "split_metadata":
        return (
            root
            / "sources"
            / "mswc"
            / str(source["release"])
            / "metadata"
            / str(asset["language"])
        )
    return (
        root
        / "sources"
        / "mswc"
        / str(source["release"])
        / str(asset["language"])
        / str(asset["original_split"])
        / str(asset["asset_id"])
    )


def _resume_acquisition(
    receipt_path: Path, plan: Mapping[str, Any], plan_sha256: str
) -> Dict[str, Any] | None:
    if not receipt_path.is_file():
        return None
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BridgeError(f"cannot load existing acquisition receipt: {exc}") from exc
    if (
        not isinstance(receipt, dict)
        or receipt.get("schema_version") != ACQUISITION_RECEIPT_SCHEMA
        or receipt.get("status") != "pass"
        or receipt.get("plan_sha256") != plan_sha256
        or receipt.get("no_reidentification_performed") is not True
        or receipt.get("redistribution_authorized") is not False
    ):
        raise BridgeError("existing acquisition receipt does not match the current plan/policy")
    assets = receipt.get("assets", [])
    expected_count = plan_summary(plan)["direct_archive_count"] + plan_summary(plan)[
        "indexed_archive_count"
    ]
    if not isinstance(assets, list) or len(assets) != expected_count:
        raise BridgeError("existing acquisition receipt has an unexpected asset count")
    fixed_assets = {
        asset["asset_id"]: asset
        for source in plan["sources"]
        for asset in [*source.get("assets", []), *source.get("metadata_assets", [])]
    }
    mswc_source = next(source for source in plan["sources"] if source["dataset_key"] == "mswc")
    for tree_plan in mswc_source["trees"]:
        language = tree_plan["language"]
        canonical = sorted(
            (
                {
                    "path": str(asset.get("source_path", "")),
                    "size": int(asset.get("download", {}).get("size_bytes", -1)),
                    "sha256": require_sha256(
                        asset.get("download", {}).get("archive_sha256"),
                        f"{asset.get('asset_id')}.archive_sha256",
                    ),
                }
                for asset in assets
                if asset.get("dataset_key") == "mswc"
                and asset.get("asset_role", "audio_archive") == "audio_archive"
                and asset.get("language") == language
            ),
            key=lambda row: row["path"],
        )
        if (
            sha256_bytes(canonical_json_bytes(canonical)) != tree_plan["asset_index_sha256"]
            or len(canonical) != tree_plan["archive_count"]
            or sum(row["size"] for row in canonical) != tree_plan["archive_total_bytes"]
        ):
            raise BridgeError(f"existing MSWC {language} archive index no longer verifies")
    seen_ids = set()
    for asset in assets:
        asset_id = str(asset.get("asset_id", ""))
        if not asset_id or asset_id in seen_ids:
            raise BridgeError("existing acquisition receipt has duplicate/empty asset IDs")
        seen_ids.add(asset_id)
        download = asset.get("download", {})
        archive = Path(str(download.get("path", "")))
        expected_sha = require_sha256(
            download.get("archive_sha256"), f"{asset_id}.archive_sha256"
        )
        expected_size = int(download.get("size_bytes", -1))
        if asset_id in fixed_assets:
            fixed = fixed_assets[asset_id]
            if expected_sha != fixed["archive_sha256"] or expected_size != fixed["size_bytes"]:
                raise BridgeError(f"existing fixed asset receipt changed: {asset_id}")
        if (
            not archive.is_file()
            or archive.stat().st_size != expected_size
            or sha256_file(archive) != expected_sha
        ):
            raise BridgeError(f"existing acquired archive no longer verifies: {archive}")
        extraction = asset.get("extraction", {})
        destination = Path(str(extraction.get("destination", "")))
        tree = extraction.get("tree", {})
        kind = tree.get("kind")
        if asset_id in fixed_assets:
            expected_tree = fixed_assets[asset_id]["expected_tree"]
        elif kind == "mswc_wav_shard":
            expected_tree = {"kind": kind, "minimum_wav_files": 1}
        else:
            raise BridgeError(f"existing acquisition receipt has unknown tree kind: {kind!r}")
        verified_tree = validate_expected_tree(destination, expected_tree)
        recorded_fingerprint = require_sha256(
            tree.get("tree_fingerprint_sha256"),
            f"{asset_id}.tree_fingerprint_sha256",
        )
        if verified_tree["tree_fingerprint_sha256"] != recorded_fingerprint:
            raise BridgeError(f"existing extracted tree no longer verifies: {destination}")
    return {**receipt, "resumed": True}


def acquire(plan_path: str | Path, root: str | Path, execute: bool = False) -> Dict[str, Any]:
    plan = load_plan(plan_path)
    summary = plan_summary(plan)
    summary["plan_sha256"] = sha256_file(plan_path)
    if not execute:
        return summary
    if os.environ.get(APPROVAL_ENV) != "YES":
        raise BridgeError(f"execution requires --execute and {APPROVAL_ENV}=YES")

    output_root = Path(root).resolve()
    receipt_path = output_root / "receipts" / "S1_acquisition.json"
    resumed = _resume_acquisition(receipt_path, plan, summary["plan_sha256"])
    if resumed is not None:
        return resumed
    archive_dir = output_root / "archives"
    receipts: List[Dict[str, Any]] = []
    tree_receipts: List[Dict[str, Any]] = []
    license_receipts: List[Mapping[str, Any]] = []
    for source in plan["sources"]:
        license_receipts.append(
            {"dataset_key": source["dataset_key"], **source["license_receipt"]}
        )
        if source["mode"] == "direct_archive":
            assets = list(source["assets"])
        else:
            assets = list(source.get("metadata_assets", []))
            for tree in source["trees"]:
                resolved, tree_receipt = fetch_hf_tree_assets(source, tree)
                assets.extend(resolved)
                tree_receipts.append(tree_receipt)
        for asset in assets:
            _validate_asset(asset, source)
            download = _download_stream(asset, archive_dir)
            extraction = safe_extract(
                Path(download["path"]),
                _asset_destination(source, asset, output_root),
                str(asset["extract_kind"]),
                asset["expected_tree"],
            )
            receipts.append(
                {
                    "dataset_key": source["dataset_key"],
                    "release": source["release"],
                    "asset_id": asset["asset_id"],
                    "asset_role": asset.get("asset_role", "audio_archive"),
                    "language": asset.get("language"),
                    "original_split": asset.get("original_split"),
                    "source_path": asset.get("source_path"),
                    "download": download,
                    "extraction": extraction,
                    "license_id": source["license_receipt"]["license_id"],
                }
            )
    result = {
        "schema_version": ACQUISITION_RECEIPT_SCHEMA,
        "status": "pass",
        "plan_sha256": summary["plan_sha256"],
        "root": str(output_root),
        "assets": receipts,
        "tree_receipts": tree_receipts,
        "license_receipts": license_receipts,
        "no_reidentification_performed": True,
        "redistribution_authorized": False,
    }
    atomic_json(receipt_path, result)
    return result
