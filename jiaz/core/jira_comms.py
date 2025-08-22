import time
from collections import deque

import typer
from jiaz.core.config_utils import (
    decode_secure_value,
    get_active_config,
    get_specific_config,
)
from jiaz.core.formatter import colorize, time_delta
from jiaz.core.validate import issue_exists, valid_jira_client, validate_sprint_config


class JiraComms:
    def __init__(self, config_name):
        self.config_used = get_specific_config(config_name)
        self.jira = valid_jira_client(
            self.config_used.get("server_url"),
            decode_secure_value(self.config_used.get("user_token")),
        )
        self.request_queue = deque(maxlen=2)

        # place all the custom field ids
        self.original_story_points = "customfield_12314040"
        self.story_points = "customfield_12310243"
        self.work_type = "customfield_12320040"
        self.sprints = "customfield_12310940"
        self.epic_link = "customfield_12311140"
        self.epic_progress = "customfield_12317141"
        self.epic_start_date = "customfield_12313941"
        self.epic_end_date = "customfield_12313942"
        self.parent_link = "customfield_12313140"
        self.status_summary = "customfield_12320841"

    def rate_limited_request(self, func, *args, **kwargs):
        """Ensures that no more than 2 requests are sent per second."""
        if len(self.request_queue) >= 2:
            time_since_first_request = time.time() - self.request_queue[0]
            if time_since_first_request < 1:
                time.sleep(1 - time_since_first_request)
        self.request_queue.append(time.time())
        return func(*args, **kwargs)

    def get_comment_details(self, comments, status):
        """Exracts the latest comment details from a list of comments."""
        if comments:
            latest_comment = max(comments, key=lambda c: c.created)
            author = latest_comment.author.displayName.split(" ")[0]
            delta = time_delta(latest_comment.created)

            # Determine the "time ago" format
            # For comments, delta.days will be negative (past time), so we need abs()
            days_ago = abs(delta.days) if delta.days < 0 else 0

            if days_ago > 0:
                time_ago = (
                    f"{days_ago} days ago"
                    if days_ago < 10 or status == "Closed"
                    else colorize(f"{days_ago} days ago", "neg")
                )
            else:
                # For same day, check seconds (delta.seconds is always positive for time within the day)
                hours = delta.seconds // 3600
                time_ago = f"{hours} hours ago" if hours > 0 else "Just now"

            return f"{author} commented {time_ago}"
        else:
            return colorize("No Comments", "neg")

    def get_most_recent_activity(self, comments, formatted_updated, status):
        """
        Compare last comment vs last update and return the more recent activity.
        Reuses existing formatting from get_comment_details and issue_utils formatting.

        Args:
            comments: List of comments
            formatted_updated: Already formatted "updated" field from issue_utils
            status: Issue status

        Returns:
            str: The more recent activity (either formatted update or commented activity)
        """
        if not comments:
            # No comments, return the formatted updated time
            return formatted_updated

        # Get comment details and raw comment time
        latest_comment = max(comments, key=lambda c: c.created)
        comment_details = self.get_comment_details(comments, status)

        # If we have both, compare raw timestamps
        try:
            from datetime import datetime

            # Parse comment timestamp
            comment_time = latest_comment.created
            if isinstance(comment_time, str):
                comment_str = comment_time.replace("Z", "+00:00")
                comment_datetime = datetime.fromisoformat(comment_str)
            else:
                comment_datetime = comment_time

            # Extract days from formatted update string to compare
            if "Updated Today" in str(formatted_updated):
                # Comment wins if it's today, otherwise update wins
                from jiaz.core.formatter import time_delta

                delta = time_delta(comment_datetime)
                days_ago = abs(delta.days) if delta.days < 0 else 0

                if days_ago == 0:
                    # Both are today, show comment since it's more specific
                    return comment_details
                else:
                    return formatted_updated
            elif "days ago" in str(formatted_updated):
                # Extract days from update string
                import re

                match = re.search(r"(\d+) days ago", str(formatted_updated))
                if match:
                    update_days = int(match.group(1))

                    # Get comment days
                    from jiaz.core.formatter import time_delta

                    delta = time_delta(comment_datetime)
                    comment_days = abs(delta.days) if delta.days < 0 else 0

                    # Return the more recent (fewer days ago)
                    if comment_days < update_days:
                        return comment_details
                    elif comment_days == update_days:
                        # Same day, prefer comment for specificity
                        return comment_details
                    else:
                        return formatted_updated
                else:
                    # Can't parse update days, default to comment
                    return comment_details
            else:
                # Unknown format, default to comment
                return comment_details

        except Exception:
            # If comparison fails, default to showing comment since it's more specific
            return comment_details

        return formatted_updated

    def get_issue(self, issue_key):
        """Retrieve a specific issue by its key."""
        if issue_exists(self, issue_key):
            return self.rate_limited_request(self.jira.issue, issue_key)
        else:
            typer.echo(colorize("Please Enter Valid Issue ID", "neg"))
            raise SystemExit(1)

    def adding_comment(self, issue_key, comment_text):
        """
        Add a comment to a JIRA issue.

        Args:
            issue_key: JIRA issue key
            comment_text: Text content of the comment

        Returns:
            comment object if successful, None otherwise
        """
        try:
            comment = self.rate_limited_request(
                self.jira.add_comment, issue_key, comment_text
            )
            return comment
        except Exception as e:
            typer.echo(colorize(f"❌ Failed to add comment: {e}", "neg"))
            return None

    def pinning_comment(self, issue_key, comment_id):
        """
        Pin a comment in a JIRA issue using the built-in JIRA library method.
        """
        try:
            # Use the built-in pin_comment method from JIRA library
            self.rate_limited_request(
                self.jira.pin_comment, issue_key, comment_id, pin=True
            )
            return True
        except Exception as e:
            typer.echo(colorize(f"❌ Failed to pin comment: {e}", "neg"))
            return False

    def get_pinned_comments(self, issue_key):
        """
        Get pinned comments for a JIRA issue using the built-in JIRA library method.

        Args:
            issue_key: JIRA issue key

        Returns:
            list: List of pinned comment texts, empty list if none or error
        """
        try:
            # Use the built-in pinned_comments method from JIRA library
            pinned_comments = self.rate_limited_request(
                self.jira.pinned_comments, issue_key
            )
            # Extract comment bodies from pinned comments
            if pinned_comments:
                return pinned_comments
            else:
                return []

        except Exception as e:
            typer.echo(colorize(f"❌ Failed to get pinned comments: {e}", "neg"))
            return []


