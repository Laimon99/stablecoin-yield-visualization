.PHONY: sync test lint format verify-sources collect build-dataset quality analysis figures report presentation presentation-powerpoint-qa reproduce reproduce-sample reproduce-with-presentation clean

sync:
	uv sync --extra dev

test:
	uv run pytest

lint:
	uv run ruff check src scripts tests

format:
	uv run ruff format src scripts tests

verify-sources:
	uv run python scripts/verify_sources.py

collect:
	uv run python scripts/collect.py --mode full

build-dataset:
	uv run python scripts/build_dataset.py --mode full

quality:
	uv run python scripts/run_quality.py --mode full

analysis:
	uv run python scripts/run_analysis.py --mode full

figures:
	uv run python scripts/render_figures.py --mode full

report:
	uv run python scripts/build_report.py --mode full
	uv run python scripts/render_report_preview.py

presentation:
	uv run python scripts/build_presentation_assets.py --mode full
	node scripts/build_presentation_deck.mjs --mode full
	uv run python scripts/build_presentation_contact_sheet.py

presentation-powerpoint-qa:
	powershell -ExecutionPolicy Bypass -File scripts/render_presentation_powerpoint.ps1
	uv run python scripts/build_presentation_contact_sheet.py --preview-dir outputs/presentation/powerpoint_preview --output outputs/presentation/stablecoin_yield_presentation_powerpoint_contact_sheet.png
	uv run python scripts/render_report_preview.py --pdf outputs/presentation/stablecoin_yield_presentation.pdf --output-dir outputs/presentation/pdf_preview --contact-sheet outputs/presentation/stablecoin_yield_presentation_pdf_contact_sheet.png

reproduce:
	uv run python scripts/reproduce_all.py --mode full

reproduce-sample:
	uv run python scripts/reproduce_all.py --mode sample

reproduce-with-presentation:
	uv run python scripts/reproduce_all.py --mode full --with-presentation

clean:
	uv run python scripts/clean_outputs.py
