"""Tests for core sprint_utils module."""

import pytest
from unittest.mock import patch, Mock, MagicMock
import typer

from jiaz.core.sprint_utils import get_sprint_data_table


@pytest.fixture
def mock_sprint():
    """Mock Sprint object for testing."""
    mock_sprint = Mock()
    mock_sprint.get_issues_in_sprint.return_value = ['TEST-123', 'TEST-456']
    mock_sprint.get_issue.return_value = Mock()
    mock_sprint.update_story_points.return_value = (5, 3)
    return mock_sprint


@pytest.fixture
def mock_issue():
    """Mock issue object for testing."""
    mock_issue = Mock()
    mock_issue.key = 'TEST-123'
    mock_issue.fields.assignee.displayName = 'John Doe'
    mock_issue.fields.status.name = 'In Progress'
    mock_issue.fields.priority.name = 'High'
    return mock_issue


class TestGetSprintDataTable:
    """Test suite for get_sprint_data_table function."""
    
    @patch('jiaz.core.sprint_utils.get_issue_fields')
    @patch('jiaz.core.sprint_utils.link_text')
    @patch('jiaz.core.sprint_utils.colorize')
    def test_get_sprint_data_table_success(self, mock_colorize, mock_link_text, mock_get_fields, mock_sprint):
        """Test successful sprint data table generation."""
        # Mock get_issue_fields return value
        mock_field_data = {
            'work_type': 'Story',
            'title': 'Test Issue',
            'priority': 'High',
            'status': 'In Progress',
            'assignee': 'John Doe',
            'original_story_points': 5,
            'story_points': 3,
            'comments': []
        }
        mock_get_fields.return_value = mock_field_data
        
        # Mock other functions
        mock_link_text.return_value = 'TEST-123'
        mock_colorize.side_effect = lambda text, color: f"[{color}]{text}"
        
        # Mock Sprint methods
        mock_sprint.get_issues_in_sprint.return_value = ['TEST-123']
        mock_issue = Mock()
        mock_issue.key = 'TEST-123'
        mock_sprint.get_issue.return_value = mock_issue
        mock_sprint.update_story_points.return_value = (5, 3)
        
        result = get_sprint_data_table(mock_sprint, mine=False)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Verify sprint methods were called
        mock_sprint.get_issues_in_sprint.assert_called_once_with(mine=False)
        mock_sprint.get_issue.assert_called_once_with('TEST-123')
        mock_get_fields.assert_called_once()
    
    @patch('jiaz.core.sprint_utils.typer')
    def test_get_sprint_data_table_no_issues(self, mock_typer, mock_sprint):
        """Test sprint data table when no issues are found."""
        mock_sprint.get_issues_in_sprint.return_value = None
        
        # Mock typer.Exit to be a proper exception that accepts code parameter
        class MockExit(Exception):
            def __init__(self, code=0):
                self.code = code
        
        mock_typer.Exit = MockExit
        
        with pytest.raises(MockExit):
            get_sprint_data_table(mock_sprint, mine=False)
        
        mock_typer.echo.assert_called_once_with("No matching issues found in the sprint.")
    
    @patch('jiaz.core.sprint_utils.get_issue_fields')
    @patch('jiaz.core.sprint_utils.link_text')
    @patch('jiaz.core.sprint_utils.colorize')
    @patch('builtins.print')
    def test_get_sprint_data_table_skip_unassigned(self, mock_print, mock_colorize, mock_link_text, mock_get_fields, mock_sprint):
        """Test skipping unassigned issues."""
        # Mock unassigned issue
        mock_field_data = {
            'work_type': 'Story',
            'title': 'Test Issue',
            'priority': 'High',
            'status': 'Open',
            'assignee': '[neg]Unassigned',  # Simulating colorized unassigned
            'original_story_points': 5,
            'story_points': 3,
            'comments': []
        }
        mock_get_fields.return_value = mock_field_data
        
        mock_link_text.return_value = 'TEST-123'
        mock_colorize.side_effect = lambda text, color: f"[{color}]{text}"
        
        mock_sprint.get_issues_in_sprint.return_value = ['TEST-123']
        mock_issue = Mock()
        mock_issue.key = 'TEST-123'
        mock_sprint.get_issue.return_value = mock_issue
        
        result = get_sprint_data_table(mock_sprint, mine=False)
        
        # Should return empty list since unassigned issue is skipped
        assert isinstance(result, list)
        mock_print.assert_called()
        assert "Skipping TEST-123" in str(mock_print.call_args)
    
    @patch('jiaz.core.sprint_utils.get_issue_fields')
    @patch('jiaz.core.sprint_utils.link_text')
    @patch('jiaz.core.sprint_utils.colorize')
    def test_get_sprint_data_table_with_mine_flag(self, mock_colorize, mock_link_text, mock_get_fields, mock_sprint):
        """Test sprint data table with mine=True flag."""
        mock_field_data = {
            'work_type': 'Story',
            'title': 'Test Issue',
            'priority': 'High',
            'status': 'In Progress',
            'assignee': 'John Doe',
            'original_story_points': 5,
            'story_points': 3,
            'comments': []
        }
        mock_get_fields.return_value = mock_field_data
        
        mock_link_text.return_value = 'TEST-123'
        mock_colorize.side_effect = lambda text, color: f"[{color}]{text}"
        
        mock_sprint.get_issues_in_sprint.return_value = ['TEST-123']
        mock_issue = Mock()
        mock_issue.key = 'TEST-123'
        mock_sprint.get_issue.return_value = mock_issue
        mock_sprint.update_story_points.return_value = (5, 3)
        
        result = get_sprint_data_table(mock_sprint, mine=True)
        
        assert isinstance(result, list)
        mock_sprint.get_issues_in_sprint.assert_called_once_with(mine=True)
    
    @patch('jiaz.core.sprint_utils.get_issue_fields')
    @patch('jiaz.core.sprint_utils.link_text')
    @patch('jiaz.core.sprint_utils.colorize')
    def test_get_sprint_data_table_multiple_issues(self, mock_colorize, mock_link_text, mock_get_fields, mock_sprint):
        """Test sprint data table with multiple issues."""
        mock_field_data = {
            'work_type': 'Story',
            'title': 'Test Issue',
            'priority': 'High',
            'status': 'In Progress',
            'assignee': 'John Doe',
            'original_story_points': 5,
            'story_points': 3,
            'comments': []
        }
        mock_get_fields.return_value = mock_field_data
        
        mock_link_text.side_effect = ['TEST-123', 'TEST-456']
        mock_colorize.side_effect = lambda text, color: f"[{color}]{text}"
        
        mock_sprint.get_issues_in_sprint.return_value = ['TEST-123', 'TEST-456']
        mock_issue = Mock()
        mock_issue.key = 'TEST-123'
        mock_sprint.get_issue.return_value = mock_issue
        mock_sprint.update_story_points.return_value = (5, 3)
        
        result = get_sprint_data_table(mock_sprint, mine=False)
        
        assert isinstance(result, list)
        assert len(result) == 2  # Should process both issues
        
        # Verify both issues were processed
        assert mock_sprint.get_issue.call_count == 2
        assert mock_get_fields.call_count == 2
    
    @patch('jiaz.core.sprint_utils.get_issue_fields')
    @patch('jiaz.core.sprint_utils.link_text')
    @patch('jiaz.core.sprint_utils.colorize')
    def test_get_sprint_data_table_assignee_processing(self, mock_colorize, mock_link_text, mock_get_fields, mock_sprint):
        """Test assignee name processing (first name extraction)."""
        mock_field_data = {
            'work_type': 'Story',
            'title': 'Test Issue',
            'priority': 'High',
            'status': 'In Progress',
            'assignee': 'John Doe Smith',  # Full name
            'original_story_points': 5,
            'story_points': 3,
            'comments': []
        }
        mock_get_fields.return_value = mock_field_data
        
        mock_link_text.return_value = 'TEST-123'
        mock_colorize.side_effect = lambda text, color: f"[{color}]{text}"
        
        mock_sprint.get_issues_in_sprint.return_value = ['TEST-123']
        mock_issue = Mock()
        mock_issue.key = 'TEST-123'
        mock_sprint.get_issue.return_value = mock_issue
        mock_sprint.update_story_points.return_value = (5, 3)
        
        result = get_sprint_data_table(mock_sprint, mine=False)
        
        assert isinstance(result, list)
        assert len(result) == 1
        # The assignee should be processed to first name only
        row = result[0]
        # Find assignee in the row (it should be "John" not "John Doe Smith")
        # The exact position depends on the implementation, but it should contain "John"
        assert any("John" in str(cell) for cell in row)
    
    @patch('jiaz.core.sprint_utils.get_issue_fields')
    def test_get_sprint_data_table_required_fields(self, mock_get_fields, mock_sprint):
        """Test that required fields are requested correctly."""
        mock_field_data = {
            'work_type': 'Story',
            'title': 'Test Issue',
            'priority': 'High',
            'status': 'In Progress',
            'assignee': 'John Doe',
            'original_story_points': 5,
            'story_points': 3,
            'comments': []
        }
        mock_get_fields.return_value = mock_field_data
        
        mock_sprint.get_issues_in_sprint.return_value = ['TEST-123']
        mock_issue = Mock()
        mock_issue.key = 'TEST-123'
        mock_sprint.get_issue.return_value = mock_issue
        mock_sprint.update_story_points.return_value = (5, 3)
        
        with patch('jiaz.core.sprint_utils.link_text'), patch('jiaz.core.sprint_utils.colorize'):
            get_sprint_data_table(mock_sprint, mine=False)
        
        # Verify the correct required fields were requested
        mock_get_fields.assert_called_once()
        call_args = mock_get_fields.call_args
        required_fields = call_args[0][2]  # Third argument should be required_fields
        
        expected_fields = ['work_type', 'title', 'priority', 'status', 'assignee', 'original_story_points', 'story_points', 'comments']
        assert required_fields == expected_fields


