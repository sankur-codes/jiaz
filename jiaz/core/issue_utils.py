import re

import pyperclip
import typer

from jiaz.core.display import display_issue
from jiaz.core.formatter import color_map, colorize, link_text, strip_ansi
from jiaz.core.jira_comms import JiraComms


def extract_sprints(sprints_data, key="name"):
    """
    Extract sprint names from the provided list of sprint strings.

    Args:
        sprints_data (list): List of string sprint info in [name=value] format.

    Returns:
        list: List of dict of sprint info.
    """
    result = ""
    # Check if sprints_data is a list and contains sprint strings
    if sprints_data and isinstance(sprints_data, list):
        sprint_info_list = []

        for sprint_str in sprints_data:
            match = re.search(r"\[(.*?)\]", sprint_str)
            if match:
                properties_str = match.group(1)
                properties = re.findall(r"(\w+)=([^,]+)", properties_str)
                sprint_dict = {key: value for key, value in properties}
                sprint_info_list.append(sprint_dict)

        # Extract and format the sprint data
        for sprint in sprint_info_list:
            result += f"{sprint.get(key, '')}, "

    return result.strip(", ")


def extract_epic_progress(epic_progress_string):
    """
    Extract progress percentage from the epic progress string.

    Args:
        epic_progress_string (str): The epic progress string in the format "Progress: 50%".

    Returns:
        str: The extracted progress percentage or "0%" if not found.
    """
    match = re.search(r'<span id="value">(.*?)</span>', epic_progress_string)
    if match:
        return match.group(1).strip()
    return "Progress not found"


def get_issue_children(jira, issue_key):
    """
    Retrieve the children of a given issue.

    Args:
        jira (JiraComms): The JiraComms instance to interact with Jira.
        issue_key (str): The key of the issue to retrieve children for.

    Returns:
        list: A list of child issue keys.
    """
    children = []
    jql = f'"Epic Link" = "{issue_key}" OR "Parent Link" = "{issue_key}" OR parent = "{issue_key}"'
    issues = jira.rate_limited_request(jira.jira.search_issues, jql, maxResults=1000)
    if not issues:
        return children
    for issue in issues:
        issue_key = issue.raw["key"]
        url = issue.permalink()
        issue_key = link_text(issue_key, url)
        status = (
            issue.fields.status.name if hasattr(issue.fields, "status") else "Unknown"
        )
        children.append(color_map(issue_key, status))
    return children


