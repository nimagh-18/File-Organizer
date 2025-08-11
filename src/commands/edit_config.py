from __future__ import annotations

from pathlib import Path

import typer
from src.config.utils import open_config_with_specific_editor

app = typer.Typer()


@app.command()
def edit_config() -> None:
    """Open the config.json file in a text editor."""
    open_config_with_specific_editor(Path("config.json"))
