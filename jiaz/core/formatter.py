from colorama import Fore, Style
import json
import csv
from io import StringIO
import re
from datetime import datetime, timezone


def strip_ansi(text):
    # Regex to remove all ANSI escape sequences (including color codes)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    # Regex to match ANSI hyperlink sequences
    ansi_hyperlink = re.compile(r'\x1b]8;;.*?\x1b\\(.*?)\x1b]8;;\x1b\\')
    if isinstance(text, str):
        # Extract text from ANSI hyperlinks
        text = ansi_hyperlink.sub(r'\1', text)
        # Remove other ANSI formatting (colors, etc.)
        return ansi_escape.sub('', text)
    return text

def time_delta(time):
    """
    Calculates the time delta between the current time and the given time.
    Args:
        time (str): The time to calculate the delta from.
    Returns:
        timedelta: The time delta object.
    """
    try:
        if isinstance(time, str) and time:
            # Handle different date formats
            time_str = time.replace("Z", "+00:00")
            if "T" in time_str:
                given_time = datetime.fromisoformat(time_str)
            else:
                # Handle date-only format like "2024-01-31"
                given_time = datetime.strptime(time_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            delta = given_time - now  # Future time - current time (positive means time left)
            return delta
        else:
            # Return a dummy delta for invalid input
            return datetime.now(timezone.utc) - datetime.now(timezone.utc)
    except Exception:
        # Return a dummy delta for any parsing errors
        return datetime.now(timezone.utc) - datetime.now(timezone.utc)

def link_text(text, url=None):
    """
    Create a clickable link using ANSI escape sequences.
    Args:
        text (str): The text to display
        url (str): The URL to link to. If None, creates a default JIRA link.
    Returns:
        str: ANSI formatted clickable link
    """

    if not url:
        from jiaz.core.config_utils import get_active_config
        url = get_active_config().get("server_url")
        url = f"{url}/browse/{text}"
    
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"
    
def colorize(text, how=None):
    if how == "pos":
        return f"{Fore.GREEN}{text}{Style.RESET_ALL}"
    elif how == "neg":
        return f"{Fore.RED}{text}{Style.RESET_ALL}"
    elif how == "neu":
        return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
    elif how == "head":
        return f"{Fore.MAGENTA}{text}{Style.RESET_ALL}"
    elif how == "info":
        return f"{Fore.CYAN}{text}{Style.RESET_ALL}"
    else:
        return f"{Fore.BLUE}{text}{Style.RESET_ALL}"
    
def color_map(text_to_be_colored, text_to_check):
    """
    Map text to a color based on its value.
    
    Args:
        text (str): The text to be colored.
    
    Returns:
        str: The colored text.
    """
    if text_to_check in ["Undefined", "New", "Not Started"]:
        return colorize(text_to_be_colored, "neg")
    elif text_to_check == "Closed":
        return colorize(text_to_be_colored, "pos")
    elif text_to_check == "In Progress":
        return colorize(text_to_be_colored, "neu")
    elif text_to_check == "Review":
        return colorize(text_to_be_colored)
    else:
        return text_to_be_colored

def get_coloured(table_content=None, header=None):
    if table_content:
        for rows in table_content:
            for i in range(len(rows)):
                text = rows[i]
                rows[i] = color_map(text, text)
        return table_content
    else:
        for i in range(len(header)):
            header[i]= colorize(header[i],"head")
        return header
    
def generate_status_summary_table(data_table, view_headers):
        """
        Generate a summary table from the sprint data.
        This function processes the sprint data to summarize the number of issues
        in different statuses, counting those with and without story points.
        Args:
            data_table (list): The data table containing sprint issues.
            view_headers (list): The headers of the data table.
        Returns:
            dict: A summary table with counts and story point sums for each status.
        """
        summary_table = {
            "Closed": {"WithPointsCount": 0, "WithoutPointsCount": 0, "StoryPointSum": 0},
            "In Progress": {"WithPointsCount": 0, "WithoutPointsCount": 0, "StoryPointSum": 0},
            "Review": {"WithPointsCount": 0, "WithoutPointsCount": 0, "StoryPointSum": 0},
            "Not Started": {"WithPointsCount": 0, "WithoutPointsCount": 0, "StoryPointSum": 0},
        }

        for rows in data_table:
            status = rows[view_headers.index("Status")]
            if status is None or status not in summary_table:
                status = "Not Started"
            
            actual_story_points = rows[view_headers.index("Actual Story Points")]
            if not isinstance(actual_story_points, str):
                summary_table[status]["WithPointsCount"] += 1
                summary_table[status]["StoryPointSum"] += float(actual_story_points)
            else:
                summary_table[status]["WithoutPointsCount"] += 1

        # Combine counts in the required format
        for status, values in summary_table.items():
            values["Count"] = f"{values['WithPointsCount']}({values['WithoutPointsCount']})" if values['WithoutPointsCount'] > 0 else values['WithPointsCount']

        return summary_table

def generate_assignee_summary_table(data_table, view_headers, statuses):
        """
        Generate a summary table for assignees in the sprint data.
        This function processes the sprint data to summarize the number of issues
        assigned to each assignee, categorized by their status and story points.
        Args:
            data_table (list): The data table containing sprint issues.
            view_headers (list): The headers of the data table.
            statuses (list): The list of statuses to summarize.
        Returns:
            list: A summary table with assignee names and their issue counts and story points.
        """
        assignee_summary = {}

        # Initialize the dictionary for all assignees
        for row in data_table:
            assignee = row[view_headers.index("Assignee")]
            if assignee not in assignee_summary:
                assignee_summary[assignee] = {status: {"count": 0, "points": 0} for status in statuses}
                assignee_summary[assignee]["Total"] = {"count": 0, "points": 0}

        # Populate the counts and points
        for row in data_table:
            assignee = row[view_headers.index("Assignee")]
            status = row[view_headers.index("Status")]
            story_points = row[view_headers.index("Actual Story Points")]
            story_points = float(story_points) if isinstance(story_points, (int, float)) else 0

            if status in statuses:
                assignee_summary[assignee][status]["count"] += 1
                assignee_summary[assignee][status]["points"] += story_points
            assignee_summary[assignee]["Total"]["count"] += 1
            assignee_summary[assignee]["Total"]["points"] += story_points

        return assignee_summary

def format_issue_table(data_table, issue_headers):
    """
    Format the data table for issue view.

    Args:
        data_table (list): The data table to format.

    Returns:
        list: A formatted data table for issue view.
    """
    #This is for issue view
    return data_table, issue_headers

def format_status_table(data_table, all_headers):
    """
    Format the data table for status view.
    
    Args:
        data_table (list): The data table to format.
    
    Returns:
        list: A formatted data table for status view.
    """
    #This is for status view
    status_headers = ["Status", "Issue Count", "Sprint Point Total"]
    status_table = generate_status_summary_table(data_table, all_headers)
    status_formatted_table = [[k, v["Count"], v["StoryPointSum"]] for k, v in status_table.items()]
    return status_formatted_table, status_headers

def format_owner_table(data_table, all_headers):
    """
    Format the data table for owner view.

    Args:
        data_table (list): The data table to format.

    Returns:
        list: A formatted data table for owner view.
    """
    #This is for owner view
    assignee_headers = ["Assignee", "Completed", "Review", "In Progress", "New", "Total"]
    statuses = ["Closed", "Review", "In Progress", "New"]
    assignee_table = generate_assignee_summary_table(data_table, all_headers, statuses)

    # Convert the summary into a table format
    assignee_formatted_table = []
    for assignee, values in assignee_table.items():
        row = [colorize(assignee, "head")]
        for status in statuses:
            count = values[status]["count"]
            points = values[status]["points"]
            formatted_value = (
                f"{count} Stories, {int(points)} Points" if count > 0 else colorize("-", "neg")
            )
            color = (
                "pos" if status == "Closed"
                else "neu" if status == "In Progress"
                else "blue" if status == "Review"
                else "neg"
            )
            row.append(colorize(formatted_value, color))
        total_count = values["Total"]["count"]
        total_points = values["Total"]["points"]
        row.append(colorize(f"{total_count} Stories, {int(total_points)} Points", "head"))
        assignee_formatted_table.append(row)

    return assignee_formatted_table, assignee_headers

def format_epic_table(data_table, all_headers):
    """
    Format the data table for epic view.

    Args:
        data_table (list): The data table to format.
        all_headers (list): The headers of the data table.

    Returns:
        list: A formatted data table for epic view.
        list: A list of headers for the data table.
    """
    #This is for epic view
    return data_table, all_headers

def format_to_json(data_table, headers):
    """
    Convert the data table to JSON format.

    Args:
        data_table (list): The data table to convert.
        headers (list): The headers of the data table.

    Returns:
        str: A JSON string representation of the data table.
    """
    cleaned_data_table = [[strip_ansi(cell) for cell in row] for row in data_table]
    json_data = [dict(zip(headers, row)) for row in cleaned_data_table]
    return json.dumps(json_data, indent=4)

def format_to_csv(data_table, headers):
    """
    Convert the data table to CSV format.

    Args:
        data_table (list): The data table to convert.
        headers (list): The headers of the data table.

    Returns:
        str: A CSV string representation of the data table.
    """

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(data_table)
    
    return output.getvalue()

def filter_columns(data_table: list[list], headers: list[str], selected_columns: list[str]):
    """
    Filters the data_table and headers to only include selected columns.

    Parameters:
    - data_table: List of rows (each row is a list of values)
    - headers: List of column names (strings)
    - selected_columns: List of column names to include

    Returns:
    - filtered_data: List of rows with only selected columns
    - filtered_headers: List of selected headers
    """
    filtered_headers, filtered_data = headers, data_table
    # If selected_columns is not empty and not the default "<pre-defined>"
    if selected_columns and (selected_columns != "<pre-defined>" or selected_columns != ""):
        # Get indices of the selected columns
        indices = [headers.index(col) for col in selected_columns if col in headers]

        # Filter the headers and the data_table rows
        filtered_headers = [headers[i] for i in indices]
        filtered_data = [[row[i] for i in indices] for row in data_table]

    return filtered_data, filtered_headers