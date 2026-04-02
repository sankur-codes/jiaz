import json
from pathlib import Path

import typer
from jiaz.core.formatter import colorize

CACHE_DIR = Path.home() / ".jiaz" / "field_cache"

# Maps logical field names used in the code to possible JIRA display names.
# Order matters: first match wins. Matching is case-insensitive.
FIELD_NAME_PATTERNS = {
    "original_story_points": ["Original Story Points", "Original Story Point Estimate"],
    "story_points": ["Story Points", "Story Point Estimate", "Story point estimate"],
    "work_type": ["Work Type"],
    "sprints": ["Sprint"],
    "epic_link": ["Epic Link"],
    "epic_progress": ["Epic Progress", "Progress"],
    "epic_start_date": [
        "Epic Start Date",
        "Start date",
        "Start Date",
        "Target start",
    ],
    "epic_end_date": ["Epic End Date", "End date", "End Date", "Target end"],
    "parent_link": ["Parent Link", "Parent"],
    "status_summary": ["Status Summary", "Flagged"],
}


def _cache_path(config_name):
    return CACHE_DIR / f"{config_name}.json"


def _load_cache(config_name):
    path = _cache_path(config_name)
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _save_cache(config_name, fields):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(_cache_path(config_name), "w") as f:
        json.dump(fields, f, indent=2)


def discover_fields(jira_client):
    """
    Query the JIRA instance for all fields and match them to known logical names.

    Works on both JIRA Server (v7+) and JIRA Cloud via /rest/api/2/field.

    Args:
        jira_client: An authenticated JIRA client instance.

    Returns:
        dict: Mapping of logical field name to customfield ID.
              Only includes fields that were found on the instance.
    """
    try:
        all_fields = jira_client.fields()
    except Exception as e:
        typer.echo(
            colorize(
                f"Warning: Could not discover custom fields: {e}. "
                "Custom field features may be unavailable.",
                "neu",
            )
        )
        return {}

    # Build a lookup: lowercase display name -> field id
    name_to_id = {}
    for field in all_fields:
        name_lower = field["name"].lower()
        name_to_id[name_lower] = field["id"]

    # Match logical names to actual field IDs
    discovered = {}
    for logical_name, candidate_names in FIELD_NAME_PATTERNS.items():
        for candidate in candidate_names:
            field_id = name_to_id.get(candidate.lower())
            if field_id:
                discovered[logical_name] = field_id
                break

    return discovered


def load_fields(config_name, jira_client):
    """
    Load custom field mappings, using cache if available, otherwise discovering
    from the JIRA instance and caching the result.

    Args:
        config_name: Name of the active configuration (used as cache key).
        jira_client: An authenticated JIRA client instance.

    Returns:
        dict: Mapping of logical field name to customfield ID.
    """
    cached = _load_cache(config_name)
    if cached is not None:
        return cached

    discovered = discover_fields(jira_client)
    if discovered:
        _save_cache(config_name, discovered)
    return discovered


def clear_cache(config_name=None):
    """
    Clear cached field mappings. If config_name is given, clear only that
    config's cache; otherwise clear all caches.
    """
    if config_name:
        path = _cache_path(config_name)
        if path.exists():
            path.unlink()
    elif CACHE_DIR.exists():
        for path in CACHE_DIR.glob("*.json"):
            path.unlink()
