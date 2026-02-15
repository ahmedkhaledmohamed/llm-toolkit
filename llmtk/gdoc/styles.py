"""
Styles for Google Docs output.

To customize: edit the STYLES dict below, or create ~/.llmtk/styles.json
with any keys you want to override. Example:

    {"font_family": "Georgia, serif", "body_font_size": "12pt"}

Only include keys you want to change — the rest use defaults.
"""

import json
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Default styles
# ─────────────────────────────────────────────────────────────────────────────
#
#   font_family      Body text font (Google Docs supports: Arial, Roboto,
#                    Times New Roman, Georgia, Verdana, Courier New, etc.)
#   code_font        Font for code blocks and inline code
#   body_font_size   Base font size (e.g., "11pt", "12pt")
#   body_line_height Line spacing multiplier (1.5 = 150%)
#   body_color       Main text color (hex)
#   heading_color    H1-H6 color (hex)
#   code_bg          Code block background color
#   code_border      Code block border color
#   code_color       Code text color
#   blockquote_border Blockquote left border color
#   blockquote_color Blockquote text color
#   link_color       Hyperlink color
#   table_border     Table border color
#   table_header_bg  Table header row background
#   table_alt_bg     Alternating table row background (unused by GDocs import)
#   hr_color         Horizontal rule color

STYLES = {
    "font_family": "'Inter', 'Helvetica Neue', Arial, sans-serif",
    "code_font": "'Roboto Mono', 'SF Mono', 'Consolas', monospace",
    "body_font_size": "11pt",
    "body_line_height": "1.6",
    "body_color": "#1a1a1a",
    "heading_color": "#111111",
    "code_bg": "#f6f8fa",
    "code_border": "#e1e4e8",
    "code_color": "#24292e",
    "blockquote_border": "#dfe2e5",
    "blockquote_color": "#6a737d",
    "link_color": "#1a73e8",
    "table_border": "#d0d7de",
    "table_header_bg": "#f6f8fa",
    "table_alt_bg": "#fafbfc",
    "hr_color": "#d0d7de",
}

# Page layout applied via Docs API after creation.
# Google Docs API doesn't support true "pageless" mode, so we use tight
# margins to approximate it. Set to None to skip page style adjustment.
# Units: Points (72pt = 1 inch).
PAGE_STYLE = {
    "margin_top": 36,      # 0.5 inch
    "margin_bottom": 36,
    "margin_left": 36,
    "margin_right": 36,
}


# ─────────────────────────────────────────────────────────────────────────────
# HTML template
# ─────────────────────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{
    font-family: {font_family};
    font-size: {body_font_size};
    line-height: {body_line_height};
    color: {body_color};
    max-width: 800px;
    margin: 0;
    padding: 0;
}}
p {{
    margin: 0 0 0.4em 0;
}}
h1, h2, h3, h4, h5, h6 {{
    color: {heading_color};
    margin: 0.8em 0 0.2em 0;
    padding: 0;
    font-weight: 600;
}}
h1 {{ font-size: 24pt; }}
h2 {{ font-size: 20pt; }}
h3 {{ font-size: 16pt; }}
h4 {{ font-size: 13pt; }}
h5 {{ font-size: 11pt; }}
h6 {{ font-size: 10pt; color: {blockquote_color}; }}
code {{
    font-family: {code_font};
    font-size: 10pt;
    background-color: {code_bg};
    border: 1px solid {code_border};
    border-radius: 3px;
    padding: 1px 4px;
    color: {code_color};
}}
pre {{
    background-color: {code_bg};
    border: 1px solid {code_border};
    border-radius: 4px;
    padding: 10px;
    margin: 0.3em 0;
    overflow-x: auto;
    line-height: 1.3;
}}
pre code {{
    border: none;
    padding: 0;
    background: none;
}}
blockquote {{
    border-left: 3px solid {blockquote_border};
    margin: 0.3em 0;
    padding: 0.2em 0.8em;
    color: {blockquote_color};
    font-style: italic;
}}
blockquote p {{
    margin: 0;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 0.3em 0;
    table-layout: auto;
}}
th {{
    border: 1px solid {table_border};
    padding: 1px 6px;
    margin: 0;
    text-align: left;
    font-size: 9pt;
    font-weight: 600;
    line-height: 1.1;
    background-color: {table_header_bg};
}}
td {{
    border: 1px solid {table_border};
    padding: 1px 6px;
    margin: 0;
    text-align: left;
    font-size: 9pt;
    line-height: 1.2;
}}
a {{
    color: {link_color};
    text-decoration: none;
}}
hr {{
    border: none;
    border-top: 1px solid {hr_color};
    margin: 0.6em 0;
}}
ul, ol {{
    padding-left: 1.5em;
    margin: 0.2em 0;
}}
li {{
    margin: 0;
    padding: 0;
}}
img {{
    max-width: 100%;
}}
</style></head><body>
{content}
</body></html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Style loading
# ─────────────────────────────────────────────────────────────────────────────

def get_styles() -> dict:
    """Return styles with user overrides applied from ~/.llmtk/styles.json."""
    styles = STYLES.copy()
    override_file = Path.home() / '.llmtk' / 'styles.json'
    if override_file.exists():
        try:
            overrides = json.loads(override_file.read_text())
            styles.update(overrides)
        except (json.JSONDecodeError, OSError):
            pass  # silently fall back to defaults
    return styles
