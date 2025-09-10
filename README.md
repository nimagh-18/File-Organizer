# File Organizer

A powerful, modular, and efficient command-line tool for organizing files into categorized directories based on file extensions, size variants, and custom rules. Features robust undo functionality, customizable configuration, and advanced progress visualization with Rich.

## Features

- **File Organization**: Automatically moves files into categorized folders (e.g., Images, Documents, Videos) based on rules defined in `file_categories.yaml`.
- **Recursive Organization**: Supports recursive traversal of subdirectories with the `--recursive` flag, with optional depth limiting via `--depth`.
- **Pattern Filtering**: Filter files using glob patterns (e.g., `*.jpg`, `report*.*`) with comprehensive validation for invalid patterns.
- **Undo Functionality**: Reverts the last organization operation, restoring files and directories using a JSON history file with efficient streaming (via `ijson`).
- **Customizable Configuration**: Edit file categories, extensions, and size-based variants interactively or via `file_categories.yaml`.
- **Advanced Progress Visualization**: Uses Rich for beautiful progress bars, file statistics, and final summaries.
- **Comprehensive Logging**: Logs all operations with Loguru, including rotation and compression for scalability.
- **System Protection**: Prevents organizing sensitive system directories using an allowlist (`allowed_path.yaml`).
- **Performance Optimization**: Uses caching (`suffix_to_category_mapping`) and set-based extensions for faster processing.
- **Modern CLI**: Built with Typer for a user-friendly command-line interface with detailed help messages.
- **Editable Installation**: Install as a standalone CLI tool (`organizer`) using `uv` or `pip`.
- **Depth-Limited Traversal**: Limit recursive processing to specific subdirectory levels (e.g., `--depth 2`).
- **Dry-Run Mode**: Preview changes without modifying files using `--dry-run`.
- **Hidden File Support**: Include hidden files with `--include-hidden`.
- **Sphinx Documentation**: Comprehensive docstrings for developer-friendly documentation.

## Before & After Example

### Without Recursive Mode

**Before running File Organizer:**

```
your-folder/
├── photo1.jpg
├── doc1.pdf
├── song1.mp3
├── script.py
├── notes.txt
├── video1.mp4
├── random.zip
├── subfolder/
│   ├── photo2.jpg
│   └── doc2.pdf
```

**Command:**

```bash
organizer organize /path/to/your-folder
```

**After running File Organizer (non-recursive):**

```
your-folder/
├── Images/
│   └── photo1.jpg
├── Documents/
│   ├── doc1.pdf
│   └── notes.txt
├── Audio/
│   └── song1.mp3
├── Code/
│   └── script.py
├── Videos/
│   └── video1.mp4
├── Archives/
│   └── random.zip
├── subfolder/  # Unchanged
│   ├── photo2.jpg
│   └── doc2.pdf
```

### With Recursive Mode and Depth Limit

**Before running File Organizer:**

```
your-folder/
├── photo1.jpg
├── doc1.pdf
├── subfolder/
│   ├── photo2.jpg
│   ├── doc2.pdf
│   └── deep/
│       ├── video2.mp4
│       └── nested/
│           └── song2.mp3
```

**Command:**

```bash
organizer organize /path/to/your-folder --recursive --depth 2
```

**After running File Organizer (recursive, depth=2):**

```
your-folder/
├── Images/
│   ├── photo1.jpg
│   └── photo2.jpg
├── Documents/
│   └── doc2.pdf
├── Videos/
│   └── video2.mp4
├── subfolder/
│   └── deep/
│       └── nested/  # Unchanged (beyond depth 2)
│           └── song2.mp3
```

## Installation

Use the `uv` package manager for a seamless setup.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/nimagh-18/File-Organizer.git
   cd File-Organizer
   ```

2. **Create and activate a virtual environment:**

   ```bash
   uv venv
   source .venv/bin/activate
   ```

3. **Install the project as an editable package:**

   ```bash
   uv tool install -e .
   ```

   This installs the `organizer` CLI command globally in the virtual environment.

## Usage

Run commands via the `organizer` CLI:

```bash
organizer [COMMAND] [OPTIONS]
```

### Organize Files

Organize files in one or more directories:

```bash
organizer organize /path/to/dir1,/path/to/dir2 --recursive --depth 2 --pattern "*.{jpg,png}"
```

- Options:
  - `--recursive` (`-r`): Organize subdirectories.
  - `--depth <int>`: Limit recursion depth (e.g., `2` for two levels; `-1` for unlimited).
  - `--pattern <glob>`: Filter files (e.g., `*.jpg`, `report*.*`).
  - `--include-hidden`: Include hidden files.
  - `--dry-run`: Simulate without changes.
  - `--force` (`-f`): Bypass security checks.
  - `--yes` (`-y`): Skip confirmation prompts.

### Undo Last Operation

Revert the last organization:

```bash
organizer undo
```

### Show Current Configuration

Display the current categorization rules:

```bash
organizer show-config
```

### Edit Configuration

Edit `file_categories.yaml` interactively or in the default editor:

```bash
organizer edit-config
```

### Add Allowed Path

Add a directory to the allowlist for organization:

```bash
organizer add-path /path/to/dir
```

## Configuration

File categorization is managed in `src/file_organizer/config/file_categories.yaml`. Example:

```yaml
defaults:
  name: Other
categories:
  - name: Images
    extensions: [".jpg", ".png"]
    variants:
      - name: Small
        min_size_mb: 0
        max_size_mb: 5
      - name: Large
        min_size_mb: 5
  - name: Documents
    extensions: [".pdf", ".txt"]
```

Edit directly or use `organizer edit-config` for an interactive experience.

## Logging & Undo

- **Logs**: Stored in `src/file_organizer/logs/` with rotation and compression (via Loguru).
- **Undo**: Uses JSON history files for efficient streaming (via `ijson`) to restore files.

## System Protection

The tool uses an allowlist (`allowed_path.yaml`) to prevent organizing sensitive directories (e.g., `/`, `/etc`, `~/.config`).

## Dependencies

- [Typer](https://typer.tiangolo.com/) for CLI
- [Rich](https://github.com/Textualize/rich) for progress visualization
- [Loguru](https://github.com/Delgan/loguru) for logging
- [ijson](https://pypi.org/project/ijson/) for JSON streaming
- [PyYAML](https://pyyaml.org/) for configuration
- [tqdm](https://tqdm.github.io/) for fallback progress bars

## Roadmap

Planned features for future releases:
- Regex-based file filtering (`--regex`)
- File deduplication using hashes
- Real-time folder watch mode (e.g., with `watchgod`)
- Multi-level undo history
- Parallel processing for large directories
- Export operation reports to CSV/HTML
- Cloud storage integration (e.g., Google Drive, Dropbox)
- AI-based file categorization

## Contributing

Contributions are welcome! Please open issues or submit pull requests on [GitHub](https://github.com/nimagh-18/File-Organizer).

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.