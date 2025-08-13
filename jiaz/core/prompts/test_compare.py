"""Tests for core prompts compare module."""

from jiaz.core.prompts.compare import (GENERIC_CONTENT_PROMPT,
                                       JIRA_DESCRIPTION_PROMPT, PROMPT)


class TestPromptConstants:
    """Test suite for prompt constants and templates."""

    def test_jira_description_prompt_exists(self):
        """Test that JIRA description prompt is defined."""
        assert JIRA_DESCRIPTION_PROMPT is not None
        assert isinstance(JIRA_DESCRIPTION_PROMPT, str)
        assert len(JIRA_DESCRIPTION_PROMPT) > 0

    def test_generic_content_prompt_exists(self):
        """Test that generic content prompt is defined."""
        assert GENERIC_CONTENT_PROMPT is not None
        assert isinstance(GENERIC_CONTENT_PROMPT, str)
        assert len(GENERIC_CONTENT_PROMPT) > 0

    def test_backward_compatibility_prompt(self):
        """Test that PROMPT exists for backward compatibility."""
        assert PROMPT is not None
        assert PROMPT == JIRA_DESCRIPTION_PROMPT

    def test_prompt_structure_jira(self):
        """Test the structure of JIRA description prompt."""
        prompt = JIRA_DESCRIPTION_PROMPT

        # Should contain key sections
        assert "EVALUATION CRITERIA" in prompt
        assert "SIMILARITY THRESHOLD" in prompt
        assert "IMPORTANT" in prompt
        assert "STANDARDIZED DESCRIPTION" in prompt
        assert "TERMINAL-FRIENDLY OUTPUT" in prompt
        assert "RESPONSE" in prompt

        # Should contain placeholders
        assert "{standardized_description}" in prompt
        assert "{terminal_friendly_output}" in prompt

        # Should specify expected response format
        assert "true" in prompt.lower()
        assert "false" in prompt.lower()

    def test_prompt_structure_generic(self):
        """Test the structure of generic content prompt."""
        prompt = GENERIC_CONTENT_PROMPT

        # Should contain key sections
        assert "EVALUATION CRITERIA" in prompt
        assert "EVALUATION THRESHOLD" in prompt
        assert "IMPORTANT" in prompt
        assert "CONTENT 1" in prompt
        assert "CONTENT 2" in prompt
        assert "RESPONSE" in prompt

        # Should contain placeholders
        assert "{comparison_context}" in prompt
        assert "{content1}" in prompt
        assert "{content2}" in prompt

        # Should specify expected response format
        assert "true" in prompt.lower()
        assert "false" in prompt.lower()


class TestPromptFormatting:
    """Test suite for prompt formatting functionality."""

    def test_jira_prompt_formatting(self):
        """Test formatting JIRA description prompt with actual values."""
        standardized_desc = "This is a standardized JIRA description with *bold* text."
        terminal_output = "This is a terminal-friendly output with ANSI codes."

        formatted_prompt = JIRA_DESCRIPTION_PROMPT.format(
            standardized_description=standardized_desc,
            terminal_friendly_output=terminal_output,
        )

        assert standardized_desc in formatted_prompt
        assert terminal_output in formatted_prompt
        assert "{standardized_description}" not in formatted_prompt
        assert "{terminal_friendly_output}" not in formatted_prompt

    def test_generic_prompt_formatting(self):
        """Test formatting generic content prompt with actual values."""
        content1 = "First piece of content for comparison."
        content2 = "Second piece of content for comparison."
        context = "similarity"

        formatted_prompt = GENERIC_CONTENT_PROMPT.format(
            content1=content1, content2=content2, comparison_context=context
        )

        assert content1 in formatted_prompt
        assert content2 in formatted_prompt
        assert context in formatted_prompt
        assert "{content1}" not in formatted_prompt
        assert "{content2}" not in formatted_prompt
        assert "{comparison_context}" not in formatted_prompt

    def test_jira_prompt_with_special_characters(self):
        """Test JIRA prompt formatting with special characters."""
        standardized_desc = (
            "Description with special chars: !@#$%^&*()_+{}[]|\\:;\"'<>,.?/"
        )
        terminal_output = "Terminal output with newlines\nand\ttabs"

        formatted_prompt = JIRA_DESCRIPTION_PROMPT.format(
            standardized_description=standardized_desc,
            terminal_friendly_output=terminal_output,
        )

        assert standardized_desc in formatted_prompt
        assert terminal_output in formatted_prompt

    def test_generic_prompt_with_different_contexts(self):
        """Test generic prompt with different comparison contexts."""
        content1 = "Sample content 1"
        content2 = "Sample content 2"

        contexts = ["similarity", "equivalence", "accuracy", "consistency"]

        for context in contexts:
            formatted_prompt = GENERIC_CONTENT_PROMPT.format(
                content1=content1, content2=content2, comparison_context=context
            )

            # Context should appear multiple times in the prompt
            assert formatted_prompt.count(context) >= 3
            assert content1 in formatted_prompt
            assert content2 in formatted_prompt


