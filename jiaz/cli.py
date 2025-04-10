import typer
from jiaz.commands import config

app = typer.Typer(help="jiaz: Jira CLI assistant")
app.add_typer(config.app, name="config")

def main():
    app()