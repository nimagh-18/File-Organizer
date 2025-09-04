from __future__ import annotations

import os
import shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import typer
import yaml
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from src.config.read_config import read_config

if TYPE_CHECKING:
    from src.config.config_type_hint import (
        Category,
        DefaultPaths,
        FileAndPathConfig,
        FileCategories,
    )


console = Console()


def add_category_to_file_categories(
    category: Category,
    config_path: Path = Path("src/config/file_categories.yaml"),
) -> None:
    """
    Add a new category to the file categories YAML configuration.

    Args:
        category: The category dictionary to add
        config_path: Path to the YAML config file

    Raises:
        typer.Exit: If there's an error reading or writing the file

    Example:
        >>> new_category = {
        ...     "name": "Videos",
        ...     "extensions": [".mp4", ".avi"],
        ...     "type": "media",
        ...     "risk": "low"
        ... }
        >>> add_category_to_file_categories(new_category)

    """
    try:
        # Read existing config
        file_categories = read_config(config_path, optimization=False)

        # Initialize categories list if not exists
        file_categories.setdefault("categories", [])

        # Check for duplicate category names
        if any(
            cat.get("name") == category.get("name")
            for cat in file_categories["categories"]
        ):
            typer.echo(
                typer.style(
                    f"Category '{category.get('name')}' already exists!",
                    fg=typer.colors.YELLOW,
                )
            )
            if not typer.confirm("Overwrite existing category?"):
                raise typer.Abort()

            # Remove existing category
            file_categories["categories"] = [
                cat
                for cat in file_categories["categories"]
                if cat.get("name") != category.get("name")
            ]

        # Add new category
        file_categories["categories"].append(category)

        # Write back to file
        with open(config_path, "w", encoding="utf-8") as file:
            yaml.safe_dump(
                file_categories,
                file,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2,
            )

        typer.echo(
            typer.style(
                f"Successfully added category: {category.get('name')}",
                fg=typer.colors.GREEN,
            )
        )

    except yaml.YAMLError as e:
        typer.echo(typer.style(f"Error writing YAML file: {e}", fg=typer.colors.RED))
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(typer.style(f"Unexpected error: {e}", fg=typer.colors.RED))
        raise typer.Exit(1)


def backup_config(config_path: Path) -> Path:
    backup_file = config_path.with_name(
        f"{config_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{config_path.suffix}"
    )
    shutil.copy2(config_path, backup_file)
    return backup_file


def delete_category_from_file_categories(
    category_name: str,
    config_path: Path = Path("src/config/file_categories.yaml"),
) -> None:
    """
    Delete a category from the file categories YAML configuration.

    Args:
        category_name: Name of the category to delete
        config_path: Path to the YAML config file

    Raises:
        typer.Exit: If there's an error reading or writing the file

    Example:
        >>> delete_category_from_file_categories("Videos")
    """
    try:
        # Read existing config
        file_categories = read_config(config_path, optimization=False)

        # Check if category exists
        if not any(
            cat.get("name") == category_name
            for cat in file_categories.get("categories", [])
        ):
            typer.echo(
                typer.style(
                    f"Category '{category_name}' not found!", fg=typer.colors.YELLOW
                )
            )
            return

        # Confirm deletion
        if not typer.confirm(
            f"Are you sure you want to delete category '{category_name}'?"
        ):
            raise typer.Abort()

        # Create backup
        backup_file = backup_config(config_path)
        typer.echo(
            typer.style(f"Backup created at: {backup_file}", fg=typer.colors.BLUE)
        )

        # Delete category
        file_categories["categories"] = [
            cat
            for cat in file_categories["categories"]
            if cat.get("name") != category_name
        ]

        # Write back to file
        with open(config_path, "w", encoding="utf-8") as file:
            yaml.safe_dump(
                file_categories,
                file,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2,
            )

        typer.echo(
            typer.style(
                f"Successfully deleted category: {category_name}",
                fg=typer.colors.GREEN,
            )
        )

    except yaml.YAMLError as e:
        typer.echo(
            typer.style(
                f"Error writing YAML file: {e}",
                fg=typer.colors.RED,
            )
        )
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(
            typer.style(
                f"Unexpected error: {e}",
                fg=typer.colors.RED,
            )
        )
        raise typer.Exit(1)


