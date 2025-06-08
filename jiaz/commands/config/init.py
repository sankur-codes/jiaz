import typer
from jiaz.core.config_utils import (
    load_config, save_config, prompt_required_with_retries, prompt_with_fallback,
    encode_token, set_active_config, prepend_warning_to_config
)

def init():
    """Initialize the configuration with required and optional fields."""
    config = load_config()

    if 'meta' not in config:
        config['meta'] = {
            'OriginalStoryPoints': "customfield_12314040",
            'StoryPoints': "customfield_12310243",
            'WorkType': "customfield_12320040"
        }

    if not [sec for sec in config.sections() if sec != 'meta']:
        typer.echo("Config file does not exist or contains no blocks. Creating default configuration.")

        server_url = prompt_required_with_retries([
            "Enter server URL (required)",
            "Server URL is required. Please enter it.",
            "Cannot proceed without Server URL. Please enter a valid URL."
        ])

        user_token = prompt_required_with_retries([
            "Enter user token (required)",
            "User token is required. Please enter it.",
            "Cannot proceed without user token. Please enter a valid token."
        ])

        encoded_token = encode_token(user_token)

        default_config = {
            'server_url': server_url,
            'user_token': encoded_token,
        }

        for key in ['jira_project', 'jira_backlog_name', 'jira_sprintboard_name']:
            value = typer.prompt(f"Enter {key.replace('_', ' ')} (optional)", type=str, default="")
            if value.strip():
                default_config[key] = value

        config['default'] = default_config

        set_active_config(config, 'default')
        save_config(config)
        typer.echo("Default configuration set and active.")

    else:
        typer.echo("Config file already exists. Adding a new configuration block.")
        new_config_name = typer.prompt("Enter a new config name")

        if new_config_name in config:
            typer.echo(f"Config name '{new_config_name}' already exists. Please choose a different name.")
            raise typer.Exit(code=1)

        server_url = prompt_with_fallback(
            "Enter server URL (leave empty to use value from default)",
            "Server URL is required. Please enter it.",
            config,
            key="server_url",
            section="default"
        )

        user_token_input = typer.prompt(
            "Enter user token (leave empty to use value from default)",
            type=str,
            default=""
        )

        if user_token_input.strip():
            encoded_token = encode_token(user_token_input)
        elif config.has_option("default", "user_token"):
            encoded_token = config.get("default", "user_token")
        else:
            user_token_raw = prompt_required_with_retries([
                "User token is required. Please enter it.",
                "Please enter a valid user token.",
                "Cannot proceed without a user token."
            ])
            encoded_token = encode_token(user_token_raw)

        new_config = {
            'server_url': server_url,
            'user_token': encoded_token,
        }

        for key in ['jira_project', 'jira_backlog_name', 'jira_sprintboard_name']:
            value = typer.prompt(f"Enter {key.replace('_', ' ')}", type=str, default="")
            if value.strip():
                new_config[key] = value

        config[new_config_name] = new_config
        save_config(config)
        typer.echo(f"New configuration block '{new_config_name}' added.")

        prepend_warning_to_config()