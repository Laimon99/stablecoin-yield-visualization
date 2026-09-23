"""Rebuild an interactive evidence companion from published aggregates, without APIs."""
from __future__ import annotations

import argparse
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from stablecoin_yield.visualization.published import render_published_static

ROOT = Path(__file__).resolve().parents[1]


def published_figures(root: Path) -> tuple[dict, list[tuple[str, str, go.Figure]]]:
    table_dir = root / "outputs/tables"
    survival = pd.read_csv(table_dir / "episode_survival.csv")
    ranks = pd.read_csv(table_dir / "ranking_churn.csv")
    robustness = pd.read_csv(table_dir / "robustness_checks.csv")
    summary = json.loads((root / "outputs/report/report_summary.json").read_text())
    # Cross-check independent aggregate files, not constants copied from slide text.
    primary = robustness.loc[robustness["check"] == "threshold_10"].iloc[0]
    if int(primary.episode_count) != summary["episodes"]["primary_count"]:
        raise ValueError("Episode count disagrees between published tables and summary")
    if int(primary.pool_count) != summary["market"]["pool_count"]:
        raise ValueError("Pool count disagrees between published tables and summary")
    if int(primary.panel_rows) != summary["market"]["pool_day_count"]:
        raise ValueError("Panel size disagrees between published tables and summary")
    if not survival.duration_days.is_monotonic_increasing or not survival.survival.is_monotonic_decreasing:
        raise ValueError("Invalid survival curve ordering")
    if not ((survival.ci_lower <= survival.survival) & (survival.survival <= survival.ci_upper)).all():
        raise ValueError("Invalid confidence interval")
    day30 = survival.loc[survival.duration_days <= 30].iloc[-1]
    if abs(day30.survival - summary["episodes"]["survival_points"]["30"]["survival"]) > .0005:
        raise ValueError("Survival headline disagrees with table")
    stats = ranks.groupby("horizon_days").churn.agg(["mean", "count"])
    for horizon, row in stats.iterrows():
        if abs(row["mean"] - summary["ranking"]["mean_churn_by_horizon"][str(horizon)]) > .0005:
            raise ValueError("Ranking headline disagrees with table")
        if int(row["count"]) != summary["ranking"]["comparison_count_by_horizon"][str(horizon)]:
            raise ValueError("Ranking denominator disagrees with table")
    fig = go.Figure()
    fig.add_scatter(x=survival.duration_days, y=survival.ci_upper, mode="lines", line=dict(width=0, shape="hv"), showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=survival.duration_days, y=survival.ci_lower, mode="lines", line=dict(width=0, shape="hv"), fill="tonexty", fillcolor="rgba(110,70,200,.16)", name="95% pointwise CI", hoverinfo="skip")
    fig.add_scatter(x=survival.duration_days, y=survival.survival, mode="lines", line=dict(color="#6941C6", width=3, shape="hv"), name="Kaplan–Meier S(t)", customdata=survival[["ci_lower", "ci_upper", "at_risk"]], hovertemplate="Day %{x}<br>S(t): %{y:.2%}<br>95% CI: %{customdata[0]:.2%}–%{customdata[1]:.2%}<br>At risk before this event time: %{customdata[2]:,.0f}<extra></extra>")
    fig.update_layout(xaxis_title="Duration t (calendar days)", yaxis_title="Probability of duration > t", yaxis_tickformat=".0%", yaxis_range=[0, 1], xaxis_range=[0, 100], updatemenus=[dict(type="buttons", direction="right", x=0, y=1.18, buttons=[dict(label="First 30 days", method="relayout", args=[{"xaxis.range": [0, 30]}]), dict(label="First 100 days", method="relayout", args=[{"xaxis.range": [0, 100]}]), dict(label="Full tail", method="relayout", args=[{"xaxis.range": [0, float(survival.duration_days.max())]}])])])
    pivot = ranks.pivot_table(index="k", columns="horizon_days", values="churn", aggfunc="mean")
    counts = ranks.pivot_table(index="k", columns="horizon_days", values="churn", aggfunc="count")
    heat = go.Figure(go.Heatmap(z=pivot.to_numpy(), x=[f"{h} day" if h == 1 else f"{h} days" for h in pivot.columns], y=[f"Top {k}" for k in pivot.index], zmin=0, zmax=1, colorscale="Blues", text=pivot.map(lambda x: f"{x:.1%}").to_numpy(), texttemplate="%{text}", customdata=counts.to_numpy(), colorbar=dict(title="Churn", tickformat=".0%"), hovertemplate="%{y}, %{x}<br>Mean churn: %{z:.2%}<br>Valid date comparisons: %{customdata:,}<extra></extra>"))
    heat.update_layout(xaxis_title="Comparison horizon", yaxis_title="Membership set")
    thresholds = robustness.loc[robustness.family == "apy_threshold"]
    bars = go.Figure(go.Bar(x=thresholds.threshold_percent, y=thresholds.episode_count, marker_color="#6941C6", customdata=thresholds[["median_duration_days", "censored_share"]], text=thresholds.episode_count, textposition="outside", hovertemplate="APY threshold: %{x}%<br>Episodes: %{y:,}<br>Median observed duration: %{customdata[0]} days<br>Right-censored: %{customdata[1]:.2%}<extra></extra>"))
    bars.update_layout(xaxis_title="APY threshold (%)", xaxis=dict(type="category"), yaxis_title="Number of episodes", yaxis_range=[0, float(thresholds.episode_count.max()) * 1.18])
    figures = [
        ("survival", "High yield usually ends quickly", fig),
        ("churn", "Ranking membership changes with the horizon", heat),
        ("thresholds", "The two-day median survives threshold changes", bars),
    ]
    for _, _, chart in figures:
        chart.update_layout(template="plotly_white", font=dict(family="Arial", size=15, color="#14213D"), height=480, margin=dict(t=85, b=60, l=75, r=35), legend=dict(orientation="h", y=-.2), paper_bgcolor="#ffffff")
    metrics = {"pool_count": int(primary.pool_count), "pool_days": int(primary.panel_rows), "episodes": int(primary.episode_count), "median_duration_days": float(primary.median_duration_days), "survival_30_days": float(day30.survival), "ci_30_lower": float(day30.ci_lower), "ci_30_upper": float(day30.ci_upper), "churn": stats.reset_index().to_dict("records"), "thresholds": thresholds[["threshold_percent", "episode_count", "median_duration_days"]].to_dict("records")}
    return metrics, figures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs/revision")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics, figures = published_figures(ROOT)
    render_published_static(ROOT, args.output_dir)
    explanations = {
        "survival": "The step curve estimates P(duration > t). Hover for the estimate, confidence interval and risk set. Use the range buttons to inspect the short episodes and the long tail. The band is the published lifelines 95% pointwise interval: it assumes independent episodes and does not adjust for repeated episodes within pools. Missingness and sample selection are additional uncertainty sources.",
        "churn": "Each cell averages valid calendar-date comparisons for one top-k size. The slide headline combines these comparisons using their actual counts, rather than giving differently sized cells equal weight. Churn includes pool entry and exit. Color uses the full 0–100% scale and cell labels expose the exact values.",
        "thresholds": "Changing the APY threshold changes the number of episodes, while the median observed episode duration remains two days in this selected sample. These are sensitivity comparisons, not independent replications or significance tests.",
    }
    sections = []
    for index, (key, title, chart) in enumerate(figures):
        sections.append(f'<section id="{key}"><h2>{index + 1}. {title}</h2><p>{explanations[key]}</p>' + pio.to_html(chart, full_html=False, include_plotlyjs=index == 0, div_id=key + "-chart", config={"responsive": True, "displaylogo": False, "scrollZoom": False}) + '</section>')
    metrics_table = pd.DataFrame([{"Measure": "Pools", "Value": metrics["pool_count"]}, {"Measure": "Pool-days", "Value": metrics["pool_days"]}, {"Measure": "Episodes at APY ≥ 10%", "Value": metrics["episodes"]}, {"Measure": "Median observed duration (days)", "Value": metrics["median_duration_days"]}, {"Measure": "Survival beyond day 30", "Value": f'{metrics["survival_30_days"]:.2%}'}, {"Measure": "95% pointwise CI at day 30", "Value": f'{metrics["ci_30_lower"]:.2%}–{metrics["ci_30_upper"]:.2%}'}]).to_html(index=False, border=0)
    html = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stablecoin Yield | Interactive evidence</title><style>
