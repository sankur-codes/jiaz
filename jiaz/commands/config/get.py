import typer

from jiaz.core.config_utils import (decode_secure_value, get_active_config,
                                    load_config)


def get(
    key: str, name: str = typer.Option(None, "--name", "-n", help="Target config block")
):
    """Get a configuration value."""
    config = load_config()
    active_config = get_active_config()
    if name is None:
        name = active_config

    if name in config and key in config[name]:
        value = config[name][key]
        if key == "user_token" or key == "gemini_api_key":
            value = decode_secure_value(value)
        typer.echo(value)
    else:
        typer.echo(f"Key '{key}' not found in config '{name}'.")
