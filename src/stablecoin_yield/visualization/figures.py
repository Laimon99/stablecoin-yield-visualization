from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from stablecoin_yield.analysis.pipeline import read_table
from stablecoin_yield.config import get_paths, load_config

FigureFunction = Callable[[Path, dict], dict[str, str]]


def render_all_figures(root: Path, mode: str = "sample") -> pd.DataFrame:
    paths = get_paths(root)
    config = load_config(root)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)
    registry = []
    for fig_id, fn in FIGURES:
        metadata = fn(root, config)
        metadata["id"] = fig_id
        metadata["mode"] = mode
        registry.append(metadata)
    frame = pd.DataFrame(registry)
    frame.to_csv(paths.figures_dir / "figure_registry.csv", index=False)
    return frame


def style(config: dict) -> dict:
    return config["visualization"]["style"]


def load_common(root: Path):
    paths = get_paths(root)
    panel = read_table(paths.analytical_dir / "pool_day_panel.parquet")
    pool_metrics = read_table(paths.analytical_dir / "pool_metrics.parquet")
    episodes = read_table(paths.analytical_dir / "yield_episodes.parquet")
    for frame in [panel, episodes]:
        if "observed_date" in frame:
            frame["observed_date"] = pd.to_datetime(frame["observed_date"])
        if "start_date" in frame:
            frame["start_date"] = pd.to_datetime(frame["start_date"])
        if "end_date" in frame:
            frame["end_date"] = pd.to_datetime(frame["end_date"])
    return paths, panel, pool_metrics, episodes


