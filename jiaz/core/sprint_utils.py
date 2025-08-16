import typer
from jiaz.core.display import (
    display_sprint_epic,
    display_sprint_issue,
    display_sprint_owner,
    display_sprint_status,
)
from jiaz.core.formatter import colorize, link_text, strip_ansi
from jiaz.core.issue_utils import get_issue_fields
from jiaz.core.jira_comms import Sprint


def get_sprint_data_table(sprint, mine=False):
    """
    Retrieve and process the data table from the sprint issues.

    This function fetches issues from the current active sprint, processes them to extract relevant details,
    and returns a structured data table.

    Args:
        sprint (Sprint): An instance of the Sprint class to interact with Jira.

    Returns:
        list: A list of lists representing the data table of sprint issues.
    """
    issues_in_sprint = sprint.get_issues_in_sprint(mine=mine)

    if issues_in_sprint is None:
        typer.echo("No matching issues found in the sprint.")
        raise typer.Exit(code=1)

    data_table = []
    for issue_key in issues_in_sprint:
        issue = sprint.get_issue(issue_key)

        # Extract fields using the unified function
        required_fields = [
            "work_type",
            "title",
            "priority",
            "status",
            "assignee",
            "original_story_points",
            "story_points",
            "comments",
        ]
        field_data = get_issue_fields(sprint, issue, required_fields)

        comments = field_data["comments"]
        issue_key = link_text(issue_key)

        if field_data["assignee"] == colorize("Unassigned", "neg"):
            print(f"\nSkipping {issue.key} as there's no assignee yet\n")
            continue

        assignee = (
            field_data["assignee"].split(" ")[0]
            if field_data["assignee"] != colorize("Unassigned", "neg")
            else field_data["assignee"]
        )

        # Get raw story points for processing (int or None)
        raw_original_points = field_data["original_story_points"]
        raw_story_points = field_data["story_points"]

        # Process story points (returns either int values or colored strings)
        processed_original_points, processed_story_points = sprint.update_story_points(
            issue, raw_original_points, raw_story_points
        )

        # Apply colorization for display if the processed values are still raw integers
        display_original_points = (
            processed_original_points
            if isinstance(processed_original_points, str)
            else (
                processed_original_points
                if processed_original_points is not None
                else colorize("Not Assigned", "neg")
            )
        )
        display_story_points = (
            processed_story_points
            if isinstance(processed_story_points, str)
            else (
                processed_story_points
                if processed_story_points is not None
                else colorize("Not Assigned", "neg")
            )
        )

        latest_comment_details = sprint.get_comment_details(
            comments, field_data["status"]
        )

        data_table.append(
            [
                assignee,
                issue_key,
                field_data["title"],
                field_data["priority"],
                field_data["work_type"],
                display_original_points,
                display_story_points,
                field_data["status"],
                latest_comment_details,
            ]
        )

    # Return everything as a bundle
    return data_table


