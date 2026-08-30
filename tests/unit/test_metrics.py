from __future__ import annotations

import pandas as pd

from stablecoin_yield.metrics.core import max_drawdown, persistence_ratio, robust_mad


def test_persistence_ratio_ignores_missing_values() -> None:
    values = pd.Series([5.0, 10.0, None, 20.0])
    assert persistence_ratio(values, 10.0) == 2 / 3


def test_max_drawdown() -> None:
    values = pd.Series([100.0, 120.0, 90.0, 150.0])
    assert round(max_drawdown(values), 4) == -0.25


def test_robust_mad_zero_for_constant_series() -> None:
    assert robust_mad(pd.Series([3.0, 3.0, 3.0])) == 0.0

