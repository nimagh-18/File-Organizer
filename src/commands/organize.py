from __future__ import annotations

from pathlib import Path

import typer
from src.core.operations import (
    create_dirs_and_move_files,
    load_config,
    remove_dirs,
    validate_directory_access,
)
from typing_extensions import Annotated

app = typer.Typer()


@app.command()
def organize(
    path: Annotated[str, typer.Argument(help="Path of the directory to organize")],
    include_hidden: Annotated[
        bool,
        typer.Option(
            "--include-hidden",
            help="Include hidden files (starting with '.') and system files in the organization process.",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show what actions would be taken without actually performing them. Use this to preview changes.",
        ),
    ] = False,
    force: bool = typer.Option(False, "--force", "-f", help="Bypass security checks."),
) -> None:
    """
    Organize an directory.

    :param path: Path of the directory to organize.
    """
    DIR_PATH = Path(path)

    # Pass the force flag to the validation function
    if not validate_directory_access(DIR_PATH, force):
        raise typer.Exit(code=1)

    UNCATEGORIZED_DIR = DIR_PATH.joinpath("Other")  # dir for unknown files

    if not dry_run:
        # Request to verify from user
        if not typer.confirm(
            typer.style(
                f"Are you sure you want to organize the directory '{DIR_PATH}'?",
                fg=typer.colors.YELLOW,
            )
        ):
            typer.echo(typer.style("Operation cancelled.", fg=typer.colors.RED))
            raise typer.Exit()

    file_categories = load_config()

    create_dirs_and_move_files(DIR_PATH, UNCATEGORIZED_DIR, file_categories, dry_run)
    remove_dirs(path=DIR_PATH, dry_run=dry_run)
