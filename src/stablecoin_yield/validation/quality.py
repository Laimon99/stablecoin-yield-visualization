from __future__ import annotations

from pathlib import Path

import pandas as pd

from stablecoin_yield.analysis.pipeline import read_table
from stablecoin_yield.config import get_paths


def quality_report(root: Path, mode: str = "sample") -> pd.DataFrame:
    paths = get_paths(root)
    panel = read_table(paths.analytical_dir / "pool_day_panel.parquet")
    pools = read_table(paths.processed_dir / "pools.parquet")
    checks = []
    if panel.empty:
        checks.append(check("panel.exists", "pool_day_panel", "critical", "failed", 0, 1))
        return pd.DataFrame(checks)
    panel["observed_date"] = pd.to_datetime(panel["observed_date"])
    checks.append(check("panel.exists", "pool_day_panel", "critical", "passed", len(panel), 0))
    duplicate_count = int(panel.duplicated(subset=["pool_id", "observed_date"]).sum())
    checks.append(
        check(
            "pool_day.unique_key",
            "pool_day_panel",
            "critical",
            "passed" if duplicate_count == 0 else "failed",
            len(panel),
            duplicate_count,
        )
    )
    for field in ["apy_total", "tvl_usd", "chain", "protocol_id", "pool_type"]:
        missing = int(panel[field].isna().sum()) if field in panel else len(panel)
        checks.append(
            check(
                f"pool_day.{field}.completeness",
                "pool_day_panel",
                "warning" if field != "apy_total" else "error",
                "passed" if missing == 0 else "warning",
                len(panel),
                missing,
            )
        )
    neg_apy = int((panel["apy_total"] < 0).sum())
    extreme_apy = int((panel["apy_total"] > 1000).sum())
    non_positive_tvl = int((panel["tvl_usd"] <= 0).sum())
    checks.extend(
        [
            check("apy.non_negative", "pool_day_panel", "error", "passed" if neg_apy == 0 else "failed", len(panel), neg_apy),
            check("apy.extreme_gt_1000", "pool_day_panel", "warning", "passed" if extreme_apy == 0 else "warning", len(panel), extreme_apy),
            check("tvl.positive", "pool_day_panel", "error", "passed" if non_positive_tvl == 0 else "failed", len(panel), non_positive_tvl),
        ]
    )
    mismatch = int(panel.get("apy_component_mismatch_flag", pd.Series(False, index=panel.index)).sum())
    checks.append(
        check(
            "apy.total_vs_components",
            "pool_day_panel",
            "warning",
            "passed" if mismatch == 0 else "warning",
            len(panel),
            mismatch,
        )
    )
    if not pools.empty:
        low_conf = int((pools["entity_resolution_confidence"] < 0.7).sum())
        checks.append(
            check(
                "entity_resolution.low_confidence",
                "pools",
                "warning",
                "passed" if low_conf == 0 else "warning",
                len(pools),
                low_conf,
            )
        )
    report = pd.DataFrame(checks)
    paths.quality_dir.mkdir(parents=True, exist_ok=True)
    report.to_csv(paths.quality_dir / "data_quality_checks.csv", index=False)
    write_quality_markdown(paths.quality_dir / "data_quality_report.md", report, panel, pools, mode)
    return report


def check(
    check_id: str,
    dataset: str,
    severity: str,
    status: str,
    evaluated_rows: int,
    failed_rows: int,
):
    return {
        "check_id": check_id,
        "dataset": dataset,
        "severity": severity,
        "status": status,
        "evaluated_rows": evaluated_rows,
        "failed_rows": failed_rows,
        "failure_rate": failed_rows / evaluated_rows if evaluated_rows else 0.0,
    }


def write_quality_markdown(
    path: Path, report: pd.DataFrame, panel: pd.DataFrame, pools: pd.DataFrame, mode: str
) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Data Quality Report\n\n")
        handle.write(f"Mode: `{mode}`\n\n")
        handle.write("## Summary\n\n")
        handle.write(f"- Pool-day rows: {len(panel):,}\n")
        handle.write(f"- Pools: {panel['pool_id'].nunique():,}\n")
        handle.write(f"- Date range: {panel['observed_date'].min()} to {panel['observed_date'].max()}\n")
        handle.write(f"- APY coverage: {panel['apy_total'].notna().mean():.1%}\n")
        handle.write(f"- Base APY coverage: {panel['apy_base'].notna().mean():.1%}\n")
        handle.write(f"- Reward APY coverage: {panel['apy_reward'].notna().mean():.1%}\n")
        handle.write(f"- TVL coverage: {panel['tvl_usd'].notna().mean():.1%}\n\n")
        handle.write("## Checks\n\n")
        handle.write(report.to_markdown(index=False))
        handle.write("\n\n")
        if not pools.empty:
            handle.write("## Coverage By Pool Type\n\n")
            coverage = pools["pool_type"].value_counts().rename_axis("pool_type").reset_index(name="pools")
            handle.write(coverage.to_markdown(index=False))
            handle.write("\n\n")

