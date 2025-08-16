"""Tests for core validate module."""

from unittest.mock import Mock, patch

import pytest
from jiaz.core.validate import issue_exists, valid_jira_client, validate_sprint_config


class TestValidationFunctions:
    """Test suite for validation functions."""

    @patch("jiaz.core.validate.JIRA")
    @patch("jiaz.core.validate.requests")
    @patch("jiaz.core.validate.typer")
    def test_valid_jira_client_success(self, mock_typer, mock_requests, mock_jira):
        """Test successful JIRA client validation."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        # Mock successful JIRA client creation
        mock_jira_instance = Mock()
        mock_jira.return_value = mock_jira_instance

        # Mock typer.Exit to be a proper exception
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code

        mock_typer.Exit = MockExit

        result = valid_jira_client("https://test.jira.com", "test_token")

        assert result == mock_jira_instance
        mock_requests.get.assert_called_once_with("https://test.jira.com", timeout=5)
        mock_jira.assert_called_once_with(
            server="https://test.jira.com", kerberos=True, token_auth="test_token"
        )
        mock_jira_instance.myself.assert_called_once()
        mock_typer.echo.assert_called_with(
            "✅ JIRA authentication successful.", err=False
        )

    @patch("jiaz.core.validate.requests")
    @patch("jiaz.core.validate.typer")
    def test_valid_jira_client_connection_error(self, mock_typer, mock_requests):
        """Test JIRA client validation with connection error."""
        # Use requests.exceptions.RequestException for proper mocking
        import requests

        mock_requests.get.side_effect = requests.exceptions.RequestException(
            "Connection failed"
        )
        mock_requests.exceptions = (
            requests.exceptions
        )  # Ensure exceptions module is available

        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code

        mock_typer.Exit = MockExit

        with pytest.raises(MockExit):
            valid_jira_client("https://invalid.jira.com", "test_token")

        mock_typer.echo.assert_called()
        assert "Unable to reach JIRA server" in str(mock_typer.echo.call_args)

    @patch("jiaz.core.validate.JIRA")
    @patch("jiaz.core.validate.requests")
    @patch("jiaz.core.validate.typer")
    def test_valid_jira_client_authentication_error(
        self, mock_typer, mock_requests, mock_jira
    ):
        """Test JIRA client validation with authentication error."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        # Mock JIRA authentication error
        from jira import JIRAError

        mock_jira_error = JIRAError(status_code=401, text="Unauthorized")
        mock_jira.side_effect = mock_jira_error

        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code

        mock_typer.Exit = MockExit

        with pytest.raises(MockExit):
            valid_jira_client("https://test.jira.com", "invalid_token")

        mock_typer.echo.assert_called()
        assert "Authentication failed" in str(mock_typer.echo.call_args)

    @patch("jiaz.core.validate.requests")
    @patch("jiaz.core.validate.typer")
    def test_valid_jira_client_with_empty_credentials(self, mock_typer, mock_requests):
        """Test JIRA client validation with empty credentials."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code

        mock_typer.Exit = MockExit

        # Even with empty token, should try to connect
        with patch("jiaz.core.validate.JIRA") as mock_jira:
            mock_jira.side_effect = Exception("Invalid credentials")

            with pytest.raises(MockExit):
                valid_jira_client("https://test.jira.com", "")

            mock_typer.echo.assert_called()

    def test_validate_sprint_config_valid(self):
        """Test sprint config validation with valid config."""
        valid_config = {
            "jira_project": "TEST",
            "jira_backlog_name": "Backlog",
            "jira_sprintboard_name": "Sprint Board",
            "jira_sprintboard_id": "123",
            "jira_board_name": "Test Board",
        }

        with patch("jiaz.core.validate.typer") as mock_typer:
            validate_sprint_config(valid_config)
            mock_typer.echo.assert_called_with(
                "✅ Sprint configuration validated successfully. Required configs are present.",
                err=False,
            )

    @patch("jiaz.core.validate.typer")
    def test_validate_sprint_config_missing_fields(self, mock_typer):
        """Test sprint config validation with missing required fields."""
        invalid_config = {
            "jira_project": "TEST",
            # Missing other required fields
        }

        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code

        mock_typer.Exit = MockExit

        with pytest.raises(MockExit):
            validate_sprint_config(invalid_config)

        mock_typer.echo.assert_called()
        assert "Missing required configuration field(s)" in str(
            mock_typer.echo.call_args
        )

    @patch("jiaz.core.validate.typer")
    def test_validate_sprint_config_empty_values(self, mock_typer):
        """Test sprint config validation with empty values."""
        invalid_config = {
            "jira_project": "",
            "jira_backlog_name": "",
            "jira_sprintboard_name": "",
            "jira_sprintboard_id": "",
            "jira_board_name": "",
        }

        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code

        mock_typer.Exit = MockExit

        with pytest.raises(MockExit):
            validate_sprint_config(invalid_config)

        mock_typer.echo.assert_called()

    def test_issue_exists_true(self):
        """Test issue_exists when issue exists."""
        mock_jira = Mock()
        mock_jira.rate_limited_request.return_value = Mock()

        result = issue_exists(mock_jira, "TEST-123")

        assert result is True
        mock_jira.rate_limited_request.assert_called_once()

    def test_issue_exists_false(self):
        """Test issue_exists when issue does not exist."""
        mock_jira = Mock()
        from jira import JIRAError

        mock_error = JIRAError(status_code=404, text="Not Found")
        mock_jira.rate_limited_request.side_effect = mock_error

        with patch("jiaz.core.validate.typer") as mock_typer:
            with patch("jiaz.core.validate.colorize") as mock_colorize:
                mock_colorize.return_value = "Issue not found"

                result = issue_exists(mock_jira, "TEST-999")

                assert result is False
                mock_colorize.assert_called_once()
                mock_typer.echo.assert_called_once()

    @patch("jiaz.core.validate.typer")
    @patch("jiaz.core.validate.colorize")
    def test_issue_exists_with_server_error(self, mock_colorize, mock_typer):
        """Test issue_exists with server error."""
        mock_jira = Mock()
        mock_colorize.return_value = "Error message"

        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code

        mock_typer.Exit = MockExit

        # Test JIRAError with non-404 status
        from jira import JIRAError

        mock_error = JIRAError(status_code=500, text="Server Error")
        mock_jira.rate_limited_request.side_effect = mock_error

        with pytest.raises(MockExit):
            issue_exists(mock_jira, "TEST-123")

        mock_typer.echo.assert_called()
        mock_colorize.assert_called()


class TestValidationIntegration:
    """Integration tests for validation module."""

    @patch("jiaz.core.validate.JIRA")
    @patch("jiaz.core.validate.requests")
    @patch("jiaz.core.validate.typer")
    def test_full_validation_workflow(self, mock_typer, mock_requests, mock_jira):
        """Test complete validation workflow."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        # Mock successful JIRA client
        mock_jira_instance = Mock()
        mock_jira.return_value = mock_jira_instance

        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code

        mock_typer.Exit = MockExit

        # Test JIRA client validation
        client = valid_jira_client("https://test.jira.com", "test_token")
        assert client == mock_jira_instance

        # Test sprint config validation
        valid_config = {
            "jira_project": "TEST",
            "jira_backlog_name": "Backlog",
            "jira_sprintboard_name": "Sprint Board",
            "jira_sprintboard_id": "123",
            "jira_board_name": "Test Board",
        }

        validate_sprint_config(valid_config)

        # Should have called typer.echo twice (once for each validation)
        assert mock_typer.echo.call_count >= 2