body{margin:0;background:#f5f7fc;color:#14213d;font:17px/1.6 Arial,sans-serif}main{max-width:1100px;margin:auto;padding:40px 24px}header{border-bottom:4px solid #6941c6;padding-bottom:25px}h1{font-size:46px;line-height:1.15;margin:12px 0}h2{font-size:27px;line-height:1.3}section{background:white;margin:32px 0;padding:28px;border-radius:12px}a{color:#47339c}nav{display:flex;gap:24px;flex-wrap:wrap}table{border-collapse:collapse;width:100%;text-align:left}td,th{padding:10px;border-bottom:1px solid #ddd}code{overflow-wrap:anywhere}.eyebrow{font-weight:bold;color:#6941c6}footer{font-size:14px}@media(max-width:600px){h1{font-size:34px}main{padding:22px 12px}section{padding:16px}}</style></head><body><main><header><p class="eyebrow">DATA VISUALIZATION / INTERACTIVE EVIDENCE</p><h1>Stablecoin yield through time</h1><p>Simone Ragusini · Student ID 945119 · s.ragusini@campus.unimib.it</p><p>250 selected pools. 137,095 pool-days. Historical analysis through 8 July 2026.</p><nav><a href="#survival">Episode survival</a><a href="#churn">Ranking churn</a><a href="#thresholds">Threshold sensitivity</a><a href="#accessible">Data summary</a></nav></header>'''
    html += "".join(sections)
    html += '<section id="accessible"><h2>Data summary</h2><p>This text and the tables provide an alternative to chart interaction.</p>' + metrics_table
    html += '<h3>Ranking churn and denominators</h3>' + pd.DataFrame(metrics["churn"]).rename(columns={"horizon_days": "Horizon (days)", "mean": "Mean churn (fraction)", "count": "Valid date × top-k comparisons"}).to_html(index=False, border=0)
    html += '<h3>Threshold sensitivity</h3>' + pd.DataFrame(metrics["thresholds"]).to_html(index=False, border=0) + '</section>'
    html += '''<footer><p>Visualization tools: Matplotlib for the static report figures and Plotly for this interactive companion. Plotly JavaScript is embedded: no CDN, account or internet connection is needed to view this file.</p><p>Sources: <a href="https://defillama.com/">DeFiLlama</a> and <a href="https://www.coingecko.com/en/api">CoinGecko</a>. This companion uses only the published aggregate tables in the <a href="https://github.com/Laimon99/stablecoin-yield-visualization">code repository</a>. Rebuild with <code>uv run python scripts/reproduce_published.py</code>.</p><p>APY is quoted annualized yield. TVL is an observed balance proxy. No investment recommendation. Original code: MIT. Original text and presentation: CC BY 4.0, Simone Ragusini (2026). Provider data and embedded Plotly.js retain their own terms. The raw historical snapshot is not distributed; aggregate reproduction is distinct from recollection using live APIs.</p></footer></main></body></html>'''
    (args.output_dir / "stablecoin_yield_interactive.html").write_text(html, encoding="utf-8")
    sources = ["outputs/report/report_summary.json", "outputs/tables/episode_survival.csv", "outputs/tables/ranking_churn.csv", "outputs/tables/robustness_checks.csv", "outputs/tables/apy_tvl_event_response.csv", "outputs/tables/depeg_event_study.csv"]
    metrics["inputs"] = {p: hashlib.sha256((ROOT / p).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for p in sources}
    metrics["versions"] = {p: version(p) for p in ["pandas", "numpy", "matplotlib", "plotly", "lifelines"]}
    (args.output_dir / "published_evidence_audit.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(f"Verified published aggregates; interactive companion: {args.output_dir}")


if __name__ == "__main__":
    main()
