import requests
import typer
from jiaz.core.formatter import colorize
from jira import JIRA, JIRAError


def valid_jira_client(server_url: str, user_token: str) -> JIRA:
    """
    Validates if the given JIRA server URL and token are correct,
    and returns a JIRA client instance if valid.

    Parameters:
        server_url (str): Base URL of the JIRA server (e.g., https://jira.example.com)
        user_token (str): Personal Access Token (PAT) or OAuth token

    Returns:
        JIRA: Authenticated JIRA client instance if validation succeeds

    Exits:
        Prints a CLI-friendly error message and exits if validation fails.
    """

    # Step 1: Check if server URL is reachable
    try:
        response = requests.get(server_url, timeout=5)
        if response.status_code >= 400:
            typer.echo(
                f"❌ JIRA server responded with status code {response.status_code}.",
                err=True,
            )
            raise typer.Exit(code=1)
    except (requests.exceptions.RequestException, ConnectionError) as e:
        typer.echo(f"❌ Unable to reach JIRA server: {e}", err=True)
        raise typer.Exit(code=1)

    # Step 2: Try to authenticate with the token
    try:
        jira_client = JIRA(server=server_url, kerberos=True, token_auth=user_token)
        # Test token validity
        jira_client.myself()
    except JIRAError as je:
        typer.echo(f"❌ Authentication failed: {je.status_code} - {je.text}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"❌ Unexpected error during JIRA authentication: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo("✅ JIRA authentication successful.", err=False)
    return jira_client


def validate_sprint_config(config):
    """
    Validates the sprint configuration to ensure all required fields are present.

    Parameters:
        config (dict): Configuration dictionary containing sprint settings

    Raises:
        typer.Exit: If any required field is missing, exits with an error message
    """
    required_fields = [
        "jira_project",
        "jira_backlog_name",
        "jira_sprintboard_name",
        "jira_sprintboard_id",
        "jira_board_name",
    ]
    missing_fields = [
        field for field in required_fields if field not in config or not config[field]
    ]

    if missing_fields:
        typer.echo(
            f"❌ Missing required configuration field(s): {missing_fields}", err=True
        )
        raise typer.Exit(code=1)

    typer.echo(
        "✅ Sprint configuration validated successfully. Required configs are present.",
        err=False,
    )


def issue_exists(jira_client, issue_id) -> bool:
    """
    Check if a JIRA issue exists. Exits gracefully using typer on error.

    Args:
        jira_client (JIRA): An authenticated JIRA client object.
        issue_id (str): The JIRA issue ID or key.

    Returns:
        bool: True if issue exists, False otherwise (with typer-style output).
    """
    try:
        jira_client.rate_limited_request(jira_client.jira.issue, issue_id)
        return True
    except JIRAError as e:
        if e.status_code == 404:
            typer.echo(colorize(f"Issue '{issue_id}' not found in JIRA.", "neg"))
            return False
        else:
            typer.echo(colorize(f"Error while fetching issue '{issue_id}': {e}", "neg"))
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(colorize(f"Unexpected error: {e}", "neg"))
        raise typer.Exit(code=1)
