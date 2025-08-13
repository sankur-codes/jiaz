"""Tests for core issue_utils module."""

from unittest.mock import Mock, patch

from jiaz.core.issue_utils import (_get_field_definitions, analyze_issue,
                                   extract_epic_progress, extract_sprints,
                                   get_issue_children, get_issue_fields)


class TestIssueUtilsFunctions:
    """Test suite for issue_utils utility functions."""

    def test_extract_sprints_with_valid_data(self):
        """Test extract_sprints with valid sprint data."""
        sprints_data = [
            "com.atlassian.greenhopper.service.sprint.Sprint@4a5b3c2d[id=123,rapidViewId=456,state=ACTIVE,name=Sprint 1,startDate=2024-01-01,endDate=2024-01-15]",
            "com.atlassian.greenhopper.service.sprint.Sprint@7e8f9a0b[id=124,rapidViewId=456,state=CLOSED,name=Sprint 2,startDate=2024-01-16,endDate=2024-01-30]",
        ]

        result = extract_sprints(sprints_data, key="name")
        assert result == "Sprint 1, Sprint 2"

    def test_extract_sprints_with_different_key(self):
        """Test extract_sprints with different key parameter."""
        sprints_data = [
            "com.atlassian.greenhopper.service.sprint.Sprint@4a5b3c2d[id=123,rapidViewId=456,state=ACTIVE,name=Sprint 1]"
        ]

        result = extract_sprints(sprints_data, key="state")
        assert result == "ACTIVE"

    def test_extract_sprints_with_empty_data(self):
        """Test extract_sprints with empty data."""
        result = extract_sprints([], key="name")
        assert result == ""

        result = extract_sprints(None, key="name")
        assert result == ""

    def test_extract_sprints_with_invalid_format(self):
        """Test extract_sprints with invalid format."""
        sprints_data = ["invalid sprint string"]
        result = extract_sprints(sprints_data, key="name")
        assert result == ""

    def test_extract_epic_progress_valid(self):
        """Test extract_epic_progress with valid progress string."""
        progress_string = 'Some text <span id="value">75%</span> more text'
        result = extract_epic_progress(progress_string)
        assert result == "75%"

    def test_extract_epic_progress_no_match(self):
        """Test extract_epic_progress with no matching pattern."""
        progress_string = "Progress: 50% but no span tag"
        result = extract_epic_progress(progress_string)
        assert result == "Progress not found"

    def test_extract_epic_progress_empty_string(self):
        """Test extract_epic_progress with empty string."""
        result = extract_epic_progress("")
        assert result == "Progress not found"

    @patch("jiaz.core.issue_utils.link_text")
    @patch("jiaz.core.issue_utils.color_map")
    def test_get_issue_children(self, mock_color_map, mock_link_text):
        """Test get_issue_children function."""
        # Setup mocks
        mock_jira = Mock()
        mock_issue1 = Mock()
        mock_issue1.raw = {"key": "CHILD-1"}
        mock_issue1.permalink.return_value = "http://jira.com/browse/CHILD-1"
        mock_issue1.fields.status.name = "In Progress"

        mock_issue2 = Mock()
        mock_issue2.raw = {"key": "CHILD-2"}
        mock_issue2.permalink.return_value = "http://jira.com/browse/CHILD-2"
        mock_issue2.fields.status.name = "Closed"

        mock_jira.rate_limited_request.return_value = [mock_issue1, mock_issue2]
        mock_link_text.side_effect = lambda key, url: f"linked_{key}"
        mock_color_map.side_effect = lambda key, status: f"colored_{key}_{status}"

        result = get_issue_children(mock_jira, "PARENT-1")

        assert len(result) == 2
        assert "colored_linked_CHILD-1_In Progress" in result
        assert "colored_linked_CHILD-2_Closed" in result

        # Verify JQL query
        expected_jql = '"Epic Link" = "PARENT-1" OR "Parent Link" = "PARENT-1" OR parent = "PARENT-1"'
        mock_jira.rate_limited_request.assert_called_once_with(
            mock_jira.jira.search_issues, expected_jql, maxResults=1000
        )

    def test_get_issue_children_no_children(self):
        """Test get_issue_children when no children found."""
        mock_jira = Mock()
        mock_jira.rate_limited_request.return_value = []

        result = get_issue_children(mock_jira, "PARENT-1")

        assert result == []

    def test_get_issue_children_status_missing(self):
        """Test get_issue_children when status is missing."""
        mock_jira = Mock()
        mock_issue = Mock()
        mock_issue.raw = {"key": "CHILD-1"}
        mock_issue.permalink.return_value = "http://jira.com/browse/CHILD-1"
        # No status field
        (
            delattr(mock_issue.fields, "status")
            if hasattr(mock_issue.fields, "status")
            else None
        )
        mock_issue.fields = Mock(spec=[])  # Empty spec to simulate missing status

        mock_jira.rate_limited_request.return_value = [mock_issue]

        with patch("jiaz.core.issue_utils.link_text") as mock_link_text:
            with patch("jiaz.core.issue_utils.color_map") as mock_color_map:
                mock_link_text.return_value = "linked_CHILD-1"
                mock_color_map.return_value = "colored_result"

                get_issue_children(mock_jira, "PARENT-1")

                mock_color_map.assert_called_with("linked_CHILD-1", "Unknown")

    @patch("jiaz.core.issue_utils.JiraComms")
    def test_get_field_definitions_structure(self, mock_jira_comms):
        """Test _get_field_definitions returns proper structure."""
        mock_jira = Mock()
        mock_jira_comms.return_value = mock_jira

        # Create a mock issue
        mock_issue = Mock()
        mock_issue.key = "TEST-123"
        mock_issue.fields.summary = "Test Summary"
        mock_issue.fields.status.name = "In Progress"

        definitions = _get_field_definitions(mock_jira, mock_issue)

        # Check structure
        assert "required" in definitions
        assert "optional" in definitions
        assert "on_demand" in definitions

        # Check required fields exist
        required_fields = ["key", "title", "type", "assignee", "reporter", "status"]
        for field in required_fields:
            assert field in definitions["required"]
            assert "header" in definitions["required"][field]
            assert "extractor" in definitions["required"][field]
            assert "exists_check" in definitions["required"][field]

    @patch("jiaz.core.issue_utils.JiraComms")
    @patch("jiaz.core.issue_utils.display_issue")
    def test_analyze_issue_basic(self, mock_display_issue, mock_jira_comms):
        """Test analyze_issue basic functionality."""
        mock_jira = Mock()
        mock_jira_comms.return_value = mock_jira

        analyze_issue(
            id="TEST-123",
            output="json",
            config="test_config",
            show=["key", "title"],
            rundown=False,
            marshal_description=False,
        )

        mock_jira_comms.assert_called_once_with(config_name="test_config")
        # display_issue is called with headers, data, output, show parameters
        mock_display_issue.assert_called_once()
        call_args = mock_display_issue.call_args[0]
        assert len(call_args) == 4  # headers, data, output, show
        assert call_args[2] == "json"  # output
        assert call_args[3] == ["key", "title"]  # show

    @patch("jiaz.core.issue_utils.JiraComms")
    def test_get_issue_fields_required_fields(self, mock_jira_comms):
        """Test get_issue_fields with required fields."""
        # Setup mock JIRA and issue
        mock_jira = Mock()
        mock_jira_comms.return_value = mock_jira

        mock_issue = Mock()
        mock_issue.key = "TEST-123"
        mock_issue.fields.summary = "Test Issue Title"
        mock_issue.fields.status.name = "In Progress"
        mock_issue.fields.assignee.displayName = "John Doe"
        mock_issue.fields.reporter.displayName = "Jane Smith"
        mock_issue.fields.issuetype.name = "Story"
        mock_issue.permalink.return_value = "https://test.jira.com/browse/TEST-123"

        required_fields = ["key", "title", "status", "assignee", "reporter", "type"]

        result = get_issue_fields(mock_jira, mock_issue, required_fields)

        # The key field is formatted with hyperlink escape sequences
        assert (
            "TEST-123" in result["key"]
            and "https://test.jira.com/browse/TEST-123" in result["key"]
        )
        assert result["title"] == "Test Issue Title"
        assert result["status"] == "In Progress"
        assert result["assignee"] == "John Doe"
        assert result["reporter"] == "Jane Smith"
        assert result["type"] == "Story"

    @patch("jiaz.core.issue_utils.JiraComms")
    def test_get_issue_fields_missing_fields(self, mock_jira_comms):
        """Test get_issue_fields with missing fields."""
        mock_jira = Mock()
        mock_jira_comms.return_value = mock_jira

        # Create mock issue with missing fields
        mock_issue = Mock()
        mock_issue.key = "TEST-123"
        mock_issue.permalink.return_value = "https://test.jira.com/browse/TEST-123"
        # Remove summary field
        mock_issue.fields = Mock(spec=[])

        required_fields = ["key", "title"]

        with patch("jiaz.core.issue_utils.colorize") as mock_colorize:
            mock_colorize.return_value = "No Title"

            result = get_issue_fields(mock_jira, mock_issue, required_fields)

            # The key field is formatted with hyperlink escape sequences
            assert (
                "TEST-123" in result["key"]
                and "https://test.jira.com/browse/TEST-123" in result["key"]
            )
            assert result["title"] == "No Title"
            mock_colorize.assert_called_with("No Title", "neg")

    @patch("jiaz.core.issue_utils.JiraComms")
    @patch("jiaz.core.issue_utils.get_issue_children")
    def test_get_issue_fields_with_children(self, mock_get_children, mock_jira_comms):
        """Test get_issue_fields with children field."""
        mock_jira = Mock()
        mock_jira_comms.return_value = mock_jira
        mock_get_children.return_value = ["CHILD-1", "CHILD-2"]

        mock_issue = Mock()
        mock_issue.key = "PARENT-123"

        result = get_issue_fields(mock_jira, mock_issue, ["children"])

        # Children field is formatted as comma-separated string
        assert result["children"] == "CHILD-1, CHILD-2"
        mock_get_children.assert_called_once_with(mock_jira, "PARENT-123")

    @patch("jiaz.core.issue_utils.JiraComms")
    @patch("jiaz.core.issue_utils.extract_sprints")
    def test_get_issue_fields_with_sprints(self, mock_extract_sprints, mock_jira_comms):
        """Test get_issue_fields with sprints field."""
        mock_jira = Mock()
        mock_jira.sprints = "customfield_12310940"
        mock_jira_comms.return_value = mock_jira
        mock_extract_sprints.return_value = "Sprint 1, Sprint 2"

        mock_issue = Mock()
        mock_issue.key = "TEST-123"
        # Setup custom field for sprints
        setattr(mock_issue.fields, "customfield_12310940", ["sprint1", "sprint2"])

        result = get_issue_fields(mock_jira, mock_issue, ["sprints"])

        assert result["sprints"] == "Sprint 1, Sprint 2"
        mock_extract_sprints.assert_called_once_with(["sprint1", "sprint2"])

    @patch("jiaz.core.issue_utils.JiraComms")
    def test_get_issue_fields_story_points(self, mock_jira_comms):
        """Test get_issue_fields with story points fields."""
        mock_jira = Mock()
        mock_jira.story_points = "customfield_12310243"
        mock_jira.original_story_points = "customfield_12314040"
        mock_jira_comms.return_value = mock_jira

        mock_issue = Mock()
        mock_issue.key = "TEST-123"
        # Setup custom fields for story points
        setattr(mock_issue.fields, "customfield_12310243", 5.0)
        setattr(mock_issue.fields, "customfield_12314040", 3.0)

        result = get_issue_fields(
            mock_jira, mock_issue, ["story_points", "original_story_points"]
        )

        assert result["story_points"] == 5.0
        assert result["original_story_points"] == 3.0

    @patch("jiaz.core.issue_utils.JiraComms")
    def test_get_issue_fields_with_invalid_field(self, mock_jira_comms):
        """Test get_issue_fields with invalid field name."""
        mock_jira = Mock()
        mock_jira_comms.return_value = mock_jira

        mock_issue = Mock()
        mock_issue.key = "TEST-123"

        with patch("jiaz.core.issue_utils.colorize") as mock_colorize:
            mock_colorize.return_value = "Unknown field: invalid_field"

            result = get_issue_fields(mock_jira, mock_issue, ["invalid_field"])

            assert result["invalid_field"] == "Unknown field: invalid_field"
            mock_colorize.assert_called_with("Unknown field: invalid_field", "neg")

    @patch("jiaz.core.issue_utils.JiraComms")
    @patch("jiaz.core.formatter.time_delta")
    def test_get_issue_fields_with_dates(self, mock_time_delta, mock_jira_comms):
        """Test get_issue_fields with date fields."""
        mock_jira = Mock()
        mock_jira_comms.return_value = mock_jira
        mock_time_delta.return_value = "2 days ago"

        mock_issue = Mock()
        mock_issue.key = "TEST-123"
        mock_issue.fields.created = "2024-01-01T10:00:00.000Z"
        mock_issue.fields.updated = "2024-01-03T10:00:00.000Z"

        result = get_issue_fields(mock_jira, mock_issue, ["created", "updated"])

        # The function should process the dates appropriately
        assert "created" in result
        assert "updated" in result
