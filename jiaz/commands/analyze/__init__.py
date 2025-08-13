import typer

from . import issue, sprint

app = typer.Typer(help="Analyzing Specific Jira Data")

app.command()(sprint.sprint)
app.command()(issue.issue)
