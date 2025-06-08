from jiaz.core.formatter import colorize, get_coloured, format_issue_table, format_status_table, format_owner_table
from tabulate import tabulate

def display_issue_table(data_table, all_headers):
    """
    Display the issue table in a formatted manner.

    Args:
        data_table (list): The complete table data.
    """
    issue_table, issue_headers = format_issue_table(data_table, all_headers)
    
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
    
def display_status_table(data_table, all_headers):
    """
    Display the status table in a formatted manner.

    Args:
        data_table (list): The complete table data.
    """
    status_table, status_headers = format_status_table(data_table, all_headers)
    print(tabulate(get_coloured(status_table), 
                    headers=get_coloured(header=status_headers), 
                    tablefmt="grid"))

def display_owner_table(data_table, all_headers):
    """
    Display the owner table in a formatted manner.

    Args:
        data_table (list): The complete table data.
    """
    owner_table, owner_headers = format_owner_table(data_table, all_headers)
    print(tabulate(get_coloured(owner_table), 
                    headers=get_coloured(header=owner_headers), 
                    tablefmt="grid", 
                    stralign="left"))