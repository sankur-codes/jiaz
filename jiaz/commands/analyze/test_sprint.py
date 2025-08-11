"""Tests for analyze sprint command module."""

import pytest
from unittest.mock import patch, Mock
import typer
from typer.testing import CliRunner

from jiaz.commands.analyze.sprint import sprint


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_config():
    """Mock configuration data."""
    return {
        'default': {
            'server_url': 'https://test.jira.com',
            'user_token': 'test_token',
            'jira_project': 'TEST'
        },
        'test_config': {
            'server_url': 'https://other.jira.com',
            'user_token': 'other_token',
            'jira_project': 'OTHER'
        }
    }


class TestSprintCommand:
    """Test suite for sprint command."""
    
    @patch('jiaz.commands.analyze.sprint.analyze_sprint')
    @patch('jiaz.commands.analyze.sprint.load_config')
    @patch('jiaz.commands.analyze.sprint.get_active_config')
    def test_sprint_basic_call(self, mock_get_active, mock_load_config, mock_analyze, mock_config):
        """Test basic sprint command call."""
        mock_get_active.return_value = 'default'
        mock_load_config.return_value = mock_config
        
        sprint(
            wrt="status",
            show=None,
            output="json",
            config="default",
            mine=False
        )
        
        mock_analyze.assert_called_once_with(
            wrt="status",
            output="json",
            config="default",
            show=None,
            mine=False
        )
    
    @patch('jiaz.commands.analyze.sprint.analyze_sprint')
    @patch('jiaz.commands.analyze.sprint.load_config')
    @patch('jiaz.commands.analyze.sprint.get_active_config')
    def test_sprint_with_all_options(self, mock_get_active, mock_load_config, mock_analyze, mock_config):
        """Test sprint command with all options."""
        mock_get_active.return_value = 'default'
        mock_load_config.return_value = mock_config
        
        sprint(
            wrt="epic",
            show="status,assignee,summary",
            output="table",
            config="test_config",
            mine=True
        )
        
        mock_analyze.assert_called_once_with(
            wrt="epic",
            output="table",
            config="test_config",
            show=["status", "assignee", "summary"],
            mine=True
        )
    
    @patch('jiaz.commands.analyze.sprint.load_config')
    @patch('jiaz.commands.analyze.sprint.get_active_config')
    def test_sprint_invalid_wrt_option(self, mock_get_active, mock_load_config, mock_config):
        """Test invalid wrt option validation."""
        mock_get_active.return_value = 'default'
        mock_load_config.return_value = mock_config
        
        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code
                
        with patch('typer.Exit', MockExit):
            with patch('typer.echo') as mock_echo:
                with pytest.raises(MockExit):
                    sprint(
                        wrt="invalid",
                        show=None,
                        output="json",
                        config="default",
                        mine=False
                    )
                
                mock_echo.assert_called_with(
                    "Invalid perspective specified. Use 'issue', 'owner', 'status', or 'epic'."
                )
    
    @patch('jiaz.commands.analyze.sprint.load_config')
    @patch('jiaz.commands.analyze.sprint.get_active_config')
    def test_sprint_invalid_output_format(self, mock_get_active, mock_load_config, mock_config):
        """Test invalid output format validation."""
        mock_get_active.return_value = 'default'
        mock_load_config.return_value = mock_config
        
        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code
                
        with patch('typer.Exit', MockExit):
            with patch('typer.echo') as mock_echo:
                with pytest.raises(MockExit):
                    sprint(
                        wrt="status",
                        show=None,
                        output="invalid",
                        config="default",
                        mine=False
                    )
                
                mock_echo.assert_called_with(
                    "Invalid output format specified. Use 'json', 'table', or 'csv'."
                )
    
    @patch('jiaz.commands.analyze.sprint.load_config')
    @patch('jiaz.commands.analyze.sprint.get_active_config')
    def test_sprint_invalid_config(self, mock_get_active, mock_load_config, mock_config):
        """Test invalid config name validation."""
        mock_get_active.return_value = 'default'
        mock_load_config.return_value = mock_config
        
        # Mock typer.Exit
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code
                
        with patch('typer.Exit', MockExit):
            with patch('typer.echo') as mock_echo:
                with pytest.raises(MockExit):
                    sprint(
                        wrt="status",
                        show=None,
                        output="json",
                        config="nonexistent",
                        mine=False
                    )
                
                mock_echo.assert_called_with(
                    "Configuration 'nonexistent' not found."
                )
    
    @patch('jiaz.commands.analyze.sprint.analyze_sprint')
    @patch('jiaz.commands.analyze.sprint.load_config')
    @patch('jiaz.commands.analyze.sprint.get_active_config')
    def test_sprint_show_field_parsing(self, mock_get_active, mock_load_config, mock_analyze, mock_config):
        """Test show field parsing."""
        mock_get_active.return_value = 'default'
        mock_load_config.return_value = mock_config
        
        # Test with comma-separated fields
        sprint(
            wrt="status",
            show="field1, field2 , field3",
            output="json",
            config="default",
            mine=False
        )
        
        mock_analyze.assert_called_once_with(
            wrt="status",
            output="json",
            config="default",
            show=["field1", "field2", "field3"],
            mine=False
        )
    
    @patch('jiaz.commands.analyze.sprint.analyze_sprint')
    @patch('jiaz.commands.analyze.sprint.load_config')
    @patch('jiaz.commands.analyze.sprint.get_active_config')
    def test_sprint_predefined_show_field(self, mock_get_active, mock_load_config, mock_analyze, mock_config):
        """Test handling of predefined show field."""
        mock_get_active.return_value = 'default'
        mock_load_config.return_value = mock_config
        
        # Test with predefined show value
        sprint(
            wrt="status",
            show="<pre-defined>",
            output="json",
            config="default",
            mine=False
        )
        
        mock_analyze.assert_called_once_with(
            wrt="status",
            output="json",
            config="default",
            show="<pre-defined>",  # Should not be parsed as list
            mine=False
        )


