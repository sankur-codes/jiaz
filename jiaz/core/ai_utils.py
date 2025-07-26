import requests
import typer
# Import typing, regex, and prompt template
from typing import Optional, List
import re
from .prompts.description import PROMPT as DESCRIPTION_PROMPT

class OllamaClient:
    """
    Generic Ollama client for interacting with local AI models.
    Provides base functionality for model availability checking and prompt querying.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "qwen3:14b"):
        """
        Initialize the Ollama client.
        
        Args:
            base_url: The Ollama server URL
            default_model: Default model to use for queries
        """
        self.base_url = base_url
        self.default_model = default_model
    
    def check_availability(self) -> bool:
        """
        Check if Ollama is running and accessible.
        
        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models from Ollama.
        
        Returns:
            List of available model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except:
            return []
    
    def query_model(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        """
        Send a prompt to the specified model and get a response.
        
        Args:
            prompt: The text prompt to send
            model: Model to use (defaults to default_model)
            **kwargs: Additional parameters for the API call
            
        Returns:
            The AI response text
            
        Raises:
            typer.Exit: If connection fails or other errors occur
        """
        if not self.check_availability():
            typer.secho("❌ Ollama is not running. Please start Ollama and ensure the specified model is available.", 
                    fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        
        model_to_use = model or self.default_model
        url = f"{self.base_url}/api/generate"
        
        # Default payload
        payload = {
            "model": model_to_use,
            "prompt": prompt,
            "stream": False,
            **kwargs  # Allow additional parameters
        }

        try:
            timeout = kwargs.get('timeout', 120)  # Default 2 minutes for AI responses
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()

            # Get the response and automatically clean it
            raw_response = response.json()["response"]
            cleaned_response = self.remove_think_block(raw_response)
            
            return cleaned_response
        except requests.exceptions.ConnectionError:
            typer.secho("❌ Cannot connect to Ollama. Make sure Ollama is running on localhost:11434", 
                    fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        except requests.exceptions.Timeout:
            typer.secho("❌ Request to Ollama timed out", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        except Exception as e:
            typer.secho(f"❌ Error communicating with Ollama: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
    
    def model_exists(self, model_name: str) -> bool:
        """
        Check if a specific model exists in Ollama.
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if model exists, False otherwise
        """
        available_models = self.get_available_models()
        return any(model_name in model for model in available_models)
    
    def remove_think_block(self,text: str) -> str:
        """
        Removes any <think>...</think> block from the response string.
        
        Args:
            text: Text that may contain <think>...</think> blocks
            
        Returns:
            Cleaned text without think blocks
        """
        return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL)



class JiraIssueAI:
    """
    JIRA-specific AI functionality for issue analysis and description standardization.
    """
    
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        """
        Initialize JIRA AI helper.
        
        Args:
            ollama_client: OllamaClient instance (creates default if None)
        """
        self.ollama = ollama_client or OllamaClient()
    
    def standardize_description(self, description: str, issue_data, model: Optional[str] = None) -> str:
        """
        Generate a standardized version of the issue description using AI.
        
        Args:
            description: Original issue description
            issue_data: JIRA issue object for context
            model: AI model to use (optional)
            
        Returns:
            Standardized description
        """
        
        # Create comprehensive prompt for description standardization
        prompt = DESCRIPTION_PROMPT.format(description=description)
        try:
            typer.secho("🤖 Generating standardized description...", fg=typer.colors.CYAN)
            standardized_desc = self.ollama.query_model(prompt, model=model)

            # Additional cleaning - remove any remaining think blocks that might have slipped through
            standardized_desc = self.ollama.remove_think_block(standardized_desc)

            return standardized_desc.strip()
        except Exception as e:
            typer.secho(f"❌ Failed to generate standardized description: {e}", fg=typer.colors.RED, err=True)
            return "Failed to generate standardized description. Please check your Ollama connection and try again."

# issue #14
#     def extract_comments_from_issue(self, jira, issue_data) -> List[Dict]:
#         """
#         Extract comments from a JIRA issue with metadata.
        
#         Args:
#             jira: JiraComms instance
#             issue_data: JIRA issue object
            
#         Returns:
#             List of comment dictionaries with metadata
#         """
#         comments = []
#         if hasattr(issue_data.fields, 'comment') and issue_data.fields.comment.comments:
#             for comment in issue_data.fields.comment.comments:
#                 comment_data = {
#                     'author': comment.author.displayName if hasattr(comment, 'author') else 'Unknown',
#                     'created': comment.created if hasattr(comment, 'created') else 'Unknown',
#                     'body': comment.body if hasattr(comment, 'body') else '',
#                     'issue_key': issue_data.key
#                 }
#                 comments.append(comment_data)
#         return comments

#     def get_subtask_comments(self, jira, issue_key: str) -> List[Dict]:
#         """
#         Get comments from all subtasks of a given issue.
        
#         Args:
#             jira: JiraComms instance
#             issue_key: Parent issue key
            
#         Returns:
#             List of comments from all subtasks
#         """
#         all_comments = []
        
#         # JQL to find subtasks
#         jql = f'parent = "{issue_key}"'
#         try:
#             subtasks = jira.rate_limited_request(jira.jira.search_issues, jql, maxResults=100)
            
#             for subtask in subtasks:
#                 subtask_comments = self.extract_comments_from_issue(jira, subtask)
#                 all_comments.extend(subtask_comments)
                
#         except Exception as e:
#             typer.secho(f"⚠️  Could not fetch subtasks for {issue_key}: {e}", fg=typer.colors.YELLOW)
        
#         return all_comments

#     def generate_progress_summary(self, issue_data, parent_comments: List[Dict], subtask_comments: List[Dict], model: Optional[str] = None) -> str:
#         """
#         Generate an AI-powered summary of ticket progress based on comments.
        
#         Args:
#             issue_data: Main issue data
#             parent_comments: Comments from the parent ticket
#             subtask_comments: Comments from subtasks
#             model: AI model to use (optional)
            
#         Returns:
#             AI-generated progress summary
#         """
#         # Prepare context
#         issue_key = issue_data.key
#         issue_title = getattr(issue_data.fields, 'summary', 'No title')
#         issue_status = getattr(issue_data.fields.status, 'name', 'Unknown') if hasattr(issue_data.fields, 'status') else 'Unknown'
#         issue_type = getattr(issue_data.fields.issuetype, 'name', 'Unknown') if hasattr(issue_data.fields, 'issuetype') else 'Unknown'
        
#         # Format comments for AI
#         formatted_comments = []
        
#         # Add parent comments
#         if parent_comments:
#             formatted_comments.append(f"=== MAIN TICKET ({issue_key}) COMMENTS ===")
#             for comment in parent_comments[-10:]:  # Last 10 comments only
#                 formatted_comments.append(f"[{comment['created'][:10]}] {comment['author']}: {comment['body'][:500]}")
        
#         # Add subtask comments
#         if subtask_comments:
#             formatted_comments.append(f"\n=== SUBTASK COMMENTS ===")
#             for comment in subtask_comments[-15:]:  # Last 15 subtask comments
#                 formatted_comments.append(f"[{comment['created'][:10]}] {comment['author']} on {comment['issue_key']}: {comment['body'][:500]}")
        
#         comments_text = "\n".join(formatted_comments) if formatted_comments else "No comments available."
        
#         # Create comprehensive prompt
#         prompt = f"""You are an expert project manager analyzing JIRA ticket progress. Based on the ticket information and comments provided, generate a comprehensive progress summary.

# TICKET INFORMATION:
# - Key: {issue_key}
# - Title: {issue_title}
# - Type: {issue_type}
# - Current Status: {issue_status}

# COMMENTS AND ACTIVITY:
# {comments_text}

# Please provide a structured progress summary that includes:

# 1. **Current Status**: What's the current state of this ticket?
# 2. **Work Completed**: What has been accomplished so far?
# 3. **Key Activities**: Major developments or decisions made
# 4. **Challenges/Blockers**: Any issues or obstacles mentioned
# 5. **Next Steps**: What appears to be planned or needed next
# 6. **Team Involvement**: Who has been actively working on this

# Guidelines:
# - Be concise but comprehensive
# - Focus on actionable insights
# - Highlight any risks or concerns
# - Use bullet points for clarity
# - If information is limited, mention that clearly
# - Ignore irrelevant or spam comments

# Generate the summary now:"""

#         try:
#             typer.secho("🤖 Generating AI-powered progress summary...", fg=typer.colors.CYAN)
#             summary = self.ollama.query_model(prompt, model=model)
#             return summary.strip()
#         except Exception as e:
#             typer.secho(f"❌ Failed to generate summary: {e}", fg=typer.colors.RED, err=True)
#             return "Failed to generate AI summary. Please check your Ollama connection and try again."
