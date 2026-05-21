"""Command-line interface for atscale-pbi-transpile.

Skeleton — actual ingest / parse / lower / emit logic is in respective subpackages.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Output SML file path.")
@click.option(
    "--diagnostics",
    type=click.Path(path_type=Path),
    help="Path to write the diagnostics sidecar file. Defaults to <output>.diag.yaml.",
)
@click.option("--validate/--no-validate", default=True, help="Validate output against OSI schema + BFO ontology.")
def main(input_path: Path, output: Path | None, diagnostics: Path | None, validate: bool) -> int:
    """Translate a Power BI Tabular Model file (.tmdl or .bim) into SML YAML."""
    click.echo(f"[skeleton] would translate: {input_path}")
    if output:
        click.echo(f"[skeleton] would write SML to: {output}")
    if diagnostics:
        click.echo(f"[skeleton] would write diagnostics to: {diagnostics}")
    click.echo(f"[skeleton] would validate: {validate}")
    click.echo("Not yet implemented. See README.md for status.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
