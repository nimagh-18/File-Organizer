import typer
from src.commands import organize, undo, show_config, edit_config

app = typer.Typer()

# اضافه کردن دستورات از ماژول‌های مختلف
app.add_typer(organize.app)
app.add_typer(undo.app)
app.add_typer(show_config.app)
app.add_typer(edit_config.app)

if __name__ == "__main__":
    app()
