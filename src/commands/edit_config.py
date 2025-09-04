from __future__ import annotations

from pathlib import Path

import typer
from src.config.config_editor import get_user_choice

app = typer.Typer()


@app.command()
def edit_config() -> None:
    """Open the config.json file in a text editor."""
    get_user_choice(Path("src/config/file_categories.yaml"))
