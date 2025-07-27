from jiaz.core.jira_comms import JiraComms
from jiaz.core.display import display_issue
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
    
    NOTE: For comprehensive data extraction with dynamic field discovery, 
    prefer using get_all_available_data() which automatically includes only 
    existing fields and provides proper headers.
    
    Args:
        jira (JiraComms): The JiraComms instance containing custom field mappings.
        issue_data: The JIRA issue data object.
        requested_fields (list): List of field names to extract. If None, returns all available fields.
    
    Returns:
        dict: Dictionary containing the requested field values with field names as keys.
        
    Available fields:
        Standard: 'key', 'title', 'type', 'assignee', 'reporter', 'status', 'priority', 
                    'labels', 'children', 'description', 'comments'
        Custom: 'work_type', 'original_story_points', 'story_points', 'sprints', 
                'epic_link', 'parent_link', 'epic_progress', 'epic_start_date', 
                'epic_end_date', 'status_summary'
    """
    if requested_fields is None:
        requested_fields = [
            'key', 'title', 'type', 'assignee', 'reporter', 'work_type', 'status', 
            'priority', 'labels', 'children', 'description', 'comments', 'parent_link', 'epic_link', 
            'epic_progress', 'epic_start_date', 'epic_end_date', 'original_story_points', 
            'story_points', 'sprints', 'status_summary'
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
        'description': lambda: strip_ansi(issue_data.fields.description) if hasattr(issue_data.fields, 'description') and issue_data.fields.description else colorize("No Description", "neg"),
        'comments': lambda: issue_data.fields.comment.comments if hasattr(issue_data.fields, 'comment') and hasattr(issue_data.fields.comment, 'comments') else [],
        
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
        'status_summary': lambda: issue_data.fields.__dict__.get(jira.status_summary, colorize("No Status Summary", "neg"))
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


def get_all_available_data(jira, issue_data):
    """
    Extract all available data fields from JIRA issue data dynamically.
    Only includes fields that actually exist in the issue data.
    
    This is the SINGLE UNIFIED function for ALL data extraction from JIRA issues.
    It replaces all previous type-specific extraction functions and handles:
    - Standard JIRA fields (key, title, assignee, etc.)
    - Custom fields (story points, epic links, etc.) 
    - Comments and descriptions
    - Dynamic field discovery (only shows fields that exist)
    
    Args:
        jira (JiraComms): The JiraComms instance containing custom field mappings.
        issue_data: The JIRA issue data object.
    
    Returns:
        tuple: (headers, data) - Lists of headers and corresponding values for existing fields.
        
    Examples:
        # Get all available data for any issue type
        headers, data = get_all_available_data(jira, issue_data)
        
        # The function automatically includes only fields that exist:
        # - Epic with progress field → "Progress" included in headers
        # - Story without progress → "Progress" completely excluded  
        # - Issue with comments → "Comments" included with comment list
        # - Issue with empty description → "Description" shows red "No Description"
        # - Missing custom field → Field completely excluded from output
    """
    # Define all possible fields with their display names and extraction logic
    all_field_definitions = {
        # Standard fields - these should always be present
        'key': {
            'header': 'Key',
            'extractor': lambda: issue_data.key if hasattr(issue_data, 'key') else colorize("Unknown", "neg"),
            'required': True
        },
        'title': {
            'header': 'Title', 
            'extractor': lambda: issue_data.fields.summary if hasattr(issue_data.fields, 'summary') else colorize("No Title", "neg"),
            'required': True
        },
        'type': {
            'header': 'Type',
            'extractor': lambda: issue_data.fields.issuetype.name if hasattr(issue_data.fields, 'issuetype') else colorize("Unknown", "neg"),
            'required': True
        },
        'assignee': {
            'header': 'Assignee',
            'extractor': lambda: issue_data.fields.assignee.displayName if hasattr(issue_data.fields, 'assignee') and issue_data.fields.assignee else colorize("Unassigned", "neg"),
            'required': True
        },
        'reporter': {
            'header': 'Reporter',
            'extractor': lambda: issue_data.fields.reporter.displayName if hasattr(issue_data.fields, 'reporter') and issue_data.fields.reporter else colorize("Unknown", "neg"),
            'required': True
        },
        'status': {
            'header': 'Status',
            'extractor': lambda: issue_data.fields.status.name if hasattr(issue_data.fields, 'status') else colorize("Undefined", "neg"),
            'required': True
        },
        'priority': {
            'header': 'Priority',
            'extractor': lambda: issue_data.fields.priority.name if hasattr(issue_data.fields, 'priority') and issue_data.fields.priority else colorize("No Priority", "neg"),
            'required': False
        },
        'labels': {
            'header': 'Labels',
            'extractor': lambda: ", ".join(issue_data.fields.labels) if hasattr(issue_data.fields, 'labels') and issue_data.fields.labels else colorize("No Labels", "neg"),
            'required': False
        },
        'children': {
            'header': 'Children',
            'extractor': lambda: get_issue_children(jira, issue_data.key if hasattr(issue_data, 'key') else ''),
            'required': False
        },
        'description': {
            'header': 'Description',
            'extractor': lambda: strip_ansi(issue_data.fields.description) if hasattr(issue_data.fields, 'description') and issue_data.fields.description else colorize("No Description", "neg"),
            'required': False
        },
        'comments': {
            'header': 'Comments',
            'extractor': lambda: issue_data.fields.comment.comments if hasattr(issue_data.fields, 'comment') and hasattr(issue_data.fields.comment, 'comments') else [],
            'required': False
        },
        
        # Custom fields - check for existence
        'work_type': {
            'header': 'Work Type',
            'extractor': lambda: (field_obj := issue_data.fields.__dict__.get(jira.work_type)) and field_obj.value or colorize("Not Set", "neg"),
            'field_id': lambda: jira.work_type,
            'required': False
        },
        'original_story_points': {
            'header': 'Initial Story Points',
            'extractor': lambda: int(val) if (val := issue_data.fields.__dict__.get(jira.original_story_points)) and val is not None else colorize("Not Set", "neg"),
            'field_id': lambda: jira.original_story_points,
            'required': False
        },
        'story_points': {
            'header': 'Actual Story Points', 
            'extractor': lambda: int(val) if (val := issue_data.fields.__dict__.get(jira.story_points)) and val is not None else colorize("Not Set", "neg"),
            'field_id': lambda: jira.story_points,
            'required': False
        },
        'sprints': {
            'header': 'Sprints',
            'extractor': lambda: extract_sprints(issue_data.fields.__dict__.get(jira.sprints, [])) if issue_data.fields.__dict__.get(jira.sprints) else colorize("No Sprints", "neg"),
            'field_id': lambda: jira.sprints,
            'required': False
        },
        'epic_link': {
            'header': 'Epic Link',
            'extractor': lambda: issue_data.fields.__dict__.get(jira.epic_link) or colorize("No Epic", "neg"),
            'field_id': lambda: jira.epic_link,
            'required': False
        },
        'parent_link': {
            'header': 'Parent Link', 
            'extractor': lambda: issue_data.fields.__dict__.get(jira.parent_link) or colorize("No Parent", "neg"),
            'field_id': lambda: jira.parent_link,
            'required': False
        },
        'epic_progress': {
            'header': 'Progress',
            'extractor': lambda: extract_epic_progress(val) if (val := issue_data.fields.__dict__.get(jira.epic_progress)) else colorize("No Progress", "neg"),
            'field_id': lambda: jira.epic_progress,
            'required': False
        },
        'epic_start_date': {
            'header': 'Start Date',
            'extractor': lambda: issue_data.fields.__dict__.get(jira.epic_start_date) or colorize("No Start Date", "neg"),
            'field_id': lambda: jira.epic_start_date,
            'required': False
        },
        'epic_end_date': {
            'header': 'End Date',
            'extractor': lambda: issue_data.fields.__dict__.get(jira.epic_end_date) or colorize("No End Date", "neg"),
            'field_id': lambda: jira.epic_end_date,
            'required': False
        },
        'status_summary': {
            'header': 'Status Summary',
            'extractor': lambda: issue_data.fields.__dict__.get(jira.status_summary) or colorize("No Status Summary", "neg"),
            'field_id': lambda: jira.status_summary,
            'required': False
        }
    }
    
    headers = []
    data = []
    
    for field_name, field_def in all_field_definitions.items():
        include_field = False
        
        if field_def['required']:
            # Always include required fields
            include_field = True
        else:
            # For optional fields, check if they exist in the issue data
            if 'field_id' in field_def:
                # Custom field - check if the custom field exists
                field_id = field_def['field_id']()
                if hasattr(issue_data.fields, field_id) or field_id in issue_data.fields.__dict__:
                    include_field = True
            else:
                # Standard field - check if it exists
                if field_name == 'priority' and hasattr(issue_data.fields, 'priority'):
                    include_field = True
                elif field_name == 'labels' and hasattr(issue_data.fields, 'labels'):
                    include_field = True
                elif field_name == 'description' and hasattr(issue_data.fields, 'description'):
                    include_field = True
                elif field_name == 'comments' and hasattr(issue_data.fields, 'comment'):
                    include_field = True
                elif field_name == 'children':
                    include_field = True  # Always include children check
        
        if include_field:
            try:
                headers.append(field_def['header'])
                extracted_value = field_def['extractor']()
                
                # Apply special formatting for certain fields
                if field_name == 'key' and extracted_value != colorize("Unknown", "neg"):
                    extracted_value = link_text(text=extracted_value, url=issue_data.permalink())
                elif field_name in ['epic_link', 'parent_link'] and extracted_value not in [colorize("No Epic", "neg"), colorize("No Parent", "neg")]:
                    extracted_value = link_text(text=extracted_value)
                elif field_name == 'children' and extracted_value and not isinstance(extracted_value, str):
                    extracted_value = ", ".join(extracted_value) if extracted_value else colorize("No Children", "neg")
                elif field_name == 'children' and not extracted_value:
                    extracted_value = colorize("No Children", "neg")
                
                data.append(extracted_value)
            except Exception as e:
                headers.append(field_def['header'])
                data.append(colorize(f"Error: {field_name}", "neg"))
    
    return headers, data

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
    print(f"Analyzing issue with id {id} using config '{config}' and  displaying in '{output}' format.")
    jira = JiraComms(config_name=config)
    issue_data = jira.get_issue(id)   

    # get issue type
    issue_type = issue_data.fields.issuetype.name if hasattr(issue_data.fields, 'issuetype') else "Unknown"
    typer.secho(f"🔍 Analyzing JIRA {issue_type}:", fg=typer.colors.CYAN, bold=True, nl=False)
    typer.secho(f" {issue_data.key}", fg=typer.colors.YELLOW, bold=True)

    # Get all available data dynamically
    headers, data = get_all_available_data(jira, issue_data)
    
    # Use unified display function for all issue types
    display_issue(headers, data, output, show)
