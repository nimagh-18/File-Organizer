from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

import typer
from loguru import logger

from file_organizer.config.utils import load_config
from file_organizer.core.constants import SystemProtector

if TYPE_CHECKING:
    from pathlib import Path

from pathlib import Path

from rich.console import Console


def validate_directory_access(path: Path, force: bool) -> bool:
    """Validate directory is safe and accessible."""
    # Load config and instantiate protector (this should be done once)
    config = load_config(file_categories=False, allowed_paths=True)
    protector = SystemProtector(config)

    # Check for force flag first
    if force:
        logger.warning(
            f"Bypassing security checks for path '{path}' due to --force flag.",
        )
        return True

    if not path.exists():
        typer.echo(
            typer.style(
                f"Error: The path '{path}' does not exist.",
                fg=typer.colors.RED,
            )
        )
        return False

    if not path.is_dir():
        typer.echo(
            typer.style(
                f"Error: The path '{path}' is not a directory.",
                fg=typer.colors.RED,
            )
        )
        return False

    if not os.access(path, os.R_OK | os.W_OK):
        typer.echo(
            typer.style(
                f"Error: Insufficient permissions to read/write in '{path}'.",
                fg=typer.colors.RED,
            )
        )
        return False

    # Use the new is_allowed method
    if not protector.is_allowed(path):
        typer.echo(
            typer.style(
                f"Error: The path '{path}' is not an allowed directory. "
                "Use --force to override this check.",
                fg=typer.colors.RED,
            )
        )
        return False

    return True


def validate_glob_pattern(pattern: str) -> bool:
    """
    Validate glob pattern syntax for use with pathlib.glob/rglob.

    Performs comprehensive validation of glob patterns including syntax checking,
    practical warnings for potentially unintended patterns, and confirmation
    for edge cases.

    :param pattern: Glob pattern to validate (e.g., "*.txt", "*.{jpg,png}").
    :type pattern: str
    :return: True if the pattern has valid glob syntax and user confirms
             any warnings, False otherwise.
    :rtype: bool
    :raises typer.Exit: If the pattern syntax is invalid or user cancels operation.

    Example:
        >>> validate_glob_pattern("*.txt")
        True
        >>> validate_glob_pattern("[invalid")  # Unclosed bracket
        # Prints error message and raises typer.Exit

    """
    console = Console()

    # Phase 1: Basic input validation
    if not _validate_input(pattern, console):
        return False

    # Phase 2: Syntax structure validation
    if not _validate_syntax_structure(pattern, console):
        return False

    # Phase 3: Practical usage warnings
    if not _check_practical_issues(pattern, console):
        return False

    # Phase 4: Final validation with pathlib engine
    return _validate_with_pathlib_engine(pattern, console)


def _validate_input(pattern: str, console: Console) -> bool:
    """
    Validate basic input requirements for the glob pattern.

    Checks for non-empty pattern and basic format requirements.

    :param pattern: Glob pattern to validate.
    :type pattern: str
    :param console: Rich console instance for output.
    :type console: Console
    :return: True if input requirements are met, False otherwise.
    :rtype: bool
    :raises typer.Exit: For empty or whitespace-only patterns.

    Example:
        >>> _validate_input("*.txt", console)
        True
        >>> _validate_input("   ", console)  # Raises Exit

    """
    if not pattern or not pattern.strip():
        console.print("[red]Error: Pattern cannot be empty[/red]")
        raise typer.Exit(1)

    if pattern.strip() == "*":
        console.print("[yellow]Warning: Pattern '*' will match all files[/yellow]")
        return True

    return True


def _validate_syntax_structure(pattern: str, console: Console) -> bool:
    """
    Validate syntactic structure of the glob pattern.

    Checks for balanced brackets, braces, and proper wildcard usage.

    :param pattern: Glob pattern to validate.
    :type pattern: str
    :param console: Rich console instance for output.
    :type console: Console
    :return: True if syntax structure is valid, False otherwise.
    :raises typer.Exit: For syntax errors with detailed examples.
    """
    # Check for unbalanced brackets
    if pattern.count("[") != pattern.count("]"):
        console.print("[red]Error: Unbalanced square brackets[/red]")
        console.print("[yellow]Valid bracket examples:[/yellow]")
        console.print("[yellow]  '[abc]'    - matches a, b, or c[/yellow]")
        console.print(
            "[yellow]  'file[0-9].txt' - matches file0.txt to file9.txt[/yellow]"
        )
        console.print("[yellow]  'image[!0-9].jpg' - excludes digits[/yellow]")
        raise typer.Exit(1)

    # Check for unbalanced braces
    if pattern.count("{") != pattern.count("}"):
        console.print("[red]Error: Unbalanced curly braces[/red]")
        console.print("[yellow]Valid brace examples:[/yellow]")
        console.print("[yellow]  '*.{jpg,png}' - matches jpg or png files[/yellow]")
        console.print(
            "[yellow]  'file{1..3}.txt' - matches file1.txt to file3.txt[/yellow]"
        )
        raise typer.Exit(1)

    # Check for invalid recursive wildcard usage
    if "**" in pattern and not (
        pattern.startswith("**") or "/**" in pattern or pattern.endswith("/**")
    ):
        console.print("[red]Error: Invalid recursive wildcard '**' usage[/red]")
        console.print("[yellow]Valid recursive patterns:[/yellow]")
        console.print("[yellow]  '**/*.txt' - all txt files recursively[/yellow]")
        console.print("[yellow]  'docs/**' - all files in docs/ recursively[/yellow]")
        console.print(
            "[yellow]  'images/**/*.jpg' - jpg files in images/ subdirs[/yellow]",
        )
        raise typer.Exit(1)
    return True