class TestSprintCommandValidation:
    """Test suite for sprint command validation."""
    
    def test_sprint_valid_wrt_options(self):
        """Test that valid wrt options are accepted."""
        valid_wrt_options = ["issue", "owner", "status", "epic"]
        
        for wrt_option in valid_wrt_options:
            with patch('jiaz.commands.analyze.sprint.analyze_sprint'):
                with patch('jiaz.commands.analyze.sprint.load_config') as mock_load:
                    with patch('jiaz.commands.analyze.sprint.get_active_config') as mock_active:
                        mock_load.return_value = {'default': {}}
                        mock_active.return_value = 'default'
                        
                        # Should not raise exception
                        sprint(
                            wrt=wrt_option,
                            show=None,
                            output="json",
                            config="default",
                            mine=False
                        )
    
    def test_sprint_valid_output_formats(self):
        """Test that valid output formats are accepted."""
        valid_formats = ["json", "table", "csv"]
        
        for format_type in valid_formats:
            with patch('jiaz.commands.analyze.sprint.analyze_sprint'):
                with patch('jiaz.commands.analyze.sprint.load_config') as mock_load:
                    with patch('jiaz.commands.analyze.sprint.get_active_config') as mock_active:
                        mock_load.return_value = {'default': {}}
                        mock_active.return_value = 'default'
                        
                        # Should not raise exception
                        sprint(
                            wrt="status",
                            show=None,
                            output=format_type,
                            config="default",
                            mine=False
                        )
    
    def test_sprint_mine_option(self):
        """Test mine option handling."""
        with patch('jiaz.commands.analyze.sprint.analyze_sprint') as mock_analyze:
            with patch('jiaz.commands.analyze.sprint.load_config') as mock_load:
                with patch('jiaz.commands.analyze.sprint.get_active_config') as mock_active:
                    mock_load.return_value = {'default': {}}
                    mock_active.return_value = 'default'
                    
                    # Test mine=True
                    sprint(
                        wrt="status",
                        show=None,
                        output="json",
                        config="default",
                        mine=True
                    )
                    mock_analyze.assert_called_with(
                        wrt="status",
                        output="json",
                        config="default",
                        show=None,
                        mine=True
                    )
                    
                    # Test mine=False (default)
                    sprint(
                        wrt="status",
                        show=None,
                        output="json",
                        config="default",
                        mine=False
                    )
                    mock_analyze.assert_called_with(
                        wrt="status",
                        output="json",
                        config="default",
                        show=None,
                        mine=False
                    )


class TestSprintCommandIntegration:
    """Integration tests for sprint command."""
    
    @patch('jiaz.commands.analyze.sprint.analyze_sprint')
    @patch('jiaz.commands.analyze.sprint.load_config')
    @patch('jiaz.commands.analyze.sprint.get_active_config')
    def test_sprint_workflow_integration(self, mock_get_active, mock_load_config, mock_analyze, mock_config):
        """Test complete workflow integration."""
        mock_get_active.return_value = 'default'
        mock_load_config.return_value = mock_config
        
        # Test that all components work together
        sprint(
            wrt="owner",
            show="status,assignee",
            output="csv",
            config="test_config",
            mine=True
        )
        
        # Verify all validations passed and analyze_sprint was called correctly
        mock_load_config.assert_called_once()
        mock_analyze.assert_called_once_with(
            wrt="owner",
            output="csv",
            config="test_config",
            show=["status", "assignee"],
            mine=True
        )
    
    def test_sprint_function_signature(self):
        """Test that the sprint function has the expected signature."""
        import inspect
        
        sig = inspect.signature(sprint)
        params = list(sig.parameters.keys())
        
        expected_params = ['wrt', 'show', 'output', 'config', 'mine']
        assert params == expected_params
        
        # Check parameter types and defaults
        # Typer parameters have OptionInfo objects as defaults, not direct values
        from typer.models import OptionInfo
        assert isinstance(sig.parameters['wrt'].default, OptionInfo)
        assert isinstance(sig.parameters['show'].default, OptionInfo)
        assert isinstance(sig.parameters['output'].default, OptionInfo)
        assert isinstance(sig.parameters['mine'].default, OptionInfo)


