"""Tests for core custom_fields module."""

import json
from unittest.mock import Mock, patch

import pytest
from jiaz.core.custom_fields import (
    FIELD_NAME_PATTERNS,
    clear_cache,
    discover_fields,
    load_fields,
)


@pytest.fixture
def mock_jira_fields():
    """Sample JIRA fields API response."""
    return [
        {"id": "customfield_10001", "name": "Story Points"},
        {"id": "customfield_10002", "name": "Sprint"},
        {"id": "customfield_10003", "name": "Epic Link"},
        {"id": "customfield_10004", "name": "Activity Type"},
        {"id": "customfield_10005", "name": "Original Story Points"},
        {"id": "customfield_10007", "name": "Start date"},
        {"id": "customfield_10008", "name": "End date"},
        {"id": "customfield_10009", "name": "Parent Link"},
        {"id": "customfield_10010", "name": "Status Summary"},
        {"id": "summary", "name": "Summary"},
        {"id": "status", "name": "Status"},
    ]


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Use a temp dir for field cache."""
    with patch("jiaz.core.custom_fields.CACHE_DIR", tmp_path):
        yield tmp_path


class TestDiscoverFields:
    """Test suite for field discovery."""

    def test_discover_fields_success(self, mock_jira_fields):
        """Test successful field discovery."""
        mock_client = Mock()
        mock_client.fields.return_value = mock_jira_fields

        result = discover_fields(mock_client)

        assert result["story_points"] == "customfield_10001"
        assert result["sprints"] == "customfield_10002"
        assert result["epic_link"] == "customfield_10003"
        assert result["work_type"] == "customfield_10004"
        assert result["original_story_points"] == "customfield_10005"
        assert result["epic_start_date"] == "customfield_10007"
        assert result["epic_end_date"] == "customfield_10008"
        assert result["parent_link"] == "customfield_10009"
        assert result["status_summary"] == "customfield_10010"

    def test_discover_fields_case_insensitive(self):
        """Test that field matching is case-insensitive."""
        mock_client = Mock()
        mock_client.fields.return_value = [
            {"id": "customfield_99", "name": "story points"},
        ]

        result = discover_fields(mock_client)

        assert result["story_points"] == "customfield_99"

    def test_discover_fields_partial_match(self):
        """Test discovery when only some fields exist on the instance."""
        mock_client = Mock()
        mock_client.fields.return_value = [
            {"id": "customfield_10001", "name": "Story Points"},
            {"id": "summary", "name": "Summary"},
        ]

        result = discover_fields(mock_client)

        assert result["story_points"] == "customfield_10001"
        assert "epic_link" not in result
        assert "sprints" not in result

    def test_discover_fields_api_failure(self):
        """Test discovery when the JIRA API call fails."""
        mock_client = Mock()
        mock_client.fields.side_effect = Exception("API error")

        result = discover_fields(mock_client)

        assert result == {}

    def test_discover_fields_ignores_builtin_fields(self):
        """Test that built-in fields (non-customfield_ IDs) are never matched."""
        mock_client = Mock()
        mock_client.fields.return_value = [
            {"id": "status", "name": "Status Summary"},
        ]

        result = discover_fields(mock_client)

        assert "status_summary" not in result

    def test_discover_fields_first_pattern_wins(self):
        """Test that the first matching pattern name wins."""
        mock_client = Mock()
        mock_client.fields.return_value = [
            {"id": "customfield_A", "name": "Start date"},
            {"id": "customfield_B", "name": "Epic Start Date"},
        ]

        result = discover_fields(mock_client)

        # "Epic Start Date" is listed first in FIELD_NAME_PATTERNS, so it wins
        assert result["epic_start_date"] == "customfield_B"


class TestLoadFields:
    """Test suite for field loading with cache."""

    def test_load_fields_from_discovery(self, temp_cache_dir, mock_jira_fields):
        """Test that fields are discovered and cached on first load."""
        mock_client = Mock()
        mock_client.fields.return_value = mock_jira_fields

        result = load_fields("test_config", mock_client)

        assert result["story_points"] == "customfield_10001"
        # Verify cache was written
        cache_file = temp_cache_dir / "test_config.json"
        assert cache_file.exists()

    def test_load_fields_from_cache(self, temp_cache_dir):
        """Test that cached fields are returned without calling the API."""
        cached = {"story_points": "customfield_cached"}
        cache_file = temp_cache_dir / "test_config.json"
        cache_file.write_text(json.dumps(cached))

        mock_client = Mock()

        result = load_fields("test_config", mock_client)

        assert result == cached
        mock_client.fields.assert_not_called()

    def test_load_fields_corrupt_cache(self, temp_cache_dir, mock_jira_fields):
        """Test that corrupt cache triggers re-discovery."""
        cache_file = temp_cache_dir / "test_config.json"
        cache_file.write_text("not valid json{{{")

        mock_client = Mock()
        mock_client.fields.return_value = mock_jira_fields

        result = load_fields("test_config", mock_client)

        assert result["story_points"] == "customfield_10001"


class TestClearCache:
    """Test suite for cache clearing."""

    def test_clear_specific_cache(self, temp_cache_dir):
        """Test clearing a specific config's cache."""
        cache_file = temp_cache_dir / "my_config.json"
        cache_file.write_text("{}")

        clear_cache("my_config")

        assert not cache_file.exists()

    def test_clear_all_caches(self, temp_cache_dir):
        """Test clearing all caches."""
        (temp_cache_dir / "config_a.json").write_text("{}")
        (temp_cache_dir / "config_b.json").write_text("{}")

        clear_cache()

        assert list(temp_cache_dir.glob("*.json")) == []

    def test_clear_nonexistent_cache(self, temp_cache_dir):
        """Test clearing cache that doesn't exist (no error)."""
        clear_cache("nonexistent")


class TestFieldNamePatterns:
    """Test suite for field name pattern coverage."""

    def test_all_logical_fields_have_patterns(self):
        """Ensure all expected logical field names are defined."""
        expected = {
            "original_story_points",
            "story_points",
            "work_type",
            "sprints",
            "epic_link",
            "epic_start_date",
            "epic_end_date",
            "parent_link",
            "status_summary",
        }
        assert set(FIELD_NAME_PATTERNS.keys()) == expected

    def test_patterns_are_non_empty_lists(self):
        """Ensure each pattern has at least one candidate name."""
        for key, patterns in FIELD_NAME_PATTERNS.items():
            assert (
                isinstance(patterns, list) and len(patterns) > 0
            ), f"{key} has invalid patterns"
