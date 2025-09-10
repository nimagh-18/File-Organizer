from __future__ import annotations

import subprocess
import sys
from enum import Enum
from typing import TYPE_CHECKING, Literal

import typer

from file_organizer.config.config_validator import validate_file_categories
from file_organizer.config.utils import (
    add_category_to_file_categories,
    delete_category_from_file_categories,
    edit_category_from_file_categories,
    load_config,
    show_better_file_categories,
)
from file_organizer.core.logo_manager import show_smart_logo
from file_organizer.core.utils import clearscreen

if TYPE_CHECKING:
    from pathlib import Path

    from file_organizer.config.config_type_hint import Category, SizeVariant

# --Choices options--
INTERACTIVE_CONSOLE = 1
DEFAULT_EDITOR = 2
CANCEL = 3


class UserChoice(Enum):
    LIST_CURRENT_CATEGORIES = 1
    NEW_CATEGORY = 2
    EDIT_EXISTING_CATEGORY = 3
    DELETE_CATEGORY = 4
    VALIDATE_CONFIG = 5


def welcome_message() -> None:
    """
    Clears the screen, prints a custom ASCII art logo,
    and a welcome message for the interactive config editor.
    """
    clearscreen()

    show_smart_logo()

    typer.echo(
        "\n"
        + typer.style(
            "Welcome to the interactive configuration editor. Let's make your life easier!",
            fg=typer.colors.BRIGHT_GREEN,
        )
        + "\n"
    )

    typer.echo(
        typer.style(
            "You can now manage your file categories and rules step by step.",
            fg=typer.colors.BRIGHT_GREEN,
        )
    )


def add_category(
    category_info: Category,
) -> None:
    user_confirm = typer.confirm("Are you sure of adding this category")

    if not user_confirm:
        typer.echo(typer.style("Operation canceled!!!", fg=typer.colors.RED))
        return

    add_category_to_file_categories(category_info)


def validate_config() -> None:
    """
    Validates the current configuration file categories.

    checks if the configuration is valid and raises an error if not.
    It is called when the user chooses to validate the configuration in the interactive editor.
    """
    validate_file_categories()


def delete_category(category_name: str) -> None:
    delete_category_from_file_categories(category_name)


def edit_category(category_name: str) -> None:
    edit_category_from_file_categories(category_name)


def get_valid_risk_level() -> Literal["low", "medium", "high"]:
    """Get validated risk level from user."""
    valid_choices: list[str] = ["low", "medium", "high"]
    while True:
        risk = typer.prompt(
            "Enter risk level (low/medium/high)",
            default="",
        ).lower()

        if (not risk) or risk in valid_choices:
            return risk
        typer.echo(
            typer.style("Invalid choice! Please try again.", fg=typer.colors.RED)
        )


def get_category_info() -> Category:
    category_name = typer.prompt("Enter category name", type=str)
    category_type = typer.prompt(
        "Enter category type (e.g., document, media)", type=str
    )
    category_risk = get_valid_risk_level()
    extensions_input = typer.prompt(
        "Enter file extensions (comma-separated, e.g., jpg,png,mp4)",
        type=str,
    )
    extensions_input = ["." + ext.lower() for ext in extensions_input.split(",")]

    variants: list[SizeVariant] = []
    add_variants: bool = typer.confirm(
        "Do you want to add size variants?",
        default=False,
    )
    while add_variants:
        variant_name = typer.prompt("Enter variant name")
        min_size_mb = typer.prompt("Enter minimum size in MB", default=0, type=int)
        max_size_mb = typer.prompt("Enter maximum size in MB", default=None, type=int)

        variants.append(
            {
                "name": variant_name,
                "min_size_mb": min_size_mb,
                "max_size_mb": max_size_mb,
            },
        )

        add_variants = typer.confirm(
            "Do you want to add another variant?",
            default=False,
        )

    return {
        "name": category_name,
        "type": category_type,
        "risk": category_risk,
        "extensions": extensions_input,
        "variants": variants,
    }


def interactive_config_editor() -> None:
    """Interactive config editor for file categories."""
    clearscreen()

    welcome_message()

    # Main menu
    while True:
        typer.echo("\n" + "━" * 50)
        choice = typer.prompt(
            typer.style(
                "Choose an action:\n"
                "1. List current categories\n"
                "2. Add new category\n"
                "3. Edit existing category\n"
                "4. Delete category\n"
                "5. Validate config\n"
                "6. Save and exit\n"
                "7. Exit without saving\n"
                "> ",
                fg=typer.colors.BRIGHT_YELLOW,
            ),
            type=int,
        )

        if choice == UserChoice.LIST_CURRENT_CATEGORIES.value:
            show_better_file_categories(load_config(file_categories=True))
        elif choice == UserChoice.NEW_CATEGORY.value:
            category_info = get_category_info()
            show_better_file_categories(category_info)

            add_category(category_info)
        elif choice == UserChoice.EDIT_EXISTING_CATEGORY.value:
            category_name = typer.prompt("Enter category name", type=str)
            edit_category(category_name)
        elif choice == UserChoice.DELETE_CATEGORY.value:
            category_name = typer.prompt("Enter category name", type=str)
            delete_category(category_name)
        elif choice == UserChoice.VALIDATE_CONFIG.value:
            validate_config()
        elif choice == 6:
            # if save_config():
            #     break
            pass
        elif choice == 7:
            # if confirm_exit():
            #     break
            pass
        else:
            typer.echo(typer.style("Invalid choice!", fg=typer.colors.RED))


def open_config_with_specific_editor(file_path: Path) -> None:
    """
    Opens a file using a specific text editor for each operating system.

    :param file_path: The Path object of the file you want to open.
    """
    if sys.platform == "win32":
        # On Windows, `start` or the file itself opens it with the default app
        command = ["start", str(file_path)]
    elif sys.platform == "darwin":  # macOS
        command = ["open", "-a", "TextEdit", str(file_path)]
    elif sys.platform.startswith("linux"):
        command = ["xdg-open", str(file_path)]  # A standard way to open files
    else:
        typer.echo(f"Unsupported operating system: {sys.platform}")
        return

    try:
        # We use `shell=True` for `start` on Windows but avoid it for others
        is_shell = sys.platform == "win32"
        subprocess.run(command, check=True, shell=is_shell)
    except FileNotFoundError:
        typer.echo(f"Error: Could not find a suitable application to open {file_path}")
    except subprocess.CalledProcessError as e:
        typer.echo(f"An error occurred while opening the file: {e}")


def get_user_choice(file_categories_path: Path) -> None:
    """
    Asks the user to choose between an interactive console or a
    default editor to edit the configuration file.
    """
    typer.echo("How would you like to edit the configuration file?")
    typer.echo("1. Use interactive console (safer)")
    typer.echo("2. Open with default editor (for advanced users)")
    typer.echo("3. Cancel")

    # Get user's choice
    choice = typer.prompt("Enter your choice", default=INTERACTIVE_CONSOLE, type=int)

    if choice == INTERACTIVE_CONSOLE:
        # Call the function for the interactive console
        typer.echo("Launching interactive console...")

        interactive_config_editor()
    elif choice == DEFAULT_EDITOR:
        # Call the function for opening the default editor
        typer.echo("Opening config file with default editor...")

        open_config_with_specific_editor(file_categories_path)
    elif choice == CANCEL:
        typer.echo("Operation canceled.")
        raise typer.Exit()
    else:
        typer.echo("Invalid choice. Please enter 1, 2, or 3.")
