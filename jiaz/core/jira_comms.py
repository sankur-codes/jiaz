from jira import JIRA
import time
from collections import deque
from jiaz.core.config_utils import get_active_config, get_specific_config, decode_token
from datetime import datetime, timezone
from jiaz.core.formatter import colorize

class JiraComms:
    def __init__(self, config_used=get_active_config()):
        self.jira = JIRA(server=config_used.get("server_url"), kerberos=True, token_auth=decode_token(config_used.get("user_token")))
        self.request_queue = deque(maxlen=2)
        

    def rate_limited_request(self, func, *args, **kwargs):
        """Ensures that no more than 2 requests are sent per second."""
        if len(self.request_queue) >= 2:
            time_since_first_request = time.time() - self.request_queue[0]
            if time_since_first_request < 1:
                time.sleep(1 - time_since_first_request)
        self.request_queue.append(time.time())
        return func(*args, **kwargs)
    
    def get_comment_details(self,comments, status):
        """Exracts the latest comment details from a list of comments."""
        if comments:
            latest_comment = max(comments,key=lambda c: c.created)
            author = latest_comment.author.displayName.split(" ")[0]
            comment_created_at = datetime.fromisoformat(latest_comment.created.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = now - comment_created_at

            # Determine the "time ago" format
            if delta.days > 0:
                time_ago = f"{delta.days} days ago" if delta.days < 10 or status == "Closed" else colorize(f"{delta.days} days ago","neg")
            else:
                hours = delta.seconds // 3600
                time_ago = f"{hours} hours ago" if hours > 0 else "Just now"

            return f"{author} commented {time_ago}" 
        else:
            return colorize("No Comments","neg")
    
class Sprint(JiraComms):
    def __init__(self, config_name=get_active_config()):
        """Initialize the Sprint class with the specified configuration."""
         # Load the specific configuration
         # If no config_name is provided, it defaults to the active config
        self.config_used = get_specific_config(config_name)
        print(f"Using configuration: {config_name}")
        super().__init__(self.config_used)

        # place all the custom field ids
        self.original_story_points = "customfield_12314040"
        self.story_points = "customfield_12310243"
        self.work_type = "customfield_12320040"

        #self.sprint_num = sprint_num
        self.sprint_id, self.sprint_name = self.get_sprint_id_and_name()

    def get_sprint_id_and_name(self, sprint_num=None):
        """Retrieve the sprint ID and name based on the sprint number or active sprint."""
    # As of now, this method fetches the active sprint from the board and returns its ID and name.
    # if sprint_num is not None:
    #     all_sprints = self.rate_limited_request(self.jira.sprints_by_name,d.boardId)
    #     for sprint in all_sprints.values():
    #         if d.sprintBoardName + " " + sprint_num == sprint['name']:
    #             return sprint['id'], sprint['name']
    # else:
        active_sprints = self.rate_limited_request(self.jira.sprints_by_name,self.config_used.get("jira_sprintboard_id"), state='active')
        for sprint in active_sprints.values():
            if self.config_used.get("jira_sprintboard_name") in sprint['name']:
                return sprint['id'], sprint['name']
        return None, None
    
    def get_issues_in_sprint(self):
        if self.sprint_name is not None:
            return self.rate_limited_request(
                self.jira.search_issues,
                f"project = '{self.config_used.get('jira_project')}' and type != Epic and labels = '{self.config_used.get('jira_backlog_name')}' and Sprint = '{self.sprint_name}' ORDER BY Rank ASC",
                maxResults=1000
            )
        return []
    
    def update_story_points(self, issue, original_story_points ,story_points):
        #Update OG story point or story point if any of these are provided
        if original_story_points is None and story_points is None:
            return colorize("Not Assigned","neg"), colorize("Not Assigned","neg")
        elif original_story_points is None:
            self.rate_limited_request(issue.update,fields={self.original_story_points: story_points})
            return int(story_points), int(story_points)
        elif story_points is None:
            self.rate_limited_request(issue.update,fields={self.story_points: original_story_points})
            return int(original_story_points), int(original_story_points)
        else:
            return int(original_story_points), int(story_points)
    
