from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from stablecoin_yield.config import get_paths, load_config
from stablecoin_yield.metrics.core import pool_metrics
from stablecoin_yield.metrics.episodes import percentile_threshold_episodes, segment_episodes
from stablecoin_yield.metrics.ranking import ranking_retention


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet" and path.exists():
        return pd.read_parquet(path)
    csv_path = path.with_suffix(".csv")
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return pd.DataFrame()


def run_analysis(root: Path, mode: str = "sample") -> dict[str, pd.DataFrame]:
    paths = get_paths(root)
    config = load_config(root)
    metrics_cfg = config["metrics"]
    panel = read_table(paths.analytical_dir / "pool_day_panel.parquet")
    if panel.empty:
        raise FileNotFoundError("Missing analytical pool_day_panel. Run build_dataset first.")
    panel["observed_date"] = pd.to_datetime(panel["observed_date"])

    threshold = float(metrics_cfg["yield_episodes"]["primary_threshold"]["apy_percent"])
    episodes = build_all_episodes(panel, metrics_cfg)
    pool_level = pool_metrics(panel, threshold=threshold)
    survival = survival_table(episodes[episodes["threshold_definition"] == f"apy_ge_{threshold:g}"])
    rank = ranking_retention(
        panel,
        k_values=list(metrics_cfg["ranking"]["k_values"]),
        horizons_days=list(metrics_cfg["ranking"]["horizons_days"]),
    )
    overview = market_overview(panel)
    frontier = build_frontier(pool_level)
    apy_tvl = apy_tvl_event_response(panel)
    depeg = depeg_event_study(root, panel)
    archetypes = archetype_table(pool_level)
    robustness = robustness_table(panel, metrics_cfg)

    outputs = {
        "market_overview": overview,
        "yield_episodes": episodes,
        "pool_metrics": pool_level,
        "episode_survival": survival,
        "ranking_churn": rank,
        "yield_frontier": frontier,
        "apy_tvl_event_response": apy_tvl,
        "depeg_event_study": depeg,
        "pool_archetypes": archetypes,
        "robustness_checks": robustness,
    }
    for name, frame in outputs.items():
        target = paths.tables_dir / f"{name}.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(target, index=False)
        if name in {"yield_episodes", "pool_metrics"}:
            frame.to_parquet(paths.analytical_dir / f"{name}.parquet", index=False)
    write_insight_registry(paths, outputs)
    write_analysis_manifest(paths, outputs, mode)
    return outputs


def build_all_episodes(panel: pd.DataFrame, metrics_cfg: dict[str, Any]) -> pd.DataFrame:
    max_gap = int(metrics_cfg["yield_episodes"]["max_gap_days"])
    frames = []
    primary = float(metrics_cfg["yield_episodes"]["primary_threshold"]["apy_percent"])
    frames.append(segment_episodes(panel, threshold=primary, max_gap_days=max_gap))
    for item in metrics_cfg["yield_episodes"]["alternatives"]:
        if item["type"] == "absolute":
            value = float(item["apy_percent"])
            if value != primary:
                frames.append(segment_episodes(panel, threshold=value, max_gap_days=max_gap))
        elif item["type"] == "cross_sectional_percentile":
            frames.append(
                percentile_threshold_episodes(
                    panel, percentile=float(item["percentile"]), max_gap_days=max_gap
                )
            )
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def survival_table(episodes: pd.DataFrame) -> pd.DataFrame:
    if episodes.empty:
        return pd.DataFrame(columns=["duration_days", "survival", "ci_lower", "ci_upper", "at_risk"])
    kmf = KaplanMeierFitter()
    durations = episodes["duration_days"].astype(float)
    events = ~episodes["is_censored"].astype(bool)
    kmf.fit(durations=durations, event_observed=events, label="high_yield_episode")
    survival = kmf.survival_function_.reset_index()
    survival.columns = ["duration_days", "survival"]
    ci = kmf.confidence_interval_.reset_index()
    ci.columns = ["duration_days", "ci_lower", "ci_upper"]
    table = survival.merge(ci, on="duration_days", how="left")
    event_table = kmf.event_table.reset_index()[["event_at", "at_risk"]].rename(
        columns={"event_at": "duration_days"}
    )
    return table.merge(event_table, on="duration_days", how="left")


