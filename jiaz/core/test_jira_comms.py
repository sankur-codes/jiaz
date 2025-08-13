"""Tests for core jira_comms module."""

from collections import deque
from unittest.mock import Mock, patch

import pytest

from jiaz.core.jira_comms import JiraComms


@pytest.fixture
def mock_config():
    """Mock config for testing."""
    return {
        "server_url": "https://test.jira.com",
        "user_token": "dGVzdF90b2tlbg==",  # base64 encoded 'test_token'
        "jira_project": "TEST",
    }


@pytest.fixture
def mock_jira_client():
    """Mock JIRA client."""
    mock_client = Mock()
    mock_client.issue.return_value = Mock()
    mock_client.add_comment.return_value = Mock()
    return mock_client


class TestJiraCommsInitialization:
    """Test suite for JiraComms initialization."""

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    def test_init_success(
        self, mock_jira_client, mock_decode, mock_get_config, mock_config
    ):
        """Test successful initialization of JiraComms."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_client = Mock()
        mock_jira_client.return_value = mock_client

        jira_comms = JiraComms("test_config")

        assert jira_comms.config_used == mock_config
        assert jira_comms.jira == mock_client
        assert isinstance(jira_comms.request_queue, deque)
        assert jira_comms.request_queue.maxlen == 2

        # Verify custom field IDs are set correctly
        assert jira_comms.original_story_points == "customfield_12314040"
        assert jira_comms.story_points == "customfield_12310243"
        assert jira_comms.work_type == "customfield_12320040"
        assert jira_comms.sprints == "customfield_12310940"
        assert jira_comms.epic_link == "customfield_12311140"
        assert jira_comms.epic_progress == "customfield_12317141"
        assert jira_comms.epic_start_date == "customfield_12313941"
        assert jira_comms.epic_end_date == "customfield_12313942"
        assert jira_comms.parent_link == "customfield_12313140"
        assert jira_comms.status_summary == "customfield_12320841"

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    def test_init_with_different_config(
        self, mock_jira_client, mock_decode, mock_get_config
    ):
        """Test initialization with different config name."""
        mock_get_config.return_value = {"server_url": "other.jira.com"}
        mock_decode.return_value = "other_token"
        mock_jira_client.return_value = Mock()

        JiraComms("other_config")

        mock_get_config.assert_called_once_with("other_config")
        mock_decode.assert_called_once()
        mock_jira_client.assert_called_once()


class TestRateLimitedRequest:
    """Test suite for rate limited request functionality."""

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    def test_rate_limited_request_no_delay_needed(
        self, mock_jira_client, mock_decode, mock_get_config, mock_config
    ):
        """Test rate limited request when no delay is needed."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_jira_client.return_value = Mock()

        jira_comms = JiraComms("test_config")

        # Mock function to call
        mock_func = Mock(return_value="test_result")

        result = jira_comms.rate_limited_request(mock_func, "arg1", kwarg1="value1")

        assert result == "test_result"
        mock_func.assert_called_once_with("arg1", kwarg1="value1")
        assert len(jira_comms.request_queue) == 1

    @patch("time.sleep")
    @patch("time.time")
    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    def test_rate_limited_request_with_delay(
        self,
        mock_jira_client,
        mock_decode,
        mock_get_config,
        mock_time,
        mock_sleep,
        mock_config,
    ):
        """Test rate limited request when delay is needed."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_jira_client.return_value = Mock()

        jira_comms = JiraComms("test_config")

        # Simulate two requests very close together
        current_time = 1000.0
        mock_time.side_effect = [current_time - 0.5, current_time - 0.5, current_time]

        # Fill the queue with two requests
        jira_comms.request_queue.append(current_time - 0.5)
        jira_comms.request_queue.append(current_time - 0.3)

        mock_func = Mock(return_value="test_result")

        result = jira_comms.rate_limited_request(mock_func, "arg1")

        assert result == "test_result"
        mock_func.assert_called_once_with("arg1")
        mock_sleep.assert_called_once()

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    def test_rate_limited_request_queue_management(
        self, mock_jira_client, mock_decode, mock_get_config, mock_config
    ):
        """Test that request queue is managed correctly."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_jira_client.return_value = Mock()

        jira_comms = JiraComms("test_config")
        mock_func = Mock(return_value="result")

        # Make three requests
        jira_comms.rate_limited_request(mock_func)
        jira_comms.rate_limited_request(mock_func)
        jira_comms.rate_limited_request(mock_func)

        # Queue should only contain 2 items (maxlen=2)
        assert len(jira_comms.request_queue) == 2
        assert mock_func.call_count == 3


