from jiaz.core.jira_comms import Sprint
from jiaz.core.formatter import link_text, colorize
from jiaz.core.display import display_sprint_issue, display_sprint_status, display_sprint_owner
from jiaz.core.issue_utils import get_issue_fields
import typer

def get_data_table(sprint, mine=False):
    """
    Retrieve and process the data table from the sprint issues.
    
    This function fetches issues from the current active sprint, processes them to extract relevant details,
    and returns a structured data table.
    
    Args:
        sprint (Sprint): An instance of the Sprint class to interact with Jira.
    
    Returns:
        list: A list of lists representing the data table of sprint issues.
    """
    issues_in_sprint = sprint.get_issues_in_sprint(mine=mine)

    if issues_in_sprint is None:
        typer.echo("No matching issues found in the sprint.")
        raise typer.Exit(code=1)

    data_table = []
    for issue_key in issues_in_sprint:
        issue = sprint.get_issue(issue_key)

        # Extract fields using the unified function
        required_fields = ['work_type', 'title', 'priority', 'status', 'assignee', 'original_story_points', 'story_points']
        field_data = get_issue_fields(sprint, issue, required_fields)
        
        comments = issue.fields.comment.comments
        url = issue.permalink()
        issue_key_link = link_text(issue_key, url)

        if issue.fields.assignee is None:
            print(f"\nSkipping {issue.key} as there's no assignee yet\n")
            continue

        assignee = field_data['assignee'].split(" ")[0] if field_data['assignee'] != colorize("Unassigned", "neg") else field_data['assignee']
        original_story_points, story_points = sprint.update_story_points(issue, field_data['original_story_points'], field_data['story_points'])
        latest_comment_details = sprint.get_comment_details(comments, field_data['status'])

        data_table.append([
            assignee, issue_key_link, field_data['title'], field_data['priority'], field_data['work_type'],
            original_story_points, story_points, field_data['status'], latest_comment_details
        ])

    # Return everything as a bundle
    return data_table


def analyze_sprint(wrt="status", output="json", config=None, show="<pre-defined>", mine=False):
    """
    Analyze the current active sprint data and display it in a specified format.
    
    This function retrieves sprint data from Jira, processes it, and displays it in a user-friendly format.
    It can be customized to focus on different perspectives such as issue, owner, or status.
    Args:
        wrt (str): The perspective to focus on. Options are 'issue', 'owner', or 'status'.
        output (str): The format to display the data. Options are 'table', 'json', or 'csv'.
        config (str): The configuration name to use for connecting to Jira.
    """
    # Placeholder for the actual implementation
    print(f"Analyzing sprint data focusing on '{wrt}' using config '{config}' and  displaying in '{output}' format.")
    sprint = Sprint(config_name=config)
    all_headers = ["Assignee", "Issue Key", "Title", "Priority", "Work Type", 
                    "Initial Story Points", "Actual Story Points", "Status", "Comment"]
    data_table = get_data_table(sprint, mine)

    # Provide data based on the perspective required
    if wrt == "issue":
        display_sprint_issue(data_table, all_headers, output, show)
    elif wrt == "owner":
        display_sprint_owner(data_table, all_headers, output, show)
    else:
        display_sprint_status(data_table, all_headers, output, show)


