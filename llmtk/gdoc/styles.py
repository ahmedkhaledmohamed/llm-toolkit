"""
Styles for Google Docs output.

Two layers of styling:
  1. HTML/CSS — applied during Drive API import (Phase 1)
  2. Docs API — applied via batchUpdate after creation (Phase 2)

To customize: create ~/.llmtk/styles.json with any keys you want to
override.  Only include keys you want to change — the rest use defaults.

Example ~/.llmtk/styles.json:
    {
        "body": {"font": "Georgia", "size": 12},
        "headings": {"h1": {"font": "Georgia", "size": 26}},
        "layout": {"pageless": true}
    }
"""

import json
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Layout defaults
# ─────────────────────────────────────────────────────────────────────────────
#   Units: Points (72pt = 1 inch).  Letter = 612 × 792 pt.
#
#   pageless:  When True, sets an extremely tall page to simulate pageless
#              mode (the Docs API has no native pageless flag).
#   margins:   Document margins in points.

LAYOUT = {
    "pageless": True,
    "margins": {
        "top": 36,       # 0.5 inch
        "bottom": 36,
        "left": 54,      # 0.75 inch
        "right": 54,
    },
    # Standard Letter dimensions; overridden when pageless is True.
    "page_width": 612,
    "page_height": 792,
}

# ─────────────────────────────────────────────────────────────────────────────
# Heading styles  (applied via Docs API Phase 2)
# ─────────────────────────────────────────────────────────────────────────────

HEADINGS = {
    "h1": {
        "font": "Inter",
        "size": 24,
        "color": "#111111",
        "bold": True,
        "space_before": 20,
        "space_after": 6,
    },
    "h2": {
        "font": "Inter",
        "size": 18,
        "color": "#111111",
        "bold": True,
        "space_before": 16,
        "space_after": 4,
    },
    "h3": {
        "font": "Inter",
        "size": 14,
        "color": "#333333",
        "bold": True,
        "space_before": 12,
        "space_after": 4,
    },
    "h4": {
        "font": "Inter",
        "size": 12,
        "color": "#333333",
        "bold": True,
        "space_before": 10,
        "space_after": 2,
    },
    "h5": {
        "font": "Inter",
        "size": 11,
        "color": "#555555",
        "bold": True,
        "space_before": 8,
        "space_after": 2,
    },
    "h6": {
        "font": "Inter",
        "size": 10,
        "color": "#6a737d",
        "bold": True,
        "space_before": 8,
        "space_after": 2,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Body / paragraph defaults  (applied via Docs API Phase 2)
# ─────────────────────────────────────────────────────────────────────────────

BODY = {
    "font": "Inter",
    "size": 11,
    "color": "#1a1a1a",
    "line_spacing": 1.15,     # multiplier (115%)
    "space_after": 6,         # pt after each paragraph
}

# ─────────────────────────────────────────────────────────────────────────────
# Code block defaults  (applied via Docs API Phase 2)
# ─────────────────────────────────────────────────────────────────────────────

CODE = {
    "font": "Roboto Mono",
    "size": 9.5,
    "color": "#24292e",
    "background": "#f6f8fa",
}

# ─────────────────────────────────────────────────────────────────────────────
# Table defaults  (applied via Docs API Phase 2)
# ─────────────────────────────────────────────────────────────────────────────

TABLE = {
    "header_background": "#f6f8fa",
    "header_bold": True,
    "cell_padding": 4,          # pt
    "border_color": "#d0d7de",
    "border_width": 0.5,        # pt
    "font_size": 9,
    "pin_header_rows": True,
}

# ─────────────────────────────────────────────────────────────────────────────
# Blockquote defaults  (applied via Docs API Phase 2)
# ─────────────────────────────────────────────────────────────────────────────

BLOCKQUOTE = {
    "color": "#6a737d",
    "italic": True,
    "indent": 36,               # pt left indent
    "space_before": 4,
    "space_after": 4,
}

# ─────────────────────────────────────────────────────────────────────────────
# Legacy CSS variables  (used in Phase 1 HTML template)
# ─────────────────────────────────────────────────────────────────────────────
#   These control the HTML/CSS sent to the Drive API import.
#   They provide reasonable initial styling that Phase 2 refines.

CSS_VARS = {
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


# ─────────────────────────────────────────────────────────────────────────────
# HTML template  (Phase 1 — sent to Drive API as import)
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
# Style loading — merges defaults with user overrides
# ─────────────────────────────────────────────────────────────────────────────

def _deep_merge(base: dict, overrides: dict) -> dict:
    """Recursively merge overrides into base dict."""
    result = base.copy()
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_styles() -> dict:
    """Return the complete style configuration with user overrides applied.

    Loads ~/.llmtk/styles.json and deep-merges into defaults.
    Returns a dict with keys: layout, headings, body, code, table,
    blockquote, css_vars.
    """
    styles = {
        "layout": LAYOUT.copy(),
        "headings": {k: v.copy() for k, v in HEADINGS.items()},
        "body": BODY.copy(),
        "code": CODE.copy(),
        "table": TABLE.copy(),
        "blockquote": BLOCKQUOTE.copy(),
        "css_vars": CSS_VARS.copy(),
    }

    override_file = Path.home() / '.llmtk' / 'styles.json'
    if override_file.exists():
        try:
            overrides = json.loads(override_file.read_text())
            styles = _deep_merge(styles, overrides)
        except (json.JSONDecodeError, OSError):
            pass  # silently fall back to defaults

    return styles


def get_css_vars() -> dict:
    """Return only CSS template variables (for Phase 1 HTML generation)."""
    return get_styles()["css_vars"]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers for Docs API color conversion
# ─────────────────────────────────────────────────────────────────────────────

def hex_to_rgb(hex_color: str) -> dict:
    """Convert '#RRGGBB' to Docs API RgbColor dict (0.0-1.0 floats)."""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return {
        "red": r / 255.0,
        "green": g / 255.0,
        "blue": b / 255.0,
    }