def _check_practical_issues(pattern: str, console: Console) -> bool:
    """
    Check for practically problematic but syntactically valid patterns.

    Identifies patterns that may not behave as users expect and seeks
    confirmation before proceeding.

    :param pattern: Glob pattern to validate.
    :type pattern: str
    :param console: Rich console instance for output.
    :type console: Console
    :return: True if user confirms to proceed with warnings, False otherwise.
    :rtype: bool
    :raises typer.Exit: If user chooses to cancel after warnings.

    Example:
        >>> _check_practical_issues("[*]", console)  # Shows warning
        # Prompts user for confirmation

    """
    # Check for literal bracket patterns that might be unintended
    if ("[*]" in pattern or "[?]" in pattern) and not _is_likely_intentional(pattern):
        console.print("[yellow]Warning: Literal bracket pattern detected[/yellow]")
        console.print("[yellow]  '[.*]' matches literal dots/stars, not wildcards")
        console.print(
            "[yellow]  Did you mean '*' for wildcard or '?' for single char?[/yellow]",
        )
        if not typer.confirm("Continue with literal pattern?"):
            raise typer.Exit(1)

    # Check for redundant path separators
    if "//" in pattern.replace("://", ""):  # Ignore protocol separators
        console.print("[yellow]Warning: Double slashes in pattern[/yellow]")
        console.print("[yellow]  '//' is redundant in glob patterns[/yellow]")
        if not typer.confirm("Continue with redundant slashes?"):
            raise typer.Exit(1)

    # Check for backslashes (might be Windows path confusion)
    if "\\" in pattern and "/" not in pattern:
        console.print("[yellow]Warning: Backslashes in pattern[/yellow]")
        console.print("[yellow]  Use '/' for path separation in glob patterns[/yellow]")
        console.print("[yellow]  '\\' is treated as literal character[/yellow]")
        if not typer.confirm("Continue with backslashes?"):
            raise typer.Exit(1)

    return True


def _is_likely_intentional(pattern: str) -> bool:
    """
    Determine if a bracket pattern is likely intentional.

    Some patterns with brackets might actually be intended as literals.

    :param pattern: Glob pattern to check.
    :type pattern: str
    :return: True if pattern appears intentionally literal, False otherwise.
    :rtype: bool

    Example:
        >>> _is_likely_intentional("[[*]]")  # Double brackets suggest intent
        True
        >>> _is_likely_intentional("[*]")    # Single brackets might be mistake
        False

    """
    # Patterns that suggest intentional literal usage
    intentional_indicators = [
        pattern.count("[") > 1,  # Multiple opening brackets
        pattern.count("]") > 1,  # Multiple closing brackets
        "[[]" in pattern,  # Escaped-like brackets
        "[]]" in pattern,  # Escaped-like brackets
        pattern.startswith("[["),  # Double opening
        pattern.endswith("]]"),  # Double closing
    ]

    return any(intentional_indicators)


def _validate_with_pathlib_engine(pattern: str, console: Console) -> bool:
    """
    Final validation using pathlib's pattern matching engine.

    Uses pathlib's internal parser to catch edge cases and truly
    invalid patterns.

    :param pattern: Glob pattern to validate.
    :type pattern: str
    :param console: Rich console instance for output.
    :type console: Console
    :return: True if pattern is valid by pathlib standards, False otherwise.
    :rtype: bool
    :raises typer.Exit: For patterns rejected by pathlib with examples.

    Example:
        >>> _validate_with_pathlib_engine("*.txt", console)
        True
        >>> _validate_with_pathlib_engine("invalid[", console)  # Might be valid
        True  # pathlib accepts this as literal

    """
    try:
        # Use pathlib's match method for final validation
        test_path = Path("test_file.txt")
        test_path.match(pattern)

    except (ValueError, re.error) as e:
        # Patterns that pathlib genuinely rejects
        console.print(f"[red]Error: Invalid pattern syntax: {str(e)}[/red]")
        console.print("[yellow]Valid pattern examples:")
        console.print("[yellow]  '*.txt'           - all text files[/yellow]")
        console.print("[yellow]  '*.{jpg,png}'     - jpg or png files[/yellow]")
        console.print("[yellow]  'file[0-9].txt'   - numbered files[/yellow]")
        console.print("[yellow]  '**/*.py'         - Python files recursively[/yellow]")
        console.print("[yellow]  'image?.jpg'      - single char wildcard[/yellow]")
        raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Unexpected validation error: {str(e)}[/red]")
        raise typer.Exit(1)
    else:
        return True
