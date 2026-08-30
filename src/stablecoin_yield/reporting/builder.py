from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from stablecoin_yield.analysis.pipeline import read_table
from stablecoin_yield.config import get_paths, load_config


@dataclass(frozen=True)
class ReportOutputs:
    markdown: Path
    pdf: Path
    summary_json: Path


def build_report(root: Path, mode: str = "sample") -> ReportOutputs:
    paths = get_paths(root)
    paths.report_dir.mkdir(parents=True, exist_ok=True)
    summary = build_summary(root, mode)
    md_path = paths.report_dir / "stablecoin_yield_report.md"
    pdf_path = paths.report_dir / "stablecoin_yield_report.pdf"
    json_path = paths.report_dir / "report_summary.json"
    md_path.write_text(render_markdown(root, summary), encoding="utf-8")
    json_path.write_text(
        json.dumps(json_safe(summary), ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    render_pdf(root, summary, pdf_path)
    return ReportOutputs(markdown=md_path, pdf=pdf_path, summary_json=json_path)


def build_summary(root: Path, mode: str) -> dict:
    paths = get_paths(root)
    config = load_config(root)
    market = read_csv(paths.tables_dir / "market_overview.csv")
    episodes = read_csv(paths.tables_dir / "yield_episodes.csv")
    survival = read_csv(paths.tables_dir / "episode_survival.csv")
    churn = read_csv(paths.tables_dir / "ranking_churn.csv")
    frontier = read_csv(paths.tables_dir / "yield_frontier.csv")
    robustness = read_csv(paths.tables_dir / "robustness_checks.csv")
    depeg = read_csv(paths.tables_dir / "depeg_event_study.csv")
    event_response = read_csv(paths.tables_dir / "apy_tvl_event_response.csv")
    archetypes = read_csv(paths.tables_dir / "pool_archetypes.csv")
    quality = read_csv(paths.quality_dir / "data_quality_checks.csv")
    figures = read_csv(paths.figures_dir / "figure_registry.csv")
    panel = read_table(paths.analytical_dir / "pool_day_panel.parquet")
    pools = read_table(paths.processed_dir / "pools.parquet")

    selected_episodes = episodes[episodes.get("threshold_definition", "") == "apy_ge_10"]
    if selected_episodes.empty and "threshold_definition" in episodes:
        selected_episodes = episodes[episodes["threshold_definition"].astype(str).str.contains("10")]

    churn_summary = {}
    churn_counts = {}
    if not churn.empty and {"horizon_days", "churn"}.issubset(churn.columns):
        grouped_churn = churn.groupby("horizon_days")["churn"]
        churn_summary = {
            str(int(horizon)): round(float(value), 3)
            for horizon, value in grouped_churn.mean().items()
        }
        churn_counts = {
            str(int(horizon)): int(value)
            for horizon, value in grouped_churn.count().items()
        }

    depeg_summary = {}
    if not depeg.empty:
        min_row = depeg.loc[depeg["price_usd"].idxmin()]
        depeg_points = {
            str(day): depeg_point(depeg, day)
            for day in [-30, -7, -1, 0, 1, 7, 30]
            if not depeg[depeg["event_time_day"] == day].empty
        }
        day_minus_1 = depeg_points.get("-1", {})
        day_zero = depeg_points.get("0", {})
        depeg_summary = {
            "stablecoin_id": str(depeg["stablecoin_id"].iloc[0]),
            "event_date": str(pd.to_datetime(depeg["event_date"].iloc[0]).date()),
            "min_price_usd": round(float(min_row["price_usd"]), 4),
            "peak_abs_deviation": round(float(depeg["peak_abs_deviation"].max()), 4),
            "max_pool_count": int(depeg["pool_count"].fillna(0).max()),
            "points": depeg_points,
            "apy_change_pp_day_minus_1_to_0": round(
                float(day_zero.get("median_apy", 0)) - float(day_minus_1.get("median_apy", 0)),
                2,
            ),
        }

    figure_records = []
    if not figures.empty:
        for row in figures.itertuples(index=False):
            files = str(getattr(row, "files", "")).split("|")
            png = next((item for item in files if item.endswith(".png")), "")
            figure_records.append(
                {
                    "id": str(row.id),
                    "title": str(row.title),
                    "question": str(row.question),
                    "message": str(row.message),
                    "sample_size": str(row.sample_size),
                    "png": png,
                }
            )

    critical_failures = 0
    warnings = 0
    quality_records = []
    if not quality.empty:
        critical_failures = int(
            ((quality["severity"] == "critical") & (quality["status"] == "failed")).sum()
        )
        warnings = int((quality["status"] == "warning").sum())
        for row in quality.itertuples(index=False):
            quality_records.append(
                {
                    "check_id": str(row.check_id),
                    "severity": str(row.severity),
                    "status": str(row.status),
                    "evaluated_rows": int(row.evaluated_rows),
                    "failed_rows": int(row.failed_rows),
                    "failure_rate": float(row.failure_rate),
                }
            )

    panel_dates = pd.to_datetime(panel["observed_date"]) if not panel.empty else pd.Series(dtype="datetime64[ns]")
    apy = panel["apy_total"] if "apy_total" in panel else pd.Series(dtype=float)
    tvl = panel["tvl_usd"] if "tvl_usd" in panel else pd.Series(dtype=float)
    screen = frontier_summary(frontier)
    pool_history = (
        frontier["pool_history_length"]
        if "pool_history_length" in frontier
        else pd.Series(dtype=float)
    )
    filters = config["metrics"]["pool_filters"]
    methodology = {
        "selection": {
            "stable_only": bool(filters["stable_only"]),
            "min_tvl_usd": float(filters["min_tvl_usd"]),
            "min_history_days": int(filters["min_history_days"]),
            "max_pools": int(filters["max_full_pools"]),
            "selection_mix": "70% highest TVL, remaining capacity highest current APY",
        },
        "panel": {
            "balanced": False,
            "entry_exit_treatment": "Observed pool-specific dates only; no synthetic backfill",
            "median_history_days": round(float(pool_history.median()), 0)
            if not pool_history.empty
            else 0,
            "min_history_observed_days": int(pool_history.min()) if not pool_history.empty else 0,
            "max_history_observed_days": int(pool_history.max()) if not pool_history.empty else 0,
        },
        "episode": {
            "threshold_percent": float(
                config["metrics"]["yield_episodes"]["primary_threshold"]["apy_percent"]
            ),
            "max_gap_days": int(config["metrics"]["yield_episodes"]["max_gap_days"]),
            "censoring": "Episodes active at each pool's last observation are right-censored",
        },
        "ranking": {
            "k_values": list(config["metrics"]["ranking"]["k_values"]),
            "horizons_days": list(config["metrics"]["ranking"]["horizons_days"]),
            "formula": "churn = 1 - |top_k(t) intersection top_k(t+h)| / k",
            "summary_aggregation": (
                "Pooled mean across valid observed-date x top-k comparisons; "
                "each valid comparison receives equal weight"
            ),
        },
        "event_study": {
            "trigger": "1-day APY increase >= 5 percentage points and APY >= 10%",
            "maximum_events_per_pool": 3,
            "window_days": [-7, 30],
        },
        "joint_screen": {
            "definition": "Pool is above the sample medians for APY, persistence and TVL",
            "pareto_frontier": False,
        },
    }

    return {
        "mode": mode,
        "market": {
            "pool_count": int(metric(market, "pool_count")),
            "pool_day_count": int(metric(market, "pool_day_count")),
            "chain_count": int(metric(market, "chain_count")),
            "protocol_count": int(metric(market, "protocol_count")),
            "median_apy": round(metric(market, "median_apy"), 2),
            "mean_apy": round(metric(market, "mean_apy"), 2),
            "p90_apy": round(float(apy.quantile(0.9)), 2) if not apy.empty else 0.0,
            "p99_apy": round(float(apy.quantile(0.99)), 2) if not apy.empty else 0.0,
            "apy_histogram": apy_histogram(apy),
            "median_tvl_usd": round(metric(market, "median_tvl_usd"), 0),
            "base_apy_coverage": round(metric(market, "base_apy_coverage"), 3),
            "reward_apy_coverage": round(metric(market, "reward_apy_coverage"), 3),
            "apy_coverage": round(float(apy.notna().mean()), 4) if not apy.empty else 0.0,
            "tvl_coverage": round(float(tvl.notna().mean()), 4) if not tvl.empty else 0.0,
            "date_min": str(panel_dates.min().date()) if not panel_dates.empty else "n/a",
            "date_max": str(panel_dates.max().date()) if not panel_dates.empty else "n/a",
        },
        "episodes": episode_summary(selected_episodes, survival),
        "ranking": {
            "mean_churn_by_horizon": churn_summary,
            "comparison_count_by_horizon": churn_counts,
            "aggregation": "comparison_weighted_mean_across_top_k",
        },
        "frontier": screen,
        "joint_screen": screen,
        "quality": {
            "critical_failures": critical_failures,
            "warning_checks": warnings,
            "checks": int(len(quality)),
            "records": quality_records,
            "warning_records": [row for row in quality_records if row["status"] == "warning"],
        },
        "robustness": robustness.to_dict(orient="records") if not robustness.empty else [],
        "depeg": depeg_summary,
        "methodology": methodology,
        "pool_types": pool_type_counts(pools),
        "pool_type_metrics": pool_type_metrics(frontier),
        "pool_type_components": pool_type_components(panel),
        "top_chains": value_counts(frontier, "chain", 6),
        "top_protocols": value_counts(frontier, "protocol_name", 6),
        "archetypes": value_counts(archetypes, "archetype", 8),
        "event_response": event_response_summary(event_response),
        "data_assets": data_assets(paths),
        "figures": figure_records,
        "sources": source_cards(),
    }


def episode_summary(selected_episodes: pd.DataFrame, survival: pd.DataFrame) -> dict:
    if selected_episodes.empty:
        return {
            "primary_count": 0,
            "primary_median_duration_days": None,
            "duration_p75": None,
            "duration_p90": None,
            "censored_share": 0.0,
            "survival_rows": int(len(survival)),
            "survival_points": {},
            "survival_curve": [],
        }
    durations = selected_episodes["duration_days"].astype(float)
    return {
        "primary_count": int(len(selected_episodes)),
        "primary_median_duration_days": round(float(durations.median()), 2),
        "duration_p75": round(float(durations.quantile(0.75)), 2),
        "duration_p90": round(float(durations.quantile(0.90)), 2),
        "censored_share": round(float(selected_episodes["is_censored"].mean()), 4)
        if "is_censored" in selected_episodes
        else 0.0,
        "survival_rows": int(len(survival)),
        "survival_points": survival_points(survival, [1, 2, 7, 30]),
        "survival_curve": survival_curve_records(survival),
    }


def frontier_summary(frontier: pd.DataFrame) -> dict:
    if frontier.empty:
        return {
            "candidate_count": 0,
            "pool_count": 0,
            "candidate_share": 0.0,
            "median_apy": 0.0,
            "median_persistence": 0.0,
            "median_tvl_usd": 0.0,
            "median_reward_share": 0.0,
            "pareto_frontier": False,
            "series": [],
        }
    candidate_series = frontier.get("frontier_candidate", pd.Series(dtype=bool))
    if candidate_series.dtype == "object":
        candidate_series = candidate_series.astype(str).str.lower().eq("true")
    else:
        candidate_series = candidate_series.astype(bool)

    def series(label: str, mask: pd.Series) -> dict:
        frame = frontier[mask]
        return {
            "name": label,
            "x": [round(float(value), 3) for value in frame["median_apy"]],
            "y": [round(float(value), 4) for value in frame["persistence_ratio_10"]],
            "bubble": [
                round(max(float(value), 1.0) / 1_000_000, 3)
                for value in frame["median_tvl_usd"]
            ],
        }

    return {
        "candidate_count": int(candidate_series.sum()),
        "pool_count": int(len(frontier)),
        "candidate_share": round(float(candidate_series.mean()), 3),
        "median_apy": round(float(frontier["median_apy"].median()), 3),
        "median_persistence": round(float(frontier["persistence_ratio_10"].median()), 3),
        "median_tvl_usd": round(float(frontier["median_tvl_usd"].median()), 0),
        "median_reward_share": round(float(frontier["median_reward_share"].median()), 3)
        if "median_reward_share" in frontier
        else 0.0,
        "pareto_frontier": False,
        "series": [
            series("Clears all three thresholds", candidate_series),
            series("Other pools", ~candidate_series),
        ],
    }


def event_response_summary(event_response: pd.DataFrame) -> dict:
    if event_response.empty:
        return {}
    return {
        "event_count_max": int(event_response["event_count"].max()),
        "points": {
            str(day): event_point(event_response, day)
            for day in [-7, 0, 7, 30]
            if not event_response[event_response["event_time_day"] == day].empty
        },
    }


def event_point(event_response: pd.DataFrame, day: int) -> dict:
    row = event_response[event_response["event_time_day"] == day].iloc[0]
    return {
        "median_apy": round(float(row["median_apy"]), 2),
        "median_tvl_index": round(float(row["median_tvl_index"]), 3),
        "event_count": int(row["event_count"]),
    }


def depeg_point(depeg: pd.DataFrame, day: int) -> dict:
    row = depeg[depeg["event_time_day"] == day].iloc[0]
    return {
        "price_usd": round(float(row["price_usd"]), 4),
        "median_apy": round(float(row["median_apy"]), 2)
        if pd.notna(row["median_apy"])
        else None,
        "median_tvl_usd": round(float(row["median_tvl_usd"]), 0)
        if pd.notna(row["median_tvl_usd"])
        else None,
        "pool_count": int(row["pool_count"]) if pd.notna(row["pool_count"]) else 0,
    }


def survival_points(survival: pd.DataFrame, days: list[int]) -> dict:
    if survival.empty:
        return {}
    out = {}
    for day in days:
        candidates = survival[survival["duration_days"] <= day]
        if candidates.empty:
            continue
        row = candidates.iloc[-1]
        out[str(day)] = {
            "survival": round(float(row["survival"]), 3),
            "at_risk": int(row["at_risk"]),
        }
    return out


def survival_curve_records(survival: pd.DataFrame) -> list[dict]:
    if survival.empty:
        return []
    columns = ["duration_days", "survival", "ci_lower", "ci_upper", "at_risk"]
    frame = survival.loc[:, columns].dropna(subset=["duration_days", "survival"])
    frame = frame.sort_values("duration_days")
    return [
        {
            "duration_days": round(float(row.duration_days), 2),
            "survival": round(float(row.survival), 6),
            "ci_lower": round(float(row.ci_lower), 6),
            "ci_upper": round(float(row.ci_upper), 6),
            "at_risk": int(row.at_risk),
        }
        for row in frame.itertuples(index=False)
    ]


def apy_histogram(apy: pd.Series, bins: int = 32) -> dict:
    values = pd.to_numeric(apy, errors="coerce").dropna().astype(float)
    if values.empty:
        return {
            "observation_count": 0,
            "clip_percentile": 0.99,
            "clip_value": 0.0,
            "min_value": 0.0,
            "bins": [],
        }
    clip_value = float(values.quantile(0.99))
    min_value = float(values.min())
    if clip_value <= min_value:
        clip_value = min_value + 1.0
    counts, edges = np.histogram(
        values.clip(upper=clip_value).to_numpy(),
        bins=bins,
        range=(min_value, clip_value),
    )
    return {
        "observation_count": int(len(values)),
        "clip_percentile": 0.99,
        "clip_value": round(clip_value, 4),
        "min_value": round(min_value, 4),
        "bins": [
            {
                "lower": round(float(edges[index]), 4),
                "upper": round(float(edges[index + 1]), 4),
                "count": int(count),
            }
            for index, count in enumerate(counts)
        ],
    }


def data_assets(paths) -> list[dict]:
    specs = [
        ("raw request envelopes", paths.raw_dir / "manifest.jsonl", "Raw provenance"),
        ("pools", paths.processed_dir / "pools.parquet", "Canonical entities"),
        ("pool snapshots", paths.processed_dir / "pool_snapshots.parquet", "Clean observations"),
        ("stablecoins", paths.processed_dir / "stablecoins.parquet", "Stablecoin metadata"),
        ("stablecoin prices", paths.processed_dir / "stablecoin_prices.parquet", "Peg context"),
        ("risk events", paths.processed_dir / "risk_events.parquet", "Event context"),
        ("pool-day panel", paths.analytical_dir / "pool_day_panel.parquet", "Analysis grain"),
        ("yield episodes", paths.analytical_dir / "yield_episodes.parquet", "Episode analysis"),
        ("pool metrics", paths.analytical_dir / "pool_metrics.parquet", "Pool summaries"),
    ]
    return [
        {
            "asset": label,
            "rows": count_rows(path),
            "role": role,
            "path": path.relative_to(paths.root).as_posix(),
        }
        for label, path, role in specs
    ]


def count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    if path.suffix == ".jsonl":
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    if path.suffix == ".parquet":
        return int(len(read_table(path)))
    if path.suffix == ".csv":
        return int(len(pd.read_csv(path)))
    return 0


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def metric(frame: pd.DataFrame, name: str) -> float:
    if frame.empty:
        return 0.0
    match = frame.loc[frame["metric"] == name, "value"]
    return float(match.iloc[0]) if not match.empty else 0.0


def pool_type_counts(pools: pd.DataFrame) -> dict[str, int]:
    if pools.empty or "pool_type" not in pools:
        return {}
    return {str(name): int(value) for name, value in pools["pool_type"].value_counts().items()}


def pool_type_metrics(frontier: pd.DataFrame) -> list[dict]:
    if frontier.empty or "pool_type" not in frontier:
        return []
    rows = []
    grouped = frontier.groupby("pool_type", dropna=False)
    for pool_type, frame in grouped:
        rows.append(
            {
                "pool_type": str(pool_type),
                "pools": int(len(frame)),
                "median_apy": round(float(frame["median_apy"].median()), 2),
                "median_tvl_usd": round(float(frame["median_tvl_usd"].median()), 0),
                "median_persistence": round(float(frame["persistence_ratio_10"].median()), 3),
            }
        )
    return sorted(rows, key=lambda item: item["pools"], reverse=True)


def pool_type_components(panel: pd.DataFrame) -> list[dict]:
    if panel.empty or "pool_type" not in panel:
        return []
    rows = []
    for pool_type, frame in panel.groupby("pool_type", dropna=False):
        rows.append(
            {
                "pool_type": str(pool_type),
                "median_base_apy": round(float(frame["apy_base"].median()), 2)
                if frame["apy_base"].notna().any()
                else 0.0,
                "median_reward_apy": round(float(frame["apy_reward"].median()), 2)
                if frame["apy_reward"].notna().any()
                else 0.0,
            }
        )
    return sorted(rows, key=lambda item: item["median_base_apy"], reverse=True)


def value_counts(frame: pd.DataFrame, column: str, limit: int) -> list[dict]:
    if frame.empty or column not in frame:
        return []
    counts = frame[column].fillna("unknown").astype(str).value_counts().head(limit)
    return [{"label": str(label), "count": int(count)} for label, count in counts.items()]


def source_cards() -> list[dict]:
    return [
        {
            "source": "DeFiLlama yields",
            "endpoint": "yields.llama.fi/pools and /chart/{pool}",
            "role": "Pool universe, APY components, TVL and history",
            "auth": "No key",
            "evidence": "15,669 live pools observed; 250 selected for full analysis",
        },
        {
            "source": "DeFiLlama stablecoins",
            "endpoint": "stablecoins.llama.fi/stablecoins and /stablecoinprices",
            "role": "Stablecoin metadata and peg-price context",
            "auth": "No key",
            "evidence": "404 assets and 2,012 price date records verified",
        },
        {
            "source": "CoinGecko Demo",
            "endpoint": "coins/markets",
            "role": "Fallback checks for selected stablecoins",
            "auth": "Optional demo key",
            "evidence": "Keyless sample returned 3 assets on 2026-07-08",
        },
        {
            "source": "Protocol documentation",
            "endpoint": "Aave, Compound, Curve, Yearn, Sky/Maker, Ethena and selected docs",
            "role": "Mechanism labels and caveats",
            "auth": "No key",
            "evidence": "Classification is metadata, not a safety rating",
        },
    ]


def render_markdown(root: Path, summary: dict) -> str:
    figures = {item["id"]: item for item in summary["figures"]}
    robustness_table = pd.DataFrame(summary["robustness"]).fillna("n/a")
    pool_type_table = pd.DataFrame(summary["pool_type_metrics"])
    source_table = pd.DataFrame(summary["sources"])
    data_assets_table = pd.DataFrame(summary["data_assets"])
    quality_table = pd.DataFrame(summary["quality"]["records"])
    archetype_table = pd.DataFrame(summary["archetypes"])
    churn = summary["ranking"]["mean_churn_by_horizon"]
    event_points = summary["event_response"].get("points", {})
    lines = [
        "# Stablecoin Yield",
        "",
        "**Project title:** The Price of Yield: Persistence, Mechanisms and TVL Response in Stablecoin DeFi",
        "",
        f"**Pipeline mode:** `{summary['mode']}`",
        "",
        "## Abstract",
        "",
        (
            "This project studies stablecoin-denominated DeFi yield as an observed data "
            "visualization problem, not as an investment ranking. The analysis combines "
            "DeFiLlama yield histories, DeFiLlama stablecoin price context, CoinGecko "
            "fallback checks and documented protocol classifications into a canonical "
            "pool-day panel. The core question is whether high APY is persistent once "
            "duration, TVL, reward dependence, stablecoin peg stress and pool mechanism "
            "are shown together."
        ),
        "",
        (
            f"The full panel covers {summary['market']['pool_count']:,} pools, "
            f"{summary['market']['pool_day_count']:,} pool-days, {summary['market']['chain_count']} "
            f"chains and {summary['market']['protocol_count']} protocols from "
            f"{summary['market']['date_min']} to {summary['market']['date_max']}. "
            f"The pool-day median APY is {summary['market']['median_apy']:.2f} percent, while "
            f"the pool-day mean is {summary['market']['mean_apy']:.2f} percent, indicating a "
            "heavy-tailed yield distribution."
        ),
        "",
        "## Research Questions",
        "",
        "1. How long do high-yield regimes last for stablecoin pools?",
        "2. Which yield components and pool mechanisms explain headline APY?",
        "3. How stable are top-yield memberships over one-day, seven-day and thirty-day horizons?",
        "4. How do peg-stress windows change the interpretation of nominal APY?",
        "5. Which pools clear transparent APY, persistence and capacity thresholds simultaneously?",
        "",
        "## Data Sources",
        "",
        source_table.to_markdown(index=False),
        "",
        "## Data Pipeline And Canonical Schema",
        "",
        (
            "Raw API responses are stored as request envelopes with payload checksums under "
            "`data/raw/`. The pipeline then builds canonical pool, stablecoin, protocol, "
            "yield mechanism and risk-event tables before producing the pool-day analytical panel."
        ),
        "",
        data_assets_table.to_markdown(index=False),
        "",
        "## Data Quality",
        "",
        (
            f"The quality suite ran {summary['quality']['checks']} checks with "
            f"{summary['quality']['critical_failures']} critical failures and "
            f"{summary['quality']['warning_checks']} warning checks. Warning rows are retained "
            "and documented rather than hidden."
        ),
        "",
        quality_table.to_markdown(index=False),
        "",
        "## Methodology",
        "",
        (
            "High-yield episodes use the main threshold APY >= 10 percent. Episodes are "
            "continuous runs above the threshold and active episodes at the final observation "
            "are treated as censored in the Kaplan-Meier survival calculation."
        ),
        "",
        (
            "Ranking churn compares top-k APY sets across one-day, seven-day and thirty-day "
            "horizons. TVL response is an observational event-time proxy, not a direct measure "
            "of wallet-level capital flow. The joint screen marks pools above the pool-level "
            "sample medians for APY, persistence and TVL without constructing a score or claiming "
            "a Pareto frontier."
        ),
        "",
        "## Main Results",
        "",
        (
            f"The main APY >= 10 percent rule detects {summary['episodes']['primary_count']:,} "
            f"episodes. The median duration is {summary['episodes']['primary_median_duration_days']} "
            f"days and the 90th percentile duration is {summary['episodes']['duration_p90']} days."
        ),
        "",
        (
            f"Comparison-weighted average top-yield churn rises from {pct(churn.get('1'))} at one day to "
            f"{pct(churn.get('7'))} at seven days and {pct(churn.get('30'))} at thirty days."
        ),
        "",
        (
            f"{summary['joint_screen']['candidate_count']} of {summary['joint_screen']['pool_count']} pools "
            f"({summary['joint_screen']['candidate_share']:.1%}) sit above the pool-level sample medians for APY, "
            f"persistence and TVL. The APY threshold is {summary['joint_screen']['median_apy']:.2f} percent, distinct from the {summary['market']['median_apy']:.2f} percent pool-day median."
        ),
        "",
        "### Pool Type Metrics",
        "",
        pool_type_table.to_markdown(index=False),
        "",
        "### Archetypes",
        "",
        archetype_table.to_markdown(index=False),
        "",
        "## Peg Stress And Event Response",
        "",
        (
            f"The selected peg-stress case is `{summary['depeg']['stablecoin_id']}` on "
            f"{summary['depeg']['event_date']}. The minimum observed price is "
            f"{summary['depeg']['min_price_usd']:.4f} USD. APY and TVL response are read as "
            "observed context, not causal estimates."
        )
        if summary["depeg"]
        else "No peg-stress event was selected.",
        "",
        f"Event response checkpoints: {json.dumps(event_points)}",
        "",
        "## Robustness Checks",
        "",
        robustness_table.to_markdown(index=False),
        "",
        "## Visual Evidence",
        "",
    ]
    for figure_id, label in [
        ("fig_01_yield_universe", "Yield universe"),
        ("fig_02_apy_distribution", "APY distribution"),
        ("fig_03_episode_survival", "Episode survival"),
        ("fig_04_ranking_churn", "Ranking churn"),
        ("fig_07_apy_tvl_relationship", "APY and TVL event response"),
        ("fig_08_depeg_event_study", "Peg-stress context"),
        ("fig_09_pool_archetypes", "Pool archetypes"),
        ("fig_10_hero_yield_frontier", "Hero joint screen"),
    ]:
        lines.append(figure_markdown(figures.get(figure_id, {}), label))
    lines.extend(
        [
            "",
            "## Limitations And Ethics",
            "",
            "APY is quoted annualized APY, not realized return. TVL change is an observed balance proxy, not direct capital flow. "
            "Protocol risk, smart contract risk, legal risk and user-specific costs are not fully measured. "
            "The project intentionally avoids recommendations, portfolio advice and a universal pool ranking.",
            "",
            "## Technical Appendix",
            "",
            "Run `uv sync --extra dev` and then `uv run python scripts/reproduce_all.py --mode sample` for a local reproducibility check. "
            "Run with `--mode full` to refresh live data within public API limits. The final manifest is written to `outputs/release_manifest.json`.",
            "",
            "## References",
            "",
            "- DeFiLlama API documentation: https://api-docs.defillama.com/llms-free.txt",
            "- DeFiLlama yields live host: https://yields.llama.fi",
            "- DeFiLlama stablecoins live host: https://stablecoins.llama.fi",
            "- CoinGecko Demo API documentation: https://docs.coingecko.com/demo/reference/coins-markets",
            "- Course requirements and notes under `docs/Project/`, `docs/Slide/` and `docs/data_visualization_notes.pdf`.",
            "",
        ]
    )
    return "\n".join(lines)


def figure_markdown(figure: dict, label: str) -> str:
    if not figure:
        return ""
    return (
        f"### {label}\n\n"
        f"![{figure['title']}]({figure['png']})\n\n"
        f"**Question:** {figure['question']}  \n"
        f"**Message:** {figure['message']}  \n"
        f"**Sample:** {figure['sample_size']}\n"
    )


def render_pdf(root: Path, summary: dict, output: Path) -> None:
    styles = landscape_styles()
    figures = {item["id"]: item for item in summary["figures"]}
    c = pdf_canvas.Canvas(str(output), pagesize=slide_size())
    c.setTitle("Stablecoin Yield Report")
    c.setAuthor("Stablecoin Yield project")
    pages = [
        lambda page: draw_landscape_cover(c, page, root, summary, figures, styles),
        lambda page: draw_rq_slide(c, page, summary, styles),
        lambda page: draw_sources_slide(c, page, summary, styles),
        lambda page: draw_pipeline_slide(c, page, summary, styles),
        lambda page: draw_quality_method_slide(c, page, summary, styles),
        lambda page: draw_visual_slide(
            c,
            page,
            root,
            figures["fig_01_yield_universe"],
            "What is the observed stablecoin yield universe?",
            [
                "The sample spans multiple chains, protocols and pool types. A single APY number is therefore not a comparable market price.",
                f"The final scope contains <b>{summary['market']['pool_count']:,} pools</b> and <b>{summary['market']['pool_day_count']:,} pool-days</b>.",
            ],
            "APY must be read with category and capacity context.",
            styles,
            mini_rows=[("Pools", f"{summary['market']['pool_count']:,}"), ("Chains", str(summary['market']['chain_count'])), ("Protocols", str(summary['market']['protocol_count']))],
        ),
        lambda page: draw_double_visual_slide(c, page, root, summary, figures, styles),
        lambda page: draw_visual_slide(
            c,
            page,
            root,
            figures["fig_03_episode_survival"],
            "How long does high APY last?",
            [
                f"The APY >= 10 percent definition produces <b>{summary['episodes']['primary_count']:,} episodes</b>.",
                f"The median episode lasts <b>{summary['episodes']['primary_median_duration_days']} days</b>; by day 30, survival is only {pct(summary['episodes']['survival_points'].get('30', {}).get('survival'))}.",
            ],
            "High APY is usually an episode, not a durable pool trait.",
            styles,
            mini_rows=[("Median", f"{summary['episodes']['primary_median_duration_days']}d"), ("P75", f"{summary['episodes']['duration_p75']}d"), ("P90", f"{summary['episodes']['duration_p90']}d")],
        ),
        lambda page: draw_visual_slide(
            c,
            page,
            root,
            figures["fig_04_ranking_churn"],
            "Are top-yield lists stable?",
            [
                "The top-yield set changes materially as the comparison horizon widens.",
                f"Comparison-weighted average churn rises from <b>{pct(summary['ranking']['mean_churn_by_horizon'].get('1'))}</b> at one day to <b>{pct(summary['ranking']['mean_churn_by_horizon'].get('30'))}</b> at thirty days.",
            ],
            "This is why the report avoids a best-pool leaderboard.",
            styles,
            mini_rows=[("1 day", pct(summary["ranking"]["mean_churn_by_horizon"].get("1"))), ("7 days", pct(summary["ranking"]["mean_churn_by_horizon"].get("7"))), ("30 days", pct(summary["ranking"]["mean_churn_by_horizon"].get("30")))],
        ),
        lambda page: draw_visual_slide(
            c,
            page,
            root,
            figures["fig_07_apy_tvl_relationship"],
            "Do APY jumps and TVL move together?",
            [
                "APY jumps and normalized TVL response are aligned in event time.",
                "The pattern is observational: TVL can move because of deposits, withdrawals, price effects, accounting changes, migrations or source revisions.",
            ],
            "APY and TVL should be read on separate clocks.",
            styles,
            mini_rows=[("Events", str(summary["event_response"].get("event_count_max", "n/a"))), ("Day -7", str(summary["event_response"].get("points", {}).get("-7", {}).get("median_tvl_index", "n/a"))), ("Day 30", str(summary["event_response"].get("points", {}).get("30", {}).get("median_tvl_index", "n/a")))],
        ),
        lambda page: draw_visual_slide(
            c,
            page,
            root,
            figures["fig_08_depeg_event_study"],
            "What happens around peg stress?",
            [
                f"The selected event is <b>{summary['depeg']['stablecoin_id']}</b> on <b>{summary['depeg']['event_date']}</b>.",
                f"The minimum observed price is <b>{summary['depeg']['min_price_usd']:.4f} USD</b>, so nominal APY needs stablecoin price context.",
            ],
            "Peg stress changes the denominator behind nominal yield.",
            styles,
            mini_rows=[("Min price", f"{summary['depeg']['min_price_usd']:.4f}"), ("Peak dev.", f"{summary['depeg']['peak_abs_deviation']:.4f}"), ("Pools", str(summary["depeg"]["max_pool_count"]))],
        ),
        lambda page: draw_visual_slide(
            c,
            page,
            root,
            figures["fig_10_hero_yield_frontier"],
            "How should yield be compared without ranking?",
            [
                f"<b>{summary['joint_screen']['candidate_count']}</b> of <b>{summary['joint_screen']['pool_count']}</b> pools clear sample medians for APY, persistence and TVL simultaneously.",
                "The joint screen keeps trade-offs visible instead of hiding them inside a score.",
            ],
            "The joint screen is descriptive, not financial advice.",
            styles,
            mini_rows=[("Candidates", str(summary["joint_screen"]["candidate_count"])), ("Share", f"{summary['joint_screen']['candidate_share']:.1%}"), ("Pools", str(summary["joint_screen"]["pool_count"]))],
        ),
        lambda page: draw_visual_slide(
            c,
            page,
            root,
            figures["fig_09_pool_archetypes"],
            "Do pools cluster into interpretable profiles?",
            [
                "Archetypes summarize pool-level patterns across APY, persistence, TVL, reward share and volatility.",
                "They are useful for discussion but are not risk labels, safety ratings or recommendations.",
            ],
            "Clusters help describe heterogeneity; they do not replace the research questions.",
            styles,
            mini_rows=[(row["label"], str(row["count"])) for row in summary["archetypes"][:4]],
        ),
        lambda page: draw_robustness_slide(c, page, summary, styles),
        lambda page: draw_limitations_slide(c, page, summary, styles),
        lambda page: draw_appendix_slide(c, page, summary, styles),
    ]
    for page_num, draw_page in enumerate(pages, start=1):
        draw_page(page_num)
        if page_num < len(pages):
            c.showPage()
    c.save()


def slide_size() -> tuple[int, int]:
    return (720, 405)


def landscape_styles() -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle(
            "LandscapeTitle",
            fontName="Courier-Bold",
            fontSize=22,
            leading=27,
            textColor=ink(),
        ),
        "subtitle": ParagraphStyle(
            "LandscapeSubtitle",
            fontName="Courier",
            fontSize=12,
            leading=16,
            textColor=muted(),
        ),
        "h1": ParagraphStyle(
            "LandscapeH1",
            fontName="Courier-Bold",
            fontSize=18,
            leading=22,
            textColor=coral(),
            alignment=TA_CENTER,
        ),
        "h2": ParagraphStyle(
            "LandscapeH2",
            fontName="Courier-Bold",
            fontSize=14,
            leading=17,
            textColor=ink(),
        ),
        "body": ParagraphStyle(
            "LandscapeBody",
            fontName="Courier",
            fontSize=10,
            leading=14,
            textColor=ink(),
        ),
        "body_small": ParagraphStyle(
            "LandscapeBodySmall",
            fontName="Courier",
            fontSize=8.1,
            leading=10.5,
            textColor=ink(),
        ),
        "caption": ParagraphStyle(
            "LandscapeCaption",
            fontName="Courier",
            fontSize=6.3,
            leading=8,
            textColor=muted(),
            alignment=TA_CENTER,
        ),
        "box": ParagraphStyle(
            "LandscapeBox",
            fontName="Courier",
            fontSize=9.0,
            leading=11.5,
            textColor=ink(),
        ),
        "table": ParagraphStyle(
            "LandscapeTable",
            fontName="Courier",
            fontSize=7.0,
            leading=8.5,
            textColor=ink(),
        ),
        "table_header": ParagraphStyle(
            "LandscapeTableHeader",
            fontName="Courier-Bold",
            fontSize=7.2,
            leading=8.7,
            textColor=colors.white,
        ),
    }


def draw_landscape_cover(c, page_num: int, root: Path, summary: dict, figures: dict, styles) -> None:
    draw_slide_background(c, page_num)
    draw_image_fit(c, root / figures["fig_10_hero_yield_frontier"]["png"], 28, 146, 315, 180)
    draw_text(c, "Stablecoin yield joint screen", 32, 126, 300, styles["caption"])
    draw_metric_strip(
        c,
        [
            (f"{summary['market']['pool_count']:,}", "pools"),
            (f"{summary['market']['pool_day_count']:,}", "pool-days"),
            (f"{summary['episodes']['primary_median_duration_days']}", "median high-yield days"),
        ],
        30,
        34,
        styles,
    )
    c.setStrokeColor(rule())
    c.line(360, 0, 360, 405)
    draw_text(
        c,
        "The price of yield",
        388,
        328,
        290,
        styles["title"],
    )
    draw_text(
        c,
        "Persistence, mechanisms and TVL response in stablecoin DeFi",
        390,
        282,
        285,
        styles["subtitle"],
    )
    draw_text(
        c,
        "A visual analytics report on why quoted stablecoin APY should be read as a regime with duration, capacity, mechanism and peg context, not as a ranked list of pools.",
        390,
        226,
        285,
        styles["body"],
    )
    draw_outline_box(
        c,
        390,
        54,
        285,
        88,
        "Scope boundary",
        "Educational analysis only. APY is quoted annualized APY, TVL is an observed proxy, and no output is financial advice or a pool recommendation.",
        styles,
    )


def draw_rq_slide(c, page_num: int, summary: dict, styles) -> None:
    draw_slide_background(c, page_num)
    draw_center_title(c, "Research questions", styles)
    churn = summary["ranking"]["mean_churn_by_horizon"]
    rows = [
        ("RQ1", "How long do high-yield regimes last?", f"Median APY >= 10 episode duration: {summary['episodes']['primary_median_duration_days']} days."),
        ("RQ2", "Which mechanisms explain headline APY?", f"Base APY coverage: {pct(summary['market']['base_apy_coverage'])}; reward APY coverage: {pct(summary['market']['reward_apy_coverage'])}."),
        ("RQ3", "How stable are top-yield sets?", f"Churn rises from {pct(churn.get('1'))} to {pct(churn.get('30'))}."),
        ("RQ4", "How does peg stress change APY interpretation?", "Nominal APY is harder to read when the stablecoin denominator moves."),
        ("RQ5", "How can pools be compared without ranking?", f"{summary['joint_screen']['candidate_count']} joint-screen candidates show trade-offs, not recommendations."),
    ]
    draw_landscape_table(c, [["RQ", "Question", "Evidence"]] + rows, [55, 300, 275], 42, 304, styles)
    draw_outline_box(
        c,
        82,
        108,
        265,
        58,
        "Reading order",
        "The report moves from measurement to interpretation: duration first, mechanism second, stability and context after that.",
        styles,
    )
    draw_outline_box(
        c,
        374,
        108,
        265,
        58,
        "Assessment logic",
        "A strong answer is not a top-pool list. It is a transparent comparison that keeps uncertainty visible.",
        styles,
    )
    draw_outline_box(
        c,
        55,
        28,
        610,
        54,
        "Design decision",
        "The report answers comparison questions without creating a leaderboard. Each research question adds context that a single APY column would hide.",
        styles,
    )


def draw_sources_slide(c, page_num: int, summary: dict, styles) -> None:
    draw_slide_background(c, page_num)
    draw_center_title(c, "Data sources and feasibility", styles)
    source_rows = [["Source", "Role", "Evidence"]]
    for row in summary["sources"]:
        source_rows.append([row["source"], row["role"], row["evidence"]])
    draw_landscape_table(c, source_rows, [135, 250, 230], 45, 312, styles)
    evidence_rows = [
        ("Yields /pools", "15,669 pools", "APY, APY components, TVL, chain, project and pool ID verified."),
        ("Yields /chart", "503 observations in sample", "Historical APY and TVL are available at pool level."),
        ("Stablecoins", "404 assets", "Peg metadata and stablecoin price context available."),
    ]
    draw_landscape_table(c, [["Endpoint", "Observed", "Minimum evidence"]] + evidence_rows, [135, 135, 350], 45, 210, styles)
    draw_outline_box(
        c,
        55,
        34,
        285,
        62,
        "Verified source constraint",
        "DeFiLlama is the primary source. CoinGecko is only fallback/enrichment because public historical depth can be plan-limited.",
        styles,
    )
    draw_outline_box(
        c,
        375,
        34,
        285,
        62,
        "Raw preservation",
        "Live responses are stored as request envelopes with checksums before transformation into canonical tables.",
        styles,
    )


def draw_pipeline_slide(c, page_num: int, summary: dict, styles) -> None:
    draw_slide_background(c, page_num)
    draw_center_title(c, "Pipeline and canonical schema", styles)
    flow_rows = [
        ("1", "Collect", "Pool, chart, stablecoin and fallback payloads."),
        ("2", "Normalize", "Timestamps, APY components, TVL and identifiers."),
        ("3", "Resolve", "Pool IDs, stablecoin exposure, protocols and pool types."),
        ("4", "Validate", "Critical, error and warning checks."),
        ("5", "Analyze", "Episodes, survival, churn, event studies and joint screening."),
        ("6", "Render", "Figures, PDF, presentation previews and manifest."),
    ]
    draw_landscape_table(c, [["Step", "Stage", "Output"]] + flow_rows, [45, 90, 215], 40, 312, styles)
    asset_rows = [["Artifact", "Rows", "Role"]]
    for row in summary["data_assets"][1:8]:
        asset_rows.append([row["asset"], f"{row['rows']:,}", row["role"]])
    draw_landscape_table(c, asset_rows, [120, 65, 130], 400, 312, styles)
    draw_outline_box(
        c,
        82,
        112,
        265,
        56,
        "Entity resolution",
        "Pool IDs preserve the DeFiLlama source identifier; stablecoin exposure uses exact IDs and documented ticker overrides.",
        styles,
    )
    draw_outline_box(
        c,
        374,
        112,
        265,
        56,
        "Canonical grain",
        "The pool-day panel is rebuilt from processed tables, not from manual spreadsheet state.",
        styles,
    )
    draw_outline_box(
        c,
        70,
        28,
        580,
        52,
        "Analytical grain",
        "The central unit is a DeFi pool observed on one UTC day. This grain supports duration, ranking churn and event-time analysis.",
        styles,
    )


def draw_quality_method_slide(c, page_num: int, summary: dict, styles) -> None:
    draw_slide_background(c, page_num)
    draw_center_title(c, "Quality gates and metric definitions", styles)
    draw_metric_strip(
        c,
        [
            (str(summary["quality"]["checks"]), "checks"),
            (str(summary["quality"]["critical_failures"]), "critical failures"),
            (str(summary["quality"]["warning_checks"]), "warnings"),
        ],
        52,
        296,
        styles,
    )
    quality_rows = [["Check", "Status", "Failed"]]
    for row in summary["quality"]["records"][:8]:
        quality_rows.append([row["check_id"], row["status"], f"{row['failed_rows']:,}"])
    draw_landscape_table(c, quality_rows, [225, 72, 55], 52, 256, styles)
    method_rows = [
        ("High-yield episode", "Continuous APY >= 10 percent run."),
        ("Survival", "Kaplan-Meier with censored active episodes retained."),
        ("Ranking churn", "1 minus top-k retention across horizons."),
        ("TVL response", "Median normalized TVL index around APY jumps."),
        ("Frontier", "Above median APY, persistence and TVL."),
    ]
    draw_landscape_table(c, [["Metric", "Definition"]] + method_rows, [95, 180], 405, 256, styles)
    draw_outline_box(
        c,
        405,
        36,
        250,
        58,
        "Quality decision",
        "Extreme APY rows are flagged, not hidden. Removing them would make the source-reported distribution look cleaner than it is.",
        styles,
    )


def draw_double_visual_slide(c, page_num: int, root: Path, summary: dict, figures: dict, styles) -> None:
    draw_slide_background(c, page_num)
    draw_right_panel(c)
    draw_text(c, "What creates headline APY?", 38, 360, 300, styles["h1"])
    draw_image_fit(c, root / figures["fig_02_apy_distribution"]["png"], 36, 218, 300, 115)
    draw_image_fit(c, root / figures["fig_06_base_vs_reward"]["png"], 36, 82, 300, 115)
    draw_text(c, "Distribution and APY composition show why a single mean APY is a weak summary.", 42, 58, 288, styles["caption"])
    y = 338
    y = draw_text(c, f"Pool-day median APY is <b>{summary['market']['median_apy']:.2f}%</b>, while pool-day mean APY is <b>{summary['market']['mean_apy']:.2f}%</b>.", 384, y, 295, styles["body"])
    y = draw_text(c, "The gap indicates a heavy-tailed distribution: a small number of extreme observations pulls the mean above the median.", 384, y - 18, 295, styles["body"])
    y = draw_text(c, "Base and reward APY describe different mechanisms. Reward-heavy pools should not be compared blindly with base-yield pools.", 384, y - 18, 295, styles["body"])
    draw_outline_box(
        c,
        382,
        38,
        300,
        64,
        "What it does not prove",
        "It does not convert quoted APY into realized dollar return after fees, slippage or reward liquidation.",
        styles,
    )
    draw_landscape_footer(c, page_num)


def draw_visual_slide(
    c,
    page_num: int,
    root: Path,
    figure: dict,
    title: str,
    narrative: list[str],
    takeaway: str,
    styles,
    mini_rows: list[tuple[str, str]] | None = None,
) -> None:
    draw_slide_background(c, page_num)
    draw_right_panel(c)
    draw_text(c, title, 34, 352, 300, styles["h1"])
    draw_image_fit(c, root / figure["png"], 30, 78, 322, 232)
    draw_text(c, fig_caption(figure), 38, 52, 300, styles["caption"])
    y = 350
    for paragraph in narrative:
        y = draw_text(c, paragraph, 390, y, 290, styles["body"])
        y -= 16
    if mini_rows:
        draw_landscape_table(c, [["Metric", "Value"], *mini_rows], [145, 105], 390, max(y - 8, 120), styles)
    draw_outline_box(c, 382, 34, 302, 64, "Key reading", takeaway, styles)
    draw_landscape_footer(c, page_num)


def draw_robustness_slide(c, page_num: int, summary: dict, styles) -> None:
    draw_slide_background(c, page_num)
    draw_center_title(c, "Robustness checks", styles)
    rows = [["Check", "Episodes", "Median days", "Censored"]]
    for row in summary["robustness"]:
        rows.append(
            [
                str(row["check"]),
                f"{int(row['episode_count']):,}",
                "n/a" if pd.isna(row["median_duration_days"]) else str(row["median_duration_days"]),
                "n/a" if pd.isna(row["censored_share"]) else pct(row["censored_share"]),
            ]
        )
    draw_landscape_table(c, rows, [170, 90, 105, 90], 52, 302, styles)
    draw_outline_box(
        c,
        52,
        28,
        280,
        52,
        "Threshold sensitivity",
        "Counts change, but median duration stays 2.0 days at 5, 10 and 20 percent APY.",
        styles,
    )
    draw_outline_box(
        c,
        380,
        28,
        280,
        52,
        "Interpretation",
        "Short duration is robust; it is not a universal forecast for every future episode.",
        styles,
    )


def draw_limitations_slide(c, page_num: int, summary: dict, styles) -> None:
    draw_slide_background(c, page_num)
    draw_center_title(c, "Limitations and responsible interpretation", styles)
    rows = [
        ("APY", "Quoted annualized APY is not realized return."),
        ("TVL", "Observed TVL is not direct wallet-level capital flow."),
        ("Peg risk", "Price deviations do not fully measure counterparty, legal, collateral or redemption risk."),
        ("Protocol risk", "Mechanism labels are descriptive, not safety ratings."),
        ("Entity resolution", "Bridged assets, renamed pools and migrations can remain ambiguous."),
        ("Visual ethics", "The report avoids unsupported causality and recommendation framing."),
    ]
    draw_landscape_table(c, [["Concept", "Boundary"]] + rows, [140, 470], 55, 306, styles)
    draw_outline_box(
        c,
        92,
        34,
        536,
        58,
        "No recommendation boundary",
        "The project never identifies a best pool. Every pool-level label is descriptive evidence for the research question.",
        styles,
    )


def draw_appendix_slide(c, page_num: int, summary: dict, styles) -> None:
    draw_slide_background(c, page_num)
    draw_center_title(c, "Reproducibility and deliverables", styles)
    command_rows = [
        ("Install", "uv sync --extra dev"),
        ("Sample", "uv run python scripts/reproduce_all.py --mode sample"),
        ("Full", "uv run python scripts/reproduce_all.py --mode full"),
        ("Report", "uv run python scripts/build_report.py --mode full"),
    ]
    draw_landscape_table(c, [["Task", "Command"]] + command_rows, [105, 385], 42, 306, styles)
    deliverable_rows = [
        ("Report PDF", "outputs/report/stablecoin_yield_report.pdf"),
        ("Report preview", "outputs/report/rendered_preview/"),
        ("Presentation", "outputs/presentation/stablecoin_yield_presentation.pptx"),
        ("Manifest", "outputs/release_manifest.json"),
    ]
    draw_landscape_table(c, [["Deliverable", "Path"]] + deliverable_rows, [125, 365], 42, 180, styles)
    draw_outline_box(
        c,
        92,
        34,
        536,
        58,
        "Final reading",
        "High APY behaves like a regime, not a stable property. The joint screen keeps trade-offs visible without ranking pools.",
        styles,
    )


def draw_slide_background(c, page_num: int) -> None:
    width, height = slide_size()
    c.setFillColor(colors.white)
    c.rect(0, 0, width, height, stroke=0, fill=1)
    draw_landscape_footer(c, page_num)


def draw_right_panel(c) -> None:
    c.setFillColor(colors.HexColor("#F0F0F0"))
    c.rect(360, 0, 360, 405, stroke=0, fill=1)


def draw_center_title(c, title: str, styles) -> None:
    draw_text(c, title, 80, 365, 560, styles["h1"])


def draw_text(c, text: str, x: float, y_top: float, width: float, style: ParagraphStyle) -> float:
    paragraph = Paragraph(text, style)
    _, height = paragraph.wrap(width, 1000)
    paragraph.drawOn(c, x, y_top - height)
    return y_top - height


def draw_image_fit(c, path: Path, x: float, y: float, max_width: float, max_height: float) -> None:
    if not path.exists():
        c.setFillColor(colors.HexColor("#F4F7FA"))
        c.rect(x, y, max_width, max_height, stroke=1, fill=1)
        c.setFillColor(ink())
        c.setFont("Courier", 8)
        c.drawString(x + 8, y + max_height / 2, f"Missing image: {path.name}")
        return
    image = ImageReader(str(path))
    width, height = image.getSize()
    scale = min(max_width / width, max_height / height)
    draw_width = width * scale
    draw_height = height * scale
    draw_x = x + (max_width - draw_width) / 2
    draw_y = y + (max_height - draw_height) / 2
    c.drawImage(image, draw_x, draw_y, width=draw_width, height=draw_height, mask="auto")


def draw_landscape_table(c, rows: list, col_widths: list[float], x: float, y_top: float, styles) -> float:
    table_rows = []
    for row_index, row in enumerate(rows):
        style = styles["table_header"] if row_index == 0 else styles["table"]
        table_rows.append([Paragraph(escape(str(cell)), style) for cell in row])
    table = Table(table_rows, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), navy()),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, rule()),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FB")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    _, height = table.wrap(sum(col_widths), 1000)
    table.drawOn(c, x, y_top - height)
    return y_top - height


