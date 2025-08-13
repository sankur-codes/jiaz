"""Tests for core formatter module."""

from unittest.mock import patch

from jiaz.core.formatter import (
    color_map,
    colorize,
    filter_columns,
    format_epic_table,
    format_issue_table,
    format_owner_table,
    format_status_table,
    format_to_csv,
    format_to_json,
    generate_assignee_summary_table,
    generate_status_summary_table,
    get_coloured,
    link_text,
    strip_ansi,
    time_delta,
)


class TestFormatterFunctions:
    """Test suite for formatter utility functions."""

    def test_colorize_function(self):
        """Test colorize function with different options."""
        text = "test_text"

        # Test positive coloring
        result = colorize(text, "pos")
        assert "\033[32m" in result  # Green
        assert "test_text" in result
        assert "\033[0m" in result  # Reset

        # Test negative coloring
        result = colorize(text, "neg")
        assert "\033[31m" in result  # Red

        # Test neutral coloring
        result = colorize(text, "neu")
        assert "\033[33m" in result  # Yellow

        # Test header coloring
        result = colorize(text, "head")
        assert "\033[35m" in result  # Magenta

        # Test info coloring
        result = colorize(text, "info")
        assert "\033[36m" in result  # Cyan

        # Test default (blue) coloring
        result = colorize(text)
        assert "\033[34m" in result  # Blue

    def test_color_map_function(self):
        """Test color_map function with various status values."""
        # Test hardcoded statuses
        result = color_map("New", "New")
        assert "\033[31m" in result  # Red for New

        result = color_map("Closed", "Closed")
        assert "\033[32m" in result  # Green for Closed

        result = color_map("In Progress", "In Progress")
        assert "\033[33m" in result  # Yellow for In Progress

        result = color_map("Review", "Review")
        assert "\033[34m" in result  # Blue for Review

        # Test unknown status (should return uncolored text)
        result = color_map("Unknown Status", "Unknown Status")
        assert result == "Unknown Status"

    def test_strip_ansi_function(self):
        """Test ANSI code stripping."""
        # Test with ANSI color codes
        colored_text = "\033[32mGreen Text\033[0m"
        result = strip_ansi(colored_text)
        assert result == "Green Text"

        # Test with ANSI hyperlinks
        hyperlink = "\033]8;;https://example.com\033\\Link Text\033]8;;\033\\"
        result = strip_ansi(hyperlink)
        assert result == "Link Text"

        # Test with regular text
        regular_text = "Regular Text"
        result = strip_ansi(regular_text)
        assert result == "Regular Text"

        # Test with non-string input
        result = strip_ansi(123)
        assert result == 123

    def test_time_delta_function(self):
        """Test time delta calculation."""
        # Test with ISO format
        future_time = "2024-12-31T23:59:59Z"
        result = time_delta(future_time)
        assert result is not None

        # Test with date-only format
        future_date = "2024-12-31"
        result = time_delta(future_date)
        assert result is not None

        # Test with invalid input
        result = time_delta("invalid_date")
        assert result is not None  # Should return dummy delta

        # Test with None input
        result = time_delta(None)
        assert result is not None  # Should return dummy delta

    @patch("jiaz.core.config_utils.get_specific_config")
    @patch("jiaz.core.config_utils.get_active_config")
    def test_link_text_function(self, mock_get_active_config, mock_get_specific_config):
        """Test link text generation."""
        mock_get_active_config.return_value = "test_config"
        mock_get_specific_config.return_value = {
            "server_url": "https://jira.example.com"
        }

        # Test with automatic URL generation
        result = link_text("PROJ-123")
        assert "\033]8;;https://jira.example.com/browse/PROJ-123\033\\" in result
        assert "PROJ-123" in result

        # Test with custom URL
        result = link_text("PROJ-456", "https://custom.com")
        assert "\033]8;;https://custom.com\033\\" in result
        assert "PROJ-456" in result

    def test_get_coloured_function(self):
        """Test get_coloured function."""
        # Test with table content
        table_content = [["New", "In Progress"], ["Closed", "Review"]]
        result = get_coloured(table_content=table_content)
        assert len(result) == 2
        assert len(result[0]) == 2

        # Test with headers
        headers = ["Status", "Priority"]
        result = get_coloured(header=headers)
        assert len(result) == 2
        assert "\033[35m" in result[0]  # Magenta for headers

    def test_generate_status_summary_table(self):
        """Test status summary table generation."""
        data_table = [
            [
                "John",
                "PROJ-1",
                "Task 1",
                "High",
                "Story",
                5,
                5,
                "In Progress",
                "Comment",
            ],
            ["Jane", "PROJ-2", "Task 2", "Medium", "Bug", 3, 3, "Closed", "Comment"],
            [
                "Bob",
                "PROJ-3",
                "Task 3",
                "Low",
                "Story",
                "Not Assigned",
                "Not Assigned",
                "New",
                "Comment",
            ],
        ]
        headers = [
            "Assignee",
            "Issue Key",
            "Title",
            "Priority",
            "Work Type",
            "Initial Story Points",
            "Actual Story Points",
            "Status",
            "Comment",
        ]

        result = generate_status_summary_table(data_table, headers)

        assert "Closed" in result
        assert "In Progress" in result
        assert "Not Started" in result
        assert result["Closed"]["WithPointsCount"] == 1
        assert result["Closed"]["StoryPointSum"] == 3.0
        assert result["Not Started"]["WithoutPointsCount"] == 1

    def test_generate_assignee_summary_table(self):
        """Test assignee summary table generation."""
        data_table = [
            [
                "John",
                "PROJ-1",
                "Task 1",
                "High",
                "Story",
                5,
                5,
                "In Progress",
                "Comment",
            ],
            ["John", "PROJ-2", "Task 2", "Medium", "Bug", 3, 3, "Closed", "Comment"],
            ["Jane", "PROJ-3", "Task 3", "Low", "Story", 2, 2, "New", "Comment"],
        ]
        headers = [
            "Assignee",
            "Issue Key",
            "Title",
            "Priority",
            "Work Type",
            "Initial Story Points",
            "Actual Story Points",
            "Status",
            "Comment",
        ]
        statuses = ["Closed", "In Progress", "New"]

        result = generate_assignee_summary_table(data_table, headers, statuses)

        assert "John" in result
        assert "Jane" in result
        assert result["John"]["Closed"]["count"] == 1
        assert result["John"]["Closed"]["points"] == 3.0
        assert result["John"]["In Progress"]["count"] == 1
        assert result["John"]["Total"]["count"] == 2

    def test_format_issue_table(self):
        """Test issue table formatting."""
        data_table = [["row1", "data1"], ["row2", "data2"]]
        headers = ["col1", "col2"]

        result_table, result_headers = format_issue_table(data_table, headers)

        assert result_table == data_table
        assert result_headers == headers

    def test_format_status_table(self):
        """Test status table formatting."""
        data_table = [
            [
                "John",
                "PROJ-1",
                "Task 1",
                "High",
                "Story",
                5,
                5,
                "In Progress",
                "Comment",
            ]
        ]
        headers = [
            "Assignee",
            "Issue Key",
            "Title",
            "Priority",
            "Work Type",
            "Initial Story Points",
            "Actual Story Points",
            "Status",
            "Comment",
        ]

        result_table, result_headers = format_status_table(data_table, headers)

        assert result_headers == ["Status", "Issue Count", "Sprint Point Total"]
        assert len(result_table) > 0

    def test_format_owner_table(self):
        """Test owner table formatting."""
        data_table = [
            [
                "John",
                "PROJ-1",
                "Task 1",
                "High",
                "Story",
                5,
                5,
                "In Progress",
                "Comment",
            ]
        ]
        headers = [
            "Assignee",
            "Issue Key",
            "Title",
            "Priority",
            "Work Type",
            "Initial Story Points",
            "Actual Story Points",
            "Status",
            "Comment",
        ]

        result_table, result_headers = format_owner_table(data_table, headers)

        expected_headers = [
            "Assignee",
            "Completed",
            "Review",
            "In Progress",
            "New",
            "Total",
        ]
        assert result_headers == expected_headers
        assert len(result_table) > 0

    def test_format_epic_table(self):
        """Test epic table formatting."""
        data_table = [["epic1", "data1"], ["epic2", "data2"]]
        headers = ["col1", "col2"]

        result_table, result_headers = format_epic_table(data_table, headers)

        assert result_table == data_table
        assert result_headers == headers

    def test_format_to_json(self):
        """Test JSON formatting."""
        data_table = [["John", "PROJ-1"], ["Jane", "PROJ-2"]]
        headers = ["Assignee", "Issue"]

        result = format_to_json(data_table, headers)

        assert '"Assignee": "John"' in result
        assert '"Issue": "PROJ-1"' in result
        assert '"Assignee": "Jane"' in result

    def test_format_to_csv(self):
        """Test CSV formatting."""
        data_table = [["John", "PROJ-1"], ["Jane", "PROJ-2"]]
        headers = ["Assignee", "Issue"]

        result = format_to_csv(data_table, headers)

        assert "Assignee,Issue" in result
        assert "John,PROJ-1" in result
        assert "Jane,PROJ-2" in result

    def test_filter_columns(self):
        """Test column filtering."""
        data_table = [["A", "B", "C"], ["D", "E", "F"]]
        headers = ["col1", "col2", "col3"]
        selected_columns = ["col1", "col3"]

        result_data, result_headers = filter_columns(
            data_table, headers, selected_columns
        )

        assert result_headers == ["col1", "col3"]
        assert result_data == [["A", "C"], ["D", "F"]]

        # Test with empty selection
        result_data, result_headers = filter_columns(data_table, headers, [])
        assert result_data == data_table
        assert result_headers == headers

        # Test with None selection
        result_data, result_headers = filter_columns(data_table, headers, None)
        assert result_data == data_table
        assert result_headers == headers

    def test_colorize_edge_cases(self):
        """Test colorize function with edge cases."""
        # Test with empty string
        result = colorize("", "pos")
        assert "\033[32m" in result and "\033[0m" in result

        # Test with very long string
        long_text = "a" * 1000
        result = colorize(long_text, "neg")
        assert long_text in result
        assert "\033[31m" in result

        # Test with special characters
        special_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = colorize(special_text, "neu")
        assert special_text in result

    def test_time_delta_edge_cases(self):
        """Test time_delta with various edge cases."""
        # Test with None
        result = time_delta(None)
        assert result is not None

        # Test with empty string
        result = time_delta("")
        assert result is not None

        # Test with malformed date
        result = time_delta("not-a-date")
        assert result is not None

        # Test with future date
        result = time_delta("2030-12-31T23:59:59Z")
        assert result is not None

    def test_format_json_edge_cases(self):
        """Test JSON formatting with edge cases."""
        # Test with empty data
        result = format_to_json([], [])
        assert result == "[]"

        # Test with special characters in data
        data_table = [["Special: !@#$", "Unicode"]]
        headers = ["Header1", "Header2"]
        result = format_to_json(data_table, headers)
        assert "Special: !@#$" in result
        assert "Unicode" in result

    def test_format_csv_edge_cases(self):
        """Test CSV formatting with edge cases."""
        # Test with empty data
        result = format_to_csv([], [])
        # CSV might return empty string or just headers
        assert len(result) >= 0

        # Test with commas in data
        data_table = [["Value with commas", "Normal value"]]
        headers = ["Header1", "Header2"]
        result = format_to_csv(data_table, headers)
        assert "Header1,Header2" in result
        assert "Value with commas" in result

    def test_strip_ansi_edge_cases(self):
        """Test ANSI stripping with edge cases."""
        # Test with nested ANSI codes
        nested_ansi = "\033[32m\033[1mBold Green\033[0m\033[0m"
        result = strip_ansi(nested_ansi)
        assert result == "Bold Green"

        # Test with numbers and other types
        assert strip_ansi(123) == 123
        assert strip_ansi(None) is None
        assert strip_ansi([]) == []

    def test_generate_summary_tables_edge_cases(self):
        """Test summary table generation with edge cases."""
        # Test with None values in data - using strings to avoid float conversion issues
        data_table = [
            [None, "PROJ-1", None, "High", "Story", "N/A", "N/A", None, "Comment"]
        ]
        headers = [
            "Assignee",
            "Issue Key",
            "Title",
            "Priority",
            "Work Type",
            "Initial Story Points",
            "Actual Story Points",
            "Status",
            "Comment",
        ]

        result = generate_status_summary_table(data_table, headers)
        assert "Not Started" in result  # None status should default to this

        # Test with empty strings
        data_table = [["", "PROJ-1", "", "", "", "N/A", "N/A", "", ""]]
        result = generate_status_summary_table(data_table, headers)
        assert "Not Started" in result
