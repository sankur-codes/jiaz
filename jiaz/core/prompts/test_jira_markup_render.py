"""Tests for JIRA markup render prompts."""

import pytest

from jiaz.core.prompts.jira_markup_render import GEMINI_PROMPT, OLLAMA_PROMPT


class TestJiraMarkupRenderPrompts:
    """Test suite for JIRA markup render prompt constants."""

    def test_ollama_prompt_exists(self):
        """Test that OLLAMA_PROMPT exists and is a string."""
        assert OLLAMA_PROMPT is not None
        assert isinstance(OLLAMA_PROMPT, str)
        assert len(OLLAMA_PROMPT) > 0

    def test_gemini_prompt_exists(self):
        """Test that GEMINI_PROMPT exists and is a string."""
        assert GEMINI_PROMPT is not None
        assert isinstance(GEMINI_PROMPT, str)
        assert len(GEMINI_PROMPT) > 0

    def test_prompts_have_placeholder(self):
        """Test that both prompts have standardised_description placeholder."""
        assert "{standardised_description}" in OLLAMA_PROMPT
        assert "{standardised_description}" in GEMINI_PROMPT

    def test_ollama_prompt_format_functionality(self):
        """Test that OLLAMA_PROMPT can be formatted with standardised_description."""
        test_description = "This is a test JIRA standardised description"
        formatted_prompt = OLLAMA_PROMPT.format(
            standardised_description=test_description
        )

        assert test_description in formatted_prompt
        assert "{standardised_description}" not in formatted_prompt

    def test_gemini_prompt_format_functionality(self):
        """Test that GEMINI_PROMPT can be formatted with standardised_description."""
        test_description = "This is a test JIRA standardised description"
        formatted_prompt = GEMINI_PROMPT.format(
            standardised_description=test_description
        )

        assert test_description in formatted_prompt
        assert "{standardised_description}" not in formatted_prompt

    def test_prompts_content_structure(self):
        """Test that prompts have expected content structure for JIRA markup rendering."""
        # Both prompts should contain instructions about JIRA markup
        ollama_lower = OLLAMA_PROMPT.lower()
        gemini_lower = GEMINI_PROMPT.lower()

        # Should contain JIRA-related terms
        jira_terms = ["jira", "markup", "format", "terminal", "ansi"]
        for term in jira_terms:
            assert any(
                term in text for text in [ollama_lower, gemini_lower]
            ), f"Missing term: {term}"

    def test_prompts_mention_ansi_codes(self):
        """Test that prompts mention ANSI escape codes."""
        assert "ANSI" in OLLAMA_PROMPT or "ansi" in OLLAMA_PROMPT
        assert "ANSI" in GEMINI_PROMPT or "ansi" in GEMINI_PROMPT

    def test_prompts_mention_markup_features(self):
        """Test that prompts mention various markup features."""
        markup_features = ["bold", "italic", "code", "link", "bullet"]

        for feature in markup_features:
            # At least one prompt should mention each feature
            mentioned_in_ollama = feature.lower() in OLLAMA_PROMPT.lower()
            mentioned_in_gemini = feature.lower() in GEMINI_PROMPT.lower()
            assert (
                mentioned_in_ollama or mentioned_in_gemini
            ), f"Feature '{feature}' not mentioned in prompts"

    def test_prompts_no_extra_placeholders(self):
        """Test that prompts don't have unintended placeholders."""
        test_description = "Test description"

        # Test OLLAMA_PROMPT
        formatted_ollama = OLLAMA_PROMPT.format(
            standardised_description=test_description
        )
        import re

        # Look for placeholders that are NOT JIRA markup patterns
        # JIRA markup includes {{code}}, {code}, but we want to allow these
        remaining_ollama = re.findall(
            r"\{(?!(?:code|standardised_description)\})[^}]*\}", formatted_ollama
        )
        # Filter out known JIRA patterns
        actual_placeholders = [
            p
            for p in remaining_ollama
            if not any(x in p for x in ["code", "standardised_description"])
        ]
        assert (
            len(actual_placeholders) == 0
        ), f"OLLAMA_PROMPT has unexpected placeholders: {actual_placeholders}"

        # Test GEMINI_PROMPT
        formatted_gemini = GEMINI_PROMPT.format(
            standardised_description=test_description
        )
        remaining_gemini = re.findall(
            r"\{(?!(?:code|standardised_description)\})[^}]*\}", formatted_gemini
        )
        actual_placeholders_gemini = [
            p
            for p in remaining_gemini
            if not any(x in p for x in ["code", "standardised_description"])
        ]
        assert (
            len(actual_placeholders_gemini) == 0
        ), f"GEMINI_PROMPT has unexpected placeholders: {actual_placeholders_gemini}"

    def test_prompts_handle_complex_descriptions(self):
        """Test that prompts handle complex JIRA descriptions."""
        complex_description = """
        *Bold text* and _italic text_

        Code block:
        {{code:java}}
        public class Example {
            // Comment
        }
        {{code}}

        - Bullet point 1
        - Bullet point 2

        [Link text|https://example.com]

        h1. Heading
        h2. Subheading
        """

        # Both prompts should handle this complex input
        formatted_ollama = OLLAMA_PROMPT.format(
            standardised_description=complex_description
        )
        formatted_gemini = GEMINI_PROMPT.format(
            standardised_description=complex_description
        )

        assert "*Bold text*" in formatted_ollama
        assert "_italic text_" in formatted_ollama
        assert "{{code:java}}" in formatted_ollama

        assert "*Bold text*" in formatted_gemini
        assert "_italic text_" in formatted_gemini
        assert "{{code:java}}" in formatted_gemini

    def test_prompts_different_but_similar_purpose(self):
        """Test that prompts are different but serve similar purpose."""
        # Prompts should be different (customized for different LLMs)
        assert OLLAMA_PROMPT != GEMINI_PROMPT

        # But both should be substantial
        assert len(OLLAMA_PROMPT) > 100
        assert len(GEMINI_PROMPT) > 100

        # Both should mention terminal output
        assert "terminal" in OLLAMA_PROMPT.lower()
        assert "terminal" in GEMINI_PROMPT.lower()

    def test_prompts_consistency(self):
        """Test that prompts are consistent across multiple accesses."""
        # Prompts should be constants
        ollama1 = OLLAMA_PROMPT
        ollama2 = OLLAMA_PROMPT
        gemini1 = GEMINI_PROMPT
        gemini2 = GEMINI_PROMPT

        assert ollama1 is ollama2
        assert gemini1 is gemini2
        assert ollama1 == ollama2
        assert gemini1 == gemini2

    def test_prompts_with_edge_cases(self):
        """Test prompts with edge case descriptions."""
        edge_cases = [
            "",  # Empty description
            " ",  # Whitespace only
            "\n\n\n",  # Newlines only
            "Simple text",  # Simple text
            "Text with {braces} and 'quotes'",  # Special characters
        ]

        for edge_case in edge_cases:
            # Both prompts should handle these cases
            try:
                ollama_result = OLLAMA_PROMPT.format(standardised_description=edge_case)
                gemini_result = GEMINI_PROMPT.format(standardised_description=edge_case)

                assert isinstance(ollama_result, str)
                assert isinstance(gemini_result, str)
                assert len(ollama_result) > 0
                assert len(gemini_result) > 0

            except Exception as e:
                pytest.fail(
                    f"Failed to format prompts with edge case '{repr(edge_case)}': {e}"
                )