def apply_theme(ax, cfg: dict) -> None:
    ax.set_facecolor(cfg["background"])
    ax.figure.set_facecolor(cfg["background"])
    ax.grid(True, color=cfg["grid"], linewidth=0.6, alpha=0.6)
    ax.tick_params(colors=cfg["text"], labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(cfg["grid"])


def pretty_pool_type(value: str) -> str:
    labels = {
        "single_stable_lending": "Single-stable lending",
        "incentive_driven": "Incentive-driven",
        "stable_stable_lp": "Stable-stable LP",
        "yield_bearing_stablecoin": "Yield-bearing stablecoin",
        "vault_aggregator": "Vault aggregator",
    }
    return labels.get(str(value), str(value).replace("_", " ").title())


def save(fig, paths, fig_id: str, title: str, question: str, message: str, sample_size: str):
    for fmt in ["png", "svg", "pdf"]:
        output = paths.figures_dir / f"{fig_id}.{fmt}"
        fig.savefig(output, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return {
        "title": title,
        "question": question,
        "message": message,
        "sample_size": sample_size,
        # The public release ships the web-friendly PNG. Vector/PDF exports are
        # still produced locally for report and presentation authoring.
        "files": (paths.figures_dir / f"{fig_id}.png").relative_to(paths.root).as_posix(),
    }


def add_footer(fig, source_note: str) -> None:
    fig.text(0.01, 0.01, source_note, ha="left", va="bottom", fontsize=8, color="#5b6673")


def fig_01_universe(root: Path, config: dict) -> dict[str, str]:
    paths, panel, pools, _ = load_common(root)
    cfg = style(config)
    fig, axes = plt.subplots(1, 2, figsize=(13.33, 7.5))
    counts = pools["pool_type"].value_counts().sort_values()
    colors = [cfg["palette"].get(idx, cfg["neutral"]) for idx in counts.index]
    axes[0].barh([pretty_pool_type(value) for value in counts.index], counts.values, color=colors)
    axes[0].set_title("Stablecoin yield sample spans several pool types", loc="left", fontsize=14)
    axes[0].set_xlabel("Pools")
    apply_theme(axes[0], cfg)
    chain_tvl = panel.groupby("chain")["tvl_usd"].median().sort_values(ascending=False).head(10)
    axes[1].bar(chain_tvl.index, chain_tvl.values / 1e6, color=cfg["focus"])
    axes[1].set_title("Median TVL is concentrated by chain", loc="left", fontsize=14)
    axes[1].set_ylabel("Median TVL, USD millions")
    axes[1].tick_params(axis="x", rotation=35)
    apply_theme(axes[1], cfg)
    fig.suptitle("Yield universe: APY comparisons need category and capacity context", fontsize=18, x=0.02, ha="left")
    add_footer(fig, cfg["source_note"])
    return save(
        fig,
        paths,
        "fig_01_yield_universe",
        "Yield universe: APY comparisons need category and capacity context",
        "What is the observed stablecoin yield universe?",
        "The sample covers multiple pool types and chains, so APY should not be compared without stratification.",
        f"pools={pools['pool_id'].nunique()}, pool-days={len(panel)}",
    )


def fig_02_apy_distribution(root: Path, config: dict) -> dict[str, str]:
    paths, panel, _, _ = load_common(root)
    cfg = style(config)
    apy = panel["apy_total"].dropna()
    cap = apy.quantile(0.99)
    fig, ax = plt.subplots(figsize=(11, 7))
    sns.histplot(apy.clip(upper=cap), bins=50, ax=ax, color=cfg["focus"])
    ax.axvline(apy.median(), color="#2a9d8f", linewidth=2, label=f"Median {apy.median():.2f}%")
    ax.axvline(apy.mean(), color="#e76f51", linewidth=2, label=f"Mean {apy.mean():.2f}%")
    ax.set_title("Headline APY is heavy-tailed, so medians matter", loc="left", fontsize=16)
    ax.set_xlabel(f"APY, percent annualized (clipped at p99={cap:.1f} for display)")
    ax.set_ylabel("Pool-days")
    ax.legend(frameon=False)
    apply_theme(ax, cfg)
    add_footer(fig, cfg["source_note"])
    return save(
        fig,
        paths,
        "fig_02_apy_distribution",
        "Headline APY is heavy-tailed, so medians matter",
        "How are APY observations distributed?",
        "A small number of extreme APY observations pulls the mean above the median.",
        f"pool-days={len(panel)}",
    )


def fig_03_survival(root: Path, config: dict) -> dict[str, str]:
    paths = get_paths(root)
    cfg = style(config)
    survival = read_table(paths.tables_dir / "episode_survival.csv")
    episodes = read_table(paths.analytical_dir / "yield_episodes.parquet")
    fig, ax = plt.subplots(figsize=(11, 7))
    if not survival.empty:
        ax.step(survival["duration_days"], survival["survival"], where="post", color=cfg["focus"], linewidth=2.5)
        ax.fill_between(
            survival["duration_days"].astype(float),
            survival["ci_lower"].astype(float),
            survival["ci_upper"].astype(float),
            color=cfg["focus"],
            alpha=0.18,
            step="post",
        )
    ax.set_ylim(0, 1.02)
    ax.set_title("Most high-yield episodes fade quickly in the observed sample", loc="left", fontsize=16)
    ax.set_xlabel("Episode duration, days")
    ax.set_ylabel("Probability episode remains above threshold")
    apply_theme(ax, cfg)
    add_footer(fig, cfg["source_note"])
    primary = episodes[episodes["threshold_definition"] == "apy_ge_10"] if not episodes.empty else episodes
    return save(
        fig,
        paths,
        "fig_03_episode_survival",
        "Most high-yield episodes fade quickly in the observed sample",
        "How long do APY >= 10 percent episodes last?",
        "Kaplan-Meier survival declines steeply at short durations, with censored active episodes retained.",
        f"episodes={len(primary)}",
    )


def fig_04_ranking_churn(root: Path, config: dict) -> dict[str, str]:
    paths = get_paths(root)
    cfg = style(config)
    rank = read_table(paths.tables_dir / "ranking_churn.csv")
    fig, ax = plt.subplots(figsize=(9, 6))
    pivot = rank.groupby(["k", "horizon_days"])["churn"].mean().unstack()
    sns.heatmap(pivot, annot=True, fmt=".1%", cmap="Blues", ax=ax, cbar_kws={"label": "Mean churn"})
    ax.set_title("Top-yield membership changes as the horizon widens", loc="left", fontsize=15)
    ax.set_xlabel("Horizon, days")
    ax.set_ylabel("Top-k set")
    add_footer(fig, cfg["source_note"])
    return save(
        fig,
        paths,
        "fig_04_ranking_churn",
        "Top-yield membership changes as the horizon widens",
        "How stable are top-yield rankings?",
        (
            "Heatmap cells show separate top-k means; pooled text summaries weight "
            "each valid observed-date/top-k comparison equally."
        ),
        f"date comparisons={len(rank)}",
    )


def frontier_plot(root: Path, config: dict, fig_id: str, hero: bool = False) -> dict[str, str]:
    paths = get_paths(root)
    cfg = style(config)
    data = read_table(paths.tables_dir / "yield_frontier.csv")
    fig, ax = plt.subplots(figsize=(13.33 if hero else 10.5, 7.5 if hero else 7))
    for pool_type, group in data.groupby("pool_type"):
        sizes = np.sqrt(group["median_tvl_usd"].clip(lower=1)) / 900
        ax.scatter(
            group["median_apy"],
            group["persistence_ratio_10"],
            s=sizes.clip(30, 900),
            alpha=0.75,
            label=pool_type.replace("_", " "),
            color=cfg["palette"].get(pool_type, cfg["neutral"]),
            edgecolor="white",
            linewidth=0.6,
        )
    if not data.empty:
        top = data.sort_values(["frontier_candidate", "median_tvl_usd"], ascending=[False, False]).head(4)
        for row in top.itertuples(index=False):
            ax.annotate(
                str(row.symbol_raw)[:14],
                (row.median_apy, row.persistence_ratio_10),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
                color=cfg["text"],
            )
    ax.set_title(
        "High yield is common; persistent high yield with capacity is rarer"
        if hero
        else "Joint screen shows the trade-off behind headline APY",
        loc="left",
        fontsize=18 if hero else 15,
    )
    ax.set_xlabel("Median APY, percent annualized")
    ax.set_ylabel("Persistence ratio: share of observed days with APY at or above 10%")
    ax.legend(frameon=False, fontsize=8, loc="best")
    apply_theme(ax, cfg)
    add_footer(fig, cfg["source_note"])
    return save(
        fig,
        paths,
        fig_id,
        "High yield is common; persistent high yield with capacity is rarer"
        if hero
        else "Joint screen shows the trade-off behind headline APY",
        "Which pools combine APY, persistence and TVL?",
        "Only a subset sits above median APY, persistence and TVL simultaneously; this is a joint threshold screen, not a recommendation.",
        f"pools={len(data)}",
    )


def fig_05_frontier(root: Path, config: dict) -> dict[str, str]:
    return frontier_plot(root, config, "fig_05_yield_persistence_frontier", hero=False)


def fig_06_base_reward(root: Path, config: dict) -> dict[str, str]:
    paths, panel, _, _ = load_common(root)
    cfg = style(config)
    summary = (
        panel.groupby("pool_type")
        .agg(base=("apy_base", "median"), reward=("apy_reward", "median"), rows=("pool_id", "size"))
        .reset_index()
        .sort_values("base", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(11, 7))
    x = np.arange(len(summary))
    ax.bar(x - 0.18, summary["base"], width=0.36, label="Base APY", color=cfg["focus"])
    ax.bar(x + 0.18, summary["reward"].fillna(0), width=0.36, label="Reward APY", color="#e76f51")
    ax.set_xticks(x, [pretty_pool_type(value) for value in summary["pool_type"]])
    ax.set_title("Base and reward APY describe different yield mechanisms", loc="left", fontsize=15)
    ax.set_ylabel("Median APY, percent annualized")
    ax.legend(frameon=False)
    apply_theme(ax, cfg)
    add_footer(fig, cfg["source_note"])
    return save(
        fig,
        paths,
        "fig_06_base_vs_reward",
        "Base and reward APY describe different yield mechanisms",
        "How much of APY comes from base versus reward components?",
        "Reward coverage is partial and reward-heavy pools should be interpreted separately.",
        f"pool-days={len(panel)}",
    )


def fig_07_apy_tvl(root: Path, config: dict) -> dict[str, str]:
    paths = get_paths(root)
    cfg = style(config)
    data = read_table(paths.tables_dir / "apy_tvl_event_response.csv")
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    if not data.empty:
        axes[0].plot(data["event_time_day"], data["median_apy"], color=cfg["focus"], linewidth=2)
        axes[1].plot(data["event_time_day"], data["median_tvl_index"], color="#2a9d8f", linewidth=2)
    for ax in axes:
        ax.axvline(0, color=cfg["warning"], linestyle="--", linewidth=1)
        apply_theme(ax, cfg)
    axes[0].set_title("After APY jumps, yield and TVL move on different clocks", loc="left", fontsize=15)
    axes[0].set_ylabel("Median APY")
    axes[1].set_ylabel("Median TVL index")
    axes[1].set_xlabel("Days since APY jump")
    add_footer(fig, cfg["source_note"] + " TVL index is an observed TVL proxy, not direct capital flow.")
    return save(
        fig,
        paths,
        "fig_07_apy_tvl_relationship",
        "After APY jumps, yield and TVL move on different clocks",
        "Are APY jumps followed by TVL changes and compression?",
        "Event-time patterns are observational and use TVL change only as a proxy.",
        f"event-time rows={len(data)}",
    )


def fig_08_depeg(root: Path, config: dict) -> dict[str, str]:
    paths = get_paths(root)
    cfg = style(config)
    data = read_table(paths.tables_dir / "depeg_event_study.csv")
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    if not data.empty:
        axes[0].plot(data["event_time_day"], data["price_usd"], color=cfg["warning"], linewidth=2)
        axes[0].axhline(1.0, color=cfg["neutral"], linestyle="--", linewidth=1)
        axes[1].plot(data["event_time_day"], data["median_apy"], color=cfg["focus"], linewidth=2)
        stable = str(data["stablecoin_id"].iloc[0])
    else:
        stable = "n/a"
    for ax in axes:
        ax.axvline(0, color=cfg["warning"], linestyle="--", linewidth=1)
        apply_theme(ax, cfg)
    axes[0].set_title("Peg stress changes the denominator behind nominal yield", loc="left", fontsize=15)
    axes[0].set_ylabel(f"{stable} price, USD")
    axes[1].set_ylabel("Median exposed-pool APY")
    axes[1].set_xlabel("Days around selected depeg/stress date")
    add_footer(fig, cfg["source_note"])
    return save(
        fig,
        paths,
        "fig_08_depeg_event_study",
        "Peg stress changes the denominator behind nominal yield",
        "How do APY and price behave around stablecoin peg stress?",
        "A depeg window makes nominal APY harder to interpret without price context.",
        f"event-window rows={len(data)}",
    )


def fig_09_archetypes(root: Path, config: dict) -> dict[str, str]:
    paths = get_paths(root)
    cfg = style(config)
    data = read_table(paths.tables_dir / "pool_archetypes.csv")
    features = [
        "median_apy",
        "apy_robust_volatility",
        "persistence_ratio_10",
        "median_reward_share",
        "median_tvl_usd",
        "tvl_drawdown",
    ]
    matrix = data.groupby("archetype")[features].median()
    normalized = (matrix - matrix.min()) / (matrix.max() - matrix.min()).replace(0, np.nan)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(normalized.fillna(0), cmap="viridis", annot=matrix.round(2), fmt="", ax=ax)
    ax.set_title("Pool archetypes separate yield level, persistence and capacity", loc="left", fontsize=15)
    ax.set_xlabel("Feature")
    ax.set_ylabel("Archetype")
    add_footer(fig, cfg["source_note"])
    return save(
        fig,
        paths,
        "fig_09_pool_archetypes",
        "Pool archetypes separate yield level, persistence and capacity",
        "Do pools cluster into interpretable profiles?",
        "Exploratory clusters summarize patterns but are not labels of safety or quality.",
        f"pools={len(data)}",
    )


def fig_10_hero(root: Path, config: dict) -> dict[str, str]:
    return frontier_plot(root, config, "fig_10_hero_yield_frontier", hero=True)


FIGURES: list[tuple[str, FigureFunction]] = [
    ("fig_01_yield_universe", fig_01_universe),
    ("fig_02_apy_distribution", fig_02_apy_distribution),
    ("fig_03_episode_survival", fig_03_survival),
    ("fig_04_ranking_churn", fig_04_ranking_churn),
    ("fig_05_yield_persistence_frontier", fig_05_frontier),
    ("fig_06_base_vs_reward", fig_06_base_reward),
    ("fig_07_apy_tvl_relationship", fig_07_apy_tvl),
    ("fig_08_depeg_event_study", fig_08_depeg),
    ("fig_09_pool_archetypes", fig_09_archetypes),
    ("fig_10_hero_yield_frontier", fig_10_hero),
]
