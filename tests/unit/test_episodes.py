from __future__ import annotations

import pandas as pd

from stablecoin_yield.metrics.episodes import segment_episodes


def panel(values: list[float | None]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "pool_id": ["p1"] * len(values),
            "observed_date": pd.date_range("2026-01-01", periods=len(values), freq="D"),
            "apy_total": values,
            "tvl_usd": [100.0] * len(values),
        }
    )


def test_episode_starts_and_ends_on_threshold_crossing() -> None:
    episodes = segment_episodes(panel([1, 12, 15, 8, 11, 7]), threshold=10, max_gap_days=1)
    assert len(episodes) == 2
    assert episodes.iloc[0]["duration_days"] == 2
    assert episodes.iloc[0]["peak_apy"] == 15
    assert episodes.iloc[1]["duration_days"] == 1


def test_episode_censored_when_active_at_last_observation() -> None:
    episodes = segment_episodes(panel([1, 12, 15]), threshold=10, max_gap_days=1)
    assert len(episodes) == 1
    assert bool(episodes.iloc[0]["is_censored"]) is True


def test_gap_breaks_episode() -> None:
    data = pd.DataFrame(
        {
            "pool_id": ["p1", "p1", "p1"],
            "observed_date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-05"]),
            "apy_total": [11, 12, 13],
            "tvl_usd": [100, 110, 120],
        }
    )
    episodes = segment_episodes(data, threshold=10, max_gap_days=1)
    assert len(episodes) == 2


def test_threshold_boundary_is_inclusive() -> None:
    episodes = segment_episodes(panel([10, 9.99]), threshold=10, max_gap_days=1)
    assert len(episodes) == 1
    assert episodes.iloc[0]["start_apy"] == 10

