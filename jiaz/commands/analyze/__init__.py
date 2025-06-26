import typer

from . import sprint

app = typer.Typer(help="Analyzing Specific Jira Data")

app.command()(sprint.sprint)