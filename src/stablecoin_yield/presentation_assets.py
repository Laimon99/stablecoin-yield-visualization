from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from stablecoin_yield.config import get_paths
from stablecoin_yield.reporting import build_summary


@dataclass(frozen=True)
class PresentationAssetOutputs:
    outline_markdown: Path
    slides_json: Path
    speaker_notes: Path


def build_presentation_assets(root: Path, mode: str = "sample") -> PresentationAssetOutputs:
    paths = get_paths(root)
    paths.presentation_dir.mkdir(parents=True, exist_ok=True)
    summary = build_summary(root, mode)
    slides = slide_plan(summary)
    outline_path = paths.presentation_dir / "stablecoin_yield_slides.md"
    json_path = paths.presentation_dir / "stablecoin_yield_slides.json"
    notes_path = paths.presentation_dir / "speaker_notes.md"
    outline_path.write_text(render_slide_markdown(slides, summary), encoding="utf-8")
    json_path.write_text(json.dumps(slides, ensure_ascii=False, indent=2), encoding="utf-8")
    notes_path.write_text(render_speaker_notes(slides), encoding="utf-8")
    pd.DataFrame(slides).to_csv(paths.presentation_dir / "stablecoin_yield_slides.csv", index=False)
    return PresentationAssetOutputs(
        outline_markdown=outline_path,
        slides_json=json_path,
        speaker_notes=notes_path,
    )


