from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    config_dir: Path
    data_dir: Path
    raw_dir: Path
    staging_dir: Path
    processed_dir: Path
    analytical_dir: Path
    samples_dir: Path
    outputs_dir: Path
    quality_dir: Path
    tables_dir: Path
    figures_dir: Path
    report_dir: Path
    presentation_dir: Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_paths(root: Path | None = None) -> ProjectPaths:
    base = root or project_root()
    return ProjectPaths(
        root=base,
        config_dir=base / "config",
        data_dir=base / "data",
        raw_dir=base / "data" / "raw",
        staging_dir=base / "data" / "staging",
        processed_dir=base / "data" / "processed",
        analytical_dir=base / "data" / "analytical",
        samples_dir=base / "data" / "samples",
        outputs_dir=base / "outputs",
        quality_dir=base / "outputs" / "quality",
        tables_dir=base / "outputs" / "tables",
        figures_dir=base / "outputs" / "figures",
        report_dir=base / "outputs" / "report",
        presentation_dir=base / "outputs" / "presentation",
    )


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise TypeError(f"Expected mapping in {path}, got {type(loaded).__name__}")
    return loaded


def load_config(root: Path | None = None) -> dict[str, Any]:
    paths = get_paths(root)
    config: dict[str, Any] = {}
    for name in ["project", "sources", "metrics", "visualization"]:
        config[name] = load_yaml(paths.config_dir / f"{name}.yaml")
    return config


def ensure_directories(paths: ProjectPaths) -> None:
    for directory in [
        paths.raw_dir,
        paths.staging_dir,
        paths.processed_dir,
        paths.analytical_dir,
        paths.samples_dir,
        paths.quality_dir,
        paths.tables_dir,
        paths.figures_dir,
        paths.report_dir,
        paths.presentation_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