class TestValidationEdgeCases:
    """Test edge cases and error conditions."""

    @patch("jiaz.core.validate.typer")
    def test_validate_sprint_config_with_none_values(self, mock_typer):
        """Test sprint config validation with None values."""
        invalid_config = {
            "jira_project": None,
            "jira_backlog_name": None,
            "jira_sprintboard_name": None,
            "jira_sprintboard_id": None,
            "jira_board_name": None,
        }

        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code

        mock_typer.Exit = MockExit

        with pytest.raises(MockExit):
            validate_sprint_config(invalid_config)

        mock_typer.echo.assert_called()

    @patch("jiaz.core.validate.typer")
    @patch("jiaz.core.validate.colorize")
    def test_issue_exists_with_unexpected_exception(self, mock_colorize, mock_typer):
        """Test issue_exists with unexpected exception."""
        mock_jira = Mock()
        mock_jira.rate_limited_request.side_effect = Exception("Unexpected error")
        mock_colorize.return_value = "Error message"

        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code

        mock_typer.Exit = MockExit

        with pytest.raises(MockExit):
            issue_exists(mock_jira, "TEST-123")

        mock_typer.echo.assert_called()
        mock_colorize.assert_called()

    def test_validate_module_imports(self):
        """Test that all required modules can be imported."""
        from jiaz.core.validate import (
            issue_exists,
            valid_jira_client,
            validate_sprint_config,
        )

        # Should be callable functions
        assert callable(valid_jira_client)
        assert callable(validate_sprint_config)
        assert callable(issue_exists)
