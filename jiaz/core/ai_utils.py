import re

# Import typing, regex, and prompt template
from typing import List, Optional

import requests
import typer
from jiaz.core.config_utils import get_gemini_api_key, should_use_gemini
from jiaz.core.formatter import colorize

# LangChain imports
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from .prompts.description import PROMPT as DESCRIPTION_PROMPT


class UnifiedLLMClient:
    """
    Unified LLM client that can use either Ollama or Gemini based on configuration.
    Provides a consistent interface regardless of the underlying provider.
    """

    def __init__(
        self, base_url: str = "http://localhost:11434", default_model: str = "qwen3:14b"
    ):
        """
        Initialize the unified LLM client.

        Args:
            base_url: The Ollama server URL (used only if Ollama is selected)
            default_model: Default Ollama model to use (used only if Ollama is selected)
        """
        self.base_url = base_url
        self.default_model = default_model
        self.use_gemini = should_use_gemini()
        self.llm = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the appropriate LLM client based on configuration."""
        if self.use_gemini:
            api_key = get_gemini_api_key()
            if api_key:
                try:
                    self.llm = ChatGoogleGenerativeAI(
                        model="gemini-2.5-pro", google_api_key=api_key, max_retries=2
                    )
                    typer.echo(colorize("🔗 Using Gemini for LLM queries", "info"))
                except Exception as e:
                    typer.echo(
                        colorize(
                            f"❌ Failed to initialize Gemini: {e}. Falling back to Ollama.",
                            "neg",
                        )
                    )
                    self.use_gemini = False
                    self._initialize_ollama()
            else:
                typer.echo(
                    colorize("⚠️  No valid Gemini API key found. Using Ollama.", "neu")
                )
                self.use_gemini = False
                self._initialize_ollama()
        else:
            self._initialize_ollama()

    def _initialize_ollama(self):
        """Initialize Ollama client."""
        try:
            self.llm = ChatOllama(model=self.default_model, base_url=self.base_url)
            typer.echo(colorize("🔗 Using Ollama for LLM queries", "info"))
        except Exception as e:
            typer.echo(colorize(f"❌ Failed to initialize Ollama: {e}", "neg"))
            raise

    def check_availability(self) -> bool:
        """
        Check if the LLM service is available.

        Returns:
            True if LLM service is available, False otherwise
        """
        if self.use_gemini:
            # For Gemini, we assume it's available if we have a valid API key
            api_key = get_gemini_api_key()
            return api_key is not None
        else:
            # For Ollama, check if the service is running
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                return response.status_code == 200
            except Exception:
                return False

    def query_model(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        """
        Send a prompt to the LLM and get a response.

        Args:
            prompt: The text prompt to send
            model: Model to use (for Ollama only, ignored for Gemini)
            **kwargs: Additional parameters for the API call

        Returns:
            The AI response text

        Raises:
            typer.Exit: If connection fails or other errors occur
        """
        if not self.check_availability():
            service_name = "Gemini" if self.use_gemini else "Ollama"
            typer.echo(
                colorize(
                    f"❌ {service_name} is not available. Please check your configuration.",
                    "neg",
                )
            )
            raise typer.Exit(code=1)

        try:
            # Create message for LangChain
            messages = [HumanMessage(content=prompt)]

            # For Ollama, we can switch models if specified
            if not self.use_gemini and model and model != self.default_model:
                # Create a new Ollama client with the specified model
                temp_llm = ChatOllama(model=model, base_url=self.base_url)
                response = temp_llm.invoke(messages)
            else:
                response = self.llm.invoke(messages)

            # Extract content from the response
            raw_response = response.content
            cleaned_response = self.remove_think_block(raw_response)

            return cleaned_response

        except Exception as e:
            service_name = "Gemini" if self.use_gemini else "Ollama"
            typer.echo(
                colorize(f"❌ Error communicating with {service_name}: {e}", "neg")
            )
            raise typer.Exit(code=1)

    def get_available_models(self) -> List[str]:
        """
        Get list of available models.

        Returns:
            List of available model names (for Ollama) or supported Gemini models
        """
        if self.use_gemini:
            # Return supported Gemini models
            return ["gemini-2.5-pro", "gemini-1.5-pro", "gemini-1.5-flash"]
        else:
            # Get Ollama models
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return [model["name"] for model in data.get("models", [])]
                return []
            except Exception:
                return []

    def model_exists(self, model_name: str) -> bool:
        """
        Check if a specific model exists.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model exists, False otherwise
        """
        available_models = self.get_available_models()
        return any(model_name in model for model in available_models)

    def remove_think_block(self, text: str) -> str:
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

    def __init__(self, llm_client: Optional[UnifiedLLMClient] = None):
        """
        Initialize JIRA AI helper.

        Args:
            llm_client: UnifiedLLMClient instance (creates default if None)
        """
        self.llm = llm_client or UnifiedLLMClient()

    def standardize_description(
        self,
        description: str,
        title: str,
        model: Optional[str] = None,
        prompt_template: Optional[str] = None,
    ) -> str:
        """
        Generate a standardized version of the issue description using AI.

        Args:
            description: Original issue description
            title: JIRA issue title object for context
            model: AI model to use (optional)
            prompt_template: Custom prompt template string with {title} and
                {description} placeholders. If None, uses built-in default.

        Returns:
            Standardized description
        """

        # Use custom prompt template if provided, otherwise use default
        template = prompt_template if prompt_template else DESCRIPTION_PROMPT
        prompt = template.format(description=description, title=title)
        try:
            typer.echo(colorize("🤖 Generating standardized description...", "info"))
            standardized_desc = self.llm.query_model(prompt, model=model)

            # Additional cleaning - remove any remaining think blocks that might have slipped through
            standardized_desc = self.llm.remove_think_block(standardized_desc)

            return standardized_desc.strip()
        except SystemExit:
            # Re-raise SystemExit exceptions (including typer.Exit) so retry mechanism can handle them
            raise
        except Exception as e:
            typer.echo(
                colorize(f"❌ Failed to generate standardized description: {e}", "neg")
            )
            return "Failed to generate standardized description. Please check your LLM connection and try again."

    def compare_content(
        self,
        content1: str,
        content2: str,
        comparison_context: str = "similarity",
        prompt_template: Optional[str] = None,
    ) -> bool:
        """
        Compare two pieces of content for similarity or other specified criteria.

        Args:
            content1: First piece of content to compare
            content2: Second piece of content to compare
            comparison_context: Context for comparison (e.g., "similarity", "equivalence", "accuracy")
            prompt_template: Custom prompt template to use. If None, uses default generic comparison prompt

        Returns:
            bool: True if contents meet the comparison criteria, False otherwise
        """
        if prompt_template:
            # Use custom prompt template
            prompt = prompt_template
        else:
            # Use generic comparison prompt from prompts module
            from .prompts.compare import GENERIC_CONTENT_PROMPT

            prompt = GENERIC_CONTENT_PROMPT.format(
                content1=content1,
                content2=content2,
                comparison_context=comparison_context,
            )

        # Get comparison result
        comparison_result = self.llm.query_model(prompt)

        # Parse the result (should be "true" or "false")
        result = comparison_result.strip().lower()

        if result == "true":
            return True
        elif result == "false":
            return False
        else:
            # If we get an unexpected response, log it and default to True to be safe
            typer.echo(
                colorize(
                    f"⚠️  Unexpected comparison result: '{result}', defaulting to similar",
                    "neu",
                )
            )
            return True

    def compare_descriptions(
        self, standardized_description: str, terminal_friendly_output: str
    ) -> bool:
        """
        Compare standardized description with terminal-friendly output for similarity.
        This is a convenience method that uses the specific JIRA comparison prompt for better accuracy.

        Args:
            standardized_description: The AI-generated standardized description with JIRA markup
            terminal_friendly_output: The terminal-rendered version with ANSI codes

        Returns:
            bool: True if descriptions are similar, False otherwise
        """
        # Use the specific JIRA comparison prompt for better accuracy
        from .prompts.compare import JIRA_DESCRIPTION_PROMPT

        jira_prompt = JIRA_DESCRIPTION_PROMPT.format(
            standardized_description=standardized_description,
            terminal_friendly_output=terminal_friendly_output,
        )

        return self.compare_content(
            content1=standardized_description,
            content2=terminal_friendly_output,
            comparison_context="JIRA description similarity",
            prompt_template=jira_prompt,
        )