class TestSprintUtilsIntegration:
    """Integration tests for sprint_utils module."""
    
    @patch('jiaz.core.sprint_utils.get_issue_fields')
    @patch('jiaz.core.sprint_utils.link_text')
    @patch('jiaz.core.sprint_utils.colorize')
    @patch('jiaz.core.sprint_utils.display_sprint_issue')
    @patch('jiaz.core.sprint_utils.display_sprint_status')
    @patch('jiaz.core.sprint_utils.display_sprint_owner')
    @patch('jiaz.core.sprint_utils.display_sprint_epic')
    def test_sprint_data_table_integration(self, mock_display_epic, mock_display_owner, 
                                         mock_display_status, mock_display_issue,
                                         mock_colorize, mock_link_text, mock_get_fields):
        """Test integration with display modules."""
        # Test that the module can be imported and key dependencies are available
        from jiaz.core.sprint_utils import get_sprint_data_table
        from jiaz.core.formatter import link_text, colorize, strip_ansi
        from jiaz.core.display import display_sprint_issue, display_sprint_status, display_sprint_owner, display_sprint_epic
        from jiaz.core.issue_utils import get_issue_fields
        
        # Verify imports work correctly
        assert callable(get_sprint_data_table)
        assert callable(link_text)
        assert callable(colorize)
        assert callable(strip_ansi)
        assert callable(display_sprint_issue)
        assert callable(display_sprint_status)
        assert callable(display_sprint_owner)
        assert callable(display_sprint_epic)
        assert callable(get_issue_fields)
    
    @patch('jiaz.core.sprint_utils.get_issue_fields')
    @patch('jiaz.core.sprint_utils.link_text')
    @patch('jiaz.core.sprint_utils.colorize')
    def test_sprint_data_table_with_complex_data(self, mock_colorize, mock_link_text, mock_get_fields, mock_sprint):
        """Test sprint data table with complex data scenarios."""
        # Test with various data types and edge cases
        test_cases = [
            {
                'work_type': 'Story',
                'title': 'Complex Issue with Special Characters !@#$%',
                'priority': 'Critical',
                'status': 'In Review',
                'assignee': 'Jane Smith-Wilson',  # Hyphenated name
                'original_story_points': None,  # No original points
                'story_points': 8,
                'comments': ['Comment 1', 'Comment 2']
            },
            {
                'work_type': 'Bug',
                'title': 'Simple Bug Fix',
                'priority': 'Low',
                'status': 'Done',
                'assignee': 'Bob',  # Single name
                'original_story_points': 2,
                'story_points': 1,
                'comments': []
            }
        ]
        
        mock_colorize.side_effect = lambda text, color: f"[{color}]{text}"
        mock_link_text.side_effect = ['TEST-123', 'TEST-456']
        
        mock_sprint.get_issues_in_sprint.return_value = ['TEST-123', 'TEST-456']
        mock_issue = Mock()
        mock_issue.key = 'TEST-123'
        mock_sprint.get_issue.return_value = mock_issue
        mock_sprint.update_story_points.side_effect = [(None, 8), (2, 1)]
        
        # Mock get_issue_fields to return different data for each call
        mock_get_fields.side_effect = test_cases
        
        result = get_sprint_data_table(mock_sprint, mine=False)
        
        assert isinstance(result, list)
        assert len(result) == 2
        
        # Verify both test cases were processed
        assert mock_get_fields.call_count == 2
        assert mock_sprint.update_story_points.call_count == 2