def slide_plan(summary: dict) -> list[dict]:
    figures = {item["id"]: item for item in summary["figures"]}

    def fig(figure_id: str) -> str:
        return figures.get(figure_id, {}).get("png", "")

    return [
        {
            "slide": 1,
            "title": "Stablecoin Yield",
            "question": "What makes stablecoin APY interpretable?",
            "takeaway": "Yield needs duration, capacity, mechanism and peg context before comparison.",
            "visual": "",
            "speaker_note": "Open with the precise scope: persistence, mechanisms and observed TVL response. State that this is not a protocol-risk model or a recommendation list.",
        },
        {
            "slide": 2,
            "title": "Research Frame",
            "question": "What did the project ask?",
            "takeaway": "Five questions connect persistence, mechanisms, ranking stability, peg stress and a transparent joint screen.",
            "visual": "",
            "speaker_note": "State the five research questions and the decision to use pool-day as the analytical grain.",
        },
        {
            "slide": 3,
            "title": "A Deliberate Analytical Sample",
            "question": "What was observed, and how were pools selected?",
            "takeaway": f"The unbalanced panel spans {summary['market']['date_min']} to {summary['market']['date_max']} and retains observed entry and exit.",
            "visual": "",
            "speaker_note": "Explain the eligibility rules: stablecoin flag, at least USD 1 million TVL and 180 history observations. The 250-pool cap combines 70 percent highest TVL with the remaining capacity highest APY.",
        },
        {
            "slide": 4,
            "title": "Auditable Definitions",
            "question": "Exactly how are episodes, churn, events and the joint screen defined?",
            "takeaway": "Every thresholded result has an explicit formula, window and censoring rule.",
            "visual": "",
            "speaker_note": "Define the main 10% episode specification, one-missing-day tolerance, right censoring, churn formula, APY-jump event trigger and the three-median joint screen. Emphasize that the screen is not a Pareto frontier.",
        },
        {
            "slide": 5,
            "title": "APY Is Heavy Tailed",
            "question": "Why are headline APY values hard to compare?",
            "takeaway": f"Pool-day median APY is {summary['market']['median_apy']:.2f}% while the pool-day mean is {summary['market']['mean_apy']:.2f}%.",
            "visual": fig("fig_02_apy_distribution"),
            "speaker_note": "Use the p99 display cap and preserved extreme-value flags to justify robust summaries without deleting source observations.",
        },
        {
            "slide": 6,
            "title": "High Yield Is Usually Short",
            "question": "How long do episodes at or above 10% APY last?",
            "takeaway": f"The median high-yield episode lasts {summary['episodes']['primary_median_duration_days']:.0f} days; only {summary['episodes']['survival_points']['30']['survival']:.1%} remain after 30 days.",
            "visual": fig("fig_03_episode_survival"),
            "speaker_note": "Explain Kaplan-Meier survival and right censoring. Report 2,668 episodes, median 2 days, p90 16 days and 1.2 percent censored.",
        },
        {
            "slide": 7,
            "title": "Rankings Lose Members Over Time",
            "question": "Do top-yield pools stay at the top?",
            "takeaway": (
                "Weighted by valid date × top-k comparisons, churn rises from "
                f"{summary['ranking']['mean_churn_by_horizon']['1']:.1%} after 1 day to "
                f"{summary['ranking']['mean_churn_by_horizon']['30']:.1%} after 30 days."
            ),
            "visual": fig("fig_04_ranking_churn"),
            "speaker_note": (
                "Define churn as one minus top-k retention. The heatmap cells are separate "
                "top-10 and top-20 date means. The text summary pools all valid "
                "observed-date/top-k comparisons, so it is weighted by their counts: "
                f"{summary['ranking']['comparison_count_by_horizon']['1']:,} at 1 day, "
                f"{summary['ranking']['comparison_count_by_horizon']['7']:,} at 7 days and "
                f"{summary['ranking']['comparison_count_by_horizon']['30']:,} at 30 days."
            ),
        },
        {
            "slide": 8,
            "title": "Mechanism Changes What APY Means",
            "question": "What sits behind headline APY?",
            "takeaway": "Base and reward components separate lending yield from incentive dependence, although reward coverage is partial.",
            "visual": "",
            "speaker_note": "Use the native chart. Contrast incentive-driven pools with base-yield categories and report 90.3 percent base coverage versus 61.6 percent reward coverage.",
        },
        {
            "slide": 9,
            "title": "APY Falls Faster Than TVL Responds",
            "question": "What happens after an observed APY jump?",
            "takeaway": "Across 453 events, median APY peaks at 18.24% on day 0 and falls to 8.33% by day 30, while median normalized TVL reaches 1.69.",
            "visual": "",
            "speaker_note": "Describe the event trigger and show the four event-time points. State immediately that TVL is an observational balance-sheet proxy, not a causal wallet-flow estimate.",
        },
        {
            "slide": 10,
            "title": "Peg Stress Changes the Yield Denominator",
            "question": "What changed during the March 2023 USDC depeg?",
            "takeaway": f"USDC fell to {summary['depeg']['min_price_usd']:.4f} USD while median exposed-pool APY rose by {summary['depeg']['apy_change_pp_day_minus_1_to_0']:.2f} percentage points from day -1 to day 0.",
            "visual": "",
            "speaker_note": "Report the selected reviewed event, the 10-pool exposure window and the descriptive APY change. Do not generalize one event into a causal risk estimate.",
        },
        {
            "slide": 11,
            "title": "Few Pools Clear All Three Thresholds",
            "question": "Which pools combine APY, persistence and capacity?",
            "takeaway": f"{summary['joint_screen']['candidate_share']:.1%} of pools are above the sample medians for APY, persistence and TVL simultaneously.",
            "visual": "",
            "speaker_note": "Call this a joint threshold screen, not a Pareto frontier. Bubble size encodes median TVL; highlighted points clear all three medians.",
        },
        {
            "slide": 12,
            "title": "The Main Duration Result Is Robust",
            "question": "Does the short-episode conclusion depend on one threshold?",
            "takeaway": "Median episode duration remains 2 days at 5%, 10% and 20% APY thresholds, with sensitivity checks for TVL, history, gaps and winsorization.",
            "visual": "",
            "speaker_note": "Show that episode counts change with the threshold but the median duration does not. Mention all five robustness families materialized by the pipeline.",
        },
        {
            "slide": 13,
            "title": "This Is Market Context, Not Total Risk",
            "question": "What does the project deliberately not claim?",
            "takeaway": "The analysis measures quoted yield, persistence, TVL, rewards and peg context, not smart-contract or counterparty safety.",
            "visual": "",
            "speaker_note": "Name the unmeasured dimensions: smart-contract, counterparty, bridge, chain, oracle, liquidity and collateral quality. This boundary is why the project avoids recommendations.",
        },
        {
            "slide": 14,
            "title": "Conclusion",
            "question": "What should the viewer remember?",
            "takeaway": "Stablecoin yield is best shown as regimes and trade-offs, not as a static ranked table.",
            "visual": "",
            "speaker_note": "Close with the one-sentence defense, reproducibility and the no-financial-advice boundary.",
        },
    ]


def render_slide_markdown(slides: list[dict], summary: dict) -> str:
    lines = [
        "# Stablecoin Yield Presentation",
        "",
        f"Mode: `{summary['mode']}`",
        "",
        "This outline is generated from pipeline outputs and is used as the source for the final deck.",
        "",
    ]
    for slide in slides:
        lines.extend(
            [
                f"## {slide['slide']}. {slide['title']}",
                "",
                f"**Question:** {slide['question']}",
                "",
                f"**Takeaway:** {slide['takeaway']}",
                "",
                f"**Visual:** `{slide['visual'] or 'none'}`",
                "",
                f"**Speaker note:** {slide['speaker_note']}",
                "",
            ]
        )
    return "\n".join(lines)


def render_speaker_notes(slides: list[dict]) -> str:
    lines = ["# Speaker Notes", ""]
    for slide in slides:
        lines.extend(
            [
                f"## Slide {slide['slide']}: {slide['title']}",
                "",
                slide["speaker_note"],
                "",
            ]
        )
    return "\n".join(lines)
