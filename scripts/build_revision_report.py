"""Add a reproducibility and uncertainty supplement to the historical report."""
from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/revision"
TMP = ROOT / "tmp/revision"
REPO = "https://github.com/Laimon99/stablecoin-yield-visualization"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    evidence = json.loads((OUT / "published_evidence_audit.json").read_text())
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="DeckTitle", fontName="Helvetica-Bold", fontSize=32, leading=38, textColor=colors.HexColor("#14213D"), spaceAfter=22))
    styles.add(ParagraphStyle(name="SectionTitle", fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=colors.HexColor("#14213D"), spaceAfter=17))
    styles.add(ParagraphStyle(name="Copy", fontName="Helvetica", fontSize=11, leading=16, spaceAfter=12, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="SmallCopy", parent=styles["Copy"], fontSize=9, leading=13))
    styles.add(ParagraphStyle(name="CodeCopy", fontName="Courier", fontSize=9, leading=14, spaceAfter=12))

    def p(text: str, style: str = "Copy") -> Paragraph:
        return Paragraph(text, styles[style])

    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#6941C6"))
        canvas.line(48, 48, 547, 48)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(48, 34, "Simone Ragusini | Stablecoin Yield | Revision: 23 September 2026")

    def write(name, story):
        path = TMP / name
        SimpleDocTemplate(str(path), leftMargin=48, rightMargin=48, topMargin=48, bottomMargin=64, title="Stablecoin Yield: reproducibility supplement", author="Simone Ragusini").build(story, onFirstPage=footer, onLaterPages=footer)
        if len(PdfReader(path).pages) != 1:
            raise ValueError(f"Supplement page overflow: {name}")
        return path

    front = write("report_front.pdf", [
        Spacer(1, 2 * cm), p("DATA VISUALIZATION", "SmallCopy"),
        p("Stablecoin Yield", "DeckTitle"),
        p("Persistence, mechanisms and observed TVL response", "SectionTitle"),
        Spacer(1, .6 * cm), p("<b>Simone Ragusini</b><br/>Student ID: 945119<br/>s.ragusini@campus.unimib.it"),
        p("Revised analytical report<br/>23 September 2026"),
        Spacer(1, .7 * cm),
        p("The empirical analysis retains the historical sample through 8 July 2026: 250 pools and 137,095 pool-days. This edition adds explicit tool attribution, an offline interactive companion, reproducibility instructions and statistical interpretation notes."),
        p("<b>Reading guide.</b> The following pages preserve the original analytical report. Appendix A documents the revision and qualifies the uncertainty and reproducibility claims. Read the two parts together."),
        p(f'<b>Code repository</b><br/><link href="{REPO}" color="#176B87">{REPO}</link>'),
        p('Original code: MIT. Original presentation, report and text: <link href="https://creativecommons.org/licenses/by/4.0/" color="#176B87">CC BY 4.0</link>, Simone Ragusini (2026). Provider data and third-party dependencies retain their own terms. See LICENSE and NOTICE.md.', "SmallCopy"),
        p("Educational descriptive analysis. Quoted APY is not realized return. The project does not identify a safest or best investment.", "SmallCopy"),
    ])
    tool_rows = [[p("Tool", "SmallCopy"), p("Concrete use", "SmallCopy")]]
    for a, b in [("Matplotlib (+ Seaborn)", "Ten static analytical figures in the report: distribution, survival, ranking churn, mechanisms, events and joint screen."), ("Plotly", "Three interactive charts: survival with confidence band and risk sets, ranking churn, and threshold sensitivity."), ("pandas / NumPy", "Canonical tables, grouped summaries and numerical transformations."), ("lifelines / scikit-learn", "Kaplan-Meier survival / exploratory standardized pool archetypes."), ("Artifact Tool / ReportLab", "PowerPoint assembly / report layout; separate from statistical estimation.")]:
        tool_rows.append([p(a, "SmallCopy"), p(b, "SmallCopy")])
    table = Table(tool_rows, colWidths=[145, 354], hAlign="LEFT")
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF0FC")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), .4, colors.HexColor("#DDDFE8")), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 8)]))
    a1 = write("report_a1.pdf", [
        p("Appendix A1. Tools and visual choices", "SectionTitle"),
        p("The two visualization tools are <b>Matplotlib and Plotly</b>. They produce actual outputs. Seaborn supports Matplotlib and is not counted as a second independent renderer."), table,
        Spacer(1, 18),
        p("<b>Why these forms?</b> A step curve represents the discrete survival estimate. Its band makes pointwise uncertainty visible. The churn heatmap compares horizon and top-k size on a fixed 0-100% color scale with numerical labels. Threshold bars show how the episode count changes while the median remains two days."),
        p("<b>Interaction with a purpose.</b> Hover displays exact estimates, confidence limits and denominators. Range buttons reveal both short episodes and the full tail. Text summaries and HTML tables provide an alternative to mouse interaction and color perception."),
        p("<b>Offline companion.</b> Open <b>stablecoin_yield_interactive.html</b> from the revision directory. Plotly.js is embedded. The file requires no account, API key, CDN or internet connection."),
        p("Installed versions: " + ", ".join(f"{k} {v}" for k, v in evidence["versions"].items()) + ". The complete Python environment is pinned in uv.lock.", "SmallCopy"),
    ])
    a2 = write("report_a2.pdf", [
        p("Appendix A2. Reproduction and rights", "SectionTitle"),
        p(f'<link href="{REPO}" color="#176B87">{REPO}</link>'),
        p("<b>Published aggregate evidence, without APIs</b>"),
        p("uv sync --frozen --extra dev<br/>uv run python scripts/reproduce_published.py<br/>uv run ruff check src scripts tests<br/>uv run pytest", "CodeCopy"),
        p("The script reads the public survival, ranking and robustness tables and the report summary. It checks counts, survival ordering, confidence limits and headline consistency before regenerating the interactive output. The audit JSON records input hashes and installed versions."),
        p("<b>Recollection and full method</b>"),
        p("uv run python scripts/reproduce_all.py --mode full", "CodeCopy"),
        p("A new clone collects provider data. An existing checkout can reuse cached responses; --refresh requests recollection. Live revisions and the current eligibility sample can change results. Run in a separate checkout to retain the historical outputs."),
        p("<b>Reproduction boundary.</b> Rebuilding aggregate figures is distinct from independently reproducing raw-to-result transformation. The historical raw and row-level provider snapshot is not publicly redistributed. The optional PowerPoint builder also requires Artifact Tool. The rendered PDF and Python evidence companion do not."),
        p("<b>Licensing.</b> Code, tests and configuration: MIT. Original report, slide text, documentation and authored visual expression: CC BY 4.0. Credit Simone Ragusini, Stablecoin Yield (2026), link the licence and repository, and identify changes. These grants exclude provider data and third-party software."),
        p('<b>Sources.</b> DeFiLlama: <link href="https://api-docs.defillama.com/" color="#176B87">API documentation</link> and <link href="https://defillama.com/terms" color="#176B87">terms</link>. CoinGecko: <link href="https://docs.coingecko.com/" color="#176B87">API documentation</link> and <link href="https://www.coingecko.com/en/api_terms" color="#176B87">terms</link>. Plotly.js retains its embedded MIT notice. Licence scope: LICENSE and NOTICE.md.', "SmallCopy"),
    ])
    a3 = write("report_a3.pdf", [
        p("Appendix A3. Statistical interpretation", "SectionTitle"),
        p(f'<b>Survival at day 30.</b> S(30) = {evidence["survival_30_days"]:.2%}, with published 95% pointwise interval {evidence["ci_30_lower"]:.2%} to {evidence["ci_30_upper"]:.2%}. S(t) means the probability that an observed episode lasts more than t calendar days. The two-day median remains unchanged.'),
        p("<b>Dependence.</b> The lifelines interval treats episodes as independent. Multiple episodes from one pool can be dependent. This interval is neither pool-clustered nor a simultaneous band. Pool-level resampling would address a different inferential question and is not claimed as part of these results."),
        p("<b>Observation boundaries.</b> An episode already active when a pool first appears can have an unobserved earlier start. A long gap terminates an observed run under the original definition; it is not evidence of an economic threshold crossing. The gap sensitivity results support the stability of the observed median but do not establish non-informative censoring."),
        p("<b>Selection.</b> The sample deliberately combines high-TVL and high-current-APY pools after eligibility filters. It is not a random market sample. The 90-day and 180-day history checks apply within pools already selected with at least 180 provider observations, and cannot recover excluded short-history pools."),
        p("<b>Ranking denominators.</b> Headline churn averages valid date-by-top-k comparisons: 2,669 at one day, 2,657 at seven days and 2,612 at 30 days. These are not independent pools. Entry, exit and changing availability can affect membership."),
        p("<b>Event response.</b> APY jumps select unusually high values, so subsequent declines can also reflect regression to the mean. TVL can vary through prices, accounting and capital movements. Available events can differ by offset. Without a control group or causal identification, the curves support descriptive timing comparisons only."),
        p("<b>What remains supported.</b> The selected historical sample has short typical high-yield episodes, increasing membership churn with horizon, and substantial contextual differences between nominal APYs. These results motivate transparent multidimensional communication rather than investment recommendations."),
    ])
    writer = PdfWriter()
    for source in [front, ROOT / "outputs/report/stablecoin_yield_report.pdf", a1, a2, a3]:
        writer.append(source)
    writer.add_metadata({"/Title": "Stablecoin Yield - Revised analytical report", "/Author": "Simone Ragusini, 945119", "/Subject": "Historical analysis with reproducibility and uncertainty supplement"})
    target = OUT / "Simone_Ragusini_945119_Report.pdf"
    with target.open("wb") as stream:
        writer.write(stream)
    print(f"Report: {target.name}, {len(writer.pages)} pages")


if __name__ == "__main__":
    main()
