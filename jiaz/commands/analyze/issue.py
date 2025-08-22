import typer
from jiaz.core.config_utils import get_active_config, load_config
from jiaz.core.issue_utils import analyze_issue


def issue(
    id: str = typer.Argument(..., help="Valid id of the issue to be analysed."),
    show: str = typer.Option(
        "",
        "--show",
        "-s",
        help="Field names to be shown. Type comma separated exact names to show only those.",
        show_default=False,
    ),
    output: str = typer.Option(
        "json",
        "--output",
        "-o",
        help="Display in a specific format. Values: json, table",
    ),
    config: str = typer.Option(
        get_active_config(),
        "--config-name",
        "-c",
        help="Configuration name to use. Default is the active config",
    ),
    rundown: bool = typer.Option(
        False,
        "--rundown",
        "-r",
        help="Generate AI-powered progress summary",
    ),
    marshal_description: bool = typer.Option(
        False,
        "--marshal-description",
        "-m",
        help="Standardize issue description using AI",
    ),
):
    """Analyze and display data for provided issue."""

    id = id.strip()

    # Validate mutual exclusivity
    if marshal_description and rundown:
        typer.echo(
            "❌ Cannot use --marshal-description and --rundown together. Please choose one."
        )
        raise typer.Exit(code=1)

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

    analyze_issue(
        id=id,
        output=output,
        config=config,
        show=show,
        rundown=rundown,
        marshal_description=marshal_description,
    )