def draw_outline_box(
    c,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    body: str,
    styles,
) -> None:
    c.setFillColor(colors.white)
    c.setStrokeColor(coral())
    c.setLineWidth(0.8)
    c.rect(x, y, width, height, stroke=1, fill=1)
    draw_text(c, f"<b>{escape(title)}</b><br/>{escape(body)}", x + 8, y + height - 9, width - 16, styles["box"])


def draw_metric_strip(c, cards: list[tuple[str, str]], x: float, y: float, styles) -> None:
    card_width = 96
    for index, (value, label) in enumerate(cards):
        left = x + index * (card_width + 8)
        c.setFillColor(colors.HexColor("#EEF2F6"))
        c.setStrokeColor(rule())
        c.rect(left, y, card_width, 46, stroke=1, fill=1)
        draw_text(c, f"<b>{escape(value)}</b><br/>{escape(label)}", left + 6, y + 35, card_width - 12, styles["box"])


def draw_landscape_footer(c, page_num: int) -> None:
    c.setStrokeColor(rule())
    c.setLineWidth(0.4)
    c.line(28, 18, 692, 18)
    c.setFillColor(muted())
    c.setFont("Courier", 6.5)
    c.drawString(30, 8, "Stablecoin Yield - educational analysis, not financial advice")
    c.drawRightString(690, 8, str(page_num))