class TestJiraMarkupRenderUsage:
    """Test suite for JIRA markup render prompt usage patterns."""

    def test_typical_jira_markup_usage(self):
        """Test typical usage with JIRA markup."""
        jira_markup = """
        h1. User Story

        *As a* user
        *I want* to format text
        *So that* I can create readable documentation

        h2. Acceptance Criteria

        - The system should support *bold* text
        - The system should support _italic_ text
        - The system should support {{monospace}} text

        h3. Code Example

        {{code:python}}
        def hello_world():
            print("Hello, World!")
        {{code}}

        See [documentation|https://docs.example.com] for more details.
        """

        # Test with both prompts
        ollama_formatted = OLLAMA_PROMPT.format(standardised_description=jira_markup)
        gemini_formatted = GEMINI_PROMPT.format(standardised_description=jira_markup)

        # Should contain the original markup
        for formatted in [ollama_formatted, gemini_formatted]:
            assert "h1. User Story" in formatted
            assert "*As a* user" in formatted
            assert "{{code:python}}" in formatted
            assert "[documentation|https://docs.example.com]" in formatted

    def test_prompt_selection_logic(self):
        """Test that prompts can be selected based on LLM type."""

        # Simulate prompt selection logic
        def select_prompt(use_gemini=False):
            return GEMINI_PROMPT if use_gemini else OLLAMA_PROMPT

        # Test selection
        ollama_selected = select_prompt(use_gemini=False)
        gemini_selected = select_prompt(use_gemini=True)

        assert ollama_selected == OLLAMA_PROMPT
        assert gemini_selected == GEMINI_PROMPT
        assert ollama_selected != gemini_selected

    def test_prompts_ready_for_ai_processing(self):
        """Test that prompts are ready for AI processing."""
        test_description = "Simple JIRA description with *bold* text"

        ollama_ready = OLLAMA_PROMPT.format(standardised_description=test_description)
        gemini_ready = GEMINI_PROMPT.format(standardised_description=test_description)

        # Should be substantial prompts ready for AI
        assert len(ollama_ready) > len(test_description)
        assert len(gemini_ready) > len(test_description)

        # Should contain clear instructions
        assert any(
            word in ollama_ready.lower()
            for word in ["format", "render", "convert", "display"]
        )
        assert any(
            word in gemini_ready.lower()
            for word in ["format", "render", "convert", "display"]
        )

    def test_empty_description_handling(self):
        """Test handling of empty descriptions."""
        empty_description = ""

        ollama_formatted = OLLAMA_PROMPT.format(
            standardised_description=empty_description
        )
        gemini_formatted = GEMINI_PROMPT.format(
            standardised_description=empty_description
        )

        # Should still be valid prompts even with empty description
        assert isinstance(ollama_formatted, str)
        assert isinstance(gemini_formatted, str)
        assert len(ollama_formatted) > 0
        assert len(gemini_formatted) > 0

        # Should still contain instructions
        assert len(ollama_formatted) > 100
        assert len(gemini_formatted) > 100
