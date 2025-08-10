# File Organizer

A powerful and fast command-line tool for organizing files into categorized directories based on their type. The tool also provides a robust undo functionality to revert the last operation.

## Features

* **File Organization**: Moves files into dedicated directories (e.g., Images, Documents) based on their file extensions.
* **Undo Functionality**: Reverts the last organization operation, restoring files to their original locations.
* **Efficient Performance**: Utilizes libraries like `ijson` and `tqdm` for optimized memory management and dynamic progress bars, even with large file sets.
* **Simple Configuration**: File categories can be easily configured and customized via a `config.json` file.
* **Comprehensive Logging**: All operations are logged to a history file, enabling accurate tracking and error management.

## Installation

To set up this project, use the `uv` package manager.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/nimagh-18/File-Organizer.git

    cd File-Organizer
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    uv venv

    # For Windows:
    .\.venv\Scripts\activate
    
    # For macOS/Linux:
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    uv sync
    ```

## Usage

The File Organizer tool can be run using `python -m file_organizer`.

### Organize Files

To organize files in a directory, pass the directory path as an argument:

```bash
python -m main.py organize "/path/to/your/files"
```

### Undo Operation

To revert the last organize operation, use the following command:

```bash
python -m main.py undo
```

### View and Edit Configuration

```bash
python -m main.py show-config
    
python -m main.py edit-config
```    

## Configuration

File categorization is managed in config.json. The file uses file extensions as keys and the desired directory name as the value.

Example:

```JSON
{      
    ".jpg": "Images",
    ".png": "Images", 
    ".mp4": "Videos",  
    ".pdf": "Documents"
}
```

## Contributing

Feel free to submit issues, fork the repository, and send pull requests.

## License

This project is licensed under the \[Insert your license here, e.g., MIT\] License.