def edit_category_from_file_categories(
    category_name: str,
    config_path: Path = Path("src/config/file_categories.yaml"),
) -> None:
    """
    Edit a specific category from the file categories configuration.

    This is the main entry point for editing a category. It:
    - Loads configuration from a YAML file
    - Prompts the user for basic category changes
    - Optionally edits size variants
    - Shows a colored diff of changes before saving
    - Writes updated configuration back to the YAML file

    :param category_name: The name of the category to edit.
    :type category_name: str
    :param config_path: Path to the YAML configuration file.
    :type config_path: Path
    """
    file_categories = read_config(config_path, optimization=False)

    if "categories" not in file_categories:
        typer.secho("Missing required 'categories' key", fg=typer.colors.RED)
        return

    category_index = next(
        (
            i
            for i, cat in enumerate(file_categories["categories"])
            if cat.get("name") == category_name
        ),
        None,
    )
    if category_index is None:
        typer.secho(f"Category '{category_name}' not found.", fg=typer.colors.YELLOW)
        return

    original_category = deepcopy(file_categories["categories"][category_index])
    updated_category = deepcopy(original_category)

    try:
        _prompt_basic_category_info(updated_category)
    except ValueError:
        return

    _edit_category_variants(updated_category)

    _show_changes_diff_tree(original_category, updated_category)

    if not typer.confirm("\nAre you sure to apply this change?"):
        typer.secho("Operation Canceled.", fg=typer.colors.RED)
        return

    file_categories["categories"][category_index] = updated_category
    with open(config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(
            file_categories,
            file,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
        )

    typer.secho(
        f"Successfully edited category: {updated_category['name']}",
        fg=typer.colors.GREEN,
    )


def _prompt_basic_category_info(category: Category) -> None:
    """
    Prompt the user to update basic category fields.

    This includes:
    - Name
    - Type
    - Extensions
    - Risk level

    :param category: The category dictionary to modify.
    :type category: Dict[str, Any]
    """
    category["name"] = typer.prompt("Enter new name", default=category.get("name"))
    category["type"] = typer.prompt("Enter new type", default=category.get("type"))

    exts_input = typer.prompt(
        "Enter new extensions (comma-separated)",
        default=",".join(category.get("extensions", [])),
    )

    category["extensions"] = [
        ext.strip() if ext.startswith(".") else f".{ext.strip()}"
        for ext in exts_input.split(",")
        if ext.strip()
    ]

    risk_input = typer.prompt(
        "Enter new risk level (low, medium, high)",
        default=category.get("risk", "low"),
    )
    if risk_input not in ("low", "medium", "high"):
        typer.secho(
            "Invalid risk level! Must be: low, medium, or high.",
            fg=typer.colors.RED,
        )
        raise ValueError
    category["risk"] = risk_input


def _edit_category_variants(category: Category) -> None:
    """
    Edit or create variants for the category.

    Allows the user to:
    - Add new variants
    - Edit existing variants
    - Delete variants
    - Create variants if none exist

    :param category: The category dictionary to modify.
    :type category: Dict[str, Any]
    """
    if "variants" not in category or not isinstance(category["variants"], list):
        if typer.confirm("This category has no variants. Do you want to add variants?"):
            category["variants"] = []
        else:
            return

    while True:
        typer.secho("\nCurrent Variants:", fg=typer.colors.MAGENTA, bold=True)
        if category["variants"]:
            for idx, var in enumerate(category["variants"], start=1):
                max_size = (
                    "∞"
                    if var.get("max_size_mb") == float("inf")
                    else var.get("max_size_mb", "∞")
                )
                typer.echo(
                    f"  {idx}. {var['name']} ({var.get('min_size_mb', 0)}MB - {max_size}MB)"
                )
        else:
            typer.echo("  (No variants defined)")

        action = typer.prompt(
            "Choose action: [e]dit / [a]dd / [d]elete / [q]uit",
            default="q",
        ).lower()

        if action == "e":
            if not category["variants"]:
                typer.secho("No variants to edit.", fg=typer.colors.RED)
                continue
            idx = typer.prompt("Enter variant number to edit", type=int)
            if 1 <= idx <= len(category["variants"]):
                var = category["variants"][idx - 1]
                var["name"] = typer.prompt("  New name", default=var["name"])
                var["min_size_mb"] = typer.prompt(
                    "  New min size (MB)", default=var.get("min_size_mb", 0), type=int
                )
                var["max_size_mb"] = typer.prompt(
                    "  New max size (MB, use -1 for ∞)",
                    default=var.get("max_size_mb", -1),
                    type=int,
                )
                if var["max_size_mb"] == -1:
                    var["max_size_mb"] = float("inf")
        elif action == "a":
            name = typer.prompt("  Variant name")
            min_size = typer.prompt("  Min size (MB)", type=int)
            max_size = typer.prompt(
                "  Max size (MB, use -1 for ∞)", default=-1, type=int
            )
            if max_size == -1:
                max_size = float("inf")
            category["variants"].append(
                {"name": name, "min_size_mb": min_size, "max_size_mb": max_size},
            )
        elif action == "d":
            if not category["variants"]:
                typer.secho("No variants to delete.", fg=typer.colors.RED)
                continue
            idx = typer.prompt("Enter variant number to delete", type=int)
            if 1 <= idx <= len(category["variants"]):
                deleted = category["variants"].pop(idx - 1)
                typer.secho(
                    f"Deleted variant: {deleted['name']}",
                    fg=typer.colors.YELLOW,
                )
        elif action == "q":
            break
        else:
            typer.secho("Invalid option!", fg=typer.colors.RED)


def _show_changes_diff_tree(
    old: Category,
    new: Category,
    title: str = "Changes Preview",
) -> None:
    """
    Show a color-coded tree diff between the old and new category configuration.

    This function recursively traverses the dictionaries and highlights:
    - Added/changed values in green
    - Removed values in red
    - Unchanged values in white

    Works with nested structures like lists and dictionaries.

    :param old: Original category dictionary.
    :type old: dict
    :param new: Updated category dictionary.
    :type new: dict
    :param title: Title for the tree view.
    :type title: str
    """
    console = Console()
    tree = Tree(Text(title, style="bold cyan"))

    def add_diff_nodes(
        parent: Tree, old_val: Category, new_val: Category, key_path: str
    ):
        """Recursively add diff nodes to the tree."""
        if isinstance(old_val, dict) and isinstance(new_val, dict):
            branch = parent.add(Text(f"{key_path} (dict)", style="bold magenta"))
            all_keys = set(old_val.keys()) | set(new_val.keys())
            for k in sorted(all_keys):
                add_diff_nodes(branch, old_val.get(k), new_val.get(k), k)
        elif isinstance(old_val, list) and isinstance(new_val, list):
            branch = parent.add(Text(f"{key_path} (list)", style="bold magenta"))
            max_len = max(len(old_val), len(new_val))
            for i in range(max_len):
                o_item = old_val[i] if i < len(old_val) else None
                n_item = new_val[i] if i < len(new_val) else None
                add_diff_nodes(branch, o_item, n_item, f"[{i}]")
        else:
            if old_val == new_val:
                parent.add(Text(f"{key_path}: {old_val}", style="white"))
            else:
                if old_val is not None:
                    parent.add(Text(f"- {key_path}: {old_val}", style="red"))
                if new_val is not None:
                    parent.add(Text(f"+ {key_path}: {new_val}", style="green"))

    add_diff_nodes(tree, old, new, "root")
    console.print(tree)


def load_config(
    *, file_categories: bool = True, allowed_paths: bool = False
) -> FileCategories | DefaultPaths | FileAndPathConfig:
    """
    Load specific or combined configurations from YAML files.

    :raises typer.Exit: If no parameters are set.
    :returns: A dictionary representing the loaded configuration.
    """
    loaded_configs = {}
    if file_categories:
        loaded_configs["file_categories"] = read_config(
            Path("src/config/file_categories.yaml")
        )

    if allowed_paths:
        loaded_configs["allowed_paths"] = read_config(
            Path("src/config/allowed_path.yaml")
        )

    if not loaded_configs:
        typer.echo(
            typer.style(
                "Nothing to load, please set at least one of the parameters: "
                "file_categories or allowed_paths.",
                fg=typer.colors.RED,
            )
        )
        raise typer.Exit(1)

    # If only one type of config is requested, return it directly
    if len(loaded_configs) == 1:
        return next(iter(loaded_configs.values()))

    # If both are requested, return a combined dictionary
    return loaded_configs


def show_better_file_categories(file_categories: FileCategories | Category) -> None:
    """
    Display file categories in a beautifully formatted, color-coded layout.

    Features:
    - Different colors for labels and values
    - Handles missing extensions
    - Shows risk level if available
    - Adaptive terminal width
    - Fallback to simple display if Rich is not available

    :param file_categories: Configuration dictionary containing file categories
    :type file_categories: Dict
    """
    try:
        # Try using Rich for beautiful tables
        console = Console()
        if os.get_terminal_size().columns >= 80:
            _display_with_rich(console, file_categories)
            return
    except:
        pass

    # Fallback to Typer-based display
    _display_with_typer(file_categories)


def _display_with_rich(console: Console, file_categories: FileCategories) -> None:
    """Display categories using Rich library for beautiful tables."""
    table = Table(
        title="File Categories Configuration",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Property", style="cyan", width=25)
    table.add_column("Value", style="white")

    # This mode occurs when the category is in interactive mode and when the user has selected the category
    if "defaults" not in file_categories and "categories" not in file_categories:
        file_categories = {
            "categories": [file_categories],
        }
    else:
        # Add defaults
        defaults = file_categories.get("defaults", {})
        table.add_row("Default Category", defaults.get("name", "Not specified"))

    # Add each category
    for index, category in enumerate(file_categories.get("categories", [])):
        table.add_row("", "")  # Empty row as separator

        # Category name row
        table.add_row(
            f"[bold]{index}.Category:[/bold]",
            f"[bold white]{category.get('name', 'Unnamed')}[/bold white]",
            style="BRIGHT_CYAN",
        )

        # Extensions
        exts = category.get("extensions", [])
        table.add_row(
            "    Extensions",
            ", ".join(exts) if exts else "[italic]No extensions[/italic]",
        )

        # Type and Risk
        table.add_row("    Type", category.get("type", "N/A"))
        table.add_row("    Risk", category.get("risk", "N/A"))

        # Variants
        if "variants" in category:
            for variant in category["variants"]:
                min_size = variant.get("min_size_mb", 0)
                max_size = variant.get("max_size_mb", "∞")
                table.add_row(
                    f"    Variant: {variant.get('name', '')}",
                    f"Size: {min_size}MB - {max_size}MB",
                )
        else:
            # Regular size constraints
            min_size = category.get("min_size_mb", 0)
            max_size = category.get("max_size_mb", "∞")
            if min_size or max_size != "∞":
                table.add_row("  Size Range", f"{min_size}MB - {max_size}MB")

    console.print(table)


def _display_with_typer(file_categories: FileCategories) -> None:
    """Fallback display using Typer when Rich is not available."""
    # Adaptive separator based on terminal width
    try:
        separator = "-" * min(80, os.get_terminal_size().columns)
    except:
        separator = "-" * 60

    # This mode occurs when the category is in interactive mode and when the user has selected the category
    if "defaults" not in file_categories and "categories" not in file_categories:
        file_categories = {
            "categories": [file_categories],
        }
    else:
        # Display defaults
        defaults = file_categories.get("defaults", {})
        typer.echo(
            typer.style("Defaults:", fg=typer.colors.BRIGHT_BLUE)
            + typer.style(
                f" {defaults.get('name', 'Not specified')}", fg=typer.colors.WHITE
            )
        )

    typer.echo(separator)

    # Display each category
    for index, category in enumerate(file_categories.get("categories", [])):
        # Category name
        typer.echo(
            typer.style(f"{index}.Category:", fg=typer.colors.BRIGHT_BLUE)
            + typer.style(f" {category.get('name', 'Unnamed')}", fg=typer.colors.WHITE)
        )

        # Extensions
        exts = category.get("extensions", [])
        typer.echo(
            typer.style("  Extensions:", fg=typer.colors.BRIGHT_BLUE)
            + typer.style(
                f" {', '.join(exts) if exts else 'No extensions'}",
                fg=typer.colors.WHITE,
            )
        )

        # Type and Risk
        typer.echo(
            typer.style("  Type:", fg=typer.colors.BRIGHT_BLUE)
            + typer.style(f" {category.get('type', 'N/A')}", fg=typer.colors.WHITE)
        )
        typer.echo(
            typer.style("  Risk:", fg=typer.colors.BRIGHT_BLUE)
            + typer.style(f" {category.get('risk', 'N/A')}", fg=typer.colors.WHITE)
        )

        # Variants or size constraints
        if "variants" in category:
            for variant in category["variants"]:
                min_size = variant.get("min_size_mb", 0)
                max_size = variant.get("max_size_mb", "∞")
                typer.echo(
                    typer.style(
                        f"  Variant: {variant.get('name', '')}",
                        fg=typer.colors.BRIGHT_BLUE,
                    )
                    + typer.style(
                        f" Size: {min_size}MB - {max_size}MB", fg=typer.colors.WHITE
                    )
                )
        else:
            min_size = category.get("min_size_mb", 0)
            max_size = category.get("max_size_mb", "∞")
            if min_size or max_size != "∞":
                typer.echo(
                    typer.style("  Size Range:", fg=typer.colors.BRIGHT_BLUE)
                    + typer.style(
                        f" {min_size}MB - {max_size}MB", fg=typer.colors.WHITE
                    )
                )

        typer.echo(separator)
