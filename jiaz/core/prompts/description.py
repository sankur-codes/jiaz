"""
Prompt templates for JIRA issue description standardisation.
"""

PROMPT = '''You are an expert in writing consistent and cleanly structured JIRA issue descriptions.

Your job is to take the input description below, analyze and understand the underlying work request,
and return it reformatted into the exact markdown structure shown here:

"""
+*USER STORY:*+

<What are we attempting to achieve? Break into user role, intent, and outcome>
*As a* ARO SRE
*I want to* <intent>
*So that* <outcome>

+*ACCEPTANCE CRITERIA:*+

<What conditions define the issue as completed? Use bullet points if needed.>

*+CUSTOMER EXPERIENCE:+*

<_Only fill out if applicable. Otherwise delete this section._>

*+BREADCRUMBS:+*

<_Where can SREs look for additional information? List links, docs, or mark N/A._>

*+NOTES:+*

<Any pre-requisites or special instructions for the engineer working on it. Also, code blocks along with its usage/meaning is pasted under here>
"""

Now reformat below JIRA description using the above template, preserving only relevant information from the raw input with a better vocabulary:

"""
{description}
"""

CRITICAL FORMATTING REQUIREMENTS:
1. Use EXACT format shown above with proper section headers
2. Each section MUST be separated by a blank line
3. Use bullet points (•) for all lists
4. Convert all URLs to JIRA format: [Text|URL]
5. Keep user story concise: As a... I want to... So that...
6. Make acceptance criteria specific and testable
7. Include all relevant links in BREADCRUMBS section
8. Put prerequisites and technical details in NOTES
9. If any section is not applicable, omit it entirely
10. Return ONLY the formatted description with no explanations
'''