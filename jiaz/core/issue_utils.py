from jiaz.core.jira_comms import JiraComms
from jiaz.core.display import display_epic, display_story, display_initiative
from jiaz.core.formatter import strip_ansi, colorize, link_text, color_map
import typer
import re
import sys
import pyperclip


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


def get_common_data(jira, issue_data):
    """
    Extract common data fields from the story data.

    Args:
        story_data (dict): The story data to format.

    Returns:
        tuple: A tuple containing common data and common values.
    """
    common_headers = ["Key", "Title", "Type", "Assignee", "Reporter", "Work Type", "Status", "Priority", "labels", "Children"]

    issue_key = issue_data.key if hasattr(issue_data, 'key') else colorize("Unknown", "neg")
    issue_title = issue_data.fields.summary if hasattr(issue_data.fields, 'summary') else colorize("No Title", "neg")
    issue_type = issue_data.fields.issuetype.name if hasattr(issue_data.fields, 'issuetype') else colorize("Unknown", "neg")
    issue_assignee = issue_data.fields.assignee.displayName if hasattr(issue_data.fields, 'assignee') and issue_data.fields.assignee else colorize("Unassigned", "neg")
    issue_reporter = issue_data.fields.reporter.displayName if hasattr(issue_data.fields, 'reporter') and issue_data.fields.reporter else colorize("Unknown", "neg")
    issue_work_type = (field_obj := issue_data.fields.__dict__.get(jira.work_type)) and field_obj.value or colorize("Undefined", "neg")
    issue_status = issue_data.fields.status.name if hasattr(issue_data.fields, 'status') else colorize("Undefined", "neg")
    issue_priority = issue_data.fields.priority.name if hasattr(issue_data.fields, 'priority') else colorize("Undefined", "neg")
    issue_labels = ", ".join(issue_data.fields.labels) if hasattr(issue_data.fields, 'labels') else colorize("No Labels", "neg")
    issue_children = get_issue_children(jira, issue_key)
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
        colorize("No Children", "neg") if not issue_children else ", ".join(issue_children)
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

## AI backed function for updated description
def marshal_issue_description(jira, issue_data, output_format="table"):
    """
    Marshal (standardize) issue description using AI and handle user confirmation.
    
    Args:
        jira: JiraComms instance
        issue_data: JIRA issue object
        output_format: Display format for comparison
        
    Returns:
        bool: True if description was updated, False otherwise
    """
    from jiaz.core.ai_utils import JiraIssueAI
    from jiaz.core.formatter import format_description_comparison
    
    # Get current description
    original_description = getattr(issue_data.fields, 'description', '') or ''
    
    if not original_description.strip():
        typer.secho("⚠️  Issue has no description to standardize.", fg=typer.colors.YELLOW)
        return False
    
    try:
        # Initialize AI helper
        jira_ai = JiraIssueAI()

        # Generate standardized description
        typer.secho(f"📝 Analyzing description for {issue_data.key}...", fg=typer.colors.CYAN)
        standardized_description = jira_ai.standardize_description(
            original_description)
        # Check if standardized description was generated
        typer.secho("🔄 Standardizing description...", fg=typer.colors.CYAN)
        
        if not standardized_description or "Failed to generate" in standardized_description:
            typer.secho("❌ Could not generate standardized description.", fg=typer.colors.RED)
            return False
        
        # Display comparison using the new comprehensive function
        typer.secho("\n" + "="*80, fg=typer.colors.BLUE)
        typer.secho("📋 DESCRIPTION COMPARISON", fg=typer.colors.BLUE, bold=True)
        typer.secho("="*80, fg=typer.colors.BLUE)
        # Display the formatted output
        output = format_description_comparison(original_description, standardized_description, output_format)
        # sys.stdout.write(output + "\n")        
        typer.secho("\n" + "="*80, fg=typer.colors.BLUE)
        typer.secho("💡 The preview shows how the content will appear with proper JIRA formatting", fg=typer.colors.CYAN)
        typer.secho("💡 All markup (bold, links, sections) is rendered as it would appear in JIRA", fg=typer.colors.CYAN)
                
        # Ask for action
        typer.secho("\nWhat would you like to do with the standardized description?", fg=typer.colors.BLUE, bold=True)
        typer.secho("1. Copy to clipboard", fg=typer.colors.GREEN)
        typer.secho("2. Exit and do nothing", fg=typer.colors.YELLOW)
        typer.secho("3. Update on JIRA", fg=typer.colors.CYAN)
        choice = typer.prompt("Enter your choice (1/2/3)", type=int)

        if choice == 1:
            pyperclip.copy(standardized_description)
            typer.secho("✅ Standardized description copied to clipboard.", fg=typer.colors.GREEN)
            return False
        elif choice == 2:
            typer.secho("❌ Exiting without updating.", fg=typer.colors.YELLOW)
            return False
        elif choice == 3:
            # Update the issue as before
            # return update_issue_description_with_backup(jira, issue_data, original_description, standardized_description)
            pass
        else:
            typer.secho("❌ Invalid choice. Exiting.", fg=typer.colors.RED)
            return False
        
    except Exception as e:
        typer.secho(f"❌ Error during description marshaling: {e}", fg=typer.colors.RED)
        return False

