from tabulate import tabulate

from jiaz.core.formatter import (colorize, filter_columns, format_epic_table,
                                 format_issue_table, format_owner_table,
                                 format_status_table, format_to_csv,
                                 format_to_json, get_coloured)


def display_sprint_issue(data_table, all_headers, output_format, show):
    """
    Display the issue table in a formatted manner.

    Args:
        data_table (list): The complete table data.
    """

    issue_table, issue_headers = format_issue_table(data_table, all_headers)

    # Remove columns that are not in the show list
    issue_table, issue_headers = filter_columns(issue_table, issue_headers, show)

    if output_format == "table":

        if show is None or (
            "Initial Story Points" in show and "Actual Story Points" in show
        ):
            # Colorise diff in story points over the sprint
            for i in range(len(issue_table)):
                init = issue_table[i][issue_headers.index("Initial Story Points")]
                later = issue_table[i][issue_headers.index("Actual Story Points")]

                # Only compare if both values are integers (not colored strings)
                if init != later:
                    issue_table[i][issue_headers.index("Actual Story Points")] = (
                        colorize(f"{later} (Change TBD)", "neg")
                    )

        print(
            tabulate(
                sorted(get_coloured(issue_table), key=lambda x: x[0]),
                headers=get_coloured(header=issue_headers),
                tablefmt="fancy_grid",
                stralign="left",
                showindex=True,
            )
        )
    elif output_format == "json":
        # Convert the table to JSON format
        print(format_to_json(issue_table, issue_headers))
    elif output_format == "csv":
        # Convert the table to CSV format
        print(format_to_csv(issue_table, issue_headers))


def display_sprint_status(data_table, all_headers, output_format, show):
    """
    Display the status table in a formatted manner.

    Args:
        data_table (list): The complete table data.
    """
    status_table, status_headers = format_status_table(data_table, all_headers)

    # Remove columns that are not in the show list
    status_table, status_headers = filter_columns(status_table, status_headers, show)

    if output_format == "table":
        print(
            tabulate(
                get_coloured(status_table),
                headers=get_coloured(header=status_headers),
                tablefmt="grid",
            )
        )
    elif output_format == "json":
        # Convert the table to JSON format
        print(format_to_json(status_table, status_headers))
    elif output_format == "csv":
        # Convert the table to CSV format
        print(format_to_csv(status_table, status_headers))


def display_sprint_owner(data_table, all_headers, output_format, show):
    """
    Display the owner table in a formatted manner.

    Args:
        data_table (list): The complete table data.
    """
    owner_table, owner_headers = format_owner_table(data_table, all_headers)

    # Remove columns that are not in the show list
    owner_table, owner_headers = filter_columns(owner_table, owner_headers, show)

    if output_format == "table":
        print(
            tabulate(
                get_coloured(owner_table),
                headers=get_coloured(header=owner_headers),
                tablefmt="grid",
                stralign="left",
            )
        )
    elif output_format == "json":
        # Convert the table to JSON format
        print(format_to_json(owner_table, owner_headers))
    elif output_format == "csv":
        # Convert the table to CSV format
        print(format_to_csv(owner_table, owner_headers))


def display_sprint_epic(data_table, all_headers, output_format, show):
    """
    Display details ofthe epics associated with issues in the sprint

    Args:
        data_table (list): The complete table data.
        all_headers (list): The headers for the data fields.
        output_format (str): The format to display the data (e.g., "table", "json", "csv").
        show (list): The fields to show in the output.
    """
    epic_table, epic_headers = format_epic_table(data_table, all_headers)
    epic_table, epic_headers = filter_columns(epic_table, epic_headers, show)
    if output_format == "table":
        print(
            tabulate(
                get_coloured(epic_table),
                headers=get_coloured(header=epic_headers),
                tablefmt="grid",
            )
        )
    elif output_format == "json":
        print(format_to_json(epic_table, epic_headers))
    elif output_format == "csv":
        print(format_to_csv(epic_table, epic_headers))


def display_issue(headers, data, output_format, show):
    """
    Universal display function for any JIRA issue type.
    Dynamically displays all available fields without type-specific formatting.

    Args:
        headers (list): The headers for the data fields.
        data (list): The data values corresponding to the headers.
        output_format (str): The format to display the data (e.g., "table", "json", "csv").
        show (list): The fields to show in the output.
    """
    # Filter columns based on the show parameter
    filtered_data, filtered_headers = filter_columns([data], headers, show)

    if output_format == "table":
        print(
            tabulate(
                list(
                    zip(
                        get_coloured(header=filtered_headers),
                        get_coloured(filtered_data)[0],
                    )
                ),  # index 0 as there is only one issue(row)
                tablefmt="grid",
                stralign="left",
            )
        )
    elif output_format == "json":
        # Convert the data to JSON format
        print(format_to_json(filtered_data, filtered_headers))
    elif output_format == "csv":
        # Convert the data to CSV format
        print(format_to_csv(filtered_data, filtered_headers))


def display_markup_description(standardised_description):
    """
    Formats the comparison of original and standardized descriptions.
    Args:
        original_description (str): Original JIRA issue description.
        standardized_description (str): AI-generated standardized description with JIRA markup.
        output_format (str): The format for the output, either 'table' or 'json'.
    Returns:
        str: The formatted comparison.
    """
    from jiaz.core.ai_utils import JiraIssueAI
    from jiaz.core.prompts.jira_markup_render import (GEMINI_PROMPT,
                                                      OLLAMA_PROMPT)

    # Initialize AI helper
    jira_ai = JiraIssueAI()
    # Dynamically select the appropriate prompt based on the LLM being used
    if jira_ai.llm.use_gemini:
        MARKUP_PROMPT = GEMINI_PROMPT
    else:
        MARKUP_PROMPT = OLLAMA_PROMPT
    prompt = MARKUP_PROMPT.format(standardised_description=standardised_description)

    # Here you would call your LLM model, e.g.:
    terminal_friendly_output = jira_ai.llm.query_model(
        prompt
    )  # Always use default model
    return terminal_friendly_output
