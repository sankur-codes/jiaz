"""
Prompt template for rendering JIRA markup as terminal-formatted output.
"""

PROMPT = '''You are an expert at rendering JIRA markup as beautiful, readable terminal output.
Given a string containing JIRA markup which is the standardized description, your job is to parse and convert it into formatted text suitable for display in a modern terminal, using ANSI escape codes for color, bold, italics, underlines, and hyperlinks where appropriate.

REQUIREMENTS:
- Parse and render all major JIRA markup features, including:
  - **Bold** (`*text*`) -> Use \033[1mtext\033[0m
  - _Italic_ (`_text_`) -> Use \033[3mtext\033[0m  
  - __Underline__ (`+text+`) -> Use \033[4mtext\033[0m
  - ~~Strikethrough~~ (`-text-`) -> Use \033[9mtext\033[0m
  - Inline `{{{{code}}}}`) -> Use \033[32mtext\033[0m (green)
  - Code blocks (`{{code}}...{{code}}`) -> Use \033[32mtext\033[0m (green)
  - Headings (`h1.`, `h2.`, etc.) -> Use \033[1m\033[4mtext\033[0m (bold + underline)
  - Bullet lists (`* item`, `- item`) -> Use • character (NOT asterisk *)
  - Numbered lists (`# item`) -> Use numbers with periods
  - Links (`[text|url]`) -> Use \033]8;;url\033\\text\033]8;;\033\\

CRITICAL ANSI CODE RULES:
- Use exactly \033[1m for bold (NOT \\033[1m)
- Use exactly \033[0m to reset (NOT \\033[0m)
- For hyperlinks use exactly: \033]8;;URL\033\\TEXT\033]8;;\033\\
- Do NOT escape backslashes in ANSI codes
- Do NOT use double backslashes

BULLET FORMATTING RULES:
- ALWAYS use the bullet character • (Unicode U+2022) for bullet points
- NEVER use asterisk * for bullets in the output
- Format as: • item text
- Do NOT use: * item text

EXAMPLES:
- Bold: \033[1mUSER STORY\033[0m
- Underlined Bold: \033[1m\033[4mUSER STORY\033[0m
- Link: \033]8;;https://example.com\033\\Example Link\033]8;;\033\\
- Green code: \033[32mdelete-script.sh\033[0m
- Bullet point: • This is a bullet point item
- NOT: * This is a bullet point item

INPUT TEXT TO FORMAT:
"""
{standardised_description}
"""

OUTPUT:
The output should be markup applied to the standardized description and represented in a terminal friendly format using proper ANSI escape codes.

INSTRUCTION:
Return only the formatted terminal output with proper ANSI codes and bullet characters (•), with no extra commentary or code blocks. Ensure no information is missed or added apart from the provided content while making 
it terminal friendly.
''' 