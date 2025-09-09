from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text
from src.config.config_type_hint import FileCategories


class BeautifulDisplayAndProgress:
    """
    A utility class for displaying progress and results with Rich.

    This class provides methods to:
    - Display advanced progress bars.
    - Show real-time file processing information.
    - Display organization statistics.
    - Show final results, errors, warnings, and success messages.

    If ``total_files`` is not provided during initialization, the class
    will start from 0 and automatically increment the count each time
    a file is processed.
    """

    def __init__(self, total_files: Optional[int] = None) -> None:
        """
        Initialize the display utility.

        :param total_files: Total number of files to process.
                            If None, starts from 0 and increments automatically.
        :type total_files: int | None
        """
        self.console = Console()
        self._total_files = total_files if total_files is not None else 0
        self._auto_counting = total_files is None

    @staticmethod
    def create_advanced_progress() -> Progress:
        """
        Create an advanced progress display with Rich components.

        :return: Configured Progress instance
        :rtype: Progress
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            TextColumn("•"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            expand=True,
            console=Console(),
        )

    def display_file_info(
        self,
        progress: Progress,
        task_id: int,
        file_path: Path,
        action: str,
        max_filename_length: int = 35,
    ) -> None:
        """
        Display real-time information about the currently processed file.

        :param progress: Progress instance to update
        :type progress: Progress
        :param task_id: ID of the progress task
        :type task_id: int
        :param file_path: Path of the file being processed
        :type file_path: Path
        :param action: Action being performed on the file
        :type action: str
        :param max_filename_length: Maximum length for filename display
        :type max_filename_length: int
        """
        # Format filename with truncation if needed
        filename = file_path.name
        if len(filename) > max_filename_length:
            filename = filename[: max_filename_length - 3] + "..."

        # Calculate file size in KB
        file_size_kb = file_path.stat().st_size / 1024

        # Build styled description text
        description_text = Text()
        description_text.append("Processing: ", style="cyan")
        description_text.append(filename, style="bold")
        description_text.append(f" ({file_path.suffix})", style="dim")
        description_text.append(" • Action: ", style="green")
        description_text.append(action)
        description_text.append(" • Size: ", style="yellow")
        description_text.append(f"{file_size_kb:.1f}KB")

        # Update progress description
        progress.update(task_id, description=description_text)

        # If auto-counting is enabled, increment total files
        if self._auto_counting:
            self._total_files += 1

    def display_organization_stats(
        self,
        file_categories: FileCategories,
        console: Optional[Console] = None,
    ) -> None:
        """
        Display statistics about the organization process.

        :param file_categories: File categorization configuration
        :type file_categories: FileCategories
        :param console: Console instance for output
        :type console: Console | None
        """
        if console is None:
            console = self.console

        stats_table = Table(title="📊 Organization Preview", show_header=False)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")

        stats_table.add_row("Total Files", str(self._total_files))
        stats_table.add_row("Categories", str(len(file_categories["categories"])))
        stats_table.add_row("Default Category", file_categories["defaults"]["name"])

        console.print(Panel(stats_table, border_style="blue"))

    def display_final_results(
        self,
        moved_count: int,
        dirs_count: int,
        error_count: int,
        moved_text: str = "Files Moved",
        dirs_text: str = "Directories Created",
        error_text: str = "Errors",
        *,
        dry_run: bool = False,
        console: Optional[Console] = None,
    ) -> None:
        """
        Display final results of the organization process.

        :param moved_count: Number of files successfully moved
        :type moved_count: int
        :param created_dirs_count: Number of directories created
        :type created_dirs_count: int
        :param error_count: Number of errors encountered
        :type error_count: int
        :param dry_run: Whether the process was a simulation
        :type dry_run: bool
        :param console: Console instance for output
        :type console: Console | None
        """
        if console is None:
            console = self.console

        results_table = Table(show_header=False, box=None)
        results_table.add_column("Metric", style="bold cyan")
        results_table.add_column("Value", style="bold green")

        prefix = "Would have" if dry_run else ""

        results_table.add_row(f"{prefix} {moved_text}", f"[bold]{moved_count}[/bold]")
        results_table.add_row(
            f"{prefix} {dirs_text}", f"[bold]{dirs_count}[/bold]"
        )
        results_table.add_row(
            f"{error_text}", f"[red]{error_count}[/red]" if error_count else "[green]0[/green]"
        )

        title = "📋 Dry Run Results" if dry_run else "✅ Organization Complete"
        border_style = "yellow" if dry_run else "green"
        console.print(Panel(results_table, title=title, border_style=border_style))

    @staticmethod
    def display_error(message: str, console: Optional[Console] = None) -> None:
        """
        Display an error message with consistent formatting.

        :param message: Error message text
        :type message: str
        :param console: Console instance for output
        :type console: Console | None
        """
        if console is None:
            console = Console()
        console.print(f"[red]Error: {message}[/red]")

    @staticmethod
    def display_warning(message: str, console: Optional[Console] = None) -> None:
        """
        Display a warning message with consistent formatting.

        :param message: Warning message text
        :type message: str
        :param console: Console instance for output
        :type console: Console | None
        """
        if console is None:
            console = Console()
        console.print(f"[yellow]Warning: {message}[/yellow]")

    @staticmethod
    def display_success(message: str, console: Optional[Console] = None) -> None:
        """
        Display a success message with consistent formatting.

        :param message: Success message text
        :type message: str
        :param console: Console instance for output
        :type console: Console | None
        """
        if console is None:
            console = Console()
        console.print(f"[green]Success: {message}[/green]")
