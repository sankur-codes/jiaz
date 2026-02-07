"""Tests for description prompt module."""

import pytest
from jiaz.core.config_utils import load_custom_prompt
from jiaz.core.prompts.description import PROMPT


class TestDescriptionPrompt:
    """Test suite for description prompt functionality."""

    def test_prompt_exists(self):
        """Test that PROMPT constant exists and is a string."""
        assert PROMPT is not None
        assert isinstance(PROMPT, str)
        assert len(PROMPT) > 0

    def test_prompt_has_placeholder(self):
        """Test that prompt has description and title placeholders."""
        assert "{description}" in PROMPT
        assert "{title}" in PROMPT

    def test_prompt_format_functionality(self):
        """Test that prompt can be formatted with description and title."""
        test_description = "This is a test JIRA issue description"
        test_title = "Test Issue Title"
        formatted_prompt = PROMPT.format(description=test_description, title=test_title)

        assert test_description in formatted_prompt
        assert test_title in formatted_prompt
        assert "{description}" not in formatted_prompt
        assert "{title}" not in formatted_prompt

    def test_prompt_content_structure(self):
        """Test that prompt has expected content structure."""
        prompt_lower = PROMPT.lower()

        # Should contain instructions about standardization
        assert any(
            word in prompt_lower
            for word in ["standard", "format", "improve", "structure"]
        )

        # Should be clear about the task
        assert len(PROMPT) > 100  # Should be substantial instruction

    def test_prompt_multiple_descriptions(self):
        """Test prompt formatting with various descriptions."""
        test_descriptions = [
            "Simple description",
            "Complex description with\nmultiple lines\nand various content",
            "Description with special characters: !@#$%^&*()",
            "",  # Empty description
            "Very long description " * 20,  # Long description
        ]

        for description in test_descriptions:
            try:
                formatted = PROMPT.format(description=description, title="Test Title")
                assert description in formatted
                assert isinstance(formatted, str)
            except Exception as e:
                pytest.fail(
                    f"Failed to format prompt with description '{description}': {e}"
                )

    def test_prompt_no_extra_placeholders(self):
        """Test that prompt doesn't have unintended placeholders."""
        # Format with test description
        test_description = "Test description"
        formatted = PROMPT.format(description=test_description, title="Test Title")

        # Check for any remaining unformatted placeholders
        import re

        remaining_placeholders = re.findall(r"\{[^}]*\}", formatted)

        # Should not have any remaining placeholders after formatting
        assert (
            len(remaining_placeholders) == 0
        ), f"Found unformatted placeholders: {remaining_placeholders}"

    def test_prompt_preserves_formatting(self):
        """Test that prompt preserves description formatting."""
        description_with_formatting = """
        Line 1
        Line 2 with indentation
            - Bullet point
            - Another bullet point

        Paragraph after blank line
        """

        formatted = PROMPT.format(
            description=description_with_formatting, title="Test Title"
        )

        # Original formatting should be preserved
        assert "Line 1" in formatted
        assert "Line 2 with indentation" in formatted
        assert "- Bullet point" in formatted

    def test_prompt_handles_special_characters(self):
        """Test that prompt handles special characters in description."""
        special_description = "Description with \"quotes\", 'apostrophes', and {braces}"

        formatted = PROMPT.format(description=special_description, title="Test Title")

        assert '"quotes"' in formatted
        assert "'apostrophes'" in formatted
        assert "{braces}" in formatted

    def test_prompt_is_well_formed(self):
        """Test that prompt is well-formed and suitable for AI."""
        # Should be substantial enough for AI processing
        assert len(PROMPT.split()) > 20  # At least 20 words

        # Should have clear instruction format
        prompt_lines = PROMPT.split("\n")
        assert len(prompt_lines) > 1  # Multi-line instruction

    def test_prompt_consistency(self):
        """Test that prompt is consistent across multiple accesses."""
        # PROMPT should be a constant
        prompt1 = PROMPT
        prompt2 = PROMPT

        assert prompt1 is prompt2  # Same object reference
        assert prompt1 == prompt2  # Same content

    def test_prompt_with_edge_case_descriptions(self):
        """Test prompt with edge case descriptions."""
        # Test with None - this should work since Python's str formatting can handle None
        result = PROMPT.format(description=None, title="Test Title")
        assert "None" in result

        # Test with non-string types that should be converted to strings
        edge_cases = [
            123,  # Non-string type
            ["list", "of", "items"],  # List type
            {"key": "value"},  # Dict type
        ]

        for edge_case in edge_cases:
            try:
                result = PROMPT.format(description=edge_case, title="Test Title")
                assert str(edge_case) in result
            except (TypeError, AttributeError):
                # These are acceptable errors for non-string types
                pass