def _get_field_definitions(jira, issue_data):
    """
    Core function that defines all field extraction logic.
    Organizes fields into categories for better management.

    Returns:
        dict: Field definitions organized by category with extraction logic.
    """
    return {
        # REQUIRED FIELDS - Always included in get_all_available_data()
        "required": {
            "key": {
                "header": "Key",
                "extractor": lambda: (
                    issue_data.key
                    if hasattr(issue_data, "key")
                    else colorize("Unknown", "neg")
                ),
                "exists_check": lambda: hasattr(issue_data, "key"),
            },
            "title": {
                "header": "Title",
                "extractor": lambda: (
                    issue_data.fields.summary
                    if hasattr(issue_data.fields, "summary")
                    else colorize("No Title", "neg")
                ),
                "exists_check": lambda: hasattr(issue_data.fields, "summary"),
            },
            "type": {
                "header": "Type",
                "extractor": lambda: (
                    issue_data.fields.issuetype.name
                    if hasattr(issue_data.fields, "issuetype")
                    else colorize("Unknown", "neg")
                ),
                "exists_check": lambda: hasattr(issue_data.fields, "issuetype"),
            },
            "assignee": {
                "header": "Assignee",
                "extractor": lambda: (
                    issue_data.fields.assignee.displayName
                    if hasattr(issue_data.fields, "assignee")
                    and issue_data.fields.assignee
                    else colorize("Unassigned", "neg")
                ),
                "exists_check": lambda: hasattr(issue_data.fields, "assignee"),
            },
            "reporter": {
                "header": "Reporter",
                "extractor": lambda: (
                    issue_data.fields.reporter.displayName
                    if hasattr(issue_data.fields, "reporter")
                    and issue_data.fields.reporter
                    else colorize("Unknown", "neg")
                ),
                "exists_check": lambda: hasattr(issue_data.fields, "reporter"),
            },
            "status": {
                "header": "Status",
                "extractor": lambda: (
                    issue_data.fields.status.name
                    if hasattr(issue_data.fields, "status")
                    else colorize("Undefined", "neg")
                ),
                "exists_check": lambda: hasattr(issue_data.fields, "status"),
            },
        },
        # OPTIONAL FIELDS - Included in get_all_available_data() if they exist
        "optional": {
            "priority": {
                "header": "Priority",
                "extractor": lambda: (
                    issue_data.fields.priority.name
                    if hasattr(issue_data.fields, "priority")
                    and issue_data.fields.priority
                    else colorize("No Priority", "neg")
                ),
                "exists_check": lambda: hasattr(issue_data.fields, "priority"),
            },
            "labels": {
                "header": "Labels",
                "extractor": lambda: (
                    ", ".join(issue_data.fields.labels)
                    if hasattr(issue_data.fields, "labels") and issue_data.fields.labels
                    else colorize("No Labels", "neg")
                ),
                "exists_check": lambda: hasattr(issue_data.fields, "labels"),
            },
            "children": {
                "header": "Children",
                "extractor": lambda: get_issue_children(
                    jira, issue_data.key if hasattr(issue_data, "key") else ""
                ),
                "exists_check": lambda: True,  # Always include children check
            },
            "updated": {
                "header": "Last Updated",
                "extractor": lambda: getattr(issue_data.fields, "updated", None)
                or colorize("No Updates", "neg"),
                "exists_check": lambda: hasattr(issue_data.fields, "updated")
                and getattr(issue_data.fields, "updated", None) is not None,
            },
        },
        # ON-DEMAND FIELDS - Only included when specifically requested
        "on_demand": {
            "description": {
                "header": "Description",
                "extractor": lambda: (
                    strip_ansi(issue_data.fields.description)
                    if hasattr(issue_data.fields, "description")
                    and issue_data.fields.description
                    else colorize("No Description", "neg")
                ),
                "exists_check": lambda: hasattr(issue_data.fields, "description"),
            },
            "comments": {
                "header": "Comments",
                "extractor": lambda: (
                    issue_data.fields.comment.comments
                    if hasattr(issue_data.fields, "comment")
                    and hasattr(issue_data.fields.comment, "comments")
                    else []
                ),
                "exists_check": lambda: hasattr(issue_data.fields, "comment"),
            },
            "status_summary": {
                "header": "Status Summary",
                "extractor": lambda: issue_data.fields.__dict__.get(jira.status_summary)
                or colorize("No Status Summary", "neg"),
                "exists_check": lambda: hasattr(issue_data.fields, jira.status_summary)
                or jira.status_summary in issue_data.fields.__dict__,
                "field_id": jira.status_summary,
            },
        },
        # CUSTOM FIELDS - Project-specific fields that may or may not exist
        "custom": {
            "work_type": {
                "header": "Work Type",
                "extractor": lambda: (
                    field_obj := issue_data.fields.__dict__.get(jira.work_type)
                )
                and field_obj.value
                or colorize("Not Set", "neg"),
                "exists_check": lambda: hasattr(issue_data.fields, jira.work_type)
                or jira.work_type in issue_data.fields.__dict__,
                "field_id": jira.work_type,
            },
            "original_story_points": {
                "header": "Initial Story Points",
                "extractor": lambda: (
                    int(val)
                    if (
                        val := issue_data.fields.__dict__.get(
                            jira.original_story_points
                        )
                    )
                    and val is not None
                    else None
                ),
                "exists_check": lambda: hasattr(
                    issue_data.fields, jira.original_story_points
                )
                or jira.original_story_points in issue_data.fields.__dict__,
                "field_id": jira.original_story_points,
            },
            "story_points": {
                "header": "Actual Story Points",
                "extractor": lambda: (
                    int(val)
                    if (val := issue_data.fields.__dict__.get(jira.story_points))
                    and val is not None
                    else None
                ),
                "exists_check": lambda: hasattr(issue_data.fields, jira.story_points)
                or jira.story_points in issue_data.fields.__dict__,
                "field_id": jira.story_points,
            },
            "sprints": {
                "header": "Sprints",
                "extractor": lambda: (
                    extract_sprints(issue_data.fields.__dict__.get(jira.sprints, []))
                    if issue_data.fields.__dict__.get(jira.sprints)
                    else colorize("No Sprints", "neg")
                ),
                "exists_check": lambda: hasattr(issue_data.fields, jira.sprints)
                or jira.sprints in issue_data.fields.__dict__,
                "field_id": jira.sprints,
            },
            "epic_link": {
                "header": "Epic Link",
                "extractor": lambda: issue_data.fields.__dict__.get(jira.epic_link)
                or colorize("No Epic", "neg"),
                "exists_check": lambda: hasattr(issue_data.fields, jira.epic_link)
                or jira.epic_link in issue_data.fields.__dict__,
                "field_id": jira.epic_link,
            },
            "parent_link": {
                "header": "Parent Link",
                "extractor": lambda: issue_data.fields.__dict__.get(jira.parent_link)
                or colorize("No Parent", "neg"),
                "exists_check": lambda: hasattr(issue_data.fields, jira.parent_link)
                or jira.parent_link in issue_data.fields.__dict__,
                "field_id": jira.parent_link,
            },
            "epic_progress": {
                "header": "Progress",
                "extractor": lambda: (
                    extract_epic_progress(val)
                    if (val := issue_data.fields.__dict__.get(jira.epic_progress))
                    else colorize("No Progress", "neg")
                ),
                "exists_check": lambda: hasattr(issue_data.fields, jira.epic_progress)
                or jira.epic_progress in issue_data.fields.__dict__,
                "field_id": jira.epic_progress,
            },
            "epic_start_date": {
                "header": "Start Date",
                "extractor": lambda: issue_data.fields.__dict__.get(
                    jira.epic_start_date
                )
                or colorize("No Start Date", "neg"),
                "exists_check": lambda: hasattr(issue_data.fields, jira.epic_start_date)
                or jira.epic_start_date in issue_data.fields.__dict__,
                "field_id": jira.epic_start_date,
            },
            "epic_end_date": {
                "header": "End Date",
                "extractor": lambda: issue_data.fields.__dict__.get(jira.epic_end_date)
                or colorize("No End Date", "neg"),
                "exists_check": lambda: hasattr(issue_data.fields, jira.epic_end_date)
                or jira.epic_end_date in issue_data.fields.__dict__,
                "field_id": jira.epic_end_date,
            },
        },
    }


