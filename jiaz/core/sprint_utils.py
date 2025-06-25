from jiaz.core.jira_comms import Sprint
from jiaz.core.formatter import link_text, colorize
from jiaz.core.display import display_issue, display_status, display_owner

def get_data_table(sprint):
    """
    Retrieve and process the data table from the sprint issues.
    
    This function fetches issues from the current active sprint, processes them to extract relevant details,
    and returns a structured data table.
    
    Args:
        sprint (Sprint): An instance of the Sprint class to interact with Jira.
    
    Returns:
        list: A list of lists representing the data table of sprint issues.
    """
    issues_in_sprint = sprint.get_issues_in_sprint()

    data_table = []
    for issue_key in issues_in_sprint:
        issue = sprint.rate_limited_request(sprint.jira.issue, issue_key)
        if str(issue.fields.issuetype) not in ["Bug", "Story", "Task"]:
            continue

        workType = (field_obj := issue.fields.__dict__.get(sprint.work_type)) and field_obj.value or colorize("Undefined", "neg")
        comments = issue.fields.comment.comments
        url = issue.permalink()
        issue_key = link_text(url, issue_key)
        title = issue.fields.summary
        priority = issue.fields.priority.name
        status = issue.fields.status.name

        if issue.fields.assignee is None:
            print(f"\nSkipping {issue.key} as there's no assignee yet\n")
            continue

        assignee = issue.fields.assignee.displayName.split(" ")[0]
        original_story_points = issue.fields.__dict__.get(sprint.original_story_points)
        story_points = issue.fields.__dict__.get(sprint.story_points)
        original_story_points, story_points = sprint.update_story_points(issue, original_story_points, story_points)
        latest_comment_details = sprint.get_comment_details(comments, status)

        data_table.append([
            issue_key, assignee, title, priority, workType,
            original_story_points, story_points, status, latest_comment_details
        ])

    # Return everything as a bundle
    return data_table


def analyze_sprint(wrt="status", output="json", config=None, show="<pre-defined>"):
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
    all_headers = ["Issue Key", "Assignee", "Title", "Priority", "Work Type", 
                    "Initial Story Points", "Actual Story Points", "Status", "Comment"]
    data_table = get_data_table(sprint)

    # Provide data based on the perspective required
    if wrt == "issue":
        display_issue(data_table, all_headers, output, show)
    elif wrt == "owner":
        display_owner(data_table, all_headers, output, show)
    else:
        display_status(data_table, all_headers, output, show)