class TestDescriptionPromptUsage:
    """Test suite for description prompt usage patterns."""

    def test_typical_usage_pattern(self):
        """Test typical usage pattern for description prompt."""
        # Simulate typical usage
        jira_description = """
        As a user, I want to be able to login to the system
        so that I can access my personal dashboard.

        Acceptance Criteria:
        - User can enter username and password
        - System validates credentials
        - User is redirected to dashboard on success
        """

        # Format the prompt
        ai_prompt = PROMPT.format(description=jira_description, title="Login Feature")

        # Should contain the original description
        assert "As a user, I want to be able to login" in ai_prompt
        assert "Acceptance Criteria:" in ai_prompt

        # Should be ready for AI processing
        assert len(ai_prompt) > len(jira_description)  # Should have added instructions

    def test_empty_description_handling(self):
        """Test handling of empty descriptions."""
        empty_description = ""
        formatted = PROMPT.format(description=empty_description, title="Test Title")

        # Should still be a valid prompt even with empty description
        assert isinstance(formatted, str)
        assert len(formatted) > 0

        # The instruction part should still be there
        assert len(formatted) > 50  # Should have substantial instruction content

    def test_prompt_reusability(self):
        """Test that prompt can be reused multiple times."""
        descriptions = ["First description", "Second description", "Third description"]

        formatted_prompts = []
        for desc in descriptions:
            formatted = PROMPT.format(description=desc, title="Test Title")
            formatted_prompts.append(formatted)

        # All should be different (due to different descriptions)
        assert len(set(formatted_prompts)) == len(descriptions)

        # But all should contain the same base instruction structure
        for i, prompt in enumerate(formatted_prompts):
            assert descriptions[i] in prompt


class TestLoadCustomPrompt:
    """Test suite for loading custom prompt templates from files."""

    def test_load_valid_custom_prompt(self, tmp_path):
        """Test loading a valid custom prompt file."""
        prompt_file = tmp_path / "my_prompt.py"
        prompt_file.write_text(
            "PROMPT = '''Custom prompt. Title: {title} Desc: {description}'''\n"
        )

        result = load_custom_prompt(str(prompt_file))
        assert result is not None
        assert "{title}" in result
        assert "{description}" in result
        assert "Custom prompt" in result

    def test_load_file_not_found(self):
        """Test that missing file returns None with warning."""
        result = load_custom_prompt("/nonexistent/path/prompt.py")
        assert result is None

    def test_load_non_py_file(self, tmp_path):
        """Test that non-.py file returns None with warning."""
        txt_file = tmp_path / "prompt.txt"
        txt_file.write_text("PROMPT = 'hello {title} {description}'")

        result = load_custom_prompt(str(txt_file))
        assert result is None

    def test_load_file_without_prompt_variable(self, tmp_path):
        """Test that file without PROMPT variable returns None."""
        prompt_file = tmp_path / "bad_prompt.py"
        prompt_file.write_text("TEMPLATE = 'not the right variable'\n")

        result = load_custom_prompt(str(prompt_file))
        assert result is None

    def test_load_file_with_syntax_error(self, tmp_path):
        """Test that file with syntax error returns None."""
        prompt_file = tmp_path / "broken.py"
        prompt_file.write_text("PROMPT = '''unclosed string\n")

        result = load_custom_prompt(str(prompt_file))
        assert result is None

    def test_load_prompt_missing_title_placeholder(self, tmp_path):
        """Test that prompt without {title} placeholder returns None."""
        prompt_file = tmp_path / "no_title.py"
        prompt_file.write_text("PROMPT = '''Only has {description}'''\n")

        result = load_custom_prompt(str(prompt_file))
        assert result is None

    def test_load_prompt_missing_description_placeholder(self, tmp_path):
        """Test that prompt without {description} placeholder returns None."""
        prompt_file = tmp_path / "no_desc.py"
        prompt_file.write_text("PROMPT = '''Only has {title}'''\n")

        result = load_custom_prompt(str(prompt_file))
        assert result is None

    def test_load_prompt_not_a_string(self, tmp_path):
        """Test that non-string PROMPT variable returns None."""
        prompt_file = tmp_path / "int_prompt.py"
        prompt_file.write_text("PROMPT = 12345\n")

        result = load_custom_prompt(str(prompt_file))
        assert result is None

    def test_loaded_prompt_can_be_formatted(self, tmp_path):
        """Test that a loaded custom prompt can be formatted with title and description."""
        prompt_file = tmp_path / "good.py"
        prompt_file.write_text(
            "PROMPT = '''Rewrite this. Title: {title}\\nDesc: {description}'''\n"
        )

        result = load_custom_prompt(str(prompt_file))
        assert result is not None

        formatted = result.format(title="My Issue", description="Fix the bug")
        assert "My Issue" in formatted
        assert "Fix the bug" in formatted
        assert "{title}" not in formatted
        assert "{description}" not in formatted