def get_issue_fields(jira, issue_data, requested_fields=None):
    """
    Extract requested data fields from JIRA issue data with consistent formatting.

    This function is a subset of get_all_available_data() that returns only the requested fields
    with the same formatting applied. The data returned by this function for any given field
    will be identical to what get_all_available_data() would return for that same field.

    Args:
        jira (JiraComms): The JiraComms instance containing custom field mappings.
        issue_data: The JIRA issue data object.
        requested_fields (list): List of field names to extract. If None, returns all available fields.

    Returns:
        dict: Dictionary containing the requested field values with field names as keys.
              All values have the same formatting as get_all_available_data() would apply.

    Available fields:
        Required: 'key', 'title', 'type', 'assignee', 'reporter', 'status'
        Optional: 'priority', 'labels', 'children', 'updated'
        On-demand: 'description', 'comments', 'status_summary' (only when explicitly requested)
        Custom: 'work_type', 'original_story_points', 'story_points', 'sprints',
               'epic_link', 'parent_link', 'epic_progress', 'epic_start_date', 'epic_end_date'
    """
    field_categories = _get_field_definitions(jira, issue_data)

    # If no specific fields requested, include all categories except on-demand
    if requested_fields is None:
        requested_fields = []
        for category in ["required", "optional", "custom"]:
            requested_fields.extend(field_categories[category].keys())

    # Create flat field mapping for easy lookup
    all_fields = {}
    for category_fields in field_categories.values():
        all_fields.update(category_fields)

    # Extract requested fields
    result = {}
    for field_name in requested_fields:
        if field_name in all_fields:
            try:
                extracted_value = all_fields[field_name]["extractor"]()

                # Apply special formatting (same as get_all_available_data)
                extracted_value = _apply_field_formatting(
                    field_name, extracted_value, issue_data
                )
                result[field_name] = extracted_value
            except Exception:
                result[field_name] = colorize(f"Error extracting {field_name}", "neg")
        else:
            result[field_name] = colorize(f"Unknown field: {field_name}", "neg")

    return result


