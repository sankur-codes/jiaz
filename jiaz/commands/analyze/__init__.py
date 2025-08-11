import typer

from . import sprint
from . import issue

app = typer.Typer(help="Analyzing Specific Jira Data")

app.command()(sprint.sprint)
app.command()(issue.issue)