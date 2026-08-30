# Presentation QA

Generated deck: `outputs/presentation/stablecoin_yield_presentation.pptx`

Pipeline mode: `full`

## Visual System

- Flutter-inspired blue, cyan, violet and coral palette with soft rounded surfaces.
- Dark gradient opening and closing slides; light analytical canvas for evidence slides.
- Deterministic 2x PNG chart assets replace renderer-sensitive vector charts for sample composition, APY distribution, survival, mechanisms, APY/TVL event response, USDC depeg context, the joint threshold screen and robustness.
- Alternating chart layouts, restrained shadows and a continuous progress marker preserve narrative rhythm without turning the deck into a dashboard.

## PowerPoint Compatibility

- Final acceptance renderer: Microsoft PowerPoint 16.0 at 1600 x 900.
- PowerPoint export evidence was reviewed during release QA and is retained only in the local, Git-ignored preview directory.
- Final renderer contact sheet: `outputs/presentation/stablecoin_yield_presentation_powerpoint_contact_sheet.png`.
- PowerPoint also exports the synchronized 14-page `outputs/presentation/stablecoin_yield_presentation.pdf`.
- PDF render evidence was reviewed during release QA and is retained only in the local, Git-ignored preview directory.
- Slides 3, 5, 6, 7, 8, 9, 10, 11 and 12 contain static chart images, so PowerPoint cannot expand point labels or apply the Italian numeric locale.
- Slide 5 labels 4.29% as the pool-day median and uses a 32-bin histogram capped at p99 only for display.
- Slide 7 identifies the headline churn values as comparison-weighted averages, reports 2,669, 2,657 and 2,612 valid observed-date/top-k comparisons, and leaves the heatmap cells as separate top-10 and top-20 means.
- Slide 11 uses unlabeled gray and coral bubbles, p95-capped sizing and explicit 4.47% APY and 6.1% persistence thresholds.
- Slide 6 focuses the Kaplan-Meier curve on the first 100 days, marks day 2 and day 30, and preserves the 626-day tail in an inset.
- The compatibility trade-off is intentional: chart appearance is deterministic, while chart internals are not editable as Office chart objects.

## Academic Revision

- Scope corrected to persistence, mechanisms and observed TVL response; no claim of complete risk or wallet-level capital-flow measurement.
- Study period, deterministic pool selection, unbalanced-panel treatment and data-quality warnings are visible.
- Episode, churn, event-study and joint-screen definitions are stated explicitly.
- The deck distinguishes the 4.29% pool-day median from the 4.47% median of pool-level APY summaries used by the joint screen.
- Ranking churn wording distinguishes the comparison-weighted pooled summaries from the six top-k-specific heatmap cells.
- `Primary episode` was removed from audience-facing copy: all 2,668 contiguous episodes under the main 10% specification are analyzed.
- APY/TVL event response reports 453 events and quantitative day -7, 0, 7 and 30 checkpoints.
- USDC case study reports the minimum price and the 1.38 percentage-point APY change from day -1 to day 0.
- `Frontier` is replaced in audience-facing copy by `joint threshold screen`; the slide states that it is not a Pareto frontier.
- Robustness covers APY thresholds, minimum TVL, minimum history, episode gaps and p1-p99 winsorization.
- The final limits slide separates measured market context from unmeasured protocol, counterparty, liquidity and investor-specific risk.

## Checks

- Slide count: 14.
- Speaker notes: present on all 14 slides.
- Artifact-tool builder: `scripts/build_presentation_deck.mjs`.
- PowerPoint QA exporter: `scripts/render_presentation_powerpoint.ps1`.
- PNG previews, layout JSON and an inspect snapshot were generated for every slide during build-time QA and are retained locally rather than distributed.
- All 390 exported bounding boxes remain inside the 1280 x 720 canvas.
- The presentation skill overflow test passes with no detected overflow.
- No layout warning tokens for overlap, clipping or overflow.
- PPTX ZIP validation: 14 slide parts, 14 note parts, zero chart parts and 11 embedded media parts.
- Manual inspection completed on the full PowerPoint contact sheet and slides 1, 2, 5, 6, 7, 9, 10, 11, 12 and 14 at 1600 x 900.
- The 14-page PDF was independently rendered with PyMuPDF; its full contact sheet and critical analytical pages match the accepted PowerPoint layout.
- Intermediate slides use a deterministic top-right number badge and progress bar; opening and closing slides retain `01 / 14` and `14 / 14`.
- Source notes, typographic symbols and English decimal formatting remain visible in the PowerPoint render.
- Final slide resolves the opening claim and preserves the no-financial-advice boundary.

## Tool Limitation

PowerPoint QA is an optional Windows-only release check because Microsoft PowerPoint is not part of the portable Python and Node environment. The reproducible core still builds the deck, chart assets, artifact previews and structural evidence without PowerPoint.
