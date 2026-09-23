from __future__ import annotations

import importlib.util
import json
import shutil
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pandas as pd
import pytest
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("published", ROOT / "scripts/reproduce_published.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_published_reconstruction_rejects_changed_headline(tmp_path: Path) -> None:
    for relative in ["outputs/tables/episode_survival.csv", "outputs/tables/ranking_churn.csv", "outputs/tables/robustness_checks.csv", "outputs/report/report_summary.json"]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    MODULE.published_figures(tmp_path)
    summary_path = tmp_path / "outputs/report/report_summary.json"
    summary = json.loads(summary_path.read_text())
    summary["ranking"]["mean_churn_by_horizon"]["30"] = .99
    summary_path.write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="Ranking headline"):
        MODULE.published_figures(tmp_path)


def test_survival_risk_and_interval_contract() -> None:
    frame = pd.read_csv(ROOT / "outputs/tables/episode_survival.csv")
    metrics, figures = MODULE.published_figures(ROOT)
    assert metrics["ci_30_lower"] < metrics["survival_30_days"] < metrics["ci_30_upper"]
    chart = figures[0][2]
    assert chart.data[2].line.shape == "hv"
    assert list(chart.data[2].customdata[:, 2]) == list(frame.at_risk)


def test_revision_has_author_tools_links_and_matching_pdf() -> None:
    folder = ROOT / "outputs/revision"
    with zipfile.ZipFile(folder / "Simone_Ragusini_945119_Stablecoin_Yield.pptx") as archive:
        slides = [n for n in archive.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
        assert len(slides) == 17
        plotly_image = (folder / "ranking_plotly.png").read_bytes()
        assert any(archive.read(name) == plotly_image for name in archive.namelist() if name.startswith("ppt/media/"))
        texts = [" ".join(ET.fromstring(archive.read(f"ppt/slides/slide{i}.xml")).itertext()) for i in range(1, 18)]
        for author_value in ["Simone Ragusini", "945119", "s.ragusini@campus.unimib.it"]:
            assert author_value in texts[0]
        assert "MATPLOTLIB" in texts[14] and "PLOTLY" in texts[14]
        assert "CC BY 4.0" in texts[15] and "MIT" in texts[15]
        rels = archive.read("ppt/slides/_rels/slide16.xml.rels").decode()
        assert "https://github.com/Laimon99/stablecoin-yield-visualization" in rels
    reader = PdfReader(folder / "Simone_Ragusini_945119_Stablecoin_Yield.pdf")
    assert len(reader.pages) == 17
    submission = ROOT / "outputs/submission/Simone_Ragusini_945119.pdf"
    assert submission.read_bytes() == (folder / "Simone_Ragusini_945119_Stablecoin_Yield.pdf").read_bytes()
    assert "Page 7" in reader.pages[14].extract_text()
    assert "s.ragusini@campus.unimib.it" in reader.pages[0].extract_text()
    assert len(PdfReader(folder / "Simone_Ragusini_945119_Report.pdf").pages) == 20
