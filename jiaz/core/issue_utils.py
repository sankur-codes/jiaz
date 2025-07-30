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

def _get_field_definitions(jira, issue_data):
    """
    Core function that defines all field extraction logic.
    Organizes fields into categories for better management.
    
    Returns:
        dict: Field definitions organized by category with extraction logic.
    """
    return {
        # REQUIRED FIELDS - Always included in get_all_available_data()
        'required': {
            'key': {
                'header': 'Key',
                'extractor': lambda: issue_data.key if hasattr(issue_data, 'key') else colorize("Unknown", "neg"),
                'exists_check': lambda: hasattr(issue_data, 'key')
            },
            'title': {
                'header': 'Title', 
                'extractor': lambda: issue_data.fields.summary if hasattr(issue_data.fields, 'summary') else colorize("No Title", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, 'summary')
            },
            'type': {
                'header': 'Type',
                'extractor': lambda: issue_data.fields.issuetype.name if hasattr(issue_data.fields, 'issuetype') else colorize("Unknown", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, 'issuetype')
            },
            'assignee': {
                'header': 'Assignee',
                'extractor': lambda: issue_data.fields.assignee.displayName if hasattr(issue_data.fields, 'assignee') and issue_data.fields.assignee else colorize("Unassigned", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, 'assignee')
            },
            'reporter': {
                'header': 'Reporter',
                'extractor': lambda: issue_data.fields.reporter.displayName if hasattr(issue_data.fields, 'reporter') and issue_data.fields.reporter else colorize("Unknown", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, 'reporter')
            },
            'status': {
                'header': 'Status',
                'extractor': lambda: issue_data.fields.status.name if hasattr(issue_data.fields, 'status') else colorize("Undefined", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, 'status')
            }
        },
        
        # OPTIONAL FIELDS - Included in get_all_available_data() if they exist
        'optional': {
            'priority': {
                'header': 'Priority',
                'extractor': lambda: issue_data.fields.priority.name if hasattr(issue_data.fields, 'priority') and issue_data.fields.priority else colorize("No Priority", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, 'priority')
            },
            'labels': {
                'header': 'Labels',
                'extractor': lambda: ", ".join(issue_data.fields.labels) if hasattr(issue_data.fields, 'labels') and issue_data.fields.labels else colorize("No Labels", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, 'labels')
            },
            'children': {
                'header': 'Children',
                'extractor': lambda: get_issue_children(jira, issue_data.key if hasattr(issue_data, 'key') else ''),
                'exists_check': lambda: True  # Always include children check
            }
        },
        
        # ON-DEMAND FIELDS - Only included when specifically requested
        'on_demand': {
            'description': {
                'header': 'Description',
                'extractor': lambda: strip_ansi(issue_data.fields.description) if hasattr(issue_data.fields, 'description') and issue_data.fields.description else colorize("No Description", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, 'description')
            },
            'comments': {
                'header': 'Comments',
                'extractor': lambda: issue_data.fields.comment.comments if hasattr(issue_data.fields, 'comment') and hasattr(issue_data.fields.comment, 'comments') else [],
                'exists_check': lambda: hasattr(issue_data.fields, 'comment')
            },
            'status_summary': {
                'header': 'Status Summary',
                'extractor': lambda: issue_data.fields.__dict__.get(jira.status_summary) or colorize("No Status Summary", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, jira.status_summary) or jira.status_summary in issue_data.fields.__dict__,
                'field_id': jira.status_summary
            },
            'updated': {
                'header': 'Last Updated',
                'extractor': lambda: issue_data.fields.updated if hasattr(issue_data.fields, 'updated') else colorize("No Updated", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, 'updated')
            }
        },
        
        # CUSTOM FIELDS - Project-specific fields that may or may not exist
        'custom': {
            'work_type': {
                'header': 'Work Type',
                'extractor': lambda: (field_obj := issue_data.fields.__dict__.get(jira.work_type)) and field_obj.value or colorize("Not Set", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, jira.work_type) or jira.work_type in issue_data.fields.__dict__,
                'field_id': jira.work_type
            },
            'original_story_points': {
                'header': 'Initial Story Points',
                'extractor': lambda: int(val) if (val := issue_data.fields.__dict__.get(jira.original_story_points)) and val is not None else None,
                'exists_check': lambda: hasattr(issue_data.fields, jira.original_story_points) or jira.original_story_points in issue_data.fields.__dict__,
                'field_id': jira.original_story_points
            },
            'story_points': {
                'header': 'Actual Story Points', 
                'extractor': lambda: int(val) if (val := issue_data.fields.__dict__.get(jira.story_points)) and val is not None else None,
                'exists_check': lambda: hasattr(issue_data.fields, jira.story_points) or jira.story_points in issue_data.fields.__dict__,
                'field_id': jira.story_points
            },
            'sprints': {
                'header': 'Sprints',
                'extractor': lambda: extract_sprints(issue_data.fields.__dict__.get(jira.sprints, [])) if issue_data.fields.__dict__.get(jira.sprints) else colorize("No Sprints", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, jira.sprints) or jira.sprints in issue_data.fields.__dict__,
                'field_id': jira.sprints
            },
            'epic_link': {
                'header': 'Epic Link',
                'extractor': lambda: issue_data.fields.__dict__.get(jira.epic_link) or colorize("No Epic", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, jira.epic_link) or jira.epic_link in issue_data.fields.__dict__,
                'field_id': jira.epic_link
            },
            'parent_link': {
                'header': 'Parent Link', 
                'extractor': lambda: issue_data.fields.__dict__.get(jira.parent_link) or colorize("No Parent", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, jira.parent_link) or jira.parent_link in issue_data.fields.__dict__,
                'field_id': jira.parent_link
            },
            'epic_progress': {
                'header': 'Progress',
                'extractor': lambda: extract_epic_progress(val) if (val := issue_data.fields.__dict__.get(jira.epic_progress)) else colorize("No Progress", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, jira.epic_progress) or jira.epic_progress in issue_data.fields.__dict__,
                'field_id': jira.epic_progress
            },
            'epic_start_date': {
                'header': 'Start Date',
                'extractor': lambda: issue_data.fields.__dict__.get(jira.epic_start_date) or colorize("No Start Date", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, jira.epic_start_date) or jira.epic_start_date in issue_data.fields.__dict__,
                'field_id': jira.epic_start_date
            },
            'epic_end_date': {
                'header': 'End Date',
                'extractor': lambda: issue_data.fields.__dict__.get(jira.epic_end_date) or colorize("No End Date", "neg"),
                'exists_check': lambda: hasattr(issue_data.fields, jira.epic_end_date) or jira.epic_end_date in issue_data.fields.__dict__,
                'field_id': jira.epic_end_date
            }
        }
    }

