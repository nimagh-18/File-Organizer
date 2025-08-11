# File Organizer

A powerful, modular, and efficient command-line tool for organizing files into categorized directories based on their type. Includes robust undo functionality, customizable configuration, and detailed logging.

## Features

- **File Organization**: Automatically moves files into categorized folders (e.g., Images, Documents, Videos) based on file extensions defined in `config.json`.
- **Undo Functionality**: Reverts the last organization operation, restoring files and directories to their previous state.
- **Customizable Configuration**: Easily edit file categories and rules via `config.json` using a built-in editor command.
- **Comprehensive Logging**: All operations are logged for transparency and troubleshooting.
- **Progress Bars**: Uses `tqdm` for dynamic progress bars during file operations.
- **Efficient Memory Usage**: Handles large directories efficiently with streaming and batching.
- **System Protection**: Prevents organizing sensitive or system directories.
- **Command-Line Interface**: Built with Typer for a modern CLI experience.

## Before & After Example

Suppose you have a folder with mixed files:

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
```

**After running File Organizer:**

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
```

## Installation

To set up this project, use the `uv` package manager.

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

3. **Install dependencies:**
   ```bash
   uv sync
   ```

## Usage

All commands are available via the CLI. Run the main entry point:

```bash
python cli.py [COMMAND] [OPTIONS]
```

### Organize Files

Organize files in a directory:

```bash
python cli.py organize "/path/to/your/files"
```
- Add `--include-hidden` to include hidden/system files.

### Undo Last Operation

Revert the last organization:

```bash
python cli.py undo
```

### Show Current Configuration

Display the current file categorization rules:

```bash
python cli.py show-config
```

### Edit Configuration

Open `config.json` in your system's default text editor:

```bash
python cli.py edit-config
```

## Configuration

File categorization is managed in `config.json`. Each key is a file extension, and the value is the target directory name.

Example:

```json
{
    ".jpg": "Images",
    ".pdf": "Documents",
    ".mp4": "Videos"
}
```
You can edit this file directly or use the `edit-config` command.

## Logging & Undo

- All operations are logged in the `src/logs/` directory.
- Undo uses the latest log to restore files and remove created directories.

## System Protection

The tool will not allow organizing system or sensitive directories (e.g., `/`, `/etc`, user home, `.config`, etc.) for safety.

## Dependencies

- [Typer](https://typer.tiangolo.com/)
- [Tqdm](https://tqdm.github.io/)
- [Loguru](https://github.com/Delgan/loguru)
- [ijson](https://pypi.org/project/ijson/)

## Roadmap

Planned features for future releases:
- Multi-directory input support
- Advanced pattern/rule-based categorization (regex, size, date, etc.)
- Dry-run mode for previewing changes
- Multi-level undo/history
- Parallel/multi-threaded processing
- HTML/Markdown operation reports
- Real-time folder watch mode
- AI-based file type detection

See `needed_features.txt` for more details.

## Contributing

Contributions are welcome! Please open issues or submit pull requests.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.