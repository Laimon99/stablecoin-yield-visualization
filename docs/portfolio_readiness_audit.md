# Public Portfolio Readiness Audit

Audit date: 2026-08-30.

## Release Criteria

| Criterion | Public-release evidence | Status |
| --- | --- | --- |
| Project is the repository focus | Project promoted to repository root; unrelated course files and example submissions removed | Complete |
| Clear portfolio narrative | Root README states the question, findings, method, deliverables and limitations | Complete |
| Exam presentation preserved | SHA-256 integrity record and independent local backup | Complete |
| No secrets | `.env` ignored; API credentials sent as headers; persisted request metadata redacts sensitive parameters | Complete |
| Portable paths | Report and summary use repository-relative paths | Complete |
| Third-party data handled responsibly | Raw responses and row-level datasets excluded; provider terms and attribution documented | Complete |
| Repository size is reasonable | Large raw/processed/analytical files and duplicate previews excluded from public history | Complete |
| Reproducible code | Locked Python environment, staged scripts, configuration and documented live-data commands | Complete |
| Portable core pipeline | Report pipeline is independent of the optional Codex-only PowerPoint builder | Complete |
| Automated quality gates | GitHub Actions runs locked install, Ruff and Pytest on `main` | Complete |
| Generated artifacts are curated | Final figures, aggregate tables, report and exam deck retained; intermediate previews removed | Complete |
| Public history is curated | `main` rebuilt as a clean portfolio release; non-main branches removed locally and remotely | Complete |

## Scope Boundary

The frozen report and presentation summarize the audited 2026-07-08 analysis. The public
repository reproduces the method against live provider data but does not promise byte-identical
reconstruction of the private historical raw snapshot. This boundary is necessary because the
providers' current terms restrict redistribution of raw data.

## Final Verification Commands

```bash
uv sync --frozen --extra dev
uv run ruff check src scripts tests
uv run pytest
```

Release verification additionally checks the PowerPoint SHA-256, PDF rendering, absence of
absolute local paths, branch topology, remote commit identity and maximum tracked file size.
