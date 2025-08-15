import typer
from jiaz.core.config_utils import load_config, save_config, set_active_config


def use(config_name: str):
    """Set the active configuration for future commands."""
    config = load_config()
    if config_name in config:
        set_active_config(config, config_name)
        save_config(config)
        typer.echo(f"Active configuration set to '{config_name}'.")
    else:
        typer.echo(f"Config '{config_name}' not found.")
