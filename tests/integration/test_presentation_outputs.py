from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_DECK_SHA256 = "0fff848c31bd67fdde2f30b66c4ab60741ad663f3da45a7a8ee20ced7bdd630f"


def test_presentation_deck_and_qa_outputs_exist() -> None:
    pptx = ROOT / "outputs" / "presentation" / "stablecoin_yield_presentation.pptx"
    pdf = ROOT / "outputs" / "presentation" / "stablecoin_yield_presentation.pdf"
    cover = ROOT / "outputs" / "presentation" / "stablecoin_yield_presentation_cover.png"
    contact_sheet = (
        ROOT
        / "outputs"
        / "presentation"
        / "stablecoin_yield_presentation_powerpoint_contact_sheet.png"
    )
    assert pptx.stat().st_size > 0
    assert hashlib.sha256(pptx.read_bytes()).hexdigest() == EXPECTED_DECK_SHA256
    assert pdf.exists() and pdf.stat().st_size > 0
    assert cover.exists() and cover.stat().st_size > 0
    assert len(PdfReader(pdf).pages) == 14
    assert contact_sheet.exists()
    with zipfile.ZipFile(pptx) as archive:
        names = archive.namelist()
    assert len([name for name in names if name.startswith("ppt/slides/slide") and name.endswith(".xml")]) == 14
    assert len([name for name in names if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")]) == 14
