"""
Prompt template for rendering JIRA markup as terminal-formatted output.
"""

PROMPT = '''You are an expert at rendering JIRA markup as beautiful, readable terminal output.
Given a string containing JIRA markup which is the standardized description, your job is to parse and convert it into formatted text suitable for display in a modern terminal, using ANSI escape codes for color, bold, italics, underlines, and hyperlinks where appropriate.

REQUIREMENTS:
- Parse and render all major JIRA markup features, including:
  - **Bold** (`*text*`)
  - _Italic_ (`_text_`)
  - __Underline__ (`+text+`)
  - ~~Strikethrough~~ (`-text-`)
  - Inline `{{{{code}}}}`)
  - Code blocks (`{{code}}...{{code}}`)
  - Headings (`h1.`, `h2.`, etc.)
  - Bullet lists (`* item`, `- item`)
  - Numbered lists (`# item`)
  - Checklists (`[ ]`, `[x]`)
  - Blockquotes (`bq. text`)
  - Links (`[text|url]`)
  - Tables (`||header||`, `|cell|`)
- Use terminal formatting (ANSI codes) to represent these features as closely as possible.
- For links, use terminal hyperlink escape sequences if supported, otherwise print the URL in [text|url] format.
- For code blocks, use a different color or background if possible.
- For tables, align columns and use ASCII/Unicode box drawing characters if possible.
- Ignore any unsupported or unknown markup gracefully.

INPUT:
{standarised_description}

OUTPUT:
The output should be markup applied to the standardized description and respresented in a terminal friendly format.


INSTRUCTION:
Return only the formatted terminal output, with no extra commentary.
''' 