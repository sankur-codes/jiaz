import typer
from jiaz.core.config_utils import (
    load_config, save_config, set_active_config, prepend_warning_to_config,
    collect_required_fields, collect_optional_fields, handle_gemini_api_key_input,
    prompt_api_key_with_retries, encode_secure_value
)

def init():
    """Initialize the configuration with required and optional fields."""
    config = load_config()

    if 'meta' not in config:
        config['meta'] = {}

    if not [sec for sec in config.sections() if sec != 'meta']:
        typer.echo("Config file does not exist or contains no blocks. Creating default configuration.")

        # Collect required fields
        required_config = collect_required_fields()
        
        # Collect optional fields
        optional_config = collect_optional_fields()
        
        # Handle Gemini API key
        gemini_config = handle_gemini_api_key_input(config)
        
        # Combine all configurations
        default_config = {**required_config, **optional_config, **gemini_config}
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

        # Collect required fields with fallback to existing config
        required_config = collect_required_fields(fallback_config=config)
        
        # Collect optional fields
        optional_config = collect_optional_fields()
        
        # Handle Gemini API key (only update meta if not already set)
        gemini_config = {}
        api_key = prompt_api_key_with_retries()
        
        if api_key:
            encoded_api_key = encode_secure_value(api_key)
            gemini_config['gemini_api_key'] = encoded_api_key
            
            # Also update meta block if not already set
            if not (config.has_section('meta') and config.has_option('meta', 'gemini_api_key')):
                if 'meta' not in config:
                    config['meta'] = {}
                config['meta']['gemini_api_key'] = encoded_api_key
            typer.echo("✅ Gemini API key validated and saved.")
        else:
            typer.echo("No Gemini API key provided. Will use Ollama for LLM queries.")
        
        # Combine all configurations
        new_config = {**required_config, **optional_config, **gemini_config}
        config[new_config_name] = new_config
        save_config(config)
        typer.echo(f"New configuration block '{new_config_name}' added.")

        prepend_warning_to_config()