from __future__ import annotations

import json
from pathlib import Path

import pytest

from stablecoin_yield.reproducibility import release_file_metadata

ROOT = Path(__file__).resolve().parents[2]


def test_release_manifest_contains_core_delivery_files() -> None:
    manifest = ROOT / "outputs" / "release_manifest.json"
    if not manifest.exists():
        pytest.skip("release manifest has not been generated")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    paths = {item["path"] for item in payload["files"]}
    assert payload["mode"] == "full"
    assert "README.md" in paths
    assert "pyproject.toml" in paths
    assert "outputs/report/stablecoin_yield_report.md" in paths
    assert "outputs/presentation/stablecoin_yield_presentation.pptx" in paths
    assert not any("__pycache__" in path or path.endswith(".pyc") for path in paths)
    assert not any(path.startswith("data/") for path in paths)
    assert not {
        "outputs/tables/pool_archetypes.csv",
        "outputs/tables/pool_metrics.csv",
        "outputs/tables/yield_episodes.csv",
        "outputs/tables/yield_frontier.csv",
    } & paths
    assert payload["file_count"] == len(payload["files"])
    for item in payload["files"]:
        artifact = ROOT / item["path"]
        assert artifact.exists(), item["path"]
        size_bytes, checksum = release_file_metadata(artifact)
        assert size_bytes == item["size_bytes"], item["path"]
        assert checksum == item["checksum"], item["path"]


def test_source_verification_paths_are_portable() -> None:
    results_path = ROOT / "outputs" / "quality" / "source_verification_results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    for result in results:
        raw_file = Path(result["raw_file"])
        assert not raw_file.is_absolute()
        assert raw_file.as_posix().startswith("data/raw/")