def coral():
    return colors.HexColor("#D86F5F")


def report_styles():
    styles = getSampleStyleSheet()
    base = styles["BodyText"]
    styles.add(
        ParagraphStyle(
            name="DeckKicker",
            parent=base,
            fontSize=7.5,
            leading=9.0,
            textColor=navy(),
            uppercase=True,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=base,
            fontSize=29,
            leading=33,
            textColor=ink(),
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=base,
            fontSize=12.5,
            leading=16,
            textColor=muted(),
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=base,
            fontSize=17,
            leading=20,
            textColor=ink(),
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=base,
            fontSize=8.7,
            leading=11.5,
            textColor=ink(),
            spaceAfter=4,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyTight",
            parent=base,
            fontSize=8.4,
            leading=10.8,
            textColor=ink(),
            spaceAfter=3,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=base,
            fontSize=7.0,
            leading=8.7,
            textColor=muted(),
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=base,
            fontSize=7.0,
            leading=8.6,
            textColor=muted(),
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CardMetric",
            parent=base,
            fontSize=8.3,
            leading=10.3,
            textColor=ink(),
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CardText",
            parent=base,
            fontSize=7.9,
            leading=9.7,
            textColor=ink(),
            spaceAfter=0,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CardTextSmall",
            parent=base,
            fontSize=7.2,
            leading=8.8,
            textColor=ink(),
            spaceAfter=0,
        )
    )
    return styles


