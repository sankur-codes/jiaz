from jiaz.core.jira_comms import JiraComms
from jiaz.core.validate import issue_exists

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
    

def analyze_issue(id: str, output: str = "json", config: str = None, show: list = None):
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

    print(f"Analyzing issue {id} with output format {output}, config {config}, showing fields {show}")
    jira = JiraComms(config_name=config)
    if issue_exists(jira, id):
        issue_data = jira.rate_limited_request(jira.jira.issue, id)
        print(f"Issue is a {issue_data.fields.issuetype.name}")
        
