from jiaz.core.jira_comms import JiraComms
from jiaz.core.display import display_epic, display_story, display_initiative
from jiaz.core.formatter import strip_ansi, colorize, link_text, color_map
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
        issue_key = issue.raw['key']
        url = issue.permalink()
        issue_key = link_text(issue_key, url)
        status = issue.fields.status.name if hasattr(issue.fields, 'status') else "Unknown"
        children.append(color_map(issue_key, status))
    return children


def get_issue_fields(jira, issue_data, requested_fields=None):
    """
    Extract requested data fields from JIRA issue data.
    
    Args:
        jira (JiraComms): The JiraComms instance containing custom field mappings.
        issue_data: The JIRA issue data object.
        requested_fields (list): List of field names to extract. If None, returns all available fields.
    
    Returns:
        dict: Dictionary containing the requested field values with field names as keys.
    """
    if requested_fields is None:
        requested_fields = [
            'key', 'title', 'type', 'assignee', 'reporter', 'work_type', 'status', 
            'priority', 'labels', 'children', 'parent_link', 'epic_link', 
            'epic_progress', 'epic_start_date', 'epic_end_date', 'original_story_points', 
            'story_points', 'sprints'
        ]
    
    # Define field extraction logic
    field_extractors = {
        # Standard fields
        'key': lambda: issue_data.key if hasattr(issue_data, 'key') else colorize("Unknown", "neg"),
        'title': lambda: issue_data.fields.summary if hasattr(issue_data.fields, 'summary') else colorize("No Title", "neg"),
        'type': lambda: issue_data.fields.issuetype.name if hasattr(issue_data.fields, 'issuetype') else colorize("Unknown", "neg"),
        'assignee': lambda: issue_data.fields.assignee.displayName if hasattr(issue_data.fields, 'assignee') and issue_data.fields.assignee else colorize("Unassigned", "neg"),
        'reporter': lambda: issue_data.fields.reporter.displayName if hasattr(issue_data.fields, 'reporter') and issue_data.fields.reporter else colorize("Unknown", "neg"),
        'status': lambda: issue_data.fields.status.name if hasattr(issue_data.fields, 'status') else colorize("Undefined", "neg"),
        'priority': lambda: issue_data.fields.priority.name if hasattr(issue_data.fields, 'priority') else colorize("Undefined", "neg"),
        'labels': lambda: ", ".join(issue_data.fields.labels) if hasattr(issue_data.fields, 'labels') else colorize("No Labels", "neg"),
        'children': lambda: get_issue_children(jira, issue_data.key if hasattr(issue_data, 'key') else ''),
        
        # Custom fields
        'work_type': lambda: (field_obj := issue_data.fields.__dict__.get(jira.work_type)) and field_obj.value or colorize("Undefined", "neg"),
        'original_story_points': lambda: issue_data.fields.__dict__.get(jira.original_story_points, colorize("Not Assigned", "neg")),
        'story_points': lambda: issue_data.fields.__dict__.get(jira.story_points, colorize("Not Assigned", "neg")),
        'sprints': lambda: extract_sprints(issue_data.fields.__dict__.get(jira.sprints, [])) if hasattr(issue_data.fields, jira.sprints) else colorize("No Sprints", "neg"),
        'epic_link': lambda: issue_data.fields.__dict__.get(jira.epic_link, colorize("No Parent", "neg")),
        'parent_link': lambda: issue_data.fields.__dict__.get(jira.parent_link, colorize("No Parent", "neg")) if hasattr(issue_data.fields, jira.parent_link) else colorize("No Parent", "neg"),
        'epic_progress': lambda: extract_epic_progress(issue_data.fields.__dict__.get(jira.epic_progress, "")) if hasattr(issue_data.fields, jira.epic_progress) else colorize("Progress Not Found", "neg"),
        'epic_start_date': lambda: issue_data.fields.__dict__.get(jira.epic_start_date, colorize("Not Assigned", "neg")) if hasattr(issue_data.fields, jira.epic_start_date) else colorize("Not Assigned", "neg"),
        'epic_end_date': lambda: issue_data.fields.__dict__.get(jira.epic_end_date, colorize("Not Assigned", "neg")) if hasattr(issue_data.fields, jira.epic_end_date) else colorize("Not Assigned", "neg"),
    }
    
    # Extract requested fields
    result = {}
    for field_name in requested_fields:
        if field_name in field_extractors:
            try:
                result[field_name] = field_extractors[field_name]()
            except Exception as e:
                result[field_name] = colorize(f"Error extracting {field_name}", "neg")
        else:
            result[field_name] = colorize(f"Unknown field: {field_name}", "neg")
    
    return result

