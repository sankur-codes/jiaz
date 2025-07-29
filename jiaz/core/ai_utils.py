import requests
import typer
# Import typing, regex, and prompt template
from typing import Optional, List
import re
from .prompts.description import PROMPT as DESCRIPTION_PROMPT
from jiaz.core.formatter import colorize

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
            typer.echo(colorize("❌ Ollama is not running. Please start Ollama and ensure the specified model is available.", "neg"))
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
            timeout = kwargs.get('timeout', 3000)  # Default 5 minutes for AI responses
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()

            # Get the response and automatically clean it
            raw_response = response.json()["response"]
            cleaned_response = self.remove_think_block(raw_response)
            
            return cleaned_response
        except requests.exceptions.ConnectionError:
            typer.echo(colorize("❌ Cannot connect to Ollama. Make sure Ollama is running on localhost:11434", "neg"))
            raise typer.Exit(code=1)
        except requests.exceptions.Timeout:
            typer.echo(colorize("❌ Request to Ollama timed out", "neg"))
            raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(colorize(f"❌ Error communicating with Ollama: {e}", "neg"))
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
    
    def standardize_description(self, description: str, title: str, model: Optional[str] = None) -> str:
        """
        Generate a standardized version of the issue description using AI.
        
        Args:
            description: Original issue description
            title: JIRA issue title object for context
            model: AI model to use (optional)
            
        Returns:
            Standardized description
        """
        
        # Create comprehensive prompt for description standardization
        prompt = DESCRIPTION_PROMPT.format(description=description, title=title)
        try:
            typer.echo(colorize("🤖 Generating standardized description...", "code"))
            standardized_desc = self.ollama.query_model(prompt, model=model)

            # Additional cleaning - remove any remaining think blocks that might have slipped through
            standardized_desc = self.ollama.remove_think_block(standardized_desc)

            return standardized_desc.strip()
        except Exception as e:
            typer.echo(colorize(f"❌ Failed to generate standardized description: {e}", "neg"))
            return "Failed to generate standardized description. Please check your Ollama connection and try again."