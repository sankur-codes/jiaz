import typer
from jiaz.core.config_utils import load_config, get_active_config
from jiaz.core.sprint_utils import analyze_sprint

def sprint(
    wrt: str = typer.Option("status", "--wrt", "-w", help="Display sprint data in specific perspective. Values: issue, owner, status, epic"),
    show: str = typer.Option(None,"--show", "-s", help="Comma separated columns to show. If not provided, all columns are shown.", show_default=False),
    output: str = typer.Option("json", "--output", "-o", help="Display in a specific format. Values: json, table, csv"),
    config: str = typer.Option(get_active_config(), "--config-name", "-c", help="Configuration name to use. Default is the active config"),
    mine: bool = typer.Option(False, "--mine", "-m", is_flag=True, help="Show only issues assigned to the current user"),
):
    """Analyze and display current active sprint data."""

    if wrt and wrt not in ["issue", "owner", "status", "epic"]:
        typer.echo("Invalid perspective specified. Use 'issue', 'owner', 'status', or 'epic'.")
        raise typer.Exit(code=1)
    if output and output not in ["json", "table", "csv"]:
        typer.echo("Invalid output format specified. Use 'json', 'table', or 'csv'.")
        raise typer.Exit(code=1)
    if config:
        config_data = load_config()
        if config not in config_data:
            typer.echo(f"Configuration '{config}' not found.")
            raise typer.Exit(code=1)
    if show and show != "<pre-defined>":
        show = [name.strip() for name in show.split(",")]

    analyze_sprint(wrt=wrt, output=output, config=config, show=show, mine=mine)
