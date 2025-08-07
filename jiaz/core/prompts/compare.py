"""
Prompt templates for comparing different types of content.
"""

# Specific prompt for comparing JIRA descriptions
JIRA_DESCRIPTION_PROMPT = '''You are an expert at evaluating content similarity and consistency.

Your task is to compare two versions of the same JIRA issue description:
1. The standardized description (with JIRA markup)
2. The terminal-friendly rendered output (with ANSI escape codes)

EVALUATION CRITERIA:
- Compare the actual CONTENT, not the formatting
- Ignore differences in markup syntax (JIRA markup vs ANSI codes)
- Focus on whether the core information, structure, and meaning are preserved
- Check that all sections (USER STORY, ACCEPTANCE CRITERIA, etc.) are present in both
- Verify that no important information was lost or significantly altered
- Minor formatting differences are acceptable

SIMILARITY THRESHOLD:
- Return "true" if the content is substantially the same
- Return "false" if there are significant content differences, missing sections, or information loss

IMPORTANT:
- Only respond with exactly "true" or "false" (lowercase, no quotes, no additional text)
- Do not provide explanations or reasoning
- Do not add any other content to your response

STANDARDIZED DESCRIPTION:
"""
{standardized_description}
"""

TERMINAL-FRIENDLY OUTPUT:
"""
{terminal_friendly_output}
"""

RESPONSE (true or false only):'''

# Generic prompt for comparing any two pieces of content
GENERIC_CONTENT_PROMPT = '''You are an expert at evaluating content {comparison_context}.

Your task is to compare two pieces of content and determine if they meet the {comparison_context} criteria.

EVALUATION CRITERIA:
- Compare the actual CONTENT and meaning, not just formatting differences
- Focus on whether the core information, structure, and intent are preserved
- Consider the context of {comparison_context} when making your evaluation
- Ignore minor formatting, styling, or markup differences
- Look for substantial equivalence in meaning and information

EVALUATION THRESHOLD:
- Return "true" if the contents meet the {comparison_context} criteria
- Return "false" if there are significant differences that fail the {comparison_context} test

IMPORTANT:
- Only respond with exactly "true" or "false" (lowercase, no quotes, no additional text)
- Do not provide explanations or reasoning
- Do not add any other content to your response

CONTENT 1:
"""
{content1}
"""

CONTENT 2:
"""
{content2}
"""

RESPONSE (true or false only):'''

# Backward compatibility - keep the original PROMPT name
PROMPT = JIRA_DESCRIPTION_PROMPT