def get_all_available_data(jira, issue_data):
    """
    Extract all available data fields from JIRA issue data dynamically.
    Only includes fields that actually exist in the issue data.

    Field inclusion logic:
    - Required fields: Always included
    - Optional fields: Included if they exist
    - On-demand fields: NEVER included (must be explicitly requested via get_issue_fields)
    - Custom fields: Included if they exist in the JIRA instance

    Args:
        jira (JiraComms): The JiraComms instance containing custom field mappings.
        issue_data: The JIRA issue data object.

    Returns:
        tuple: (headers, data) - Lists of headers and corresponding values for existing fields.

    Examples:
        # Get all available data for any issue type (excludes on-demand fields)
        headers, data = get_all_available_data(jira, issue_data)

        # To include on-demand fields like comments, description:
        data_dict = get_issue_fields(jira, issue_data, ['key', 'title', 'comments', 'description'])
    """
    field_categories = _get_field_definitions(jira, issue_data)

    headers = []
    data = []

    # Include required and optional fields (but NOT on-demand fields)
    categories_to_include = ["required", "optional", "custom"]

    for category in categories_to_include:
        for field_name, field_def in field_categories[category].items():
            # Check if field exists before including it
            try:
                if field_def["exists_check"]():
                    headers.append(field_def["header"])
                    extracted_value = field_def["extractor"]()

                    # Apply special formatting
                    extracted_value = _apply_field_formatting(
                        field_name, extracted_value, issue_data
                    )
                    data.append(extracted_value)
            except Exception:
                # Skip fields that cause errors during existence check
                continue

    return headers, data


def _apply_field_formatting(field_name, value, issue_data):
    """
    Apply special formatting to specific field types.

    Args:
        field_name (str): The name of the field
        value: The extracted value
        issue_data: The JIRA issue data object

    Returns:
        Formatted value
    """
    # Import here to avoid circular imports
    from jiaz.core.formatter import colorize, link_text

    if field_name == "key" and value != colorize("Unknown", "neg"):
        return link_text(text=value, url=issue_data.permalink())
    elif field_name in ["epic_link", "parent_link"] and value not in [
        colorize("No Epic", "neg"),
        colorize("No Parent", "neg"),
    ]:
        return link_text(text=value)
    # elif field_name in ['original_story_points', 'story_points']:
    #     # For story points, apply colorization only for display
    #     return value if value is not None else colorize("Not Set", "neg")
    elif field_name == "children":
        if value and not isinstance(value, str):
            return ", ".join(value) if value else colorize("No Children", "neg")
        elif not value:
            return colorize("No Children", "neg")
    elif field_name == "epic_end_date" and value != colorize("No End Date", "neg"):
        from jiaz.core.formatter import time_delta

        try:
            delta = time_delta(value)
            if hasattr(delta, "days"):
                if delta.days <= 0:
                    return colorize("Target Date Passed", "neg")
                elif delta.days <= 15:
                    return colorize(f"{delta.days} days left", "neu")
                elif delta.days > 15:
                    return colorize(f"{delta.days} days left", "pos")
        except Exception:
            # If time_delta fails, just return the original value
            pass
        return value
    elif field_name == "updated" and value != colorize("No Updates", "neg"):
        try:
            from jiaz.core.formatter import time_delta

            delta = time_delta(value)
            # For 'updated', we calculate how long ago it was updated
            # Negative delta means past time, so we use abs() to get positive days ago
            days_ago = abs(delta.days) if delta.days < 0 else 0

            if days_ago == 0:
                return colorize("Updated Today", "pos")
            elif days_ago <= 7:
                return colorize(f"{days_ago} days ago", "pos")
            elif days_ago <= 10:
                return colorize(f"{days_ago} days ago", "neu")
            else:
                return colorize(f"{days_ago} days ago", "neg")
        except Exception:
            # If time formatting fails, just return the original value
            return value
    return value