def cover_page(summary: dict, styles) -> list:
    return [
        Spacer(1, 0.16 * inch),
        Paragraph("STABLECOIN YIELD", styles["DeckKicker"]),
        HRFlowable(width="100%", thickness=1.0, color=rule(), spaceBefore=5, spaceAfter=16),
        Paragraph("The price of yield", styles["ReportTitle"]),
        Paragraph(
            "Persistence, mechanisms and TVL response in stablecoin DeFi",
            styles["ReportSubtitle"],
        ),
        Paragraph(
            "A complete visual analytics report on why quoted stablecoin APY should be read as a regime with duration, capacity, mechanism and peg context, not as a ranked list of pools.",
            styles["Body"],
        ),
        Spacer(1, 0.15 * inch),
        metric_card_grid(
            [
                (f"{summary['market']['pool_count']:,}", "pools"),
                (f"{summary['market']['pool_day_count']:,}", "pool-days"),
                (f"{summary['market']['median_apy']:.2f}%", "pool-day median APY"),
                (f"{summary['episodes']['primary_count']:,}", "APY >= 10 episodes"),
                (f"{summary['episodes']['primary_median_duration_days']}", "median episode days"),
                (f"{summary['joint_screen']['candidate_share']:.1%}", "joint-screen share"),
            ],
            styles,
        ),
        Spacer(1, 0.28 * inch),
        callout(
            "Scope boundary",
            "Educational visual analytics only. APY is quoted annualized APY, TVL is an observed proxy, and no output is financial advice, a safety rating or a pool recommendation.",
            styles,
        ),
        Spacer(1, 0.23 * inch),
        Paragraph(
            f"Observation window: {summary['market']['date_min']} to {summary['market']['date_max']}. Full pipeline mode. Sources: DeFiLlama, CoinGecko fallback checks and selected protocol documentation.",
            styles["Small"],
        ),
        Spacer(1, 0.2 * inch),
        Paragraph("REPORT STRUCTURE", styles["DeckKicker"]),
        insight_grid(
            [
                ("Data foundation", "Verified public APIs, raw request envelopes, canonical schema and quality gates."),
                ("Analytical core", "High-yield episodes, ranking churn, APY components, event response and joint screening."),
                ("Responsible reading", "Robustness, limitations, ethics and technical reproducibility are part of the main report."),
            ],
            styles,
        ),
    ]


