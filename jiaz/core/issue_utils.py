from jiaz.core.jira_comms import JiraComms

def get_issue_data(jira: JiraComms, issue_id: str):
    """
    Fetch issue data from JIRA.

    Arguments:
    -----------
    jira: JIRA client instance.
    issue_id: ID of the issue to fetch.

    Returns:
    --------
    dict: Issue data.
    """
    # try:
    #     issue = jira.rate

    # return issue
    pass
    

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