class TestPromptValidation:
    """Test suite for prompt validation and quality."""

    def test_jira_prompt_instructions_clarity(self):
        """Test that JIRA prompt has clear instructions."""
        prompt = JIRA_DESCRIPTION_PROMPT

        # Should clearly specify what to compare
        assert "compare" in prompt.lower()
        assert "jira" in prompt.lower()
        assert "description" in prompt.lower()

        # Should specify response format clearly
        assert "only respond with exactly" in prompt.lower()
        assert "no quotes" in prompt.lower()
        assert "no additional text" in prompt.lower()

        # Should mention key evaluation criteria
        assert "content" in prompt.lower()
        assert "formatting" in prompt.lower()
        assert "markup" in prompt.lower()

    def test_generic_prompt_instructions_clarity(self):
        """Test that generic prompt has clear instructions."""
        prompt = GENERIC_CONTENT_PROMPT

        # Should clearly specify comparison task
        assert "compare" in prompt.lower()
        assert "content" in prompt.lower()
        assert "criteria" in prompt.lower()

        # Should specify response format clearly
        assert "only respond with exactly" in prompt.lower()
        assert "no quotes" in prompt.lower()
        assert "no additional text" in prompt.lower()

        # Should be flexible for different contexts
        assert "context" in prompt.lower()
        assert "evaluation" in prompt.lower()

    def test_prompt_response_format_specification(self):
        """Test that prompts clearly specify expected response format."""
        for prompt in [JIRA_DESCRIPTION_PROMPT, GENERIC_CONTENT_PROMPT]:
            # Should specify exact response format
            assert "true or false only" in prompt.lower()
            assert "lowercase" in prompt.lower()

            # Should discourage additional content
            assert "do not provide explanations" in prompt.lower()
            assert "do not add" in prompt.lower()

    def test_prompt_length_and_structure(self):
        """Test that prompts are well-structured and appropriately sized."""
        for prompt_name, prompt in [
            ("JIRA", JIRA_DESCRIPTION_PROMPT),
            ("Generic", GENERIC_CONTENT_PROMPT),
        ]:
            # Should be substantial but not excessively long
            assert (
                500 < len(prompt) < 3000
            ), f"{prompt_name} prompt length should be reasonable"

            # Should have clear section breaks
            assert (
                prompt.count("\n") > 10
            ), f"{prompt_name} prompt should have multiple sections"

            # Should have consistent formatting
            assert (
                '"""' in prompt
            ), f"{prompt_name} prompt should use proper section markers"


class TestPromptEdgeCases:
    """Test suite for edge cases in prompt handling."""

    def test_jira_prompt_with_empty_values(self):
        """Test JIRA prompt formatting with empty values."""
        formatted_prompt = JIRA_DESCRIPTION_PROMPT.format(
            standardized_description="", terminal_friendly_output=""
        )

        # Should still format correctly even with empty values
        assert "STANDARDIZED DESCRIPTION:" in formatted_prompt
        assert "TERMINAL-FRIENDLY OUTPUT:" in formatted_prompt
        assert "RESPONSE" in formatted_prompt

    def test_generic_prompt_with_empty_values(self):
        """Test generic prompt formatting with empty values."""
        formatted_prompt = GENERIC_CONTENT_PROMPT.format(
            content1="", content2="", comparison_context=""
        )

        # Should still format correctly even with empty values
        assert "CONTENT 1:" in formatted_prompt
        assert "CONTENT 2:" in formatted_prompt
        assert "RESPONSE" in formatted_prompt

    def test_jira_prompt_with_very_long_content(self):
        """Test JIRA prompt with very long content."""
        long_content = "A" * 10000  # Very long string

        formatted_prompt = JIRA_DESCRIPTION_PROMPT.format(
            standardized_description=long_content, terminal_friendly_output=long_content
        )

        # Should handle long content without issues
        assert long_content in formatted_prompt
        assert len(formatted_prompt) > 20000

    def test_generic_prompt_with_unicode_content(self):
        """Test generic prompt with Unicode content."""
        unicode_content1 = "Content with émojis 🚀 and ñicode 中文"
        unicode_content2 = "Другой контент with مختلف languages"

        formatted_prompt = GENERIC_CONTENT_PROMPT.format(
            content1=unicode_content1,
            content2=unicode_content2,
            comparison_context="similarity",
        )

        # Should handle Unicode content correctly
        assert unicode_content1 in formatted_prompt
        assert unicode_content2 in formatted_prompt


class TestPromptIntegration:
    """Integration tests for prompt module."""

    def test_all_prompts_importable(self):
        """Test that all prompts can be imported together."""
        from jiaz.core.prompts.compare import (GENERIC_CONTENT_PROMPT,
                                               JIRA_DESCRIPTION_PROMPT, PROMPT)

        # All should be accessible
        prompts = [JIRA_DESCRIPTION_PROMPT, GENERIC_CONTENT_PROMPT, PROMPT]
        for prompt in prompts:
            assert prompt is not None
            assert isinstance(prompt, str)
            assert len(prompt) > 0

    def test_prompt_module_structure(self):
        """Test the overall structure of the prompts module."""
        import jiaz.core.prompts.compare as compare_module

        # Should have expected attributes
        assert hasattr(compare_module, "JIRA_DESCRIPTION_PROMPT")
        assert hasattr(compare_module, "GENERIC_CONTENT_PROMPT")
        assert hasattr(compare_module, "PROMPT")

        # Module should have proper docstring
        assert compare_module.__doc__ is not None
        assert "Prompt templates" in compare_module.__doc__

    def test_prompts_usability_in_ai_utils(self):
        """Test that prompts can be used as expected in ai_utils context."""
        # Test that prompts can be formatted and used as they would be in real code
        standardized = "# USER STORY\nAs a user, I want to test this feature."
        terminal = "USER STORY\nAs a user, I want to test this feature."

        jira_prompt = JIRA_DESCRIPTION_PROMPT.format(
            standardized_description=standardized, terminal_friendly_output=terminal
        )

        # Should be ready for AI consumption
        assert "USER STORY" in jira_prompt
        assert "true or false only" in jira_prompt
        assert len(jira_prompt) > 1000  # Should be substantial

        # Generic prompt test
        generic_prompt = GENERIC_CONTENT_PROMPT.format(
            content1="Original text",
            content2="Modified text",
            comparison_context="similarity",
        )

        assert "Original text" in generic_prompt
        assert "Modified text" in generic_prompt
        assert "similarity" in generic_prompt