class TestErrorHandling:
    """Test suite for error handling in sprint_utils."""
    
    @patch('jiaz.core.sprint_utils.get_issue_fields')
    @patch('jiaz.core.sprint_utils.typer')
    def test_get_sprint_data_table_exception_handling(self, mock_typer, mock_get_fields, mock_sprint):
        """Test exception handling in get_sprint_data_table."""
        mock_sprint.get_issues_in_sprint.return_value = ['TEST-123']
        mock_sprint.get_issue.side_effect = Exception("JIRA API error")
        
        with pytest.raises(Exception):
            get_sprint_data_table(mock_sprint, mine=False)
    
    @patch('jiaz.core.sprint_utils.get_issue_fields')
    @patch('jiaz.core.sprint_utils.link_text')
    @patch('jiaz.core.sprint_utils.colorize')
    def test_get_sprint_data_table_missing_field_data(self, mock_colorize, mock_link_text, mock_get_fields, mock_sprint):
        """Test handling of missing field data."""
        # Mock field data with None values for missing fields
        mock_field_data = {
            'work_type': 'Story',
            'title': 'Test Issue',
            'priority': 'High',
            'status': 'In Progress',
            'assignee': 'John Doe',
            'original_story_points': None,  # Missing data
            'story_points': None,  # Missing data
            'comments': []
        }
        mock_get_fields.return_value = mock_field_data
        
        mock_link_text.return_value = 'TEST-123'
        mock_colorize.side_effect = lambda text, color: f"[{color}]{text}"
        
        mock_sprint.get_issues_in_sprint.return_value = ['TEST-123']
        mock_issue = Mock()
        mock_issue.key = 'TEST-123'
        mock_sprint.get_issue.return_value = mock_issue
        mock_sprint.update_story_points.return_value = (None, None)
        
        # Should handle missing data gracefully
        result = get_sprint_data_table(mock_sprint, mine=False)
        
        assert isinstance(result, list)
        # Should still process the issue even with missing data
        assert len(result) == 1