def get_common_data(jira, issue_data):
    """
    Extract common data fields from the story data.

    Args:
        story_data (dict): The story data to format.

    Returns:
        tuple: A tuple containing common data and common values.
    """
    common_headers = ["Key", "Title", "Type", "Assignee", "Reporter", "Work Type", "Status", "Priority", "labels", "Children"]
    common_fields = ['key', 'title', 'type', 'assignee', 'reporter', 'work_type', 'status', 'priority', 'labels', 'children']
    
    # Get field data using the unified function
    field_data = get_issue_fields(jira, issue_data, common_fields)
    
    # Format data for display (apply link formatting and handle negative cases)
    issue_key = field_data['key']
    common_data = [
        issue_key if issue_key == colorize("Unknown", "neg") else link_text(text=issue_key, url=issue_data.permalink()),
        field_data['title'],
        field_data['type'],
        colorize("Unassigned", "neg") if field_data['assignee'] == colorize("Unassigned", "neg") or not field_data['assignee'] else field_data['assignee'],
        colorize("Unknown", "neg") if field_data['reporter'] == colorize("Unknown", "neg") or not field_data['reporter'] else field_data['reporter'],
        colorize("Undefined", "neg") if field_data['work_type'] == colorize("Undefined", "neg") or not field_data['work_type'] else field_data['work_type'],
        colorize("Undefined", "neg") if field_data['status'] == colorize("Undefined", "neg") or not field_data['status'] else field_data['status'],
        colorize("Undefined", "neg") if field_data['priority'] == colorize("Undefined", "neg") or not field_data['priority'] else field_data['priority'],
        colorize("No Labels", "neg") if field_data['labels'] == colorize("No Labels", "neg") or not field_data['labels'] else field_data['labels'],
        colorize("No Children", "neg") if not field_data['children'] else ", ".join(field_data['children'])
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
    epic_fields = ['parent_link', 'epic_progress', 'epic_start_date', 'epic_end_date']
    
    # Get field data using the unified function
    field_data = get_issue_fields(jira, issue_data, epic_fields)
    
    epic_data = [
        colorize("No Parent", "neg") if field_data['parent_link'] == colorize("No Parent", "neg") or not field_data['parent_link'] else link_text(text=field_data['parent_link']),
        colorize("Progress Not Found", "neg") if field_data['epic_progress'] == colorize("Progress Not Found", "neg") or not field_data['epic_progress'] else field_data['epic_progress'],
        colorize("Not Assigned", "neg") if field_data['epic_start_date'] == colorize("Not Assigned", "neg") or not field_data['epic_start_date'] else field_data['epic_start_date'],
        colorize("Not Assigned", "neg") if field_data['epic_end_date'] == colorize("Not Assigned", "neg") or not field_data['epic_end_date'] else field_data['epic_end_date']
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
    # Initiative data is identical to epic data
    return get_epic_data(jira, issue_data)

def get_story_data(jira, issue_data):
    """
    Extract story-specific data fields from the issue data.

    Args:
        issue_data (dict): The issue data to extract story information from.

    Returns:
        tuple: A tuple containing story-specific headers and values.
    """
    story_headers = ["Parent", "Initial Story Points", "Actual Story Points", "Sprints"]
    story_fields = ['epic_link', 'original_story_points', 'story_points', 'sprints']
    
    # Get field data using the unified function
    field_data = get_issue_fields(jira, issue_data, story_fields)
    
    story_data = [
        colorize("No Parent", "neg") if field_data['epic_link'] == colorize("No Parent", "neg") or not field_data['epic_link'] else link_text(text=field_data['epic_link']),
        colorize("Not Assigned", "neg") if field_data['original_story_points'] == colorize("Not Assigned", "neg") or not field_data['original_story_points'] else int(field_data['original_story_points']),
        colorize("Not Assigned", "neg") if field_data['story_points'] == colorize("Not Assigned", "neg") or not field_data['story_points'] else int(field_data['story_points']),
        colorize("No Sprints", "neg") if field_data['sprints'] == colorize("No Sprints", "neg") or not field_data['sprints'] else field_data['sprints']
    ]
    return story_headers, story_data

def get_custom_field_subset(jira, issue_data, field_names):
    """
    Convenience function to extract a custom subset of fields from JIRA issue data.
    
    Example usage:
        # Get only assignee and status
        data = get_custom_field_subset(jira, issue_data, ['assignee', 'status'])
        
        # Get all story-related fields
        data = get_custom_field_subset(jira, issue_data, ['epic_link', 'story_points', 'sprints'])
        
        # Get all epic/initiative fields
        data = get_custom_field_subset(jira, issue_data, ['parent_link', 'epic_progress', 'epic_start_date', 'epic_end_date'])
    
    Available field names:
        Standard fields: 'key', 'title', 'type', 'assignee', 'reporter', 'status', 'priority', 'labels', 'children'
        Custom fields: 'work_type', 'original_story_points', 'story_points', 'sprints', 'epic_link', 'parent_link', 
                      'epic_progress', 'epic_start_date', 'epic_end_date'
    
    Args:
        jira (JiraComms): The JiraComms instance containing custom field mappings.
        issue_data: The JIRA issue data object.
        field_names (list): List of field names to extract.
    
    Returns:
        dict: Dictionary containing the requested field values with field names as keys.
    """
    return get_issue_fields(jira, issue_data, field_names)

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
