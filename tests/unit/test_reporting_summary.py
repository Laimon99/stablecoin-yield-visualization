from __future__ import annotations

import pandas as pd

from stablecoin_yield.reporting.builder import episode_summary


def test_episode_summary_exposes_ordered_survival_curve() -> None:
    episodes = pd.DataFrame(
        {
            "duration_days": [2, 4],
            "is_censored": [False, True],
        }
    )
    survival = pd.DataFrame(
        {
            "duration_days": [2.0, 0.0, 1.0],
            "survival": [0.4, 1.0, 0.55],
            "ci_lower": [0.35, 1.0, 0.5],
            "ci_upper": [0.45, 1.0, 0.6],
            "at_risk": [40, 100, 55],
        }
    )

    summary = episode_summary(episodes, survival)

    assert [row["duration_days"] for row in summary["survival_curve"]] == [0.0, 1.0, 2.0]
    assert summary["survival_curve"][2] == {
        "duration_days": 2.0,
        "survival": 0.4,
        "ci_lower": 0.35,
        "ci_upper": 0.45,
        "at_risk": 40,
    }