# def update_issue_description_with_backup(jira, issue_data, original_description, new_description):
#     """
#     Update issue description and add original as pinned comment.
    
#     Args:
#         jira: JiraComms instance
#         issue_data: JIRA issue object
#         original_description: Original description to backup
#         new_description: New standardized description
        
#     Returns:
#         bool: True if successful, False otherwise
#     """
#     try:
#         # Add original description as pinned comment
#         backup_comment = f"""📋 **Original Description (Backup)**

# This comment contains the original description before AI standardization on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}.

# ---

# {original_description}

# ---
# *This backup was created automatically by jiaz AI description marshaling.*"""
        
#         typer.secho("💾 Creating backup comment with original description...", fg=typer.colors.CYAN)
#         jira.rate_limited_request(jira.jira.add_comment, issue_data.key, backup_comment)
        
#         # Update the description
#         typer.secho("🔄 Updating issue description...", fg=typer.colors.CYAN)
#         jira.rate_limited_request(
#             issue_data.update, 
#             fields={'description': new_description}
#         )
        
#         typer.secho("✅ Description updated successfully!", fg=typer.colors.GREEN)
#         typer.secho(f"📌 Original description backed up as pinned comment", fg=typer.colors.GREEN)
        
#         return True
        
#     except Exception as e:
#         typer.secho(f"❌ Failed to update issue: {e}", fg=typer.colors.RED)
#         return False


def analyze_issue(id: str, output="json", config=None, show="<pre-defined>", rundown=False, marshal_description=False):
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

    # Handle description marshaling if requested
    if marshal_description:
        marshal_issue_description(jira, issue_data, output)
        # For marshal description, we only show the comparison and exit
        return

    # # Handle progress summary from comment if requested - issue #14
    # if rundown:
    #     from jiaz.core.ai_utils import JiraIssueAI
    #     jira_ai = JiraIssueAI()
        
    #     typer.secho("📝 Extracting comments from main ticket and subtasks...", fg=typer.colors.CYAN)
    #     parent_comments = jira_ai.extract_comments_from_issue(jira, issue_data)
    #     subtask_comments = jira_ai.get_subtask_comments(jira, issue_data.key)
        
    #     total_comments = len(parent_comments) + len(subtask_comments)
    #     typer.secho(f"📊 Found {len(parent_comments)} parent comments and {len(subtask_comments)} subtask comments", fg=typer.colors.BLUE)
        
    #     if total_comments > 0:
    #         summary = jira_ai.generate_progress_summary(issue_data, parent_comments, subtask_comments, ai_model)
    #         typer.echo("\n" + "="*80)
    #         typer.secho("🤖 AI PROGRESS SUMMARY", fg=typer.colors.GREEN, bold=True)
    #         typer.echo("="*80)
    #         typer.echo(summary)
    #         typer.echo("="*80)
    #     else:
    #         typer.secho("⚠️  No comments found for AI analysis", fg=typer.colors.YELLOW)
    #     return

    # Get common data
    common_headers, common_data = get_common_data(jira, issue_data)

    if issue_data.fields.issuetype.name == "Epic":
        # Get epic specific data
        epic_headers, epic_data = get_epic_data(jira, issue_data)
        display_epic(common_headers+epic_headers, [common_data+epic_data], output, show)
    elif issue_data.fields.issuetype.name == "Initiative":
        # Get initiative specific data
        initiative_headers, initiative_data = get_initiative_data(jira, issue_data)
        display_initiative(common_headers+initiative_headers, [common_data+initiative_data], output, show)
    else:
        # Get story specific data
        story_headers, story_data = get_story_data(jira, issue_data)
        display_story(common_headers+story_headers, [common_data+story_data], output, show)