def abstract_page(summary: dict, styles) -> list:
    return [
        page_title("Abstract", "Why a high APY is not a complete claim", styles),
        Paragraph(
            "Stablecoin DeFi yield is often presented as a single percentage, but the same quoted APY can mean very different things. It can be a base lending rate, an incentive campaign, a reward-token subsidy, a transient imbalance in a stable-stable pool, or an artefact of denominator stress when the underlying stablecoin moves away from its peg.",
            styles["Body"],
        ),
        Paragraph(
            f"This report treats yield as a time-varying observed regime. The analysis combines DeFiLlama yield histories, stablecoin price context, CoinGecko fallback checks and documented protocol classifications into a canonical pool-day panel with {summary['market']['pool_day_count']:,} observations.",
            styles["Body"],
        ),
        Paragraph(
            f"The main empirical result is deliberately simple: high quoted yield is common, but persistent high yield with meaningful capacity is rarer. The main APY >= 10 percent specification detects {summary['episodes']['primary_count']:,} episodes with a median duration of {summary['episodes']['primary_median_duration_days']} days.",
            styles["Body"],
        ),
        Spacer(1, 0.12 * inch),
        two_column_cards(
            [
                ("Contribution 1", "A reproducible data pipeline that preserves raw API envelopes, checksums and canonical analytical tables."),
                ("Contribution 2", "A duration-based definition of high-yield regimes that avoids treating one-day APY snapshots as durable pool traits."),
            ],
            [
                ("Contribution 3", "A visual framework that compares APY, persistence and TVL without producing a hidden score or investment ranking."),
                ("Contribution 4", "An explicit responsible-use layer covering APY, TVL, peg stress, source dependence and visual ethics."),
            ],
            styles,
        ),
        Spacer(1, 0.16 * inch),
        callout(
            "Interpretation",
            "The report answers a data visualization question: how should yield be read and compared? It does not answer which pool should be used.",
            styles,
        ),
    ]


def research_questions_page(summary: dict, styles) -> list:
    churn = summary["ranking"]["mean_churn_by_horizon"]
    return [
        page_title("Research Questions", "From headline APY to interpretable visual evidence", styles),
        Paragraph(
            "The questions are sequenced from measurement to interpretation. The first two define what is being observed; the next two test stability and context; the final question turns the evidence into a responsible comparison design.",
            styles["Body"],
        ),
        research_question_table(
            [
                (
                    "RQ1",
                    "How long do high-yield regimes last?",
                    f"APY >= 10 percent episodes have median duration {summary['episodes']['primary_median_duration_days']} days.",
                ),
                (
                    "RQ2",
                    "Which mechanisms explain headline APY?",
                    f"Base APY coverage is {pct(summary['market']['base_apy_coverage'])}; reward APY coverage is {pct(summary['market']['reward_apy_coverage'])}.",
                ),
                (
                    "RQ3",
                    "How stable are top-yield sets?",
                    f"Comparison-weighted average churn rises from {pct(churn.get('1'))} to {pct(churn.get('30'))} between 1 and 30 days.",
                ),
                (
                    "RQ4",
                    "How does peg stress change interpretation?",
                    "A depeg window changes the stablecoin denominator behind nominal APY.",
                ),
                (
                    "RQ5",
                    "How can pools be compared without ranking?",
                    f"{summary['joint_screen']['candidate_count']} pools clear median APY, persistence and TVL simultaneously.",
                ),
            ],
            styles,
        ),
        Spacer(1, 0.14 * inch),
        callout(
            "Why these questions matter",
            "They prevent the report from becoming a leaderboard. Each question adds context that a single APY column would hide.",
            styles,
        ),
    ]


def data_sources_page(summary: dict, styles) -> list:
    return [
        page_title("Data Sources", "The project uses public sources with recorded constraints", styles),
        Paragraph(
            "Every source used in the final pipeline has an official documentation path, a live-request check and a recorded fallback. The source registry is not just a bibliography: it defines what can be trusted, what is missing, and where interpretation must remain cautious.",
            styles["Body"],
        ),
        source_table(summary["sources"], styles),
        Spacer(1, 0.14 * inch),
        callout(
            "Source decision",
            "DeFiLlama is the primary data source because it provides both current pool metadata and per-pool historical yield charts. CoinGecko is used only as a fallback/enrichment check, not as a hidden replacement source.",
            styles,
        ),
        Spacer(1, 0.12 * inch),
        Paragraph(
            "The live verification found a practical endpoint discrepancy: official documentation lists Yields & APY paths, while the working host for yield data is `yields.llama.fi`. The adapter keeps the base URL configurable and the discrepancy is documented as a source risk.",
            styles["Body"],
        ),
    ]


