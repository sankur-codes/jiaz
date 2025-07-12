from jiaz.core.formatter import colorize, get_coloured, format_issue_table, format_status_table, format_owner_table, format_to_json, format_to_csv, filter_columns, format_story_data, format_epic_data, format_initiative_data
from tabulate import tabulate

def display_sprint_issue(data_table, all_headers, output_format, show):
    """
    Display the issue table in a formatted manner.

    Args:
        data_table (list): The complete table data.
    """

    issue_table, issue_headers = format_issue_table(data_table, all_headers)

    # Remove columns that are not in the show list
    issue_table ,issue_headers = filter_columns(issue_table, issue_headers, show)

    if output_format == "table":

        if show and "Initial Story Points" in show and "Actual Story Points" in show:
            # Colorise diff in story points over the sprint
            for i in range(len(issue_table)):
                init = issue_table[i][issue_headers.index("Initial Story Points")]
                later = issue_table[i][issue_headers.index("Actual Story Points")]
                if init != later:
                    issue_table[i][issue_headers.index("Actual Story Points")] = colorize(f"{int(later)} (Change TBD)","neg")

        print(tabulate(sorted(get_coloured(issue_table),key=lambda x:x[0]), 
                        headers=get_coloured(header=issue_headers), 
                        tablefmt="fancy_grid", 
                        stralign="left",
                        showindex=True))
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
    status_table ,status_headers = filter_columns(status_table, status_headers, show)

    if output_format == "table":
        print(tabulate(get_coloured(status_table), 
                        headers=get_coloured(header=status_headers), 
                        tablefmt="grid"))
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
    owner_table ,owner_headers = filter_columns(owner_table, owner_headers, show)

    if output_format == "table":
        print(tabulate(get_coloured(owner_table), 
                        headers=get_coloured(header=owner_headers), 
                        tablefmt="grid", 
                        stralign="left"))
    elif output_format == "json":
        # Convert the table to JSON format
        print(format_to_json(owner_table, owner_headers))
    elif output_format == "csv":
        # Convert the table to CSV format
        print(format_to_csv(owner_table, owner_headers))

def display_story(story_header, story_data, output_format, show):
    """
    Display the story data in a formatted manner.
    Args:
        story_data (dict): The story data to display.
        output_format (str): The format to display the data (e.g., "table", "json", "csv").
        show (list): The fields to show in the output.
    """
    story_header, story_data = format_story_data(story_header,story_data)
    filtered_data, filtered_headers = filter_columns(story_data, story_header, show)

    if output_format == "table":
        print(tabulate(
            list(zip(get_coloured(header=filtered_headers), get_coloured(filtered_data)[0])), # index 0 as there is only one issue(row)
            tablefmt="grid", 
            stralign="left"))
    elif output_format == "json":
        # Convert the story data to JSON format
        print(format_to_json(filtered_data, filtered_headers))

def display_epic(epic_header, epic_data, output_format, show):
    """
    Display the epic data in a formatted manner.

    Args:
        epic_data (dict): The epic data to display.
        output_format (str): The format to display the data (e.g., "table", "json", "csv").
        show (list): The fields to show in the output.
    """
    epic_header, epic_data = format_epic_data(epic_header, epic_data)
    filtered_data, filtered_headers = filter_columns(epic_data, epic_header, show)

    if output_format == "table":
        print(tabulate(
            list(zip(get_coloured(header=filtered_headers), get_coloured(filtered_data)[0])), # index 0 as there is only one issue(row)
            tablefmt="grid", 
            stralign="left"))
    elif output_format == "json":
        # Convert the epic data to JSON format
        print(format_to_json(filtered_data, filtered_headers))

def display_initiative(initiative_header, initiative_data, output_format, show):
    """
    Display the initiative data in a formatted manner.

    Args:
        initiative_data (dict): The initiative data to display.
        output_format (str): The format to display the data (e.g., "table", "json", "csv").
        show (list): The fields to show in the output.
    """
    initiative_header, initiative_data = format_initiative_data(initiative_header,initiative_data)
    filtered_data, filtered_headers = filter_columns(initiative_data, initiative_header, show)

    if output_format == "table":
        print(tabulate(
            list(zip(get_coloured(header=filtered_headers), get_coloured(filtered_data)[0])), # index 0 as there is only one issue(row)
            tablefmt="grid", 
            stralign="left"))
    elif output_format == "json":
        # Convert the initiative data to JSON format
        print(format_to_json(filtered_data, filtered_headers))