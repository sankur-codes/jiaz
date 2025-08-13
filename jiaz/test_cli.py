"""Tests for CLI module."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from jiaz.cli import app, main


@pytest.fixture
def runner():
    return CliRunner()


class TestCLI:
    """Test suite for CLI functionality."""

    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        assert callable(main)

    def test_app_creation(self):
        """Test that Typer app is created properly."""
        assert app is not None
        assert hasattr(app, "callback")  # Typer apps have callback attribute

    def test_cli_help_command(self, runner):
        """Test CLI help command."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "jiaz: Jira CLI assistant" in result.output
        assert "config" in result.output
        assert "analyze" in result.output

    def test_config_subcommand_available(self, runner):
        """Test that config subcommand is available."""
        result = runner.invoke(app, ["config", "--help"])

        assert result.exit_code == 0
        # Should show config-related commands
        assert any(
            word in result.output.lower()
            for word in ["config", "configuration", "init", "set", "get", "list"]
        )

    def test_analyze_subcommand_available(self, runner):
        """Test that analyze subcommand is available."""
        result = runner.invoke(app, ["analyze", "--help"])

        assert result.exit_code == 0
        # Should show analyze-related commands
        assert any(
            word in result.output.lower() for word in ["analyze", "issue", "sprint"]
        )

    def test_invalid_command(self, runner):
        """Test behavior with invalid command."""
        result = runner.invoke(app, ["invalid_command"])

        assert result.exit_code != 0
        # Typer should show error for unknown command

    @patch("jiaz.cli.app")
    def test_main_function_calls_app(self, mock_app):
        """Test that main function calls the app."""
        main()
        mock_app.assert_called_once()

    def test_config_subcommands_integration(self, runner):
        """Test config subcommands are properly integrated."""
        # Test config init help
        result = runner.invoke(app, ["config", "init", "--help"])
        assert result.exit_code == 0

        # Test config set help
        result = runner.invoke(app, ["config", "set", "--help"])
        assert result.exit_code == 0

        # Test config get help
        result = runner.invoke(app, ["config", "get", "--help"])
        assert result.exit_code == 0

        # Test config list help
        result = runner.invoke(app, ["config", "list", "--help"])
        assert result.exit_code == 0

        # Test config use help
        result = runner.invoke(app, ["config", "use", "--help"])
        assert result.exit_code == 0

    def test_analyze_subcommands_integration(self, runner):
        """Test analyze subcommands are properly integrated."""
        # Test analyze issue help
        result = runner.invoke(app, ["analyze", "issue", "--help"])
        assert result.exit_code == 0

        # Test analyze sprint help
        result = runner.invoke(app, ["analyze", "sprint", "--help"])
        assert result.exit_code == 0

    def test_cli_without_arguments(self, runner):
        """Test CLI behavior when called without arguments."""
        result = runner.invoke(app, [])

        # Should show help or available commands (may exit with 2 for missing command)
        assert result.exit_code in [0, 2]
        assert len(result.output) > 0  # Should produce some output

    def test_cli_version_or_info(self, runner):
        """Test CLI provides proper information."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "jiaz: Jira CLI assistant" in result.output

        # Check that both main command groups are listed
        help_text = result.output.lower()
        assert "config" in help_text
        assert "analyze" in help_text

    def test_nested_command_structure(self, runner):
        """Test that nested command structure works properly."""
        # Test that we can access nested commands

        # Config commands
        config_commands = ["init", "set", "get", "list", "use"]
        for cmd in config_commands:
            result = runner.invoke(app, ["config", cmd, "--help"])
            assert result.exit_code == 0, f"Config {cmd} command failed"

        # Analyze commands
        analyze_commands = ["issue", "sprint"]
        for cmd in analyze_commands:
            result = runner.invoke(app, ["analyze", cmd, "--help"])
            assert result.exit_code == 0, f"Analyze {cmd} command failed"

    def test_error_handling_for_malformed_commands(self, runner):
        """Test error handling for malformed commands."""
        # Test incomplete commands
        result = runner.invoke(app, ["config"])
        # Should either show config help or error
        assert result.exit_code in [0, 2]  # 0 for help, 2 for missing command

        result = runner.invoke(app, ["analyze"])
        # Should either show analyze help or error
        assert result.exit_code in [0, 2]  # 0 for help, 2 for missing command

    def test_app_attributes(self):
        """Test that app has expected attributes and structure."""
        # Test that app is a Typer instance
        assert hasattr(app, "callback")

        # Test basic functionality by invoking help
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Should show available commands in help
        help_text = result.output.lower()
        assert "config" in help_text or "analyze" in help_text


class TestMainFunction:
    """Test suite specifically for the main function."""

    @patch("jiaz.cli.app")
    def test_main_execution(self, mock_app):
        """Test main function execution."""
        # Test that main can be called without arguments
        main()

        # Verify that the app was called
        mock_app.assert_called_once()

    def test_main_is_entry_point(self):
        """Test that main function serves as proper entry point."""
        # The main function should exist and be importable
        from jiaz.cli import main

        assert callable(main)

        # It should be able to handle being called directly
        # We won't actually call it to avoid side effects
        assert main.__name__ == "main"


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def test_full_command_chain_help(self, runner):
        """Test full command chain help output."""
        # Test full help hierarchy
        commands_to_test = [
            ["--help"],
            ["config", "--help"],
            ["config", "init", "--help"],
            ["config", "set", "--help"],
            ["config", "get", "--help"],
            ["config", "list", "--help"],
            ["config", "use", "--help"],
            ["analyze", "--help"],
            ["analyze", "issue", "--help"],
            ["analyze", "sprint", "--help"],
        ]

        for command_chain in commands_to_test:
            result = runner.invoke(app, command_chain)
            assert result.exit_code == 0, f"Command chain {command_chain} failed"
            assert (
                len(result.output) > 0
            ), f"Command chain {command_chain} produced no output"

    def test_cli_import_structure(self):
        """Test that CLI imports are structured correctly."""
        # Test that we can import the main components
        from jiaz.cli import app, main
        from jiaz.commands import analyze, config

        # Verify imports work
        assert app is not None
        assert main is not None
        assert config is not None
        assert analyze is not None

        # Verify structure
        assert hasattr(config, "app")
        assert hasattr(analyze, "app")