def source_verification_page(summary: dict, styles) -> list:
    return [
        page_title("Source Verification", "Feasibility checks before analysis", styles),
        Paragraph(
            "The first gate verified that the project could be completed without inventing fields or requiring paid data. The checks confirmed that APY, base APY, reward APY, TVL, pool IDs, stablecoin metadata and price context were available for the selected scope.",
            styles["Body"],
        ),
        evidence_table(
            [
                ("Yields pool universe", "15,669 live pools", "Core fields verified: chain, project, symbol, TVL, APY components, pool ID."),
                ("Stable candidate pool set", "489 candidates", "Stablecoin filter with TVL and history constraints exceeded the required sample."),
                ("Historical pool charts", "503 observations in sample request", "Per-pool history provides daily APY and TVL after UTC normalization."),
                ("Stablecoin metadata", "404 assets", "Stablecoin IDs, symbols, peg types and price fields available."),
                ("CoinGecko fallback", "3 keyless assets", "Works for small fallback checks; historical depth may require a key."),
            ],
            styles,
        ),
        Spacer(1, 0.13 * inch),
        callout(
            "Stage gate result",
            "The project is feasible with public data. No paid API key is required for the final DeFiLlama-based analysis; a CoinGecko key would only improve optional historical fallback depth.",
            styles,
        ),
    ]


def pipeline_page(summary: dict, styles) -> list:
    return [
        page_title("Pipeline", "Raw evidence is preserved before transformation", styles),
        Paragraph(
            "The pipeline is designed so that every final table can be traced back to raw source responses. Raw payloads are wrapped in request envelopes with URL, retrieval time, source ID and checksum. The analytical panel is then rebuilt from canonical processed tables, not from ad hoc notebook state.",
            styles["Body"],
        ),
        process_flow_table(
            [
                ("1", "Collect", "Download pool, chart, stablecoin and fallback payloads; preserve raw envelopes."),
                ("2", "Normalize", "Parse timestamps, APY components, TVL, pool identifiers and stablecoin metadata."),
                ("3", "Resolve entities", "Link source pool IDs to canonical pool IDs, protocols and stablecoin exposures."),
                ("4", "Validate", "Run critical, error and warning checks on analytical inputs."),
                ("5", "Analyze", "Build episodes, survival, churn, event studies, joint screening and archetypes."),
                ("6", "Communicate", "Render figures, report, presentation, previews and release manifest."),
            ],
            styles,
        ),
        Spacer(1, 0.14 * inch),
        data_asset_table(summary["data_assets"], styles),
    ]


def canonical_schema_page(summary: dict, styles) -> list:
    return [
        page_title("Canonical Schema", "The analytical grain is pool-day", styles),
        Paragraph(
            "The central table is `pool_day_panel`: one DeFi pool observed on one UTC day. This grain makes duration, ranking churn and event-time analysis possible without mixing current pool metadata with historical observations.",
            styles["Body"],
        ),
        schema_table(
            [
                ("pools", "Canonical pool entity, source pool ID, protocol, chain, pool type, assets, confidence fields."),
                ("pool_snapshots", "Daily APY, base APY, reward APY, TVL and provenance fields."),
                ("stablecoins", "Stablecoin IDs, symbols, design type, peg and external IDs."),
                ("yield_mechanisms", "Documented mechanism category with confidence and evidence caveats."),
                ("risk_events", "Peg and protocol context used for event-study windows."),
                ("pool_day_panel", "Joined analytical table used for metrics, figures and tests."),
            ],
            styles,
        ),
        Spacer(1, 0.12 * inch),
        two_column_cards(
            [
                ("Entity resolution", "Pool IDs preserve the source DeFiLlama identifier. Stablecoin exposure uses exact IDs when available and documented ticker overrides for common collisions."),
                ("Why overrides matter", "Ticker-only matching can choose the wrong stablecoin when wrapped, bridged or yield-bearing forms share a symbol."),
            ],
            [
                ("Quality field", "Each pool carries `entity_resolution_confidence` and low-confidence mappings are checked."),
                ("Known limitation", "Historical pool composition changes are treated as interval summaries, not intraday balance reconstructions."),
            ],
            styles,
        ),
    ]


def data_quality_page(summary: dict, styles) -> list:
    return [
        page_title("Data Quality", "Warnings are retained and explained", styles),
        Paragraph(
            f"The quality suite ran {summary['quality']['checks']} checks on the full outputs. There are {summary['quality']['critical_failures']} critical failures. Warning checks are retained because they describe real source behavior: sparse TVL gaps and a small number of extreme APY values.",
            styles["Body"],
        ),
        quality_summary_cards(summary, styles),
        Spacer(1, 0.12 * inch),
        quality_table(summary["quality"]["records"], styles),
        Spacer(1, 0.11 * inch),
        callout(
            "Quality decision",
            "Extreme APY observations are flagged rather than silently removed. Removing them would make the yield distribution look cleaner than the source-reported market.",
            styles,
        ),
    ]


def methodology_page(summary: dict, styles) -> list:
    return [
        page_title("Metric Methodology", "The report measures regimes, not investment outcomes", styles),
        Paragraph(
            "The metrics are chosen to answer visualization questions. They deliberately avoid portfolio backtesting, realized returns or user-level profitability because those would require transaction-level assumptions that the source data do not contain.",
            styles["Body"],
        ),
        method_table(
            [
                ("High-yield episode", "A continuous run where total APY is at least 10 percent. The run ends when APY falls below threshold or the history gap exceeds the configured allowance."),
                ("Kaplan-Meier survival", "Estimates the probability that an active high-yield episode remains above threshold while retaining censored active episodes."),
                ("Ranking churn", "Compares top-k APY sets across 1, 7 and 30 day horizons; churn is 1 minus retention."),
                ("APY/TVL event response", "Aligns APY jumps in event time and shows median APY and normalized TVL index around the jump."),
                ("Peg-stress study", "Aligns exposed-pool APY with stablecoin price movement around the selected peg deviation."),
                ("Joint threshold screen", "Marks pools above the pool-level sample medians for APY, persistence and TVL. It is a descriptive filter, not a Pareto frontier or score."),
            ],
            styles,
        ),
        Spacer(1, 0.12 * inch),
        callout(
            "Responsible metric boundary",
            "APY is quoted annualized APY, not realized return. TVL is an observed balance proxy, not direct capital flow.",
            styles,
        ),
    ]


def yield_universe_page(root: Path, summary: dict, figures: dict, styles) -> list:
    return [
        page_title("Result 1", "The stablecoin yield universe is heterogeneous", styles),
        Paragraph(
            f"The sample spans {summary['market']['chain_count']} chains and {summary['market']['protocol_count']} protocols. Pool types range from single-stable lending markets to stable-stable LPs, incentive-driven pools, vault aggregators and yield-bearing stablecoins.",
            styles["Body"],
        ),
        two_column_layout(
            scaled_image(root / figures["fig_01_yield_universe"]["png"], 4.55 * inch, 3.35 * inch),
            small_table(summary["pool_type_metrics"], ["pool_type", "pools", "median_apy"], ["Type", "Pools", "APY"], styles),
            styles,
        ),
        Paragraph(fig_caption(figures["fig_01_yield_universe"]), styles["Caption"]),
        proof_pair(
            "What this proves",
            "Stablecoin yield is not one homogeneous market: the sample mixes mechanisms, chains and capacity profiles.",
            "What it does not prove",
            "It does not rank pool types by safety or expected realized return.",
            styles,
        ),
    ]


def apy_mechanism_page(root: Path, summary: dict, figures: dict, styles) -> list:
    return [
        page_title("Result 2", "Headline APY is heavy-tailed and mechanism-dependent", styles),
        Paragraph(
            f"Across pool-day observations, the median APY is {summary['market']['median_apy']:.2f} percent, while the mean is {summary['market']['mean_apy']:.2f} percent. The 90th percentile is {summary['market']['p90_apy']:.2f} percent and the 99th percentile is {summary['market']['p99_apy']:.2f} percent. This gap is why medians and distribution views matter.",
            styles["Body"],
        ),
        scaled_image(root / figures["fig_02_apy_distribution"]["png"], 6.7 * inch, 2.3 * inch),
        Paragraph(fig_caption(figures["fig_02_apy_distribution"]), styles["Caption"]),
        Spacer(1, 0.04 * inch),
        scaled_image(root / figures["fig_06_base_vs_reward"]["png"], 6.7 * inch, 2.25 * inch),
        Paragraph(fig_caption(figures["fig_06_base_vs_reward"]), styles["Caption"]),
        proof_pair(
            "What this proves",
            "Medians are more stable summaries than means, and reward APY changes the meaning of the headline number.",
            "What it does not prove",
            "It does not convert reward APY into realized dollar return after fees, slippage or token liquidation.",
            styles,
        ),
    ]


def episode_survival_page(root: Path, summary: dict, figures: dict, styles) -> list:
    points = summary["episodes"]["survival_points"]
    return [
        page_title("Result 3", "High APY is usually short-lived", styles),
        Paragraph(
            f"The primary APY >= 10 percent definition produces {summary['episodes']['primary_count']:,} episodes. The median duration is {summary['episodes']['primary_median_duration_days']} days, the 75th percentile is {summary['episodes']['duration_p75']} days and the 90th percentile is {summary['episodes']['duration_p90']} days.",
            styles["Body"],
        ),
        two_column_layout(
            scaled_image(root / figures["fig_03_episode_survival"]["png"], 4.65 * inch, 3.45 * inch),
            survival_checkpoint_table(points, styles),
            styles,
        ),
        Paragraph(fig_caption(figures["fig_03_episode_survival"]), styles["Caption"]),
        proof_pair(
            "What this proves",
            "High APY should be treated as an episode: by day 2 the estimated survival is already below half.",
            "What it does not prove",
            "It does not forecast the exact future lifetime of a currently active pool.",
            styles,
        ),
    ]


def ranking_churn_page(root: Path, summary: dict, figures: dict, styles) -> list:
    churn = summary["ranking"]["mean_churn_by_horizon"]
    counts = summary["ranking"]["comparison_count_by_horizon"]
    return [
        page_title("Result 4", "Leaderboards are unstable across horizons", styles),
        Paragraph(
            f"The comparison-weighted average top-yield churn is {pct(churn.get('1'))} at one day, {pct(churn.get('7'))} at seven days and {pct(churn.get('30'))} at thirty days. Each valid observed-date/top-k comparison receives equal weight; the corresponding sample sizes are {counts.get('1'):,}, {counts.get('7'):,} and {counts.get('30'):,}. The heatmap cells remain the separate top-10 and top-20 means. The longer the horizon, the less stable the apparent top-yield set becomes.",
            styles["Body"],
        ),
        two_column_layout(
            scaled_image(root / figures["fig_04_ranking_churn"]["png"], 4.65 * inch, 3.35 * inch),
            churn_table(churn, styles),
            styles,
        ),
        Paragraph(fig_caption(figures["fig_04_ranking_churn"]), styles["Caption"]),
        proof_pair(
            "What this proves",
            "The observed top-yield set is horizon-sensitive: a leaderboard hides substantial turnover.",
            "What it does not prove",
            "It does not mean every high-yield pool is unstable; it means rank membership is not a durable label.",
            styles,
        ),
    ]


def event_response_page(root: Path, summary: dict, figures: dict, styles) -> list:
    points = summary["event_response"].get("points", {})
    return [
        page_title("Result 5", "APY jumps and TVL move on different clocks", styles),
        Paragraph(
            "The event response aligns APY jump events from seven days before to thirty days after the jump. TVL is normalized within each event, so the curve should be read as a median index rather than a dollar-weighted flow estimate.",
            styles["Body"],
        ),
        two_column_layout(
            scaled_image(root / figures["fig_07_apy_tvl_relationship"]["png"], 4.65 * inch, 3.35 * inch),
            event_checkpoint_table(points, styles),
            styles,
        ),
        Paragraph(fig_caption(figures["fig_07_apy_tvl_relationship"]), styles["Caption"]),
        proof_pair(
            "What this proves",
            "APY jumps and TVL response should be read on separate clocks rather than as one instantaneous mechanism.",
            "What it does not prove",
            "It is not causal evidence of deposits chasing yield; TVL can move for several accounting and price reasons.",
            styles,
        ),
    ]


