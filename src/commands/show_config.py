from __future__ import annotations

import json

import typer
from src.core.operations import load_config

app = typer.Typer()


@app.command()
def show_config() -> None:
    config = load_config()
    typer.echo(json.dumps(config, indent=4, ensure_ascii=False))
