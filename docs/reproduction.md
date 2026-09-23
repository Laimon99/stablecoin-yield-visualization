# Reproducing the evidence

Repository: https://github.com/Laimon99/stablecoin-yield-visualization

## 1. Published aggregates, no API access

On Windows with Python 3.11 and an accented checkout path, run
`$env:PYTHONPATH = (Resolve-Path src).Path` in PowerShell from the project root
before the Python commands. Python 3.11 can decode editable-install path files
using the Windows locale. A checkout under an ASCII-only path avoids this issue.

```sh
git clone https://github.com/Laimon99/stablecoin-yield-visualization.git
cd stablecoin-yield-visualization
uv sync --frozen --extra dev
uv run python scripts/reproduce_published.py
uv run ruff check src scripts tests
uv run pytest
```

Open `outputs/revision/stablecoin_yield_interactive.html` in a browser. It embeds
Plotly.js and works offline. The script checks aggregate counts, survival and
churn against independently stored summary values before producing the charts.
The JSON audit records numerical outputs, input SHA-256 hashes with LF-normalized
text, and actual installed versions. `uv.lock` pins the complete Python environment.

This path reproduces the published aggregate evidence, not the original raw-data
transformation. Inputs are `episode_survival.csv`, `ranking_churn.csv`,
`robustness_checks.csv`, and `report_summary.json` in the existing outputs folders.
Run `--output-dir PATH` to build a separate copy without altering deliverables.

## 2. Full method against provider data

```sh
uv run python scripts/reproduce_all.py --mode full
```

This pipeline uses the local cache if available. In a new clone it collects live
provider responses. `--refresh` requests fresh collection. Provider access, rate
limits and terms apply. The resulting sample and values can change. Run this in
a separate checkout if you want to retain the frozen July 2026 outputs.

Raw and row-level provider datasets are excluded from public distribution.
Consequently the repository does not claim exact raw-to-result reconstruction
of the historical July snapshot. The historical local data remain available to
the author for examination and do not become open data through MIT or CC BY.

## 3. Presentation and report revision

The revised PowerPoint has a separate builder and preserves the original deck:

```sh
node scripts/build_revised_presentation.mjs --skip-preview
uv run python scripts/build_revision_report.py
```

Run the published-evidence script first. The deck reads the committed narrative
configuration, report summary, existing static heatmap and evidence audit.
It writes a draft to `tmp/revision/candidate.pptx`. It requires the optional
`@oai/artifact-tool` runtime. Specify its entry point through
`ARTIFACT_TOOL_ENTRYPOINT` or its package through `ARTIFACT_TOOL_PACKAGE_DIR`.
The distributable PDF/PPTX can be viewed without this runtime. This optional
layout dependency is separate from the portable Python evidence pipeline.

The evidence command also rebuilds Matplotlib survival and event charts from
published tables. The revised event charts use numerical day offsets, including
all observed daily aggregate rows, rather than equally spaced category labels.
The survival chart uses a step curve and the existing pointwise confidence band.

On Windows with Microsoft PowerPoint, the repository's renderer exports a
chosen deck without showing a presentation window:

```powershell
./scripts/render_presentation_powerpoint.ps1 -InputPptx tmp/revision/candidate.pptx -OutputDir tmp/revision/powerpoint_preview -OutputPdf tmp/revision/presentation.pdf
```

## Tool-to-output mapping

| Tool | Role | Source / output |
| --- | --- | --- |
| pandas, NumPy | Canonical tables, summaries | `src/stablecoin_yield/analysis/` |
| lifelines | Kaplan–Meier survival and pointwise intervals | `analysis/pipeline.py` |
| Matplotlib, with Seaborn support | Static analytical graphics | `visualization/figures.py`, ten report figures |
| Plotly | Interactive survival, churn and sensitivity | `scripts/reproduce_published.py`, HTML companion |
| Artifact Tool | PowerPoint layout and presentation-specific charts | `scripts/build_revised_presentation.mjs` |
| ReportLab, pypdf | Original report, revision appendix and PDF assembly | report builders |

The two visualization tools claimed for the course requirement are Matplotlib
and Plotly. Installing a library alone does not constitute using it.

## Single-PDF submission

The sole exam upload is `outputs/submission/Simone_Ragusini_945119.pdf`.
Its page 7 embeds a static Plotly export from the HTML companion. To reproduce
that image, open the companion in a browser and export its `churn-chart` with
`Plotly.toImage(document.getElementById('churn-chart'), {format:'png', width:1000, height:460, scale:2})`.
Save the decoded PNG as `outputs/revision/ranking_plotly.png`. This image is also
included in the source package, so rebuilding the deck does not require browser
export. The two tools are documented on page 15. Interactivity is optional;
the PDF includes the labels and interpretations needed for asynchronous review.
