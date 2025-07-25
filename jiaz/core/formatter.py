from colorama import Fore, Style
import json
import csv
from io import StringIO
import re

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

def link_text(text, url=None):
    if not url:
        url = f"https://issues.redhat.com/browse/{text}"
    # Create ANSI hyperlink escape sequence for clickable terminal links
    return f"\033]8;;{url}\033\\{colorize(text, 'neu')}\033]8;;\033\\"
    
def colorize(text, how=None):
    if how == "pos":
        return f"{Fore.GREEN}{text}{Style.RESET_ALL}"
    elif how == "neg":
        return f"{Fore.RED}{text}{Style.RESET_ALL}"
    elif how == "neu":
        return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
    elif how == "head":
        return f"{Fore.MAGENTA}{text}{Style.RESET_ALL}"
    elif how == "code":
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

def format_story_data(story_header, story_data):
    """
    Format the story data for display.

    Args:
        story_data (dict): The story data to format.

    Returns:
        dict: A formatted dictionary with relevant fields.
    """
    return story_header, story_data

    
def format_epic_data(epic_header, epic_data):
    """
    Format the epic data for display.

    Args:
        epic_data (dict): The epic data to format.

    Returns:
        dict: A formatted dictionary with relevant fields.
    """
    return epic_header, epic_data

def format_initiative_data(initiative_header, initiative_data):
    """
    Format the initiative data for display.

    Args:
        initiative_data (dict): The initiative data to format.

    Returns:
        dict: A formatted dictionary with relevant fields.
    """

    return initiative_header, initiative_data


def convert_jira_markup_for_display(text: str) -> str:
    """
    Convert JIRA markup to terminal-friendly format for better readability, including hyperlinks.
    """
    if not text:
        return text

    # First, normalize line breaks and clean up the text
    text = text.strip()
    
    # Handle JIRA sections with proper spacing - these need to be on separate lines
    # Headers: +*SECTION:*+ or *+SECTION:+*
    text = re.sub(r'\+\*([^*]+):\*\+', lambda m: f"\n\n{colorize(f'{m.group(1).upper()}:', 'head')}\n", text)
    text = re.sub(r'\*\+([^+]+):\+\*', lambda m: f"\n\n{colorize(f'{m.group(1).upper()}:', 'head')}\n", text)
    
    # Bold text: *text* - but avoid matching the headers we just processed
    text = re.sub(r'(?<!\+)\*([^*]+)\*(?!\+)', lambda m: colorize(m.group(1), "neu"), text)
    
    # Italics: _text_
    text = re.sub(r'_([^_]+)_', lambda m: colorize(m.group(1), "neu"), text)
    
    # Code blocks: {code}...{code} 
    text = re.sub(r'\{code\}(.*?)\{code\}', lambda m: f"\n{colorize('┌─ CODE BLOCK', 'head')}\n{colorize(m.group(1).strip(), 'code')}\n{colorize('└─', 'head')}\n", text, flags=re.DOTALL)
    
    # Inline code: {{code}}
    text = re.sub(r'\{\{([^}]+)\}\}', lambda m: colorize(f"`{m.group(1)}`", "code"), text)
    
    # Hyperlinks: [text|url] - convert to clickable terminal links
    text = re.sub(r'\[([^\|\]]+)\|([^\]]+)\]', lambda m: link_text(m.group(1), m.group(2)), text)
    
    # Lists: • item with proper indentation and line breaks
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        # Handle bullet points
        if re.match(r'^\s*•\s+', line):
            processed_lines.append(f"  {line.strip()}")
        # Handle numbered lists  
        elif re.match(r'^\s*\d+\.\s+', line):
            processed_lines.append(f"  {line.strip()}")
        else:
            processed_lines.append(line)
    
    text = '\n'.join(processed_lines)
    
    # Strikethrough: -text-
    text = re.sub(r'-(\w+)-', lambda m: colorize(m.group(1), "neg"), text)
    
    # Clean up excessive newlines but preserve section spacing
    # Remove more than 3 consecutive newlines
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    
    # Ensure proper spacing after section headers
    text = re.sub(r'(\n\n[A-Z ]+:)\n([^\n])', r'\1\n\n\2', text)
    
    # Clean up any trailing whitespace on lines
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    
    return text.strip()


def format_description_comparison(original: str, standardized: str, output_format: str = "table") -> str:
    """
    Format original and standardized descriptions for side-by-side comparison.
    
    Args:
        original: Original description
        standardized: AI-generated standardized description
        output_format: Output format (table or json)
        
    Returns:
        Formatted comparison string
    """
    from tabulate import tabulate
    import json
    import shutil
    
    # Clean descriptions
    original_clean = original.strip() if original else "No description provided"
    standardized_clean = standardized.strip() if standardized else "No standardized description generated"
    
    if output_format == "table":
        # Get current terminal width dynamically
        try:
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 120  # Fallback width
        
        # Reserve space for table borders, padding, and separators (approximately 20 characters)
        table_overhead = 20
        available_width = max(terminal_width - table_overhead, 80)  # Minimum total width of 80
        
        # Split remaining width equally between two columns
        column_width = available_width // 2
        
        # Ensure minimum column width for readability
        column_width = max(column_width, 35)
        
        headers = [
            colorize("ORIGINAL DESCRIPTION", "neg"),
            colorize("STANDARDIZED DESCRIPTION (JIRA PREVIEW)", "pos")
        ]
        
        # Convert JIRA markup to terminal-friendly format for display
        standardized_display = convert_jira_markup_for_display(standardized_clean)
        
        # Ensure proper formatting for original description too
        original_formatted = original_clean.replace('\r\n', '\n').replace('\r', '\n')
        
        # Create a single row with complete descriptions
        comparison_data = [[original_formatted, standardized_display]]
        
        return tabulate(
            comparison_data,
            headers=headers,
            tablefmt="fancy_grid",
            stralign="left",
            maxcolwidths=[column_width, column_width],
            colalign=("left", "left"),
            numalign="left"
        )
    elif output_format == "json":
        comparison_data = {
            "original_description": original_clean,
            "standardized_description_raw": standardized_clean,
            "standardized_description_preview": convert_jira_markup_for_display(standardized_clean)
        }
        return json.dumps(comparison_data, indent=2)
    
    else:
        # Default key-value format
        standardized_display = convert_jira_markup_for_display(standardized_clean)
        # Ensure proper formatting for original description too
        original_formatted = original_clean.replace('\r\n', '\n').replace('\r', '\n')
        return f"""
{colorize("ORIGINAL DESCRIPTION:", "neg")}
{original_formatted}

{colorize("STANDARDIZED DESCRIPTION (JIRA PREVIEW):", "pos")}
{standardized_display}
"""