class Sprint(JiraComms):
    def __init__(self, config_name=get_active_config()):
        """Initialize the Sprint class with the specified configuration."""
        # Load the specific configuration
        # If no config_name is provided, it defaults to the active config
        super().__init__(config_name)
        validate_sprint_config(self.config_used)
        print(f"Using configuration: {config_name}")

        # self.sprint_num = sprint_num
        self.sprint_id, self.sprint_name = self.get_sprint_id_and_name()
        self.get_board_jql()

    def get_sprint_id_and_name(self, sprint_num=None):
        """Retrieve the sprint ID and name based on the sprint number or active sprint."""
        # As of now, this method fetches the active sprint from the board and returns its ID and name.
        # if sprint_num is not None:
        #     all_sprints = self.rate_limited_request(self.jira.sprints_by_name,d.boardId)
        #     for sprint in all_sprints.values():
        #         if d.sprintBoardName + " " + sprint_num == sprint['name']:
        #             return sprint['id'], sprint['name']
        # else:
        active_sprints = self.rate_limited_request(
            self.jira.sprints_by_name,
            self.config_used.get("jira_sprintboard_id"),
            state="active",
        )
        for sprint in active_sprints.values():
            if self.config_used.get("jira_sprintboard_name") in sprint["name"]:
                return sprint["id"], sprint["name"]
        return None, None

    def get_issues_in_sprint(self, mine=False):
        """Retrieve issues in the current active sprint."""
        sprint_jql = self.get_board_jql()
        curr_user_jql = "assignee = currentUser() AND "
        if mine:
            sprint_jql = curr_user_jql + sprint_jql
        sprint_issues = []
        if sprint_jql:
            # If the sprint name is part of the JQL, we can use it to filter issues
            if self.sprint_name:
                sprint_jql = f"Sprint = '{self.sprint_name}' AND " + sprint_jql
                print(f"Using JQL: {sprint_jql}")
            sprint_issues = self.rate_limited_request(
                self.jira.search_issues, sprint_jql, maxResults=1000
            )
        elif self.sprint_name is not None:
            generic_jql = f"project = '{self.config_used.get('jira_project')}' and type != Epic and labels = '{self.config_used.get('jira_backlog_name')}' and Sprint = '{self.sprint_name}' ORDER BY Rank ASC"
            if mine:
                generic_jql = curr_user_jql + generic_jql
            sprint_issues = self.rate_limited_request(
                self.jira.search_issues, generic_jql, maxResults=1000
            )
        if not sprint_issues:
            typer.echo(
                "No issues found in the current active sprint with provided configuration."
            )
            raise SystemExit(1)
        return sprint_issues

    # ToDo : Make story point updation optional with a flag and then uncomment the update lines
    def update_story_points(self, issue, original_story_points, story_points):
        # Update OG story point or story point if any of these are provided
        if original_story_points is None and story_points is None:
            return colorize("Not Assigned", "neg"), colorize("Not Assigned", "neg")
        elif original_story_points is None:
            # self.rate_limited_request(issue.update,fields={self.original_story_points: story_points})
            return int(story_points), int(story_points)
        elif story_points is None:
            # self.rate_limited_request(issue.update,fields={self.story_points: original_story_points})
            return int(original_story_points), int(original_story_points)
        else:
            return int(original_story_points), int(story_points)

    def get_board_jql(self):
        """Retrieve issues from a specific board."""

        board_config = self.jira._session.get(
            f'{self.config_used.get("server_url")}/rest/agile/1.0/board/{self.config_used.get("jira_sprintboard_id")}/configuration'
        ).json()
        if not board_config:
            typer.echo("Unable to retrieve board configuration.")
        # Extract the filter ID from the board configuration
        filter_id = board_config.get("filter", {}).get("id")
        if not filter_id:
            typer.echo("Unable to retrieve filter ID from board configuration.")
        # Retrieve the JQL from the filter using the filter ID
        filter_jql = getattr(self.jira.filter(filter_id), "jql", None)

        if not filter_jql:
            typer.echo("Unable to retrieve JQL from filter.")

        return filter_jql
