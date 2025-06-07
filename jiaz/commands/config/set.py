import typer
from jiaz.core.config_utils import load_config, save_config, encode_token, get_active_config, decode_token

def set(
    key: str,
    value: str,
    name: str = typer.Option(None, "--name", "-n", help="Target config block")
):
    """Set a configuration key-value pair."""
    config = load_config()
    active_config = get_active_config()

    # If --name is not provided, operate on active config block
    if name is None:
        name = active_config

    # Block user from modifying the meta block
    if name == "meta":
        typer.echo("Cannot modify 'meta' block. It is reserved for internal use.")
        raise typer.Exit(code=1)

    if name in config:
        section = config[name]
        is_update = key in section

        # If updating an existing key in active block, ask for confirmation
        if is_update and name == active_config:
            old_value = decode_token(section[key]) if key == "user_token" else section[key]
            confirm = typer.confirm(
                f"You are updating key '{key}' in active config block '{name}' from '{old_value}' to '{value}'. Continue?"
            )
            if not confirm:
                typer.echo("Update aborted by user.")
                raise typer.Exit()

        section[key] = encode_token(value) if key == 'user_token' else value

        save_config(config)

        typer.echo(
            f"{'Config updated' if is_update else 'Config added'} in '{name}': {key}={value}"
        )
    else:
        typer.echo(f"Config '{name}' not found. Use 'list' to view available configs.")