# AI backed function for updated description
def marshal_issue_description(jira, issue_data):
    """
    Marshal (standardize) issue description using AI and handle user confirmation.

    Args:
        jira: JiraComms instance
        issue_data: JIRA issue object
        output_format: Display format for comparison

    Returns:
        bool: True if description was updated, False otherwise
    """
    from jiaz.core.ai_utils import JiraIssueAI
    from jiaz.core.display import display_markup_description

    # Get current description and title from generic function
    required_fields = get_issue_fields(jira, issue_data, ["description", "title"])

    original_description = required_fields["description"]
    original_title = required_fields["title"]

    if "No Description" in original_description:
        typer.echo(colorize("⚠️  Issue has no description to standardize.", "neu"))
        return False

    try:
        # Initialize AI helper
        jira_ai = JiraIssueAI()

        # Generate standardized description with retry functionality
        typer.echo(
            colorize(f"📝 Analyzing description for {issue_data.key}...", "info")
        )
        standardized_description = _execute_with_retry(
            lambda: jira_ai.standardize_description(
                original_description, original_title
            ),
            "standardizing description",
        )

        if standardized_description is None:
            return False

        # Check if standardized description was generated
        typer.echo(colorize("🔄 Standardizing completed...", "info"))

        if (
            not standardized_description
            or "Failed to generate" in standardized_description
        ):
            typer.echo(
                colorize("❌ Could not generate standardized description.", "neg")
            )
            return False

        # Initial menu
        choice = show_menu(include_display=True)

        if choice == "d":
            # Display the standardized description on terminal with retry functionality
            typer.echo(
                colorize(
                    "🖥️  Rendering standardized description to display on terminal...",
                    "info",
                )
            )
            import shutil

            term_width = shutil.get_terminal_size((80, 20)).columns
            print("\n" + "=" * term_width)
            centered_title = "STANDARDIZED DESCRIPTION".center(term_width)
            typer.echo(colorize(centered_title, "head"))
            print("=" * term_width)
            pyperclip.copy(standardized_description)

            # Retry loop for terminal rendering
            while True:
                terminal_friendly_output = _execute_with_retry(
                    lambda: display_markup_description(standardized_description),
                    "rendering description for display",
                )

                if terminal_friendly_output is None:
                    # If display failed, still show the menu but without display functionality
                    typer.echo(
                        colorize(
                            "⚠️  Display rendering failed, but you can still copy or update the description.",
                            "neu",
                        )
                    )
                    choice = show_menu(include_display=False)
                    break
                else:
                    # Compare standardized description with terminal-friendly output
                    typer.echo(colorize("🔍 Validating rendering accuracy...", "info"))
                    from jiaz.core.ai_utils import JiraIssueAI

                    jira_ai = JiraIssueAI()
                    compare_result = _execute_with_retry(
                        lambda: jira_ai.compare_descriptions(
                            standardized_description, terminal_friendly_output
                        ),
                        "comparing descriptions for accuracy",
                    )

                    if compare_result is None:
                        # If comparison failed, still show the output but with warning
                        typer.echo(
                            colorize(
                                "⚠️  Could not validate rendering accuracy, but displaying output anyway.",
                                "neu",
                            )
                        )
                        print(terminal_friendly_output)
                        print("=" * term_width)
                        choice = show_menu(include_display=False)
                        break
                    elif compare_result:
                        # Descriptions are similar, proceed normally
                        typer.echo(
                            colorize("✅ Rendering validation successful.", "pos")
                        )
                        print(terminal_friendly_output)
                        print("=" * term_width)
                        choice = show_menu(include_display=False)
                        break
                    else:
                        # Descriptions are not similar, offer retry for display rendering
                        typer.echo(
                            colorize(
                                "⚠️ Rendering description for display failed (likely due to unmatched content)",
                                "neu",
                            )
                        )
                        retry_choice = _show_retry_menu(
                            "display rendering due to content mismatch"
                        )

                        if retry_choice == "r":
                            typer.echo(
                                colorize("🔄 Retrying terminal rendering...", "info")
                            )
                            # Continue the loop to retry just the terminal_friendly_output generation
                            continue
                        else:
                            typer.echo(
                                colorize(
                                    "⚠️ You can still copy or update the description.",
                                    "neu",
                                )
                            )
                            print("=" * term_width)
                            choice = show_menu(include_display=False)
                            break

        if choice == "c":
            pyperclip.copy(standardized_description)
            typer.echo(
                colorize("✅ Standardized description copied to clipboard.", "pos")
            )
            return False
        elif choice == "u":
            return update_issue_description_with_backup(
                jira, issue_data, original_description, standardized_description
            )
        elif choice == "e":
            typer.echo(colorize("❌ Exiting without updating.", "neu"))
            return False
        else:
            typer.echo(colorize("❌ Invalid choice. Exiting.", "neg"))
            return False

    except Exception as e:
        typer.echo(colorize(f"❌ Error during description marshaling: {e}", "neg"))
        return False


