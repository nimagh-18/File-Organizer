from __future__ import annotations

import locale
import os
import sys
from functools import lru_cache

import typer


@lru_cache(maxsize=1)
def check_terminal_capabilities() -> tuple[bool, bool, int]:
    """
    Check the capabilities of the user's terminal.

    Performs three checks:
    1. Unicode support (stdout encoding or preferred locale)
    2. Color support (including Windows-specific handling)
    3. Terminal width

    :return: Tuple with:
        - bool: Unicode support
        - bool: Color support
        - int: Terminal width in columns
    """
    # Check Unicode support
    encoding = (sys.stdout.encoding or "").lower()
    if not encoding:
        encoding = locale.getpreferredencoding(False).lower()
    supports_unicode = encoding.startswith("utf")

    # Check color support
    supports_colors = False
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        if sys.platform != "win32":
            supports_colors = True
        else:
            try:
                from colorama import just_fix_windows_console

                just_fix_windows_console()
                supports_colors = True
            except ImportError:
                pass

    # Get terminal width
    try:
        terminal_width = os.get_terminal_size().columns
    except (AttributeError, OSError):
        terminal_width = 80

    return supports_unicode, supports_colors, terminal_width


def get_smart_logo() -> str:
    """
    Get an adaptive logo string based on terminal capabilities.

    Returns one of:
    - Compact one-line logo (width < 50)
    - Full Unicode logo
    - ASCII fallback logo
    """
    unicode_support, _, width = check_terminal_capabilities()

    if width < 50:
        return "📁 FILE ORGANIZER 📂" if unicode_support else "[FILE ORGANIZER]"

    if unicode_support:
        return (
            "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃  🗂️   FILE ORGANIZER MANAGER   🗃️    ┃\n"
            "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
            "┃                                    ┃\n"
            "┃   ░█▀▀░█░░░█▀█░█▀▀░▀█▀░█▀▀░█▀▄     ┃\n"
            "┃   ░█▀▀░█░░░█▀█░▀▀█░░█░░█▀▀░█▀▄     ┃\n"
            "┃   ░▀▀▀░▀▀▀░▀░▀░▀▀▀░░▀░░▀▀▀░▀░▀     ┃\n"
            "┃                                    ┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
        )

    return (
        "+--------------------------------------+\n"
        "|       FILE ORGANIZER MANAGER         |\n"
        "+--------------------------------------+\n"
        "|      _____ _   _  ___  _____  __     |\n"
        "|     |  ___| \\ | |/ _ \\/ _ \\ \\/ /     |\n"
        "|     | |_  |  \\| | | | | | | \\  /     |\n"
        "|     |  _| | |\\  | |_| | |_| /  \\     |\n"
        "|     |_|   |_| \\_|\\___/ \\___/_/\\_\\    |\n"
        "|                                      |\n"
        "+--------------------------------------+"
    )


def show_smart_logo() -> None:
    """Print the smart logo with color if supported."""
    _, color_support, _ = check_terminal_capabilities()
    logo = get_smart_logo()

    if color_support:
        try:
            from typer import colors, style

            typer.echo(style(logo, fg=colors.BRIGHT_CYAN))
            return
        except ImportError:
            pass

    typer.echo(logo)