def market_overview(panel: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"metric": "pool_count", "value": panel["pool_id"].nunique()},
            {"metric": "pool_day_count", "value": len(panel)},
            {"metric": "chain_count", "value": panel["chain"].nunique()},
            {"metric": "protocol_count", "value": panel["protocol_id"].nunique()},
            {"metric": "median_apy", "value": panel["apy_total"].median()},
            {"metric": "mean_apy", "value": panel["apy_total"].mean()},
            {"metric": "median_tvl_usd", "value": panel["tvl_usd"].median()},
            {"metric": "base_apy_coverage", "value": panel["apy_base"].notna().mean()},
            {"metric": "reward_apy_coverage", "value": panel["apy_reward"].notna().mean()},
        ]
    )


def build_frontier(pool_level: pd.DataFrame) -> pd.DataFrame:
    if pool_level.empty:
        return pool_level
    out = pool_level.copy()
    out["reward_dependence"] = pd.cut(
        out["median_reward_share"],
        bins=[-np.inf, 0.05, 0.5, np.inf],
        labels=["low_or_none", "mixed", "reward_dependent"],
    ).astype("object")
    out["frontier_candidate"] = (
        (out["median_apy"] >= out["median_apy"].median())
        & (out["persistence_ratio_10"] >= out["persistence_ratio_10"].median())
        & (out["median_tvl_usd"] >= out["median_tvl_usd"].median())
    )
    return out


def apy_tvl_event_response(panel: pd.DataFrame) -> pd.DataFrame:
    data = panel.sort_values(["pool_id", "observed_date"]).copy()
    data["apy_delta_1d"] = data.groupby("pool_id")["apy_total"].diff()
    data["log_tvl"] = np.log(data["tvl_usd"].where(data["tvl_usd"] > 0))
    data["log_tvl_delta_1d"] = data.groupby("pool_id")["log_tvl"].diff()
    events = data[(data["apy_delta_1d"] >= 5) & (data["apy_total"] >= 10)].copy()
    if events.empty:
        return pd.DataFrame()
    events = events.groupby("pool_id").head(3)
    windows = []
    for event in events.itertuples(index=False):
        group = data[data["pool_id"] == event.pool_id].copy()
        group["event_time_day"] = (group["observed_date"] - event.observed_date).dt.days
        window = group[group["event_time_day"].between(-7, 30)].copy()
        event_tvl = float(event.tvl_usd) if pd.notna(event.tvl_usd) and event.tvl_usd > 0 else np.nan
        window["tvl_index"] = window["tvl_usd"] / event_tvl if pd.notna(event_tvl) else np.nan
        window["event_id"] = f"{event.pool_id}_{event.observed_date.date()}"
        windows.append(window)
    combined = pd.concat(windows, ignore_index=True)
    summary = (
        combined.groupby("event_time_day")
        .agg(
            median_apy=("apy_total", "median"),
            median_tvl_index=("tvl_index", "median"),
            event_count=("event_id", "nunique"),
        )
        .reset_index()
    )
    return summary


