"""Tests for core ai_utils module."""

import unittest.mock
from unittest.mock import Mock, patch

import pytest
import typer

from jiaz.core.ai_utils import JiraIssueAI, UnifiedLLMClient


class TestUnifiedLLMClient:
    """Test suite for UnifiedLLMClient."""

    @patch("jiaz.core.ai_utils.should_use_gemini")
    @patch("jiaz.core.ai_utils.get_gemini_api_key")
    @patch("jiaz.core.ai_utils.ChatGoogleGenerativeAI")
    @patch("jiaz.core.ai_utils.typer")
    def test_init_with_gemini(
        self, mock_typer, mock_gemini_ai, mock_get_api_key, mock_should_use_gemini
    ):
        """Test initialization with Gemini."""
        mock_should_use_gemini.return_value = True
        mock_get_api_key.return_value = "test_api_key"
        mock_llm_instance = Mock()
        mock_gemini_ai.return_value = mock_llm_instance

        client = UnifiedLLMClient()

        assert client.use_gemini is True
        assert client.llm == mock_llm_instance
        mock_gemini_ai.assert_called_once_with(
            model="gemini-2.5-pro", google_api_key="test_api_key", max_retries=2
        )
        mock_typer.echo.assert_called_with(
            unittest.mock.ANY
        )  # Called for success message

    @patch("jiaz.core.ai_utils.should_use_gemini")
    @patch("jiaz.core.ai_utils.get_gemini_api_key")
    @patch("jiaz.core.ai_utils.ChatOllama")
    @patch("jiaz.core.ai_utils.typer")
    def test_init_with_ollama_fallback(
        self, mock_typer, mock_ollama_ai, mock_get_api_key, mock_should_use_gemini
    ):
        """Test initialization with Ollama as fallback."""
        mock_should_use_gemini.return_value = True
        mock_get_api_key.return_value = None  # No API key
        mock_llm_instance = Mock()
        mock_ollama_ai.return_value = mock_llm_instance

        client = UnifiedLLMClient()

        assert client.use_gemini is False
        assert client.llm == mock_llm_instance
        mock_ollama_ai.assert_called_once_with(
            base_url="http://localhost:11434", model="qwen3:14b"
        )

    @patch("jiaz.core.ai_utils.should_use_gemini")
    @patch("jiaz.core.ai_utils.ChatOllama")
    @patch("jiaz.core.ai_utils.typer")
    def test_init_with_ollama_direct(
        self, mock_typer, mock_ollama_ai, mock_should_use_gemini
    ):
        """Test initialization directly with Ollama."""
        mock_should_use_gemini.return_value = False
        mock_llm_instance = Mock()
        mock_ollama_ai.return_value = mock_llm_instance

        client = UnifiedLLMClient()

        assert client.use_gemini is False
        assert client.llm == mock_llm_instance
        mock_ollama_ai.assert_called_once_with(
            base_url="http://localhost:11434", model="qwen3:14b"
        )

    @patch("jiaz.core.ai_utils.should_use_gemini")
    @patch("jiaz.core.ai_utils.get_gemini_api_key")
    @patch("jiaz.core.ai_utils.ChatGoogleGenerativeAI")
    @patch("jiaz.core.ai_utils.ChatOllama")
    @patch("jiaz.core.ai_utils.typer")
    def test_gemini_initialization_failure(
        self,
        mock_typer,
        mock_ollama_ai,
        mock_gemini_ai,
        mock_get_api_key,
        mock_should_use_gemini,
    ):
        """Test Gemini initialization failure fallback to Ollama."""
        mock_should_use_gemini.return_value = True
        mock_get_api_key.return_value = "test_api_key"
        mock_gemini_ai.side_effect = Exception("Gemini init failed")
        mock_ollama_instance = Mock()
        mock_ollama_ai.return_value = mock_ollama_instance

        client = UnifiedLLMClient()

        assert client.use_gemini is False
        assert client.llm == mock_ollama_instance
        # Check that error message was displayed
        error_calls = [
            call
            for call in mock_typer.echo.call_args_list
            if "Failed to initialize Gemini" in str(call)
        ]
        assert len(error_calls) > 0

    @patch("jiaz.core.ai_utils.should_use_gemini")
    @patch("jiaz.core.ai_utils.ChatOllama")
    @patch("jiaz.core.ai_utils.typer")
    def test_ollama_initialization_failure(
        self, mock_typer, mock_ollama_ai, mock_should_use_gemini
    ):
        """Test Ollama initialization failure."""
        mock_should_use_gemini.return_value = False
        mock_ollama_ai.side_effect = Exception("Ollama init failed")

        with pytest.raises(Exception, match="Ollama init failed"):
            UnifiedLLMClient()

        # Check that error message was displayed
        error_calls = [
            call
            for call in mock_typer.echo.call_args_list
            if "Failed to initialize Ollama" in str(call)
        ]
        assert len(error_calls) > 0

    def test_query_model_with_mock_llm(self):
        """Test query_model method."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=False):
            with patch("jiaz.core.ai_utils.ChatOllama") as mock_ollama:
                mock_llm_instance = Mock()
                mock_llm_instance.invoke.return_value = Mock(content="Test response")
                mock_ollama.return_value = mock_llm_instance

                client = UnifiedLLMClient()
                # Mock check_availability to return True so query doesn't fail
                with patch.object(client, "check_availability", return_value=True):
                    result = client.query_model("Test prompt")

                assert result == "Test response"
                mock_llm_instance.invoke.assert_called_once()

    def test_check_availability_with_llm(self):
        """Test check_availability method when LLM is available."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=False):
            with patch("jiaz.core.ai_utils.ChatOllama"):
                with patch("requests.get") as mock_get:
                    mock_get.return_value.status_code = 200
                    client = UnifiedLLMClient()
                    assert client.check_availability() is True

    def test_check_availability_without_llm(self):
        """Test check_availability method when LLM is not available."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=False):
            with patch("jiaz.core.ai_utils.ChatOllama"):
                with patch("requests.get") as mock_get:
                    mock_get.side_effect = Exception("Connection failed")
                    client = UnifiedLLMClient()
                    assert client.check_availability() is False

    def test_check_availability_with_gemini_no_api_key(self):
        """Test check_availability with Gemini but no API key."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=True):
            with patch("jiaz.core.ai_utils.get_gemini_api_key", return_value=None):
                with patch("jiaz.core.ai_utils.ChatOllama"):
                    with patch("requests.get") as mock_get:
                        mock_get.side_effect = Exception("Connection failed")
                        client = UnifiedLLMClient()
                        assert client.check_availability() is False

    def test_check_availability_with_gemini_api_key(self):
        """Test check_availability with Gemini and API key."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=True):
            with patch(
                "jiaz.core.ai_utils.get_gemini_api_key", return_value="test_key"
            ):
                with patch("jiaz.core.ai_utils.ChatGoogleGenerativeAI"):
                    client = UnifiedLLMClient()
                    assert client.check_availability() is True

    def test_query_model_with_unavailable_ollama(self):
        """Test query_model method when Ollama is unavailable."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=False):
            with patch("jiaz.core.ai_utils.ChatOllama"):
                with patch("requests.get") as mock_get:
                    mock_get.side_effect = Exception("Connection failed")
                    client = UnifiedLLMClient()

                    # Should raise typer.Exit when Ollama is unavailable
                    with pytest.raises(typer.Exit) as exc_info:
                        client.query_model("Test prompt")
                    assert exc_info.value.exit_code == 1

    def test_query_model_with_unavailable_gemini(self):
        """Test query_model method when Gemini is unavailable."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=True):
            with patch("jiaz.core.ai_utils.get_gemini_api_key", return_value=None):
                with patch("jiaz.core.ai_utils.ChatOllama"):
                    with patch("requests.get") as mock_get:
                        mock_get.side_effect = Exception("Connection failed")
                        client = UnifiedLLMClient()

                        # Should raise typer.Exit when Gemini API key is unavailable and Ollama fallback fails
                        with pytest.raises(typer.Exit) as exc_info:
                            client.query_model("Test prompt")
                        assert exc_info.value.exit_code == 1


class TestJiraIssueAI:
    """Test suite for JiraIssueAI."""

    def test_init_with_default_client(self):
        """Test initialization with default LLM client."""
        with patch("jiaz.core.ai_utils.UnifiedLLMClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance

            ai = JiraIssueAI()

            assert ai.llm == mock_client_instance
            mock_client_class.assert_called_once_with()

    def test_init_with_custom_client(self):
        """Test initialization with custom LLM client."""
        mock_client = Mock()
        ai = JiraIssueAI(llm_client=mock_client)

        assert ai.llm == mock_client

    def test_standardize_description(self):
        """Test standardize_description method."""
        with patch("jiaz.core.ai_utils.UnifiedLLMClient") as mock_client_class:
            mock_client = Mock()
            mock_client.query_model.return_value = "Standardized description"
            mock_client.remove_think_block.return_value = "Standardized description"
            mock_client_class.return_value = mock_client

            ai = JiraIssueAI()
            result = ai.standardize_description("Original description", "Test Title")

            assert result == "Standardized description"
            mock_client.query_model.assert_called_once()
            # Check that the prompt contains the original description
            call_args = mock_client.query_model.call_args[0][0]
            assert "Original description" in call_args

    def test_compare_content(self):
        """Test compare_content method."""
        with patch("jiaz.core.ai_utils.UnifiedLLMClient") as mock_client_class:
            mock_client = Mock()
            mock_client.query_model.return_value = "true"
            mock_client_class.return_value = mock_client

            ai = JiraIssueAI()
            content1 = "Content 1"
            content2 = "Content 2"
            result = ai.compare_content(content1, content2)

            assert result is True
            mock_client.query_model.assert_called_once()

    def test_compare_descriptions(self):
        """Test compare_content method for descriptions."""
        with patch("jiaz.core.ai_utils.UnifiedLLMClient") as mock_client_class:
            mock_client = Mock()
            mock_client.query_model.return_value = "true"
            mock_client_class.return_value = mock_client

            ai = JiraIssueAI()
            original = "Original description"
            standardised = "Standardized description"
            result = ai.compare_content(original, standardised, "similarity")

            assert result is True
            mock_client.query_model.assert_called_once()

    @patch("jiaz.core.ai_utils.typer")
    def test_llm_error_handling(self, mock_typer):
        """Test error handling in LLM operations."""
        with patch("jiaz.core.ai_utils.UnifiedLLMClient") as mock_client_class:
            mock_client = Mock()
            mock_client.query_model.side_effect = Exception("LLM service error")
            mock_client.remove_think_block.return_value = "Error message"
            mock_client_class.return_value = mock_client

            ai = JiraIssueAI()

            result = ai.standardize_description("Test description", "Test Title")

            # Should return error message instead of crashing
            assert "Failed to generate standardized description" in result

    def test_methods_with_llm_available(self):
        """Test that methods work when LLM is available."""
        with patch("jiaz.core.ai_utils.UnifiedLLMClient") as mock_client_class:
            mock_client = Mock()
            mock_client.query_model.return_value = "Test response"
            mock_client.remove_think_block.return_value = "Test response"
            mock_client_class.return_value = mock_client

            ai = JiraIssueAI()

            # Test each method
            result1 = ai.standardize_description("Test description", "Test Title")
            result2 = ai.compare_content("Content1", "Content2")

            assert result1 == "Test response"
            assert result2 is True  # compare_content returns boolean

            # Verify LLM was called for each method
            assert mock_client.query_model.call_count == 2

    @patch("jiaz.core.ai_utils.typer")
    def test_standardize_description_with_unavailable_llm(self, mock_typer):
        """Test standardize_description when LLM is unavailable."""
        with patch("jiaz.core.ai_utils.UnifiedLLMClient") as mock_client_class:
            mock_client = Mock()
            mock_client.query_model.side_effect = typer.Exit(code=1)
            mock_client.remove_think_block.return_value = "Error message"
            mock_client_class.return_value = mock_client

            ai = JiraIssueAI()
            result = ai.standardize_description("Test description", "Test Title")

            # Should return error message when LLM is unavailable
            assert "Failed to generate standardized description" in result

    @patch("jiaz.core.ai_utils.typer")
    def test_compare_content_with_unavailable_llm(self, mock_typer):
        """Test compare_content when LLM is unavailable."""
        with patch("jiaz.core.ai_utils.UnifiedLLMClient") as mock_client_class:
            mock_client = Mock()
            mock_client.query_model.side_effect = typer.Exit(code=1)
            mock_client_class.return_value = mock_client

            ai = JiraIssueAI()

            # Should raise typer.Exit when LLM is unavailable
            with pytest.raises(typer.Exit) as exc_info:
                ai.compare_content("Content1", "Content2")
            assert exc_info.value.exit_code == 1

    def test_get_available_models_ollama(self):
        """Test get_available_models for Ollama."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=False):
            with patch("jiaz.core.ai_utils.ChatOllama"):
                with patch("requests.get") as mock_get:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "models": [{"name": "qwen3:14b"}, {"name": "llama2:7b"}]
                    }
                    mock_get.return_value = mock_response

                    client = UnifiedLLMClient()
                    models = client.get_available_models()

                    assert "qwen3:14b" in models
                    assert "llama2:7b" in models

    def test_get_available_models_ollama_failure(self):
        """Test get_available_models for Ollama when request fails."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=False):
            with patch("jiaz.core.ai_utils.ChatOllama"):
                with patch("requests.get") as mock_get:
                    mock_get.side_effect = Exception("Connection failed")

                    client = UnifiedLLMClient()
                    models = client.get_available_models()

                    assert models == []

    def test_get_available_models_gemini(self):
        """Test get_available_models for Gemini."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=True):
            with patch(
                "jiaz.core.ai_utils.get_gemini_api_key", return_value="test_key"
            ):
                with patch("jiaz.core.ai_utils.ChatGoogleGenerativeAI"):
                    client = UnifiedLLMClient()
                    models = client.get_available_models()

                    assert "gemini-2.5-pro" in models
                    assert "gemini-1.5-pro" in models
                    assert "gemini-1.5-flash" in models

    def test_model_exists(self):
        """Test model_exists method."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=False):
            with patch("jiaz.core.ai_utils.ChatOllama"):
                with patch("requests.get") as mock_get:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "models": [{"name": "qwen3:14b"}]
                    }
                    mock_get.return_value = mock_response

                    client = UnifiedLLMClient()

                    assert client.model_exists("qwen3") is True  # Partial match
                    assert client.model_exists("nonexistent") is False

    def test_query_model_with_different_ollama_model(self):
        """Test query_model with different Ollama model."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=False):
            with patch("jiaz.core.ai_utils.ChatOllama") as mock_ollama:
                mock_llm_instance = Mock()
                mock_llm_instance.invoke.return_value = Mock(content="Test response")
                mock_ollama.return_value = mock_llm_instance

                client = UnifiedLLMClient()
                with patch.object(client, "check_availability", return_value=True):
                    result = client.query_model("Test prompt", model="llama2:7b")

                assert result == "Test response"
                # Should be called twice: once for initialization, once for temp_llm
                assert mock_ollama.call_count == 2

    def test_query_model_with_llm_invocation_error(self):
        """Test query_model when LLM invocation raises an exception."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=False):
            with patch("jiaz.core.ai_utils.ChatOllama") as mock_ollama:
                mock_llm_instance = Mock()
                mock_llm_instance.invoke.side_effect = Exception(
                    "LLM invocation failed"
                )
                mock_ollama.return_value = mock_llm_instance

                client = UnifiedLLMClient()
                with patch.object(client, "check_availability", return_value=True):
                    with pytest.raises(typer.Exit) as exc_info:
                        client.query_model("Test prompt")
                    assert exc_info.value.exit_code == 1

    def test_remove_think_block(self):
        """Test remove_think_block method."""
        with patch("jiaz.core.ai_utils.should_use_gemini", return_value=False):
            with patch("jiaz.core.ai_utils.ChatOllama"):
                client = UnifiedLLMClient()

                # Test with think block
                text_with_think = "Some text <think>thinking...</think> more text"
                cleaned = client.remove_think_block(text_with_think)
                assert cleaned == "Some text more text"

                # Test without think block
                text_without_think = "Just normal text"
                cleaned = client.remove_think_block(text_without_think)
                assert cleaned == "Just normal text"

    def test_compare_content_with_unexpected_result(self):
        """Test compare_content with unexpected AI result."""
        with patch("jiaz.core.ai_utils.UnifiedLLMClient") as mock_client_class:
            mock_client = Mock()
            mock_client.query_model.return_value = "maybe"  # Unexpected result
            mock_client_class.return_value = mock_client

            ai = JiraIssueAI()
            result = ai.compare_content("Content1", "Content2")

            # Should default to True for unexpected result
            assert result is True

    def test_compare_descriptions_method(self):
        """Test compare_descriptions method."""
        with patch("jiaz.core.ai_utils.UnifiedLLMClient") as mock_client_class:
            mock_client = Mock()
            mock_client.query_model.return_value = "true"
            mock_client_class.return_value = mock_client

            ai = JiraIssueAI()
            result = ai.compare_descriptions("Standard desc", "Terminal output")

            assert result is True
            mock_client.query_model.assert_called_once()


class TestIntegration:
    """Integration tests for ai_utils module."""

    @patch("jiaz.core.ai_utils.should_use_gemini")
    @patch("jiaz.core.ai_utils.ChatOllama")
    def test_end_to_end_ollama_workflow(self, mock_ollama, mock_should_use_gemini):
        """Test end-to-end workflow with Ollama."""
        mock_should_use_gemini.return_value = False
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="Ollama response")
        mock_ollama.return_value = mock_llm

        # Create AI instance and test workflow
        ai = JiraIssueAI()
        # Mock check_availability to return True so workflow doesn't fail
        with patch.object(ai.llm, "check_availability", return_value=True):
            result = ai.standardize_description(
                "Test description for standardization", "Test Title"
            )

        assert "Ollama response" in result
        assert ai.llm.use_gemini is False

    @patch("jiaz.core.ai_utils.should_use_gemini")
    @patch("jiaz.core.ai_utils.get_gemini_api_key")
    @patch("jiaz.core.ai_utils.ChatGoogleGenerativeAI")
    def test_end_to_end_gemini_workflow(
        self, mock_gemini, mock_get_api_key, mock_should_use_gemini
    ):
        """Test end-to-end workflow with Gemini."""
        mock_should_use_gemini.return_value = True
        mock_get_api_key.return_value = "test_key"
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="Gemini response")
        mock_gemini.return_value = mock_llm

        # Create AI instance and test workflow
        ai = JiraIssueAI()
        result = ai.standardize_description(
            "Test description for standardization", "Test Title"
        )

        assert "Gemini response" in result
        assert ai.llm.use_gemini is True

    @patch("jiaz.core.ai_utils.should_use_gemini")
    @patch("jiaz.core.ai_utils.ChatOllama")
    def test_end_to_end_ollama_unavailable_workflow(
        self, mock_ollama, mock_should_use_gemini
    ):
        """Test end-to-end workflow when Ollama is unavailable."""
        mock_should_use_gemini.return_value = False
        mock_ollama.return_value = Mock()  # Create mock instance for initialization

        # Create AI instance
        ai = JiraIssueAI()

        # Mock check_availability to return False (Ollama unavailable)
        with patch.object(ai.llm, "check_availability", return_value=False):
            result = ai.standardize_description(
                "Test description for standardization", "Test Title"
            )

        # Should return error message when Ollama is unavailable
        assert "Failed to generate standardized description" in result
        assert ai.llm.use_gemini is False
