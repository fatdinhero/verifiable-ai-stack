from __future__ import annotations

import sys
from pathlib import Path

import typer
import yaml

from cognitum.cna.reporter import report_json, report_markdown
from cognitum.cna.rules import RULES

app = typer.Typer(
    name="cognitum-cna",
    help="Compliance-Normprüfung für Wärmepumpenanlagen (GEG / KfW-BEG / TA Lärm / VDI 4645)",
    add_completion=False,
)


@app.command()
def check(
    input: Path = typer.Option(..., "--input", "-i", help="Pfad zur YAML-Parameterdatei"),
    output: Path = typer.Option(
        None, "--output", "-o", help="Ausgabepfad für Markdown-Report (ohne Angabe: JSON auf stdout)"
    ),
) -> None:
    if not input.exists():
        typer.echo(f"Fehler: Datei nicht gefunden: {input}", err=True)
        raise typer.Exit(2)

    with open(input, encoding="utf-8") as fh:
        params: dict = yaml.safe_load(fh) or {}

    results = [rule.evaluate(params) for rule in RULES]
    failed = [r for r in results if not r.passed]

    if output:
        output.write_text(report_markdown(results), encoding="utf-8")
        typer.echo(f"Markdown-Report geschrieben: {output}")

    typer.echo(report_json(results))

    raise typer.Exit(1 if failed else 0)


def main() -> None:
    app()