class TestSprintCommandEdgeCases:
    """Test edge cases for sprint command."""
    
    @patch('jiaz.commands.analyze.sprint.analyze_sprint')
    @patch('jiaz.commands.analyze.sprint.load_config')
    @patch('jiaz.commands.analyze.sprint.get_active_config')
    def test_sprint_none_show_field(self, mock_get_active, mock_load_config, mock_analyze, mock_config):
        """Test handling of None show field."""
        mock_get_active.return_value = 'default'
        mock_load_config.return_value = mock_config
        
        sprint(
            wrt="status",
            show=None,
            output="json",
            config="default",
            mine=False
        )
        
        mock_analyze.assert_called_once_with(
            wrt="status",
            output="json",
            config="default",
            show=None,  # Should remain None
            mine=False
        )
    
    @patch('jiaz.commands.analyze.sprint.analyze_sprint')
    @patch('jiaz.commands.analyze.sprint.load_config')
    @patch('jiaz.commands.analyze.sprint.get_active_config')
    def test_sprint_single_show_field(self, mock_get_active, mock_load_config, mock_analyze, mock_config):
        """Test handling of single show field."""
        mock_get_active.return_value = 'default'
        mock_load_config.return_value = mock_config
        
        sprint(
            wrt="status",
            show="status",
            output="json",
            config="default",
            mine=False
        )
        
        mock_analyze.assert_called_once_with(
            wrt="status",
            output="json",
            config="default",
            show=["status"],  # Should be converted to list
            mine=False
        )
    
    @patch('jiaz.commands.analyze.sprint.analyze_sprint')
    @patch('jiaz.commands.analyze.sprint.load_config')
    @patch('jiaz.commands.analyze.sprint.get_active_config')
    def test_sprint_default_values(self, mock_get_active, mock_load_config, mock_analyze, mock_config):
        """Test that default values are properly set."""
        mock_get_active.return_value = 'test_config'
        mock_load_config.return_value = mock_config
        
        sprint(
            wrt="status",
            show=None,
            output="json",
            config="test_config",
            mine=False
        )
        
        mock_analyze.assert_called_once_with(
            wrt="status",  # Default wrt
            output="json",  # Default output
            config="test_config",  # From get_active_config
            show=None,  # Default show
            mine=False  # Default mine
        )
    
    def test_sprint_command_docstring(self):
        """Test that the sprint command has proper documentation."""
        assert sprint.__doc__ is not None
        assert "Analyze and display current active sprint data" in sprint.__doc__


class TestSprintCommandErrorHandling:
    """Test error handling in sprint command."""
    
    def test_sprint_with_invalid_wrt_values(self):
        """Test sprint command with various invalid wrt values."""
        invalid_wrt_values = ["invalid", "tickets", "tasks"]
        
        for invalid_wrt in invalid_wrt_values:
            with patch('jiaz.commands.analyze.sprint.load_config') as mock_load:
                with patch('jiaz.commands.analyze.sprint.get_active_config') as mock_active:
                    with patch('jiaz.commands.analyze.sprint.analyze_sprint') as mock_analyze:
                        mock_load.return_value = {'default': {}}
                        mock_active.return_value = 'default'
                        
                        class MockExit(Exception):
                            def __init__(self, code=0):
                                self.code = code
                        
                        with patch('typer.Exit', MockExit):
                            with patch('typer.echo') as mock_echo:
                                with pytest.raises(MockExit):
                                    sprint(
                                        wrt=invalid_wrt,
                                        show=None,
                                        output="json",
                                        config="default",
                                        mine=False
                                    )
                                
                                mock_echo.assert_called_with(
                                    "Invalid perspective specified. Use 'issue', 'owner', 'status', or 'epic'."
                                )
    
    def test_sprint_with_invalid_output_values(self):
        """Test sprint command with various invalid output values."""
        invalid_output_values = ["invalid", "xml", "yaml"]
        
        for invalid_output in invalid_output_values:
            with patch('jiaz.commands.analyze.sprint.load_config') as mock_load:
                with patch('jiaz.commands.analyze.sprint.get_active_config') as mock_active:
                    with patch('jiaz.commands.analyze.sprint.analyze_sprint') as mock_analyze:
                        mock_load.return_value = {'default': {}}
                        mock_active.return_value = 'default'
                        
                        class MockExit(Exception):
                            def __init__(self, code=0):
                                self.code = code
                        
                        with patch('typer.Exit', MockExit):
                            with patch('typer.echo') as mock_echo:
                                with pytest.raises(MockExit):
                                    sprint(
                                        wrt="status",
                                        show=None,
                                        output=invalid_output,
                                        config="default",
                                        mine=False
                                    )
                                
                                mock_echo.assert_called_with(
                                    "Invalid output format specified. Use 'json', 'table', or 'csv'."
                                )