def depeg_page(root: Path, summary: dict, figures: dict, styles) -> list:
    depeg = summary["depeg"]
    return [
        page_title("Result 6", "Peg stress changes what nominal yield means", styles),
        Paragraph(
            f"The selected case is {depeg['stablecoin_id']} on {depeg['event_date']}. The minimum observed price is {depeg['min_price_usd']:.4f} USD and the event window includes up to {depeg['max_pool_count']} exposed {plural(depeg['max_pool_count'], 'pool')}.",
            styles["Body"],
        ),
        scaled_image(root / figures["fig_08_depeg_event_study"]["png"], 6.7 * inch, 3.85 * inch),
        Paragraph(fig_caption(figures["fig_08_depeg_event_study"]), styles["Caption"]),
        proof_pair(
            "What this proves",
            "Peg stress changes the denominator behind nominal yield and should be shown next to APY.",
            "What it does not prove",
            "It is one context case study, not a general causal estimate for all depeg events or stablecoins.",
            styles,
        ),
    ]


def frontier_page(root: Path, summary: dict, figures: dict, styles) -> list:
    return [
        page_title(
            "Hero Visualization",
            "A joint threshold screen shows trade-offs without ranking pools",
            styles,
        ),
        Paragraph(
            f"{summary['joint_screen']['candidate_count']} of {summary['joint_screen']['pool_count']} pools ({summary['joint_screen']['candidate_share']:.1%}) sit above the pool-level sample medians for APY, persistence and TVL. The pool-level APY threshold is {summary['joint_screen']['median_apy']:.2f} percent; the {summary['market']['median_apy']:.2f} percent result reported for the distribution is instead the median across pool-day observations. This is a descriptive three-threshold screen, not a Pareto frontier, and it keeps the dimensions visible instead of compressing them into a hidden score.",
            styles["Body"],
        ),
        scaled_image(root / figures["fig_10_hero_yield_frontier"]["png"], 6.75 * inch, 4.25 * inch),
        Paragraph(fig_caption(figures["fig_10_hero_yield_frontier"]), styles["Caption"]),
        proof_pair(
            "What this proves",
            "Only a subset clears APY, persistence and capacity simultaneously, so the trade-off must remain visible.",
            "What it does not prove",
            "The joint screen is not a hidden score and does not identify a best pool.",
            styles,
        ),
    ]


def archetypes_page(root: Path, summary: dict, figures: dict, styles) -> list:
    return [
        page_title("Exploratory Structure", "Pool archetypes summarize patterns, not safety", styles),
        Paragraph(
            "The archetype analysis groups pools by standardized pool-level features such as median APY, persistence, TVL, reward share and volatility. These labels are descriptive summaries and should not be read as quality or risk ratings.",
            styles["Body"],
        ),
        two_column_layout(
            scaled_image(root / figures["fig_09_pool_archetypes"]["png"], 4.55 * inch, 3.35 * inch),
            label_count_table(summary["archetypes"], "Archetype", styles),
            styles,
        ),
        Paragraph(fig_caption(figures["fig_09_pool_archetypes"]), styles["Caption"]),
        proof_pair(
            "What this proves",
            "Pool-level features form recognizable profiles that help summarize the observed universe.",
            "What it does not prove",
            "Archetypes are exploratory clusters, not safety labels or quality ratings.",
            styles,
        ),
        Spacer(1, 0.1 * inch),
        callout(
            "Discussion use",
            "Use archetypes as a way to explain heterogeneity during the oral defense, then return to the primary evidence: duration, mechanism, churn, peg context and joint-screen trade-offs.",
            styles,
        ),
    ]


def robustness_page(summary: dict, styles) -> list:
    return [
        page_title("Robustness", "The main result is not a threshold artefact", styles),
        Paragraph(
            "Robustness checks ask whether the short-duration finding depends on the primary APY >= 10 percent threshold or on low-capacity observations. The answer is no for the central interpretation: high-yield episodes remain short across 5, 10 and 20 percent thresholds.",
            styles["Body"],
        ),
        robust_table(pd.DataFrame(summary["robustness"]).fillna("n/a"), styles),
        Spacer(1, 0.12 * inch),
        two_column_cards(
            [
                ("Threshold sensitivity", "Episode counts change as expected when the APY threshold moves, but median duration remains 2.0 days at 5, 10 and 20 percent."),
                ("TVL sensitivity", "Minimum-TVL filters reduce the number of included episodes, mainly by removing lower-capacity observations."),
            ],
            [
                ("Censoring", f"The primary censored share is {pct(summary['episodes']['censored_share'])}, so active final episodes do not dominate the result."),
                ("Interpretation", "The stable finding is regime shortness, not a universal law about all future DeFi yields."),
            ],
            styles,
        ),
    ]


def limitations_page(summary: dict, styles) -> list:
    return [
        page_title("Limitations And Ethics", "What the report does not claim", styles),
        Paragraph(
            "The report is intentionally conservative. It is a data visualization and analytics project, not a financial product, portfolio model or protocol risk rating.",
            styles["Body"],
        ),
        method_table(
            [
                ("APY", "Quoted annualized APY is not realized return. Realized return would require transaction-level deposits, withdrawals, compounding, fees, reward conversion and price paths."),
                ("TVL", "Observed TVL is not net capital flow. It can include deposits, withdrawals, price changes, accounting changes, migrations and source revisions."),
                ("Stablecoin risk", "Peg stress is observed through price deviations, but counterparty, legal, collateral, redemption and smart-contract risk are not fully measured."),
                ("Protocol risk", "Mechanism classification is descriptive. Documentation references do not imply security or quality."),
                ("Entity resolution", "Ticker collisions, bridged assets, renamed pools and migrated pools can remain ambiguous despite confidence scoring."),
                ("Visual ethics", "Figures avoid unsupported causality, sensational APY framing and red/green-only risk language."),
            ],
            styles,
        ),
        Spacer(1, 0.12 * inch),
        callout(
            "No recommendation boundary",
            "The report never identifies a best pool. Any pool-level label is descriptive evidence for the research question, not a recommendation.",
            styles,
        ),
    ]


def technical_appendix_page(summary: dict, styles) -> list:
    return [
        page_title("Technical Appendix", "Reproducibility and references", styles),
        Paragraph(
            "The final deliverables are generated by scripts, not manual spreadsheet edits. The same pipeline rebuilds raw collection outputs, processed tables, analytical tables, quality reports, figures, report, presentation previews and the release manifest.",
            styles["Body"],
        ),
        command_table(
            [
                ("Install", "uv sync --extra dev"),
                ("Sample run", "uv run python scripts/reproduce_all.py --mode sample"),
                ("Full run", "uv run python scripts/reproduce_all.py --mode full"),
                ("Report only", "uv run python scripts/build_report.py --mode full"),
                ("Preview PDF", "uv run python scripts/render_report_preview.py"),
            ],
            styles,
        ),
        Spacer(1, 0.12 * inch),
        deliverables_table(
            [
                ("Report PDF", "outputs/report/stablecoin_yield_report.pdf"),
                ("Report markdown", "outputs/report/stablecoin_yield_report.md"),
                ("Rendered PDF preview", "outputs/report/rendered_preview/"),
                ("Report contact sheet", "outputs/report/stablecoin_yield_report_contact_sheet.png"),
                ("Presentation deck", "outputs/presentation/stablecoin_yield_presentation.pptx"),
                ("Release manifest", "outputs/release_manifest.json"),
            ],
            styles,
        ),
        Spacer(1, 0.12 * inch),
        references_table(
            [
                ("DeFiLlama API docs", "https://api-docs.defillama.com/llms-free.txt"),
                ("DeFiLlama yields host", "https://yields.llama.fi"),
                ("DeFiLlama stablecoins host", "https://stablecoins.llama.fi"),
                ("CoinGecko Demo API", "https://docs.coingecko.com/demo/reference/coins-markets"),
                ("Project documentation", "docs/source_registry.md, docs/methodology.md, docs/data_dictionary.md"),
            ],
            styles,
        ),
        Spacer(1, 0.1 * inch),
        callout(
            "Release manifest",
            "The reproducibility manifest is written to `outputs/release_manifest.json` and records generated artifacts for the final full pipeline.",
            styles,
        ),
        Spacer(1, 0.12 * inch),
        insight_grid(
            [
                ("Final reading", "High APY is a regime, not a stable property."),
                ("Best visual answer", "The joint threshold screen communicates trade-offs without ranking pools."),
                ("Responsible boundary", "The work is educational analytics, not financial advice."),
            ],
            styles,
        ),
    ]


def page_title(kicker: str, title: str, styles) -> Table:
    table = Table(
        [[
            [
                Paragraph(escape(kicker.upper()), styles["DeckKicker"]),
                Paragraph(escape(title), styles["SectionTitle"]),
            ]
        ]],
        colWidths=[6.35 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return table


def metric_card_grid(cards: list[tuple[str, str]], styles) -> Table:
    rows = []
    for start in range(0, len(cards), 3):
        rows.append([metric_card(value, label, styles) for value, label in cards[start : start + 3]])
    table = Table(rows, colWidths=[2.05 * inch, 2.05 * inch, 2.05 * inch], rowHeights=[0.72 * inch] * len(rows))
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), panel()),
                ("BOX", (0, 0), (-1, -1), 0.6, rule()),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def metric_card(value: str, label: str, styles) -> Paragraph:
    return Paragraph(
        f'<font size="19"><b>{escape(value)}</b></font><br/><font size="7.5" color="#555555">{escape(label)}</font>',
        styles["CardMetric"],
    )


def insight_grid(cards: list[tuple[str, str]], styles) -> Table:
    table = Table(
        [[insight_card(title, body, styles) for title, body in cards]],
        colWidths=[2.02 * inch, 2.02 * inch, 2.02 * inch],
        rowHeights=[1.28 * inch],
    )
    table.setStyle(card_table_style())
    return table


def insight_card(title: str, body: str, styles) -> Paragraph:
    return Paragraph(f"<b>{escape(title)}</b><br/>{escape(body)}", styles["CardText"])


def two_column_cards(
    left: list[tuple[str, str]], right: list[tuple[str, str]], styles
) -> Table:
    table = Table(
        [[card_stack(left, styles), card_stack(right, styles)]],
        colWidths=[3.03 * inch, 3.03 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), panel()),
                ("BOX", (0, 0), (-1, -1), 0.6, rule()),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, rule()),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def card_stack(items: list[tuple[str, str]], styles) -> list[Paragraph | Spacer]:
    flowables: list[Paragraph | Spacer] = []
    for index, (title, body) in enumerate(items):
        flowables.append(Paragraph(f"<b>{escape(title)}</b><br/>{escape(body)}", styles["CardText"]))
        if index < len(items) - 1:
            flowables.append(Spacer(1, 0.07 * inch))
    return flowables