def _execute_with_retry(operation, operation_name):
    """
    Execute an operation with retry functionality for timeout scenarios.

    Args:
        operation: Function to execute (lambda or callable)
        operation_name: Human-readable name of the operation for error messages

    Returns:
        Result of the operation or None if user cancels
    """
    import typer

    while True:
        try:
            return operation()
        except typer.Exit as e:
            # Check if this was a timeout or connection error
            # In this case, we want to offer retry options
            if e.exit_code == 1:
                typer.echo(
                    colorize(
                        f"⚠️  {operation_name.capitalize()} failed (likely due to timeout or connection issue).",
                        "neu",
                    )
                )
                retry_choice = _show_retry_menu(operation_name)

                if retry_choice == "r":
                    typer.echo(colorize(f"🔄 Retrying {operation_name}...", "info"))
                    continue  # Retry the operation
                elif retry_choice == "e":
                    typer.echo(colorize(f"❌ Exiting {operation_name}.", "neu"))
                    return None
                else:
                    typer.echo(colorize("❌ Invalid choice. Exiting.", "neg"))
                    return None
            else:
                # Re-raise for other exit codes
                raise
        except Exception as e:
            typer.echo(
                colorize(f"❌ Unexpected error during {operation_name}: {e}", "neg")
            )
            return None


def _show_retry_menu(operation_name):
    """
    Show retry menu options when an operation times out.

    Args:
        operation_name: Human-readable name of the operation

    Returns:
        User's choice (r/e)
    """
    typer.echo(
        colorize(
            f"\nWhat would you like to do about the failed {operation_name}?", "head"
        )
    )
    typer.echo(colorize("* Retry the operation - (r)", "info"))
    typer.echo(colorize("* Exit/Cancel - (e)", "neg"))
    return typer.prompt("\nEnter your choice (r/e)", type=str)


