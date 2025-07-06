import typer
from jiaz.core.config_utils import load_config, get_active_config
from jiaz.core.sprint_utils import analyze_sprint
from jiaz.core.issue_utils import analyze_issue

def issue(
    id: str = typer.Argument(..., help="Valid id of the issue to be analysed."),
    format_description: bool = typer.Option(False, "--fmt-desc", "-f", is_flag=True, help="Standardize issue description in a consistent format"),
    show: str = typer.Option("", "--show", "-s", help="Field names to be shown. Type comma separated exact names to show only those.", show_default=False),
    output: str = typer.Option("json", "--output", "-o", help="Display in a specific format. Values: json, table, csv"),
    config: str = typer.Option(get_active_config(), "--config-name", "-c", help="Configuration name to use. Default is the active config"),
):
    """Analyze and display data for provided issue."""

    id = id.strip()
    if output and output not in ["json", "table"]:
        typer.echo("Invalid output format specified. Use 'json' or 'table'.")
        raise typer.Exit(code=1)
    if config:
        config_data = load_config()
        if config not in config_data:
            typer.echo(f"Configuration '{config}' not found.")
            raise typer.Exit(code=1)
    if show and show != "<pre-defined>":
        show = [name.strip() for name in show.split(",")]

    analyze_issue(id=id, output=output, config=config, show=show)
