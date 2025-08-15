import typer
from jiaz.commands import analyze, config

app = typer.Typer(help="jiaz: Jira CLI assistant")
app.add_typer(config.app, name="config")
app.add_typer(analyze.app, name="analyze")


def main():
    app()