def get_issue_fields(jira, issue_data, requested_fields=None):
    """
    Extract requested data fields from JIRA issue data.
    
    Args:
        jira (JiraComms): The JiraComms instance containing custom field mappings.
        issue_data: The JIRA issue data object.
        requested_fields (list): List of field names to extract. If None, returns all available fields.
    
    Returns:
        dict: Dictionary containing the requested field values with field names as keys.
        
    Available fields:
        Required: 'key', 'title', 'type', 'assignee', 'reporter', 'status'
        Optional: 'priority', 'labels', 'children'
        On-demand: 'description', 'comments', 'status_summary', 'updated' (only when explicitly requested)
        Custom: 'work_type', 'original_story_points', 'story_points', 'sprints', 
               'epic_link', 'parent_link', 'epic_progress', 'epic_start_date', 'epic_end_date'
    """
    field_categories = _get_field_definitions(jira, issue_data)
    
    # If no specific fields requested, include all categories except on-demand
    if requested_fields is None:
        requested_fields = []
        for category in ['required', 'optional', 'custom']:
            requested_fields.extend(field_categories[category].keys())
    
    # Create flat field mapping for easy lookup
    all_fields = {}
    for category_fields in field_categories.values():
        all_fields.update(category_fields)
    
    # Extract requested fields
    result = {}
    for field_name in requested_fields:
        if field_name in all_fields:
            try:
                result[field_name] = all_fields[field_name]['extractor']()
            except Exception as e:
                result[field_name] = colorize(f"Error extracting {field_name}", "neg")
        else:
            result[field_name] = colorize(f"Unknown field: {field_name}", "neg")
    
    return result

def get_all_available_data(jira, issue_data):
    """
    Extract all available data fields from JIRA issue data dynamically.
    Only includes fields that actually exist in the issue data.
    
    Field inclusion logic:
    - Required fields: Always included
    - Optional fields: Included if they exist
    - On-demand fields: NEVER included (must be explicitly requested via get_issue_fields)
    - Custom fields: Included if they exist in the JIRA instance
    
    Args:
        jira (JiraComms): The JiraComms instance containing custom field mappings.
        issue_data: The JIRA issue data object.
    
    Returns:
        tuple: (headers, data) - Lists of headers and corresponding values for existing fields.
        
    Examples:
        # Get all available data for any issue type (excludes on-demand fields)
        headers, data = get_all_available_data(jira, issue_data)
        
        # To include on-demand fields like comments, description:
        data_dict = get_issue_fields(jira, issue_data, ['key', 'title', 'comments', 'description'])
    """
    field_categories = _get_field_definitions(jira, issue_data)
    
    headers = []
    data = []
    
    # Include required and optional fields (but NOT on-demand fields)
    categories_to_include = ['required', 'optional', 'custom']
    
    for category in categories_to_include:
        for field_name, field_def in field_categories[category].items():
            # Check if field exists before including it
            try:
                if field_def['exists_check']():
                    headers.append(field_def['header'])
                    extracted_value = field_def['extractor']()
                    
                    # Apply special formatting
                    extracted_value = _apply_field_formatting(field_name, extracted_value, issue_data)
                    data.append(extracted_value)
            except Exception as e:
                # Skip fields that cause errors during existence check
                continue
    
    return headers, data

def _apply_field_formatting(field_name, value, issue_data):
    """
    Apply special formatting to specific field types.
    
    Args:
        field_name (str): The name of the field
        value: The extracted value
        issue_data: The JIRA issue data object
    
    Returns:
        Formatted value
    """
    # Import here to avoid circular imports
    from jiaz.core.formatter import link_text, colorize
    
    if field_name == 'key' and value != colorize("Unknown", "neg"):
        return link_text(text=value, url=issue_data.permalink())
    elif field_name in ['epic_link', 'parent_link'] and value not in [colorize("No Epic", "neg"), colorize("No Parent", "neg")]:
        return link_text(text=value)
    elif field_name in ['original_story_points', 'story_points']:
        # For story points, apply colorization only for display
        return value if value is not None else colorize("Not Set", "neg")
    elif field_name == 'children':
        if value and not isinstance(value, str):
            return ", ".join(value) if value else colorize("No Children", "neg")
        elif not value:
            return colorize("No Children", "neg")
    
    return value

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
