from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from stablecoin_yield.source_verification import verify_sources

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def verify(root: Annotated[Path, typer.Option(help="Project root")] = Path(".")) -> None:
    results = verify_sources(root.resolve())
    for result in results:
        console.print(
            f"{result.source} {result.endpoint}: {result.status_code} "
            f"rows={result.summary.get('row_count', result.summary.get('stablecoin_count'))} "
            f"raw={result.raw_file}"
        )
