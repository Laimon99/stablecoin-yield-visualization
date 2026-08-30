from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from stablecoin_yield.reporting import build_summary

ROOT = Path(__file__).resolve().parents[2]


def test_report_generation_outputs_markdown_pdf_and_summary() -> None:
    private_inputs = [
        ROOT / "outputs" / "tables" / "yield_episodes.csv",
        ROOT / "outputs" / "tables" / "yield_frontier.csv",
        ROOT / "outputs" / "tables" / "pool_archetypes.csv",
        ROOT / "data" / "analytical" / "pool_day_panel.parquet",
        ROOT / "data" / "processed" / "pools.parquet",
    ]
    if not all(path.exists() for path in private_inputs):
        pytest.skip("private analytical inputs are not present in the public release")
    summary = build_summary(ROOT, "full")
    assert all(not Path(asset["path"]).is_absolute() for asset in summary["data_assets"])
    assert summary["market"]["pool_count"] > 0
    histogram = summary["market"]["apy_histogram"]
    assert len(histogram["bins"]) == 32
    assert sum(row["count"] for row in histogram["bins"]) == histogram["observation_count"]
    assert round(histogram["clip_value"], 2) == summary["market"]["p99_apy"]
    assert summary["episodes"]["primary_count"] > 0
    churn = pd.read_csv(ROOT / "outputs" / "tables" / "ranking_churn.csv")
    grouped_churn = churn.groupby("horizon_days")["churn"]
    for horizon, expected_mean in grouped_churn.mean().items():
        key = str(int(horizon))
        assert summary["ranking"]["mean_churn_by_horizon"][key] == round(
            float(expected_mean), 3
        )
        assert summary["ranking"]["comparison_count_by_horizon"][key] == int(
            grouped_churn.count().loc[horizon]
        )
    assert summary["ranking"]["aggregation"] == "comparison_weighted_mean_across_top_k"
    assert (ROOT / "outputs" / "report" / "stablecoin_yield_report.md").exists()
    assert (ROOT / "outputs" / "report" / "stablecoin_yield_report.pdf").exists()
    assert (ROOT / "outputs" / "report" / "report_summary.json").exists()
