from __future__ import annotations

from pathlib import Path

import typer
from file_organizer.config.config_editor import get_user_choice
from file_organizer.config.file_allowed_logs_config_path import file_categories_path

app = typer.Typer()


@app.command()
def edit_config() -> None:
    """Open the config.json file in a text editor."""
    get_user_choice(file_categories_path)
