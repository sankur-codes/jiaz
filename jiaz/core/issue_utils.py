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



def get_common_data(jira, issue_data):
    """
    Extract common data fields from the story data.

    Args:
        story_data (dict): The story data to format.

    Returns:
        tuple: A tuple containing common data and common values.
    """
    common_headers = ["Key", "Title", "Type", "Assignee", "Reporter", "Work Type", "Status", "Priority", "labels"]

    issue_key = issue_data.key if hasattr(issue_data, 'key') else colorize("Unknown", "neg")
    issue_title = issue_data.fields.summary if hasattr(issue_data.fields, 'summary') else colorize("No Title", "neg")
    issue_type = issue_data.fields.issuetype.name if hasattr(issue_data.fields, 'issuetype') else colorize("Unknown", "neg")
    issue_assignee = issue_data.fields.assignee.displayName if hasattr(issue_data.fields, 'assignee') and issue_data.fields.assignee else colorize("Unassigned", "neg")
    issue_reporter = issue_data.fields.reporter.displayName if hasattr(issue_data.fields, 'reporter') and issue_data.fields.reporter else colorize("Unknown", "neg")
    issue_work_type = (field_obj := issue_data.fields.__dict__.get(jira.work_type)) and field_obj.value or colorize("Undefined", "neg")
    issue_status = issue_data.fields.status.name if hasattr(issue_data.fields, 'status') else colorize("Undefined", "neg")
    issue_priority = issue_data.fields.priority.name if hasattr(issue_data.fields, 'priority') else colorize("Undefined", "neg")
    issue_labels = ", ".join(issue_data.fields.labels) if hasattr(issue_data.fields, 'labels') else colorize("No Labels", "neg")
    #issue_description = strip_ansi(issue_data.fields.description) if hasattr(issue_data.fields, 'description') else colorize("No Description", "neg")
    common_data = [
        issue_key if issue_key == colorize("Unknown", "neg") else link_text(text=issue_key, url=issue_data.permalink()),
        issue_title,
        issue_type,
        colorize("Unassigned", "neg") if issue_assignee == colorize("Unassigned", "neg") or not issue_assignee else issue_assignee,
        colorize("Unknown", "neg") if issue_reporter == colorize("Unknown", "neg") or not issue_reporter else issue_reporter,
        colorize("Undefined", "neg") if issue_work_type == colorize("Undefined", "neg") or not issue_work_type else issue_work_type,
        colorize("Undefined", "neg") if issue_status == colorize("Undefined", "neg") or not issue_status else issue_status,
        colorize("Undefined", "neg") if issue_priority == colorize("Undefined", "neg") or not issue_priority else issue_priority,
        colorize("No Labels", "neg") if issue_labels == colorize("No Labels", "neg") or not issue_labels else issue_labels,
    ]
    return common_headers, common_data

def get_epic_data(jira, issue_data):
    """
    Extract epic-specific data fields from the issue data.

    Args:
        issue_data (dict): The issue data to extract epic information from.

    Returns:
        tuple: A tuple containing epic-specific headers and values.
    """
    epic_headers = ["Parent", "Progress", "Start Date", "End Date"]
    parent = issue_data.fields.__dict__.get(jira.parent_link, colorize("No Parent", "neg")) if hasattr(issue_data.fields, jira.parent_link) else colorize("No Parent", "neg")
    epic_progress = extract_epic_progress(issue_data.fields.__dict__.get(jira.epic_progress, "")) if hasattr(issue_data.fields, jira.epic_progress) else colorize("Progress Not Found", "neg")
    epic_start_date = issue_data.fields.__dict__.get(jira.epic_start_date, colorize("Not Assigned", "neg")) if hasattr(issue_data.fields, jira.epic_start_date) else colorize("Not Assigned", "neg")
    epic_end_date = issue_data.fields.__dict__.get(jira.epic_end_date, colorize("Not Assigned", "neg")) if hasattr(issue_data.fields, jira.epic_end_date) else colorize("Not Assigned", "neg")
    epic_data = [
        colorize("No Parent", "neg") if parent == colorize("No Parent", "neg") or not parent else link_text(text=parent),
        colorize("Progress Not Found", "neg") if epic_progress == colorize("Progress Not Found", "neg") or not epic_progress else epic_progress,
        colorize("Not Assigned", "neg") if epic_start_date == colorize("Not Assigned", "neg") or not epic_start_date else epic_start_date,
        colorize("Not Assigned", "neg") if epic_end_date == colorize("Not Assigned", "neg") or not epic_end_date else epic_end_date
    ]
    return epic_headers, epic_data

