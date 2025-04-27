import typer
from jiaz.core.config_utils import load_config, save_config, encode_token, get_active_config, decode_token

def set(
    key: str,
    value: str,
    name: str = typer.Option(None, "--name", "-n", help="Target config block")
):
    """Set a configuration key-value pair."""
    config = load_config()
    active_config = get_active_config(config)

    if name is None:
        name = active_config

    if name in config:
        section = config[name]
        is_update = key in section

        section[key] = encode_token(value) if key == 'user_token' else value
        
        save_config(config)

        if is_update:
            typer.echo(f"Config updated in '{name}': {key}={value}")
        else:
            typer.echo(f"Config added in '{name}': {key}={value}")
    else:
        typer.echo(f"Config '{name}' not found. Use 'list' to view available configs.")