class TestCommentOperations:
    """Test suite for comment-related operations."""

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    def test_get_comment_details_with_comments(
        self, mock_jira_client, mock_decode, mock_get_config, mock_config
    ):
        """Test getting comment details when comments exist."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_jira_client.return_value = Mock()

        jira_comms = JiraComms("test_config")

        # Mock comment objects
        mock_comment1 = Mock()
        mock_comment1.created = "2024-01-01T10:00:00Z"
        mock_comment1.author.displayName = "John Doe"

        mock_comment2 = Mock()
        mock_comment2.created = "2024-01-02T10:00:00Z"
        mock_comment2.author.displayName = "Jane Smith"

        comments = [mock_comment1, mock_comment2]

        with patch("jiaz.core.jira_comms.time_delta") as mock_time_delta:
            mock_delta = Mock()
            mock_delta.days = 5
            mock_time_delta.return_value = mock_delta

            result = jira_comms.get_comment_details(comments, "Open")

            assert "Jane" in result  # Should use latest comment author's first name
            assert "commented" in result
            assert "days ago" in result

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    def test_get_comment_details_no_comments(
        self, mock_jira_client, mock_decode, mock_get_config, mock_config
    ):
        """Test getting comment details when no comments exist."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_jira_client.return_value = Mock()

        jira_comms = JiraComms("test_config")

        with patch("jiaz.core.jira_comms.colorize") as mock_colorize:
            mock_colorize.return_value = "No Comments"

            result = jira_comms.get_comment_details([], "Open")

            assert result == "No Comments"
            mock_colorize.assert_called_once_with("No Comments", "neg")

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    def test_get_comment_details_hours_ago(
        self, mock_jira_client, mock_decode, mock_get_config, mock_config
    ):
        """Test comment details with hours format."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_jira_client.return_value = Mock()

        jira_comms = JiraComms("test_config")

        mock_comment = Mock()
        mock_comment.created = "2024-01-01T10:00:00Z"
        mock_comment.author.displayName = "Test User"

        with patch("jiaz.core.jira_comms.time_delta") as mock_time_delta:
            mock_delta = Mock()
            mock_delta.days = 0
            mock_delta.seconds = 7200  # 2 hours
            mock_time_delta.return_value = mock_delta

            result = jira_comms.get_comment_details([mock_comment], "Open")

            assert "Test" in result
            assert "2 hours ago" in result

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    def test_adding_comment_success(
        self, mock_jira_client, mock_decode, mock_get_config, mock_config
    ):
        """Test successfully adding a comment."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_client = Mock()
        mock_comment = Mock()
        mock_client.add_comment.return_value = mock_comment
        mock_jira_client.return_value = mock_client

        jira_comms = JiraComms("test_config")

        result = jira_comms.adding_comment("TEST-123", "Test comment")

        assert result == mock_comment
        mock_client.add_comment.assert_called_once_with("TEST-123", "Test comment")

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    @patch("jiaz.core.jira_comms.typer")
    @patch("jiaz.core.jira_comms.colorize")
    def test_adding_comment_failure(
        self,
        mock_colorize,
        mock_typer,
        mock_jira_client,
        mock_decode,
        mock_get_config,
        mock_config,
    ):
        """Test adding comment failure."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_client = Mock()
        mock_client.add_comment.side_effect = Exception("JIRA error")
        mock_jira_client.return_value = mock_client
        mock_colorize.return_value = "Error message"

        jira_comms = JiraComms("test_config")

        result = jira_comms.adding_comment("TEST-123", "Test comment")

        assert result is None
        mock_typer.echo.assert_called_once()
        mock_colorize.assert_called_once()


class TestIssueOperations:
    """Test suite for issue-related operations."""

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    @patch("jiaz.core.jira_comms.issue_exists")
    def test_get_issue_success(
        self,
        mock_issue_exists,
        mock_jira_client,
        mock_decode,
        mock_get_config,
        mock_config,
    ):
        """Test successfully getting an issue."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_client = Mock()
        mock_issue = Mock()
        mock_client.issue.return_value = mock_issue
        mock_jira_client.return_value = mock_client
        mock_issue_exists.return_value = True

        jira_comms = JiraComms("test_config")

        result = jira_comms.get_issue("TEST-123")

        assert result == mock_issue
        mock_issue_exists.assert_called_once_with(jira_comms, "TEST-123")
        mock_client.issue.assert_called_once_with("TEST-123")

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    @patch("jiaz.core.jira_comms.issue_exists")
    @patch("jiaz.core.jira_comms.typer")
    @patch("jiaz.core.jira_comms.colorize")
    def test_get_issue_not_exists(
        self,
        mock_colorize,
        mock_typer,
        mock_issue_exists,
        mock_jira_client,
        mock_decode,
        mock_get_config,
        mock_config,
    ):
        """Test getting an issue that doesn't exist."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_jira_client.return_value = Mock()
        mock_issue_exists.return_value = False
        mock_colorize.return_value = "Error message"

        jira_comms = JiraComms("test_config")

        with pytest.raises(SystemExit):
            jira_comms.get_issue("INVALID-123")

        mock_issue_exists.assert_called_once_with(jira_comms, "INVALID-123")
        mock_typer.echo.assert_called_once()
        mock_colorize.assert_called_once_with("Please Enter Valid Issue ID", "neg")


class TestIntegration:
    """Integration tests for JiraComms."""

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    def test_full_workflow(
        self, mock_jira_client, mock_decode, mock_get_config, mock_config
    ):
        """Test complete workflow of JiraComms operations."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_client = Mock()
        mock_jira_client.return_value = mock_client

        # Initialize JiraComms
        jira_comms = JiraComms("test_config")

        # Test that all custom fields are properly initialized
        expected_fields = {
            "original_story_points": "customfield_12314040",
            "story_points": "customfield_12310243",
            "work_type": "customfield_12320040",
            "sprints": "customfield_12310940",
            "epic_link": "customfield_12311140",
            "epic_progress": "customfield_12317141",
            "epic_start_date": "customfield_12313941",
            "epic_end_date": "customfield_12313942",
            "parent_link": "customfield_12313140",
            "status_summary": "customfield_12320841",
        }

        for field_name, field_id in expected_fields.items():
            assert getattr(jira_comms, field_name) == field_id

        # Test that request queue is initialized
        assert isinstance(jira_comms.request_queue, deque)
        assert jira_comms.request_queue.maxlen == 2

        # Test rate limiting functionality
        mock_func = Mock(return_value="result")
        result1 = jira_comms.rate_limited_request(mock_func, "arg1")
        result2 = jira_comms.rate_limited_request(mock_func, "arg2")

        assert result1 == "result"
        assert result2 == "result"
        assert len(jira_comms.request_queue) == 2

        # Verify all calls were made
        mock_func.assert_any_call("arg1")
        mock_func.assert_any_call("arg2")

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    def test_comment_workflow_integration(
        self, mock_jira_client, mock_decode, mock_get_config, mock_config
    ):
        """Test comment-related workflow integration."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_client = Mock()
        mock_jira_client.return_value = mock_client

        jira_comms = JiraComms("test_config")

        # Test comment details with empty list
        with patch("jiaz.core.jira_comms.colorize", return_value="No Comments"):
            result = jira_comms.get_comment_details([], "Open")
            assert result == "No Comments"

        # Test adding comment
        mock_comment = Mock()
        mock_client.add_comment.return_value = mock_comment

        result = jira_comms.adding_comment("TEST-123", "Integration test comment")
        assert result == mock_comment

        # Verify the request was rate-limited
        assert len(jira_comms.request_queue) == 1


class TestErrorHandling:
    """Test suite for error handling scenarios."""

    @patch("jiaz.core.jira_comms.get_specific_config")
    def test_init_with_invalid_config(self, mock_get_config):
        """Test initialization with invalid config."""
        mock_get_config.side_effect = Exception("Config not found")

        with pytest.raises(Exception):
            JiraComms("invalid_config")

    @patch("jiaz.core.jira_comms.get_specific_config")
    @patch("jiaz.core.jira_comms.decode_secure_value")
    @patch("jiaz.core.jira_comms.valid_jira_client")
    def test_rate_limited_request_exception_handling(
        self, mock_jira_client, mock_decode, mock_get_config, mock_config
    ):
        """Test rate limited request with exception."""
        mock_get_config.return_value = mock_config
        mock_decode.return_value = "test_token"
        mock_jira_client.return_value = Mock()

        jira_comms = JiraComms("test_config")

        # Mock function that raises exception
        mock_func = Mock(side_effect=Exception("API error"))

        with pytest.raises(Exception):
            jira_comms.rate_limited_request(mock_func, "arg1")

        # Request should still be added to queue even if function fails
        assert len(jira_comms.request_queue) == 1
