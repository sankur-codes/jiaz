import typer

from . import get, init, list, set, use

app = typer.Typer(help="Manage JIRA configuration")

app.command()(get.get)
app.command()(set.set)
app.command()(init.init)
app.command()(list.list)
app.command()(use.use)
