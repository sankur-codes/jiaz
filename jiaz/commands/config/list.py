import typer
from jiaz.core.config_utils import load_config, decode_token, get_active_config

def list(name: str = typer.Option(None, '--name', '-n', help="List key-value pairs for a specific config name")):
    """List all configurations or key-value pairs for a specific config."""
    config = load_config()

    if name is None:
        sections = [s for s in config.sections() if s != 'meta']
        if sections:
            typer.echo("Available configurations:")
            for section in sections:
                typer.echo(section)
            active_config = get_active_config(config)
            typer.echo(f"\nActive configuration: {active_config}")
        else:
            typer.echo("No configuration found.")
    else:
        if name in config:
            typer.echo(f"Configuration for '{name}':")
            for key, value in config.items(name):
                if key == 'user_token':
                    value = decode_token(value)
                typer.echo(f"{key} = {value}")
        else:
            typer.echo(f"Config '{name}' not found.")
