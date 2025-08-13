"""Tests for analyze issue command module."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from jiaz.commands.analyze.issue import issue


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_config():
    """Mock configuration data."""
    return {
        "default": {
            "server_url": "https://test.jira.com",
            "user_token": "test_token",
            "jira_project": "TEST",
        },
        "test_config": {
            "server_url": "https://other.jira.com",
            "user_token": "other_token",
            "jira_project": "OTHER",
        },
    }


class TestIssueCommand:
    """Test suite for issue command."""

    @patch("jiaz.commands.analyze.issue.analyze_issue")
    @patch("jiaz.commands.analyze.issue.load_config")
    @patch("jiaz.commands.analyze.issue.get_active_config")
    def test_issue_basic_call(
        self, mock_get_active, mock_load_config, mock_analyze, mock_config
    ):
        """Test basic issue command call."""
        mock_get_active.return_value = "default"
        mock_load_config.return_value = mock_config

        # Call with explicit default values since typer defaults don't resolve in direct function calls
        issue(
            id="TEST-123",
            show="",
            output="json",
            config="default",
            rundown=False,
            marshal_description=False,
        )

        mock_analyze.assert_called_once_with(
            id="TEST-123",
            output="json",
            config="default",
            show="",
            rundown=False,
            marshal_description=False,
        )

    @patch("jiaz.commands.analyze.issue.analyze_issue")
    @patch("jiaz.commands.analyze.issue.load_config")
    @patch("jiaz.commands.analyze.issue.get_active_config")
    def test_issue_with_all_options(
        self, mock_get_active, mock_load_config, mock_analyze, mock_config
    ):
        """Test issue command with all options."""
        mock_get_active.return_value = "default"
        mock_load_config.return_value = mock_config

        issue(
            id="TEST-456",
            show="status,assignee,summary",
            output="table",
            config="test_config",
            rundown=True,
            marshal_description=False,
        )

        mock_analyze.assert_called_once_with(
            id="TEST-456",
            output="table",
            config="test_config",
            show=["status", "assignee", "summary"],
            rundown=True,
            marshal_description=False,
        )

    @patch("jiaz.commands.analyze.issue.load_config")
    @patch("jiaz.commands.analyze.issue.get_active_config")
    def test_issue_mutual_exclusivity_error(
        self, mock_get_active, mock_load_config, mock_config
    ):
        """Test that rundown and marshal_description are mutually exclusive."""
        mock_get_active.return_value = "default"
        mock_load_config.return_value = mock_config

        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code

        with patch("typer.Exit", MockExit):
            with patch("typer.echo") as mock_echo:
                with pytest.raises(MockExit):
                    issue(
                        id="TEST-123",
                        show="",
                        output="json",
                        config="default",
                        rundown=True,
                        marshal_description=True,
                    )

                mock_echo.assert_called_with(
                    "❌ Cannot use --marshal-description and --rundown together. Please choose one."
                )

    @patch("jiaz.commands.analyze.issue.load_config")
    @patch("jiaz.commands.analyze.issue.get_active_config")
    def test_issue_invalid_output_format(
        self, mock_get_active, mock_load_config, mock_config
    ):
        """Test invalid output format validation."""
        mock_get_active.return_value = "default"
        mock_load_config.return_value = mock_config

        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code

        with patch("jiaz.commands.analyze.issue.typer.Exit", MockExit):
            with patch("jiaz.commands.analyze.issue.typer.echo") as mock_echo:
                with pytest.raises(MockExit):
                    issue(
                        id="TEST-123",
                        show="",
                        output="invalid",
                        config="default",
                        rundown=False,
                        marshal_description=False,
                    )

                mock_echo.assert_called_with(
                    "Invalid output format specified. Use 'json' or 'table'."
                )

    @patch("jiaz.commands.analyze.issue.load_config")
    @patch("jiaz.commands.analyze.issue.get_active_config")
    def test_issue_invalid_config(self, mock_get_active, mock_load_config, mock_config):
        """Test invalid config name validation."""
        mock_get_active.return_value = "default"
        mock_load_config.return_value = mock_config

        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code

        with patch("typer.Exit", MockExit):
            with patch("typer.echo") as mock_echo:
                with pytest.raises(MockExit):
                    issue(
                        id="TEST-123",
                        show="",
                        output="json",
                        config="nonexistent",
                        rundown=False,
                        marshal_description=False,
                    )

                mock_echo.assert_called_with("Configuration 'nonexistent' not found.")

    @patch("jiaz.commands.analyze.issue.analyze_issue")
    @patch("jiaz.commands.analyze.issue.load_config")
    @patch("jiaz.commands.analyze.issue.get_active_config")
    def test_issue_show_field_parsing(
        self, mock_get_active, mock_load_config, mock_analyze, mock_config
    ):
        """Test show field parsing."""
        mock_get_active.return_value = "default"
        mock_load_config.return_value = mock_config

        # Test with comma-separated fields
        issue(
            id="TEST-123",
            show="field1, field2 , field3",
            output="json",
            config="default",
            rundown=False,
            marshal_description=False,
        )

        mock_analyze.assert_called_once_with(
            id="TEST-123",
            output="json",
            config="default",
            show=["field1", "field2", "field3"],
            rundown=False,
            marshal_description=False,
        )

    @patch("jiaz.commands.analyze.issue.analyze_issue")
    @patch("jiaz.commands.analyze.issue.load_config")
    @patch("jiaz.commands.analyze.issue.get_active_config")
    def test_issue_id_stripping(
        self, mock_get_active, mock_load_config, mock_analyze, mock_config
    ):
        """Test that issue ID is properly stripped of whitespace."""
        mock_get_active.return_value = "default"
        mock_load_config.return_value = mock_config

        issue(
            id="  TEST-123  ",
            show="",
            output="json",
            config="default",
            rundown=False,
            marshal_description=False,
        )

        mock_analyze.assert_called_once_with(
            id="TEST-123",
            output="json",
            config="default",
            show="",
            rundown=False,
            marshal_description=False,
        )

    @patch("jiaz.commands.analyze.issue.analyze_issue")
    @patch("jiaz.commands.analyze.issue.load_config")
    @patch("jiaz.commands.analyze.issue.get_active_config")
    def test_issue_predefined_show_field(
        self, mock_get_active, mock_load_config, mock_analyze, mock_config
    ):
        """Test handling of predefined show field."""
        mock_get_active.return_value = "default"
        mock_load_config.return_value = mock_config

        # Test with predefined show value
        issue(
            id="TEST-123",
            show="<pre-defined>",
            output="json",
            config="default",
            rundown=False,
            marshal_description=False,
        )

        mock_analyze.assert_called_once_with(
            id="TEST-123",
            output="json",
            config="default",
            show="<pre-defined>",  # Should not be parsed as list
            rundown=False,
            marshal_description=False,
        )


class TestIssueCommandValidation:
    """Test suite for issue command validation."""

    def test_issue_valid_output_formats(self):
        """Test that valid output formats are accepted."""
        valid_formats = ["json", "table"]

        for format_type in valid_formats:
            with patch("jiaz.commands.analyze.issue.analyze_issue"):
                with patch("jiaz.commands.analyze.issue.load_config") as mock_load:
                    with patch(
                        "jiaz.commands.analyze.issue.get_active_config"
                    ) as mock_active:
                        mock_load.return_value = {"default": {}}
                        mock_active.return_value = "default"

                        # Should not raise exception
                        issue(
                            id="TEST-123",
                            show="",
                            output=format_type,
                            config="default",
                            rundown=False,
                            marshal_description=False,
                        )

    def test_issue_boolean_options(self):
        """Test boolean option handling."""
        with patch("jiaz.commands.analyze.issue.analyze_issue") as mock_analyze:
            with patch("jiaz.commands.analyze.issue.load_config") as mock_load:
                with patch(
                    "jiaz.commands.analyze.issue.get_active_config"
                ) as mock_active:
                    mock_load.return_value = {"default": {}}
                    mock_active.return_value = "default"

                    # Test rundown=True
                    issue(
                        id="TEST-123",
                        show="",
                        output="json",
                        config="default",
                        rundown=True,
                        marshal_description=False,
                    )
                    mock_analyze.assert_called_with(
                        id="TEST-123",
                        output="json",
                        config="default",
                        show="",
                        rundown=True,
                        marshal_description=False,
                    )

                    # Test marshal_description=True
                    issue(
                        id="TEST-123",
                        show="",
                        output="json",
                        config="default",
                        rundown=False,
                        marshal_description=True,
                    )
                    mock_analyze.assert_called_with(
                        id="TEST-123",
                        output="json",
                        config="default",
                        show="",
                        rundown=False,
                        marshal_description=True,
                    )


class TestIssueCommandIntegration:
    """Integration tests for issue command."""

    @patch("jiaz.commands.analyze.issue.analyze_issue")
    @patch("jiaz.commands.analyze.issue.load_config")
    @patch("jiaz.commands.analyze.issue.get_active_config")
    def test_issue_workflow_integration(
        self, mock_get_active, mock_load_config, mock_analyze, mock_config
    ):
        """Test complete workflow integration."""
        mock_get_active.return_value = "default"
        mock_load_config.return_value = mock_config

        # Test that all components work together
        issue(
            id="PROJ-789",
            show="status,assignee",
            output="table",
            config="test_config",
            rundown=False,
            marshal_description=True,
        )

        # Verify all validations passed and analyze_issue was called correctly
        mock_load_config.assert_called_once()
        mock_analyze.assert_called_once_with(
            id="PROJ-789",
            output="table",
            config="test_config",
            show=["status", "assignee"],
            rundown=False,
            marshal_description=True,
        )

    def test_issue_function_signature(self):
        """Test that the issue function has the expected signature."""
        import inspect

        sig = inspect.signature(issue)
        params = list(sig.parameters.keys())

        expected_params = [
            "id",
            "show",
            "output",
            "config",
            "rundown",
            "marshal_description",
        ]
        assert params == expected_params

        # Check parameter types and defaults
        assert sig.parameters["id"].annotation == str
        # Typer parameters have OptionInfo objects as defaults, not direct values
        from typer.models import OptionInfo

        assert isinstance(sig.parameters["show"].default, OptionInfo)
        assert isinstance(sig.parameters["output"].default, OptionInfo)
        assert isinstance(sig.parameters["rundown"].default, OptionInfo)
        assert isinstance(sig.parameters["marshal_description"].default, OptionInfo)


class TestIssueCommandEdgeCases:
    """Test edge cases for issue command."""

    @patch("jiaz.commands.analyze.issue.analyze_issue")
    @patch("jiaz.commands.analyze.issue.load_config")
    @patch("jiaz.commands.analyze.issue.get_active_config")
    def test_issue_empty_show_field(
        self, mock_get_active, mock_load_config, mock_analyze, mock_config
    ):
        """Test handling of empty show field."""
        mock_get_active.return_value = "default"
        mock_load_config.return_value = mock_config

        issue(
            id="TEST-123",
            show="",
            output="json",
            config="default",
            rundown=False,
            marshal_description=False,
        )

        mock_analyze.assert_called_once_with(
            id="TEST-123",
            output="json",
            config="default",
            show="",  # Should remain empty string
            rundown=False,
            marshal_description=False,
        )

    @patch("jiaz.commands.analyze.issue.analyze_issue")
    @patch("jiaz.commands.analyze.issue.load_config")
    @patch("jiaz.commands.analyze.issue.get_active_config")
    def test_issue_single_show_field(
        self, mock_get_active, mock_load_config, mock_analyze, mock_config
    ):
        """Test handling of single show field."""
        mock_get_active.return_value = "default"
        mock_load_config.return_value = mock_config

        issue(
            id="TEST-123",
            show="status",
            output="json",
            config="default",
            rundown=False,
            marshal_description=False,
        )

        mock_analyze.assert_called_once_with(
            id="TEST-123",
            output="json",
            config="default",
            show=["status"],  # Should be converted to list
            rundown=False,
            marshal_description=False,
        )

    def test_issue_command_docstring(self):
        """Test that the issue command has proper documentation."""
        assert issue.__doc__ is not None
        assert "Analyze and display data for provided issue" in issue.__doc__
