from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from stablecoin_yield.config import get_paths
from stablecoin_yield.raw import utc_timestamp

BINARY_RELEASE_SUFFIXES = {".pdf", ".png", ".pptx", ".webp"}


@dataclass(frozen=True)
class ManifestOutput:
    path: Path
    file_count: int


def build_release_manifest(root: Path, mode: str) -> ManifestOutput:
    paths = get_paths(root)
    manifest_path = paths.outputs_dir / "release_manifest.json"
    paths.outputs_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for path in iter_release_files(root):
        if path == manifest_path:
            continue
        size_bytes, checksum = release_file_metadata(path)
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": size_bytes,
                "checksum": checksum,
            }
        )
    payload = {
        "project": "stablecoin_yield",
        "mode": mode,
        "created_at": utc_timestamp(),
        "file_count": len(records),
        "files": records,
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return ManifestOutput(path=manifest_path, file_count=len(records))


def release_file_metadata(path: Path) -> tuple[int, str]:
    """Hash bytes as Git exports them under the repository's line-ending policy."""
    data = path.read_bytes()
    if path.suffix.lower() not in BINARY_RELEASE_SUFFIXES:
        text = data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        newline = "\r\n" if path.suffix.lower() == ".ps1" else "\n"
        data = text.replace("\n", newline).encode("utf-8")
    return len(data), f"sha256:{hashlib.sha256(data).hexdigest()}"


def iter_release_files(root: Path) -> list[Path]:
    include_dirs = [
        ".github",
        "config",
        "src",
        "scripts",
        "tests",
        "outputs/quality",
    ]
    include_files = [
        "README.md",
        "LICENSE",
        "NOTICE.md",
        "Makefile",
        "pyproject.toml",
        "uv.lock",
        ".env.example",
        ".gitattributes",
        ".gitignore",
        "outputs/analysis_manifest.json",
    ]
    include_globs = {
        "docs": ["*.md"],
        "outputs/figures": ["*.png", "figure_registry.csv"],
        "outputs/tables": [
            "apy_tvl_event_response.csv",
            "depeg_event_study.csv",
            "episode_survival.csv",
            "market_overview.csv",
            "ranking_churn.csv",
            "robustness_checks.csv",
        ],
        "outputs/report": [
            "stablecoin_yield_report.md",
            "stablecoin_yield_report.pdf",
            "stablecoin_yield_report_contact_sheet.png",
            "report_design_review.md",
            "report_summary.json",
        ],
        "outputs/presentation": [
            "stablecoin_yield_presentation.pptx",
            "stablecoin_yield_presentation.pdf",
            "stablecoin_yield_presentation_powerpoint_contact_sheet.png",
            "speaker_notes.md",
            "presentation_qa.md",
        ],
    }
    files: list[Path] = []
    for relative in include_files:
        path = root / relative
        if path.exists() and path.is_file():
            files.append(path)
    for relative_dir in include_dirs:
        directory = root / relative_dir
        if not directory.exists():
            continue
        files.extend(
            path
            for path in directory.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix not in {".pyc", ".tmp"}
        )
    for relative_dir, patterns in include_globs.items():
        directory = root / relative_dir
        if not directory.exists():
            continue
        for pattern in patterns:
            files.extend(path for path in directory.glob(pattern) if path.is_file())
    return sorted(set(files), key=lambda item: item.relative_to(root).as_posix())
