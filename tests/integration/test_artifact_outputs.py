from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]


def require(path: Path) -> Path:
    if not path.exists():
        pytest.skip(f"Missing generated artifact: {path.relative_to(ROOT)}")
    return path


def test_generated_tables_cover_required_analysis_outputs() -> None:
    # Only aggregated analytical evidence is distributed in the public release.
    # Row-level/provider-derived tables are regenerated locally from source data.
    required = [
        "market_overview.csv",
        "episode_survival.csv",
        "ranking_churn.csv",
        "apy_tvl_event_response.csv",
        "depeg_event_study.csv",
        "robustness_checks.csv",
    ]
    for name in required:
        path = require(ROOT / "outputs" / "tables" / name)
        frame = pd.read_csv(path)
        assert not frame.empty, name


def test_figure_registry_uses_portable_relative_paths() -> None:
    registry = pd.read_csv(require(ROOT / "outputs" / "figures" / "figure_registry.csv"))
    assert len(registry) >= 10
    for files in registry["files"]:
        for item in str(files).split("|"):
            assert not Path(item).is_absolute()
            assert (ROOT / item).exists()
