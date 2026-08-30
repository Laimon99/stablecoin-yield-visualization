from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_depeg_event_study_has_observed_exposed_pool_apy() -> None:
    path = ROOT / "outputs" / "tables" / "depeg_event_study.csv"
    if not path.exists():
        pytest.skip("depeg event study has not been generated")
    frame = pd.read_csv(path)
    assert not frame.empty
    assert frame["pool_count"].max() > 0
    assert frame["median_apy"].notna().any()
    assert frame["peak_abs_deviation"].max() > 0