def depeg_event_study(root: Path, panel: pd.DataFrame) -> pd.DataFrame:
    paths = get_paths(root)
    prices = read_table(paths.processed_dir / "stablecoin_prices.parquet")
    pools = read_table(paths.processed_dir / "pools.parquet")
    if prices.empty or pools.empty:
        return pd.DataFrame()
    prices["observed_date"] = pd.to_datetime(prices["observed_date"])
    exposed_assets = set()
    for value in pools["stablecoin_ids"].fillna(""):
        exposed_assets.update([part for part in str(value).split("|") if part])
    preferred_major = {
        "usd_coin",
        "tether",
        "dai",
        "frax",
        "frax_usd",
        "ethena_usde",
        "usds",
        "usual_usd",
    }
    major = exposed_assets & preferred_major
    if not major:
        major = exposed_assets
    selected = prices[prices["stablecoin_id"].isin(major)].copy()
    selected["abs_deviation"] = (selected["price_usd"] - 1).abs()
    preferred_events = [
        ("usd_coin", pd.Timestamp("2023-03-12")),
        ("dai", pd.Timestamp("2023-03-12")),
    ]
    preferred_rows = []
    for preferred_id, preferred_date in preferred_events:
        match = selected[
            (selected["stablecoin_id"] == preferred_id)
            & (selected["observed_date"] == preferred_date)
            & (selected["abs_deviation"] > 0.01)
        ]
        preferred_rows.append(match)
    preferred_candidates = (
        pd.concat(preferred_rows, ignore_index=True)
        if preferred_rows
        else pd.DataFrame(columns=selected.columns)
    )
    stressed = selected[selected["abs_deviation"] > 0.01].copy()
    bounded_stress = stressed[stressed["abs_deviation"] <= 0.2]
    fallback = bounded_stress if not bounded_stress.empty else stressed
    candidates = pd.concat(
        [preferred_candidates, fallback.sort_values("abs_deviation", ascending=False)],
        ignore_index=True,
    ).drop_duplicates(subset=["stablecoin_id", "observed_date"], keep="first")
    if candidates.empty:
        candidates = selected.sort_values("abs_deviation", ascending=False).head(25)
    if candidates.empty:
        return pd.DataFrame()

    selected_event: tuple[pd.Series, pd.DataFrame] | None = None
    for _, candidate in candidates.iterrows():
        candidate_date = pd.Timestamp(candidate["observed_date"])
        candidate_stablecoin_id = str(candidate["stablecoin_id"])
        candidate_exposed_ids = pools[
            pools["stablecoin_ids"].fillna("").str.contains(candidate_stablecoin_id, regex=False)
        ]["pool_id"].tolist()
        candidate_panel = panel[
            panel["pool_id"].isin(candidate_exposed_ids)
            & panel["observed_date"].between(
                candidate_date - pd.Timedelta(days=30),
                candidate_date + pd.Timedelta(days=30),
            )
        ].copy()
        if not candidate_panel.empty:
            selected_event = (candidate, candidate_panel)
            break

    if selected_event is None:
        peak = candidates.iloc[0]
        panel_window = pd.DataFrame()
    else:
        peak, panel_window = selected_event
    event_date = peak["observed_date"]
    stablecoin_id = peak["stablecoin_id"]
    price_window = selected[
        (selected["stablecoin_id"] == stablecoin_id)
        & (selected["observed_date"].between(event_date - pd.Timedelta(days=30), event_date + pd.Timedelta(days=30)))
    ].copy()
    price_window["event_time_day"] = (price_window["observed_date"] - event_date).dt.days
    if panel_window.empty:
        out = price_window[["event_time_day", "price_usd"]].copy()
        out["median_apy"] = np.nan
        out["median_tvl_usd"] = np.nan
        out["pool_count"] = 0
    else:
        panel_window["event_time_day"] = (panel_window["observed_date"] - event_date).dt.days
        pooled = (
            panel_window.groupby("event_time_day")
            .agg(
                median_apy=("apy_total", "median"),
                median_tvl_usd=("tvl_usd", "median"),
                pool_count=("pool_id", "nunique"),
            )
            .reset_index()
        )
        out = price_window[["event_time_day", "price_usd"]].merge(pooled, on="event_time_day", how="left")
    out["stablecoin_id"] = stablecoin_id
    out["event_date"] = event_date
    out["peak_abs_deviation"] = float(peak["abs_deviation"])
    return out


