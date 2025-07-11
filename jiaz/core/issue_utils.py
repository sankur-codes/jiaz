from jiaz.core.jira_comms import JiraComms
from jiaz.core.display import display_epic, display_story, display_initiative
from jiaz.core.formatter import strip_ansi, colorize, link_text
import typer
import re

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
            match = re.search(r'\[(.*?)\]', sprint_str)
            if match:
                properties_str = match.group(1)
                properties = re.findall(r'(\w+)=([^,]+)', properties_str)
                sprint_dict = {key: value for key, value in properties}
                sprint_info_list.append(sprint_dict)

        # Extract and format the sprint data
        for sprint in sprint_info_list:
            result += f"{sprint.get(key, '')}, "

    return result.strip(', ')


def get_common_data(jira, issue_data):
    """
    Extract common data fields from the story data.

    Args:
        story_data (dict): The story data to format.

    Returns:
        tuple: A tuple containing common data and common values.
    """
    common_headers = ["Key", "Title", "Type", "Assignee", "Reporter", "Work Type", "Status", "Priority", "labels", "Description"]

    issue_key = issue_data.key if hasattr(issue_data, 'key') else colorize("Unknown", "neg")
    issue_title = issue_data.fields.summary if hasattr(issue_data.fields, 'summary') else colorize("No Title", "neg")
    issue_type = issue_data.fields.issuetype.name if hasattr(issue_data.fields, 'issuetype') else colorize("Unknown", "neg")
    issue_assignee = issue_data.fields.assignee.displayName if hasattr(issue_data.fields, 'assignee') and issue_data.fields.assignee else colorize("Unassigned", "neg")
    issue_reporter = issue_data.fields.reporter.displayName if hasattr(issue_data.fields, 'reporter') and issue_data.fields.reporter else colorize("Unknown", "neg")
    issue_work_type = (field_obj := issue_data.fields.__dict__.get(jira.work_type)) and field_obj.value or colorize("Undefined", "neg")
    issue_status = issue_data.fields.status.name if hasattr(issue_data.fields, 'status') else colorize("Undefined", "neg")
    issue_priority = issue_data.fields.priority.name if hasattr(issue_data.fields, 'priority') else colorize("Undefined", "neg")
    issue_labels = ", ".join(issue_data.fields.labels) if hasattr(issue_data.fields, 'labels') else colorize("No Labels", "neg")
    issue_description = strip_ansi(issue_data.fields.description) if hasattr(issue_data.fields, 'description') else colorize("No Description", "neg")
    common_data = [
        issue_key if issue_key == colorize("Unknown", "neg") else link_text(text=issue_key, url=issue_data.permalink()),
        issue_title,
        issue_type,
        issue_assignee,
        issue_reporter,
        issue_work_type,
        issue_status,
        issue_priority,
        issue_labels,
        issue_description
    ]    
    return common_headers, common_data

def get_epic_data(issue_data):
    """
    Extract epic-specific data fields from the issue data.

    Args:
        issue_data (dict): The issue data to extract epic information from.

    Returns:
        tuple: A tuple containing epic-specific headers and values.
    """
    epic_headers = []
    epic_data = [
        
    ]
    return epic_headers, [epic_data]

def get_initiative_data(issue_data):
    """
    Extract initiative-specific data fields from the issue data.

    Args:
        issue_data (dict): The issue data to extract initiative information from.

    Returns:
        tuple: A tuple containing initiative-specific headers and values.
    """
    initiative_headers = []
    initiative_data = [
        
    ]
    return initiative_headers, [initiative_data]

def get_story_data(jira, issue_data):
    """
    Extract story-specific data fields from the issue data.

    Args:
        issue_data (dict): The issue data to extract story information from.

    Returns:
        tuple: A tuple containing story-specific headers and values.
    """
    story_headers = ["Initial Story Points", "Actual Story Points", "Sprints", "Parent"] # Parents should contain issue id with link
    original_story_points = issue_data.fields.__dict__.get(jira.original_story_points, colorize("Not Assigned", "neg"))
    actual_story_points = issue_data.fields.__dict__.get(jira.story_points, colorize("Not Assigned", "neg"))
    sprints = extract_sprints(issue_data.fields.__dict__.get(jira.sprints, [])) if hasattr(issue_data.fields, jira.sprints) else colorize("No Sprints", "neg")
    parent = issue_data.fields.__dict__.get(jira.parent, colorize("No Parent", "neg"))
    story_data = [
        original_story_points,
        actual_story_points,
        sprints,
        parent if parent == colorize("No Parent", "neg") else link_text(text=parent)
    ]
    return story_headers, story_data

def analyze_issue(id: str, output="json", config=None, show="<pre-defined>"):
    """
    Analyze and display data for provided issue.

    Arguments:
    -----------
        id: Valid id of the issue to be analyzed.
        output: Display format (json, table).
        config: Configuration name to use.
        show: List of field names to be shown.
    """
    # Placeholder for actual implementation

    print(f"Analyzing issue with id {id} using config '{config}' and  displaying in '{output}' format.")
    jira = JiraComms(config_name=config)
    issue_data = jira.get_issue(id)   

    # get issue type
    issue_type = issue_data.fields.issuetype.name if hasattr(issue_data.fields, 'issuetype') else "Unknown"
    typer.secho(f"🔍 Analyzing JIRA {issue_type}:", fg=typer.colors.CYAN, bold=True, nl=False)
    typer.secho(f" {issue_data.key}", fg=typer.colors.YELLOW, bold=True)

    # Get common data
    common_headers, common_data = get_common_data(jira, issue_data)

    if issue_type == "Epic":
        # Get epic specific data
        epic_headers, epic_data = get_epic_data(jira, issue_data)
        display_epic(common_headers+epic_headers, common_data+epic_data, output, show)
    elif issue_type == "Initiative":
        # Get initiative specific data
        initiative_headers, initiative_data = get_initiative_data(jira, issue_data)
        display_initiative(common_headers+initiative_headers, common_data+initiative_data, output, show)
    else:
        # Get story specific data
        story_headers, story_data = get_story_data(jira, issue_data)
        display_story(common_headers+story_headers, [common_data+story_data], output, show)