def get_epic_data_table(sprint, sprint_issue_keys):
    """
    Retrieve and process the data table from the sprint issues. This function fetches issues from the current active sprint, processes them to extract the epics being worked upon in the sprint,
    and returns a structured data table.
    Args:
        sprint (Sprint): An instance of the Sprint class to interact with Jira.
        sprint_issue_keys (list): A list of issue keys (strings) representing the issues in the sprint.
    Returns:
        list: A list of lists representing the data table of epic issues.
        list: A list of headers for the data table.
    """

    epic_headers = [
        "Assignee",
        "Issue Key",
        "Title",
        "Reporter",
        "Priority",
        "Work Type",
        "Progress %",
        "Start Date",
        "Target Date",
        "Status",
        "Last Updated",
        "Comments",
    ]
    epic_table = []

    # Collect epic keys from sprint issues
    sprint_epics = set()  # Use set to avoid duplicates

    # First, check if any issues in the sprint are epics themselves
    for issue_key in sprint_issue_keys:
        try:
            issue_type = get_issue_fields(
                sprint, sprint.get_issue(issue_key), ["type"]
            )["type"]
            if issue_type == "Epic":
                sprint_epics.add(issue_key)
        except Exception as e:
            print(f"Warning: Could not check type for issue {issue_key}: {e}")
            continue

    # Then, extract epic links from all issues in the sprint
    for issue_key in sprint_issue_keys:
        try:
            epic_link = get_issue_fields(
                sprint, sprint.get_issue(issue_key), ["epic_link"]
            )["epic_link"]
            if epic_link != colorize("No Epic", "neg"):
                # Remove ANSI color codes and add to set
                clean_epic_key = strip_ansi(epic_link)
                sprint_epics.add(clean_epic_key)
        except Exception as e:
            print(f"Warning: Could not get epic link for issue {issue_key}: {e}")
            continue

    # Process each unique epic
    for epic_key in sprint_epics:
        try:
            # Request epic data with correct field names
            epic_data = get_issue_fields(
                sprint,
                sprint.get_issue(epic_key),
                [
                    "key",
                    "assignee",
                    "title",
                    "reporter",
                    "priority",
                    "work_type",
                    "epic_progress",
                    "epic_start_date",
                    "epic_end_date",
                    "status",
                    "updated",
                    "comments",
                ],
            )

            # Process assignee and reporter names
            assignee = (
                epic_data["assignee"].split(" ")[0]
                if epic_data["assignee"] != colorize("Unassigned", "neg")
                else epic_data["assignee"]
            )
            reporter = (
                epic_data["reporter"].split(" ")[0]
                if epic_data["reporter"] != colorize("Unassigned", "neg")
                else epic_data["reporter"]
            )

            # Process comments properly
            latest_comment_details = sprint.get_comment_details(
                epic_data["comments"], epic_data["status"]
            )

            # Add epic data to table
            epic_table.append(
                [
                    assignee,
                    epic_data["key"],  # Use formatted key with link
                    epic_data["title"],
                    reporter,
                    epic_data["priority"],
                    epic_data["work_type"],
                    epic_data["epic_progress"],
                    epic_data["epic_start_date"],
                    epic_data["epic_end_date"],
                    epic_data["status"],
                    epic_data["updated"],
                    latest_comment_details,
                ]
            )

        except Exception as e:
            print(f"Error processing epic {epic_key}: {e}")
            continue
    return epic_table, epic_headers


def analyze_sprint(
    wrt="status", output="json", config=None, show="<pre-defined>", mine=False
):
    """
    Analyze the current active sprint data and display it in a specified format.

    This function retrieves sprint data from Jira, processes it, and displays it in a user-friendly format.
    It can be customized to focus on different perspectives such as issue, owner, or status.
    Args:
        wrt (str): The perspective to focus on. Options are 'issue', 'owner', or 'status'.
        output (str): The format to display the data. Options are 'table', 'json', or 'csv'.
        config (str): The configuration name to use for connecting to Jira.
    """
    # Placeholder for the actual implementation
    print(
        f"Analyzing sprint data focusing on '{wrt}' using config '{config}' and  displaying in '{output}' format."
    )
    sprint = Sprint(config_name=config)
    all_headers = [
        "Assignee",
        "Issue Key",
        "Title",
        "Priority",
        "Work Type",
        "Initial Story Points",
        "Actual Story Points",
        "Status",
        "Comment",
    ]
    data_table = get_sprint_data_table(sprint, mine)

    # Provide data based on the perspective required
    if wrt == "issue":
        display_sprint_issue(data_table, all_headers, output, show)
    elif wrt == "owner":
        display_sprint_owner(data_table, all_headers, output, show)
    elif wrt == "epic":
        data_table, all_headers = get_epic_data_table(
            sprint,
            [strip_ansi(issue[all_headers.index("Issue Key")]) for issue in data_table],
        )
        display_sprint_epic(data_table, all_headers, output, show)
    else:
        display_sprint_status(data_table, all_headers, output, show)
