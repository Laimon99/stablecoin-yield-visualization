"""Rebuild the refined deck evidence; optionally audit the private historical panel."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from stablecoin_yield.analysis.pipeline import apy_tvl_event_response
from stablecoin_yield.visualization.published import render_published_static

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "outputs/refinement"


def refresh_local() -> None:
    panel_path = ROOT / "data/analytical/pool_day_panel.parquet"
    panel = pd.read_parquet(panel_path).sort_values(["pool_id", "observed_date"])
    summary = json.loads((ROOT / "outputs/report/report_summary.json").read_text())
    event_table = apy_tvl_event_response(panel)
    event_table.to_csv(EVIDENCE / "apy_tvl_event_response.csv", index=False)
    points = event_table.set_index("event_time_day")
    summary["event_response"] = {
        "event_count_max": int(points.loc[0, "event_count"]),
        "points": {str(t): {k: float(v) if k != "event_count" else int(v)
                             for k, v in points.loc[t].items()} for t in [-7, 0, 7, 30]},
    }
    components = []
    for pool_type, group in panel.groupby("pool_type"):
        item = {"pool_type": pool_type, "rows": len(group)}
        for name in ["base", "reward"]:
            values = group[f"apy_{name}"]
            item[f"median_{name}_apy"] = float(values.median()) if values.notna().any() else None
            item[f"{name}_count"] = int(values.count())
            item[f"{name}_coverage"] = float(values.notna().mean())
        components.append(item)
    summary["pool_type_components"] = sorted(components, key=lambda x: x["median_base_apy"] or 0, reverse=True)
    pd.DataFrame(components).to_csv(EVIDENCE / "mechanism_coverage.csv", index=False)

    # Paired endpoint sensitivity: retain exactly the same events at t=0 and t=30.
    delta = panel.groupby("pool_id").apy_total.diff()
    gap = panel.groupby("pool_id").observed_date.diff().dt.days
    legacy = panel[(delta >= 5) & (panel.apy_total >= 10)].groupby("pool_id").head(3)
    events = panel[(delta >= 5) & (panel.apy_total >= 10) & gap.eq(1)].groupby("pool_id").head(3)
    paired = []
    groups = {key: group.set_index("observed_date") for key, group in panel.groupby("pool_id")}
    for row in events.itertuples():
        group = groups[row.pool_id]
        end = row.observed_date + pd.Timedelta(days=30)
        if end not in group.index or not pd.notna(row.tvl_usd) or row.tvl_usd <= 0:
            continue
        last = group.loc[end]
        if pd.notna(last.apy_total) and pd.notna(last.tvl_usd) and last.tvl_usd > 0:
            paired.append([row.apy_total, last.apy_total, last.tvl_usd / row.tvl_usd])
    paired = np.asarray(paired)

    # Resample whole pools to retain dependence between a pool's repeated episodes.
    episodes = pd.read_parquet(ROOT / "data/analytical/yield_episodes.parquet")
    episodes = episodes[episodes.threshold_definition.eq("apy_ge_10")].copy()
    pools = panel.pool_id.unique()
    risk = np.zeros((len(pools), 30))
    failures = np.zeros_like(risk)
    for i, pool in enumerate(pools):
        subset = episodes[episodes.pool_id.eq(pool)]
        duration = subset.duration_days.to_numpy()
        observed = ~subset.is_censored.to_numpy(dtype=bool)
        for day in range(1, 31):
            risk[i, day-1] = (duration >= day).sum()
            failures[i, day-1] = ((duration == day) & observed).sum()
    rng = np.random.default_rng(945119)
    weights = rng.multinomial(len(pools), np.full(len(pools), 1 / len(pools)), size=2000)
    at_risk = weights @ risk
    deaths = weights @ failures
    estimates = np.prod(1 - np.divide(deaths, at_risk, out=np.zeros_like(deaths), where=at_risk > 0), axis=1)
    ci = np.quantile(estimates, [.025, .975])
    first_dates = panel.groupby("pool_id").observed_date.min()
    left_count = sum(episodes.start_date.eq(episodes.pool_id.map(first_dates)))
    next_dates = panel.groupby("pool_id").observed_date.shift(-1)
    gap_ends = set(zip(panel.loc[(next_dates-panel.observed_date).dt.days.gt(2), "pool_id"],
                       panel.loc[(next_dates-panel.observed_date).dt.days.gt(2), "observed_date"], strict=True))
    gap_count = sum((r.pool_id, r.end_date) in gap_ends for r in episodes.itertuples())
    audit = {
        "panel_sha256": hashlib.sha256(panel_path.read_bytes()).hexdigest(),
        "legacy_event_count": len(legacy), "legacy_nonconsecutive_events": int(gap.loc[legacy.index].gt(1).sum()),
        "corrected_event_count": len(events), "corrected_event_pools": int(events.pool_id.nunique()),
        "paired_endpoint_count": len(paired), "paired_apy_0": float(np.median(paired[:, 0])),
        "paired_apy_30": float(np.median(paired[:, 1])), "paired_tvl_30": float(np.median(paired[:, 2])),
        "pool_bootstrap_replicates": 2000, "pool_bootstrap_seed": 945119,
        "pool_bootstrap_ci_30": ci.tolist(), "left_boundary_episodes": int(left_count),
        "gap_terminated_episodes": int(gap_count),
        "scope": "Pool bootstrap is conditional on the selected sample and original observed-run definition; it does not correct selection or observation-boundary bias.",
    }
    (EVIDENCE / "refinement_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    (EVIDENCE / "report_summary.json").write_text(json.dumps(summary, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-local", action="store_true", help="Recompute aggregate evidence from the author's private historical panel.")
    parser.add_argument("--output-dir", type=Path, default=EVIDENCE)
    args = parser.parse_args()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if args.refresh_local:
        refresh_local()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(EVIDENCE / "apy_tvl_event_response.csv")
    summary = json.loads((EVIDENCE / "report_summary.json").read_text())
    for day, values in summary["event_response"]["points"].items():
        observed = events.set_index("event_time_day").loc[int(day)]
        for key, value in values.items():
            if not np.isclose(observed[key], value):
                raise ValueError(f"Event evidence disagrees at day {day}: {key}")
    render_published_static(ROOT, args.output_dir, events=events)
    print(json.dumps(json.loads((EVIDENCE / "refinement_audit.json").read_text()), indent=2))


if __name__ == "__main__":
    main()
