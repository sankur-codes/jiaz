import os
import typer
from pathlib import Path

app = typer.Typer(help="Manage JIRA configuration")

CONFIG_DIR = Path.home() / ".jiaz"
CONFIG_FILE = CONFIG_DIR / "config"

@app.command()
def set(key: str, value: str):
    """Set a configuration key-value pair"""
    CONFIG_DIR.mkdir(exist_ok=True)
    lines = []
    if CONFIG_FILE.exists():
        lines = CONFIG_FILE.read_text().splitlines()
        lines = [line for line in lines if not line.startswith(f"{key}=")]
    lines.append(f"{key}={value}")
    CONFIG_FILE.write_text("\n".join(lines) + "\n")
    typer.echo(f"Config set: {key}={value}")

@app.command()
def get(key: str):
    """Get a configuration value by key"""
    if CONFIG_FILE.exists():
        lines = CONFIG_FILE.read_text().splitlines()
        for line in lines:
            if line.startswith(f"{key}="):
                typer.echo(line.split("=", 1)[1])
                return
    typer.echo(f"Key '{key}' not found.")

@app.command()
def list():
    """List all configurations"""
    if CONFIG_FILE.exists():
        typer.echo(CONFIG_FILE.read_text())
    else:
        typer.echo("No configuration found.")