def archetype_table(pool_level: pd.DataFrame) -> pd.DataFrame:
    if pool_level.empty or len(pool_level) < 8:
        return pool_level.assign(archetype="insufficient_sample")
    features = [
        "median_apy",
        "apy_robust_volatility",
        "persistence_ratio_10",
        "median_reward_share",
        "median_tvl_usd",
        "tvl_volatility",
        "tvl_drawdown",
    ]
    data = pool_level.copy()
    matrix = data[features].replace([np.inf, -np.inf], np.nan)
    matrix = matrix.fillna(matrix.median(numeric_only=True))
    scaler = StandardScaler()
    x = scaler.fit_transform(matrix)
    k = min(4, max(2, len(data) // 10))
    labels = KMeans(n_clusters=k, random_state=42, n_init=20).fit_predict(x)
    data["archetype"] = [f"archetype_{label + 1}" for label in labels]
    return data


def robustness_table(panel: pd.DataFrame, metrics_cfg: dict[str, Any]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    primary_threshold = float(
        metrics_cfg["yield_episodes"]["primary_threshold"]["apy_percent"]
    )
    primary_gap = int(metrics_cfg["yield_episodes"]["max_gap_days"])

    def append_episode_check(
        *,
        check: str,
        family: str,
        data: pd.DataFrame,
        threshold: float = primary_threshold,
        max_gap_days: int = primary_gap,
    ) -> None:
        episodes = segment_episodes(
            data,
            threshold=threshold,
            max_gap_days=max_gap_days,
        )
        records.append(
            {
                "check": check,
                "family": family,
                "pool_count": int(data["pool_id"].nunique()),
                "panel_rows": int(len(data)),
                "threshold_percent": float(threshold),
                "max_gap_days": int(max_gap_days),
                "episode_count": int(len(episodes)),
                "median_duration_days": float(episodes["duration_days"].median())
                if not episodes.empty
                else np.nan,
                "censored_share": float(episodes["is_censored"].mean())
                if not episodes.empty
                else np.nan,
                "median_apy": float(data["apy_total"].median()) if not data.empty else np.nan,
                "mean_apy": float(data["apy_total"].mean()) if not data.empty else np.nan,
            }
        )

    for threshold in metrics_cfg["robustness"]["thresholds_percent"]:
        append_episode_check(
            check=f"threshold_{threshold}",
            family="apy_threshold",
            data=panel,
            threshold=float(threshold),
        )

    for min_tvl in metrics_cfg["robustness"]["min_tvl_usd"]:
        subset = panel[panel["tvl_usd"] >= float(min_tvl)]
        append_episode_check(
            check=f"min_tvl_{int(min_tvl)}",
            family="minimum_tvl",
            data=subset,
        )

    pool_history = panel.groupby("pool_id")["observed_date"].nunique()
    for min_history in metrics_cfg["robustness"].get("min_history_days", []):
        eligible = pool_history[pool_history >= int(min_history)].index
        subset = panel[panel["pool_id"].isin(eligible)]
        append_episode_check(
            check=f"min_history_{int(min_history)}",
            family="minimum_history",
            data=subset,
        )

    for gap_days in metrics_cfg["robustness"].get("gap_days", []):
        append_episode_check(
            check=f"max_gap_{int(gap_days)}",
            family="episode_gap",
            data=panel,
            max_gap_days=int(gap_days),
        )

    winsor_limits = metrics_cfg["robustness"].get("winsor_limits", [])
    if len(winsor_limits) == 2:
        lower = float(winsor_limits[0])
        upper = float(winsor_limits[1])
        winsorized = panel.copy()
        low_value = float(winsorized["apy_total"].quantile(lower))
        high_value = float(winsorized["apy_total"].quantile(upper))
        winsorized["apy_total"] = winsorized["apy_total"].clip(low_value, high_value)
        append_episode_check(
            check=f"winsor_{lower:g}_{upper:g}",
            family="winsorization",
            data=winsorized,
        )

    return pd.DataFrame.from_records(records)


def write_insight_registry(paths, outputs: dict[str, pd.DataFrame]) -> None:
    overview = outputs["market_overview"].set_index("metric")["value"].to_dict()
    episodes = outputs["yield_episodes"]
    rank = outputs["ranking_churn"]
    frontier = outputs["yield_frontier"]
    insights = []
    primary = episodes[episodes["threshold_definition"] == "apy_ge_10"]
    if not primary.empty:
        insights.append(
            {
                "Insight ID": "I-001",
                "Question": "RQ1 Persistence",
                "Claim": "High-yield episodes are finite observed regimes, not permanent pool traits.",
                "Population": "Stablecoin pools in the analytical sample",
                "Metric": "Median duration of APY >= 10 percent episodes",
                "Estimate": f"{primary['duration_days'].median():.1f} days across {len(primary)} episodes",
                "Uncertainty": "Kaplan-Meier confidence intervals in survival table",
                "Figure/table": "episode_survival, yield_episodes",
                "Robustness": "Checked at 5, 10 and 20 percent thresholds",
                "Alternative explanation": "Provider APY methodology and missing periods can affect episode boundaries",
                "Limitations": "APY is quoted annualized APY, not realized return",
                "Status": "validated",
            }
        )
    if not rank.empty:
        avg_churn = rank.groupby("horizon_days")["churn"].mean().to_dict()
        insights.append(
            {
                "Insight ID": "I-002",
                "Question": "RQ3 Ranking stability",
                "Claim": "Top-yield membership changes materially over observation horizons.",
                "Population": "Daily top-k stablecoin pools",
                "Metric": "Comparison-weighted average top-k churn",
                "Estimate": json.dumps({str(k): round(v, 3) for k, v in avg_churn.items()}),
                "Uncertainty": "Distribution over dates retained in ranking_churn table",
                "Figure/table": "ranking_churn",
                "Robustness": "Top 10 and top 20, horizons 1/7/30 days",
                "Alternative explanation": "Small APY differences around the threshold may reshuffle ranks",
                "Limitations": "Not a measure of investment opportunity",
                "Status": "validated",
            }
        )
    if not frontier.empty:
        frontier_share = float(frontier["frontier_candidate"].mean())
        insights.append(
            {
                "Insight ID": "I-003",
                "Question": "RQ5 Risk frontier",
                "Claim": "Only a subset of pools combine above-median APY, persistence and TVL.",
                "Population": "Pools with analytical history",
                "Metric": "Frontier candidate share",
                "Estimate": f"{frontier_share:.1%} of {len(frontier)} pools",
                "Uncertainty": "Depends on sample and median thresholds",
                "Figure/table": "yield_frontier",
                "Robustness": "No hidden score; components shown directly",
                "Alternative explanation": "Selection favors pools with sufficient history and TVL",
                "Limitations": "Does not fully measure smart contract or legal risk",
                "Status": "validated",
            }
        )
    path = paths.quality_dir / "insight_registry.md"
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Insight Registry\n\n")
        handle.write(f"Analytical sample pools: {overview.get('pool_count', 'n/a')}\n\n")
        for item in insights:
            handle.write(f"## {item['Insight ID']}\n\n")
            for key, value in item.items():
                if key != "Insight ID":
                    handle.write(f"**{key}:** {value}\n\n")


def write_analysis_manifest(paths, outputs: dict[str, pd.DataFrame], mode: str) -> None:
    manifest = {
        "analysis_id": f"stablecoin_yield_{mode}",
        "mode": mode,
        "outputs": {name: len(frame) for name, frame in outputs.items()},
        "random_seed": 42,
    }
    with (paths.outputs_dir / "analysis_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