# Function to show menu options
def show_menu(include_display=True):
    """
    Show menu options for handling standardized description.

    Args:
        include_display (bool): Whether to include the display option
    """
    question = (
        "\nWhat would you like to do with the standardized description?"
        if include_display
        else "\nWhat would you like to do next?"
    )
    typer.echo(colorize(question, "head"))

    if include_display:
        typer.echo(
            colorize(
                "* Display on terminal (takes some time ⏳) and copy - (d)", "info"
            )
        )
    typer.echo(colorize("* Copy to clipboard - (c)", "pos"))
    typer.echo(colorize("* Update on JIRA - (u)", "neu"))
    typer.echo(colorize("* Exit - (e)", "neg"))

    choices = "d/c/u/e" if include_display else "c/u/e"
    return typer.prompt(f"Enter your choice ({choices})", type=str)


def update_issue_description_with_backup(
    jira, issue_data, original_description, new_description
):
    """
    Generic function to update issue description and create backup comment.

    Args:
        issue_data: JIRA issue object
        original_description: Original description to backup
        new_description: New description to set
        backup_reason: Reason for the backup (default: "AI standardization")

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if there is a backup comment already in pinned comments
        pinned_comments = jira.get_pinned_comments(issue_data.key)
        backup_exists = any(
            "*Original Description (Backup)*" in comment.raw["comment"]["body"]
            for comment in pinned_comments
        )

        pin_success = False  # Initialize for proper scope

        if backup_exists:
            typer.echo(
                colorize(
                    "🔄 Backup comment already exists, skipping backup creation...",
                    "info",
                )
            )
        else:
            # Create backup comment text
            backup_comment = (
                f"""📋 **Original Description (Backup)**\n\n{original_description}"""
            )

            # Add backup comment
            typer.echo(
                colorize(
                    "💾 Creating backup comment with original description...", "info"
                )
            )
            comment = jira.adding_comment(issue_data.key, backup_comment)

            if not comment:
                typer.echo(colorize("❌ Failed to create backup comment", "neg"))
                return False

            # Pin the backup comment
            typer.echo(colorize("📌 Pinning backup comment...", "info"))
            pin_success = jira.pinning_comment(issue_data.key, comment.id)

            if not pin_success:
                typer.echo(
                    colorize("⚠️ Backup comment created but could not be pinned", "neu")
                )

        # Update the description (always executed whether backup exists or not)
        typer.echo(colorize("🔄 Updating issue description...", "info"))
        jira.rate_limited_request(
            issue_data.update, fields={"description": new_description}
        )

        typer.echo(colorize("✅ Description updated successfully!", "pos"))

        if backup_exists:
            typer.echo(colorize("📌 Original description previously backed up", "pos"))
        else:
            pin_message = (
                "📌 Original description backed up as pinned comment"
                if pin_success
                else "📌 Original description backed up as comment"
            )
            typer.echo(colorize(pin_message, "pos"))

        return True

    except Exception as e:
        typer.echo(colorize(f"❌ Failed to update issue: {e}", "neg"))
        return False


def analyze_issue(
    id: str,
    output="json",
    config=None,
    show="<pre-defined>",
    rundown=False,
    marshal_description=False,
):
    """
    Analyze and display data for provided issue.

    Arguments:
    -----------
        id: Valid id of the issue to be analyzed.
        output: Display format (json, table).
        config: Configuration name to use.
        show: List of field names to be shown.
    """
    print(
        f"Analyzing issue with id {id} using config '{config}' and  displaying in '{output}' format."
    )
    jira = JiraComms(config_name=config)
    issue_data = jira.get_issue(id)

    # get issue type
    issue_type = (
        issue_data.fields.issuetype.name
        if hasattr(issue_data.fields, "issuetype")
        else "Unknown"
    )
    typer.echo(colorize(f"🔍 Analyzing JIRA {issue_type}: {issue_data.key}", "info"))

    # Handle description marshaling if requested
    if marshal_description:
        marshal_issue_description(jira, issue_data)
        # For marshal description, we only show the comparison and exit
        return

    # Get all available data dynamically
    headers, data = get_all_available_data(jira, issue_data)

    # Use unified display function for all issue types
    display_issue(headers, data, output, show)
