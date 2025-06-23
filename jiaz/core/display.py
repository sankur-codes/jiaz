from jiaz.core.formatter import colorize, get_coloured, format_issue_table, format_status_table, format_owner_table, format_to_json, format_to_csv
from tabulate import tabulate
import json

def display_issue(data_table, all_headers, output_format):
    """
    Display the issue table in a formatted manner.

    Args:
        data_table (list): The complete table data.
    """
    issue_table, issue_headers = format_issue_table(data_table, all_headers)
    
    if output_format == "table":
        # Colorise diff in story points over the sprint
        for i in range(len(issue_table)):
            init = issue_table[i][issue_headers.index("Initial Story Points")]
            later = issue_table[i][issue_headers.index("Actual Story Points")]
            if init != later:
                issue_table[i][issue_headers.index("Actual Story Points")] = colorize(f"{int(later)} (Change TBD)","neg")

        print(tabulate(sorted(get_coloured(issue_table),key=lambda x:x[issue_headers.index("Assignee")]), 
                        headers=get_coloured(header=issue_headers), 
                        tablefmt="fancy_grid", 
                        stralign="left",
                        showindex=True))
    elif output_format == "json":
        # Convert the table to JSON format
        json_output = format_to_json(issue_table, issue_headers)
        print(json_output)
    elif output_format == "csv":
        # Convert the table to CSV format
        csv_output = format_to_csv(issue_table, issue_headers)
        print(csv_output)

def display_status(data_table, all_headers, output_format):
    """
    Display the status table in a formatted manner.

    Args:
        data_table (list): The complete table data.
    """
    status_table, status_headers = format_status_table(data_table, all_headers)

    if output_format == "table":
        print(tabulate(get_coloured(status_table), 
                        headers=get_coloured(header=status_headers), 
                        tablefmt="grid"))
    elif output_format == "json":
        # Convert the table to JSON format
        json_output = format_to_json(status_table, status_headers)
        print(json_output)
    elif output_format == "csv":
        # Convert the table to CSV format
        csv_output = format_to_csv(status_table, status_headers)
        print(csv_output)

def display_owner(data_table, all_headers, output_format):
    """
    Display the owner table in a formatted manner.

    Args:
        data_table (list): The complete table data.
    """
    owner_table, owner_headers = format_owner_table(data_table, all_headers)

    if output_format == "table":
        print(tabulate(get_coloured(owner_table), 
                        headers=get_coloured(header=owner_headers), 
                        tablefmt="grid", 
                        stralign="left"))
    elif output_format == "json":
        # Convert the table to JSON format
        json_output = format_to_json(owner_table, owner_headers)
        print(json_output)
    elif output_format == "csv":
        # Convert the table to CSV format
        csv_output = format_to_csv(owner_table, owner_headers)
        print(csv_output)