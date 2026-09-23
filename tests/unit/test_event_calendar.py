import pandas as pd

from stablecoin_yield.analysis.pipeline import apy_tvl_event_response


def test_jump_after_missing_calendar_days_does_not_consume_event_cap():
    panel = pd.DataFrame({
        "pool_id": ["a"] * 8,
        "observed_date": pd.to_datetime([
            "2026-01-01", "2026-01-04", "2026-01-05", "2026-01-06",
            "2026-01-07", "2026-01-08", "2026-01-09", "2026-01-10",
        ]),
        "apy_total": [1, 12, 1, 14, 1, 16, 1, 18],
        "tvl_usd": [100] * 8,
    })
    events = apy_tvl_event_response(panel).set_index("event_time_day")
    assert events.loc[0, "event_count"] == 3
    assert events.loc[0, "median_apy"] == 16
    assert events.loc[0, "median_tvl_index"] == 1


def test_only_nonconsecutive_jump_produces_no_event():
    panel = pd.DataFrame({
        "pool_id": ["a", "a"],
        "observed_date": pd.to_datetime(["2026-01-01", "2026-01-04"]),
        "apy_total": [1, 12], "tvl_usd": [100, 100],
    })
    assert apy_tvl_event_response(panel).empty
