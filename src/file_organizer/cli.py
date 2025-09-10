import typer

from file_organizer.commands import add_path, edit_config, organize, show_config, undo

app = typer.Typer()

# Add commands from different modules
app.add_typer(organize.app)
app.add_typer(undo.app)
app.add_typer(show_config.app)
app.add_typer(edit_config.app)
app.add_typer(add_path.app)

if __name__ == "__main__":
    app()