def get_initiative_data(jira, issue_data):
    """
    Extract initiative-specific data fields from the issue data.

    Args:
        issue_data (dict): The issue data to extract initiative information from.

    Returns:
        tuple: A tuple containing initiative-specific headers and values.
    """
    initiative_headers = ["Parent", "Progress", "Start Date", "End Date"]
    parent = issue_data.fields.__dict__.get(jira.parent_link, colorize("No Parent", "neg")) if hasattr(issue_data.fields, jira.parent_link) else colorize("No Parent", "neg")
    initiative_progress = extract_epic_progress(issue_data.fields.__dict__.get(jira.epic_progress, "")) if hasattr(issue_data.fields, jira.epic_progress) else colorize("Progress Not Found", "neg")
    initiative_start_date = issue_data.fields.__dict__.get(jira.epic_start_date, colorize("Not Assigned", "neg")) if hasattr(issue_data.fields, jira.epic_start_date) else colorize("Not Assigned", "neg")
    initiative_end_date = issue_data.fields.__dict__.get(jira.epic_end_date, colorize("Not Assigned", "neg")) if hasattr(issue_data.fields, jira.epic_end_date) else colorize("Not Assigned", "neg")
    initiative_data = [
        colorize("No Parent", "neg") if parent == colorize("No Parent", "neg") or not parent else link_text(text=parent),
        colorize("Progress Not Found", "neg") if initiative_progress == colorize("Progress Not Found", "neg") or not initiative_progress else initiative_progress,
        colorize("Not Assigned", "neg") if initiative_start_date == colorize("Not Assigned", "neg") or not initiative_start_date else initiative_start_date,
        colorize("Not Assigned", "neg") if initiative_end_date == colorize("Not Assigned", "neg") or not initiative_end_date else initiative_end_date
    ]
    return initiative_headers, initiative_data

def get_story_data(jira, issue_data):
    """
    Extract story-specific data fields from the issue data.

    Args:
        issue_data (dict): The issue data to extract story information from.

    Returns:
        tuple: A tuple containing story-specific headers and values.
    """
    story_headers = ["Parent", "Initial Story Points", "Actual Story Points", "Sprints"]
    parent = issue_data.fields.__dict__.get(jira.epic_link, colorize("No Parent", "neg"))
    original_story_points = issue_data.fields.__dict__.get(jira.original_story_points, colorize("Not Assigned", "neg"))
    actual_story_points = issue_data.fields.__dict__.get(jira.story_points, colorize("Not Assigned", "neg"))
    sprints = extract_sprints(issue_data.fields.__dict__.get(jira.sprints, [])) if hasattr(issue_data.fields, jira.sprints) else colorize("No Sprints", "neg")
    story_data = [
        colorize("No Parent", "neg") if parent == colorize("No Parent", "neg") or not parent else link_text(text=parent),
        colorize("Not Assigned", "neg") if original_story_points == colorize("Not Assigned", "neg") or not original_story_points else int(original_story_points),
        colorize("Not Assigned", "neg") if actual_story_points == colorize("Not Assigned", "neg") or not actual_story_points else int(actual_story_points),
        colorize("No Sprints", "neg") if sprints == colorize("No Sprints", "neg") or not sprints else sprints
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
        display_epic(common_headers+epic_headers, [common_data+epic_data], output, show)
    elif issue_type == "Initiative":
        # Get initiative specific data
        initiative_headers, initiative_data = get_initiative_data(jira, issue_data)
        display_initiative(common_headers+initiative_headers, [common_data+initiative_data], output, show)
    else:
        # Get story specific data
        story_headers, story_data = get_story_data(jira, issue_data)
        display_story(common_headers+story_headers, [common_data+story_data], output, show)
