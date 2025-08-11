from __future__ import annotations

import json

import typer
from src.core.validator import load_config

app = typer.Typer()


@app.command()
def show_config() -> None:
    config = load_config(file_categories=True, allowed_path=True)
    typer.echo(json.dumps(config, indent=4, ensure_ascii=False))
