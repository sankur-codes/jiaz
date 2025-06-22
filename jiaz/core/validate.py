from jira import JIRA, JIRAError
import requests
import typer

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
            typer.echo(f"❌ JIRA server responded with status code {response.status_code}.", err=True)
            raise typer.Exit(code=1)
    except requests.exceptions.RequestException as e:
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