def callout(title: str, body: str, styles) -> Table:
    table = Table(
        [[Paragraph(f"<b>{escape(title)}</b><br/>{escape(body)}", styles["CardText"])]],
        colWidths=[6.35 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F7FA")),
                ("BOX", (0, 0), (-1, -1), 0.7, rule()),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def proof_pair(
    left_title: str,
    left_body: str,
    right_title: str,
    right_body: str,
    styles,
) -> Table:
    return two_column_cards(
        [(left_title, left_body)],
        [(right_title, right_body)],
        styles,
    )


def research_question_table(rows: list[tuple[str, str, str]], styles) -> Table:
    data = [["RQ", "Question", "Evidence in this report"]]
    for rq, question, evidence in rows:
        data.append(
            [
                Paragraph(f"<b>{escape(rq)}</b>", styles["CardMetric"]),
                Paragraph(escape(question), styles["CardText"]),
                Paragraph(escape(evidence), styles["CardText"]),
            ]
        )
    table = Table(data, colWidths=[0.55 * inch, 2.5 * inch, 3.05 * inch])
    table.setStyle(table_style(font_size=7.4))
    return table


def source_table(rows: list[dict], styles) -> Table:
    data = [["Source", "Role", "Auth", "Evidence"]]
    for row in rows:
        data.append(
            [
                Paragraph(f"<b>{escape(row['source'])}</b><br/><font size='6'>{escape(row['endpoint'])}</font>", styles["CardTextSmall"]),
                Paragraph(escape(row["role"]), styles["CardTextSmall"]),
                Paragraph(escape(row["auth"]), styles["CardTextSmall"]),
                Paragraph(escape(row["evidence"]), styles["CardTextSmall"]),
            ]
        )
    table = Table(data, colWidths=[1.55 * inch, 2.0 * inch, 0.75 * inch, 1.95 * inch])
    table.setStyle(table_style(font_size=6.8))
    return table


def evidence_table(rows: list[tuple[str, str, str]], styles) -> Table:
    data = [["Check", "Observed evidence", "Interpretation"]]
    for check, evidence, interpretation in rows:
        data.append(
            [
                Paragraph(escape(check), styles["CardTextSmall"]),
                Paragraph(f"<b>{escape(evidence)}</b>", styles["CardTextSmall"]),
                Paragraph(escape(interpretation), styles["CardTextSmall"]),
            ]
        )
    table = Table(data, colWidths=[1.55 * inch, 1.3 * inch, 3.35 * inch])
    table.setStyle(table_style(font_size=7.0))
    return table


def process_flow_table(rows: list[tuple[str, str, str]], styles) -> Table:
    data = []
    for step, title, body in rows:
        data.append(
            [
                Paragraph(f"<b>{escape(step)}</b>", styles["CardMetric"]),
                Paragraph(f"<b>{escape(title)}</b>", styles["CardText"]),
                Paragraph(escape(body), styles["CardText"]),
            ]
        )
    table = Table(data, colWidths=[0.45 * inch, 1.1 * inch, 4.55 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, rule()),
                ("LINEBELOW", (0, 0), (-1, -2), 0.35, rule()),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def data_asset_table(rows: list[dict], styles) -> Table:
    data = [["Artifact", "Rows", "Role"]]
    for row in rows:
        data.append(
            [
                Paragraph(escape(row["asset"]), styles["CardTextSmall"]),
                Paragraph(f"{row['rows']:,}", styles["CardTextSmall"]),
                Paragraph(escape(row["role"]), styles["CardTextSmall"]),
            ]
        )
    table = Table(data, colWidths=[2.15 * inch, 0.85 * inch, 3.05 * inch])
    table.setStyle(table_style(font_size=6.9))
    return table


def schema_table(rows: list[tuple[str, str]], styles) -> Table:
    data = [["Table", "Main contents"]]
    for table_name, contents in rows:
        data.append(
            [
                Paragraph(f"<b>{escape(table_name)}</b>", styles["CardText"]),
                Paragraph(escape(contents), styles["CardText"]),
            ]
        )
    table = Table(data, colWidths=[1.55 * inch, 4.7 * inch])
    table.setStyle(table_style(font_size=7.2))
    return table


def quality_summary_cards(summary: dict, styles) -> Table:
    quality = summary["quality"]
    market = summary["market"]
    return metric_card_grid(
        [
            (str(quality["checks"]), "quality checks"),
            (str(quality["critical_failures"]), "critical failures"),
            (str(quality["warning_checks"]), "warning checks"),
            (pct(market["apy_coverage"]), "APY coverage"),
            (pct(market["base_apy_coverage"]), "base APY coverage"),
            (pct(market["reward_apy_coverage"]), "reward APY coverage"),
        ],
        styles,
    )


def quality_table(rows: list[dict], styles) -> Table:
    data = [["Check", "Severity", "Status", "Failed"]]
    for row in rows:
        data.append(
            [
                Paragraph(escape(row["check_id"]), styles["CardTextSmall"]),
                Paragraph(escape(row["severity"]), styles["CardTextSmall"]),
                Paragraph(escape(row["status"]), styles["CardTextSmall"]),
                Paragraph(f"{row['failed_rows']:,}", styles["CardTextSmall"]),
            ]
        )
    table = Table(data, colWidths=[3.0 * inch, 1.0 * inch, 1.0 * inch, 0.85 * inch])
    table.setStyle(table_style(font_size=6.7))
    return table


def method_table(rows: list[tuple[str, str]], styles) -> Table:
    data = [["Concept", "Operational definition"]]
    for concept, definition in rows:
        data.append(
            [
                Paragraph(f"<b>{escape(concept)}</b>", styles["CardText"]),
                Paragraph(escape(definition), styles["CardText"]),
            ]
        )
    table = Table(data, colWidths=[1.55 * inch, 4.75 * inch])
    table.setStyle(table_style(font_size=7.2))
    return table


def two_column_layout(left, right, styles) -> Table:
    table = Table([[left, right]], colWidths=[4.75 * inch, 1.55 * inch])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def small_table(rows: list[dict], fields: list[str], labels: list[str], styles) -> Table:
    data = [labels]
    for row in rows[:7]:
        data.append([Paragraph(format_cell(row.get(field), field), styles["CardTextSmall"]) for field in fields])
    table = Table(data, colWidths=[0.78 * inch, 0.36 * inch, 0.48 * inch])
    table.setStyle(table_style(font_size=5.9))
    return table


def survival_checkpoint_table(points: dict, styles) -> Table:
    data = [["Day", "Survival", "At risk"]]
    for day in ["1", "2", "7", "30"]:
        row = points.get(day, {})
        data.append(
            [
                Paragraph(day, styles["CardTextSmall"]),
                Paragraph(pct(row.get("survival")), styles["CardTextSmall"]),
                Paragraph(f"{row.get('at_risk', 'n/a')}", styles["CardTextSmall"]),
            ]
        )
    table = Table(data, colWidths=[0.4 * inch, 0.55 * inch, 0.55 * inch])
    table.setStyle(table_style(font_size=6.3))
    return table


def churn_table(churn: dict, styles) -> Table:
    data = [["Horizon", "Mean churn"]]
    for day in ["1", "7", "30"]:
        data.append([Paragraph(f"{day}d", styles["CardTextSmall"]), Paragraph(pct(churn.get(day)), styles["CardTextSmall"])])
    table = Table(data, colWidths=[0.65 * inch, 0.85 * inch])
    table.setStyle(table_style(font_size=6.5))
    return table


def event_checkpoint_table(points: dict, styles) -> Table:
    data = [["Day", "APY", "TVL idx"]]
    for day in ["-7", "0", "7", "30"]:
        row = points.get(day, {})
        data.append(
            [
                Paragraph(day, styles["CardTextSmall"]),
                Paragraph(f"{row.get('median_apy', 'n/a')}", styles["CardTextSmall"]),
                Paragraph(f"{row.get('median_tvl_index', 'n/a')}", styles["CardTextSmall"]),
            ]
        )
    table = Table(data, colWidths=[0.38 * inch, 0.55 * inch, 0.58 * inch])
    table.setStyle(table_style(font_size=6.1))
    return table


def label_count_table(rows: list[dict], label: str, styles) -> Table:
    data = [[label, "Pools"]]
    for row in rows:
        data.append([Paragraph(escape(row["label"]), styles["CardTextSmall"]), Paragraph(str(row["count"]), styles["CardTextSmall"])])
    table = Table(data, colWidths=[0.95 * inch, 0.55 * inch])
    table.setStyle(table_style(font_size=6.3))
    return table


def robust_table(frame: pd.DataFrame, styles) -> Table:
    columns = ["check", "episode_count", "median_duration_days", "censored_share"]
    labels = ["Check", "Episodes", "Median days", "Censored"]
    rows = [labels]
    for row in frame[columns].itertuples(index=False):
        values = []
        for column, value in zip(columns, row, strict=True):
            if column == "censored_share" and value != "n/a":
                values.append(pct(value))
            elif column == "episode_count" and value != "n/a":
                values.append(f"{int(value):,}")
            else:
                values.append(str(value))
        rows.append([Paragraph(escape(value), styles["CardTextSmall"]) for value in values])
    table = Table(rows, colWidths=[2.0 * inch, 1.1 * inch, 1.3 * inch, 1.1 * inch])
    table.setStyle(table_style(font_size=7.0))
    return table


def command_table(rows: list[tuple[str, str]], styles) -> Table:
    data = [["Task", "Command"]]
    for task, command in rows:
        data.append(
            [
                Paragraph(escape(task), styles["CardText"]),
                Paragraph(f"<font face='Courier'>{escape(command)}</font>", styles["CardTextSmall"]),
            ]
        )
    table = Table(data, colWidths=[1.25 * inch, 5.0 * inch])
    table.setStyle(table_style(font_size=7.2))
    return table


def references_table(rows: list[tuple[str, str]], styles) -> Table:
    data = [["Reference", "Location"]]
    for label, location in rows:
        data.append([Paragraph(escape(label), styles["CardTextSmall"]), Paragraph(escape(location), styles["CardTextSmall"])])
    table = Table(data, colWidths=[1.65 * inch, 4.6 * inch])
    table.setStyle(table_style(font_size=6.8))
    return table


def deliverables_table(rows: list[tuple[str, str]], styles) -> Table:
    data = [["Deliverable", "Path"]]
    for label, path in rows:
        data.append(
            [
                Paragraph(escape(label), styles["CardTextSmall"]),
                Paragraph(f"<font face='Courier'>{escape(path)}</font>", styles["CardTextSmall"]),
            ]
        )
    table = Table(data, colWidths=[1.55 * inch, 4.7 * inch])
    table.setStyle(table_style(font_size=6.8))
    return table


def card_table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.8, rule()),
            ("INNERGRID", (0, 0), (-1, -1), 0.8, rule()),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]
    )


def table_style(font_size: float = 8) -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), navy()),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), font_size),
            ("GRID", (0, 0), (-1, -1), 0.25, rule()),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FB")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


def scaled_image(path: Path, max_width: float, max_height: float):
    if not path.exists():
        return Paragraph(f"Missing image: {escape(path.as_posix())}", getSampleStyleSheet()["BodyText"])
    width, height = ImageReader(str(path)).getSize()
    scale = min(max_width / width, max_height / height)
    return Image(str(path), width=width * scale, height=height * scale)


def fig_caption(figure: dict) -> str:
    return f"{figure['question']} {figure['message']} Sample: {figure['sample_size']}."


def format_cell(value, field: str) -> str:
    if value is None:
        return "n/a"
    if field == "pool_type":
        return pool_type_label(str(value))
    if field.endswith("_apy"):
        return f"{float(value):.1f}%"
    if field.endswith("_usd"):
        return fmt_usd(float(value))
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def pool_type_label(value: str) -> str:
    labels = {
        "single_stable_lending": "Lending",
        "incentive_driven": "Incentives",
        "stable_stable_lp": "Stable LP",
        "yield_bearing_stablecoin": "Yield-bearing",
        "vault_aggregator": "Vault",
    }
    return labels.get(value, value.replace("_", " "))


def draw_footer(canvas, doc) -> None:
    canvas.saveState()
    page_width, _ = A4
    canvas.setStrokeColor(rule())
    canvas.setLineWidth(0.4)
    canvas.line(doc.leftMargin, 0.48 * inch, page_width - doc.rightMargin, 0.48 * inch)
    canvas.setFillColor(muted())
    canvas.setFont("Helvetica", 7)
    canvas.drawString(doc.leftMargin, 0.32 * inch, "Stablecoin Yield - educational analysis, not financial advice")
    canvas.drawRightString(page_width - doc.rightMargin, 0.32 * inch, str(doc.page))
    canvas.restoreState()


def navy():
    return colors.HexColor("#17324D")


def ink():
    return colors.HexColor("#111827")


def muted():
    return colors.HexColor("#5B6673")


def panel():
    return colors.HexColor("#EEF2F6")


def rule():
    return colors.HexColor("#CBD5E1")


def fmt_usd(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.0f}"


def plural(count: int, singular: str) -> str:
    return singular if count == 1 else f"{singular}s"


def pct(value) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.1%}"


def json_safe(value):
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if value is None or isinstance(value, str | bool | int):
        return value
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
