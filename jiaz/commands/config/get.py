import typer
from jiaz.core.config_utils import load_config, decode_token, get_active_config

def get(
    key: str,
    name: str = typer.Option(None, "--name", "-n", help="Target config block")
):
    """Get a configuration value."""
    config = load_config()
    active_config = get_active_config(config)

    if name is None:
        name = active_config

    if name in config and key in config[name]:
        value = config[name][key]
        if key == "user_token":
            value = decode_token(value)
        typer.echo(value)
    else:
        typer.echo(f"Key '{key}' not found in config '{name}'.")
