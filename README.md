# LLM Toolkit

Bridge LLM workflows to the traditional ways of working.

LLMs produce great output in markdown. The rest of the world runs on Google Docs, Slides, Confluence, and PDF. This toolkit bridges that gap.

## Install

```bash
pip install llm-toolkit
```

Or for development:

```bash
git clone https://github.com/ahmedkhaledmohamed/llm-toolkit.git
cd llm-toolkit
pip install -e .
```

## Setup (Google APIs)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use an existing one)
3. Enable **Google Drive API** and **Google Docs API**
4. Create OAuth 2.0 credentials → Desktop app
5. Download the JSON and save as `~/.llmtk/credentials.json`
6. Run any `llmtk` command — browser opens for one-time OAuth consent

---

## Tools

### `llmtk gdoc` — Markdown ↔ Google Docs

**Push** a markdown file to Google Docs:

```bash
llmtk gdoc push analysis.md
llmtk gdoc push analysis.md --title "Q1 Analysis" --folder "Work"
echo "# Quick note" | llmtk gdoc push --stdin --title "Quick Note"
```

**Pull** comments from a Google Doc as markdown (for feeding back to your LLM):

```bash
llmtk gdoc pull https://docs.google.com/document/d/1xABC.../edit
```

Output:

```markdown
## Feedback from: Q1 Analysis
> Pulled: 2026-02-14 15:30 from https://docs.google.com/...

### Open Comments
- **John Smith** (on "...reduced latency by 40%..."): "Can you add the baseline?" [open]
- **Sarah Lee** (on "...team allocation..."): "Missing the infra team" [open]
```

**List** recently created docs:

```bash
llmtk gdoc list
```

---

## Customizing Styles

The default styling produces clean, professional Google Docs with tight spacing optimized for LLM-generated content.

### Quick Override

Create `~/.llmtk/styles.json` with any keys you want to change:

```json
{
    "font_family": "Georgia, serif",
    "body_font_size": "12pt",
    "heading_color": "#2c3e50"
}
```

Only include keys you want to override — the rest use defaults.

### Available Style Keys

| Key | Default | What it controls |
|-----|---------|-----------------|
| `font_family` | Inter, Helvetica Neue, Arial | Body text font |
| `code_font` | Roboto Mono, SF Mono, Consolas | Code block font |
| `body_font_size` | 11pt | Base font size |
| `body_line_height` | 1.6 | Line spacing multiplier |
| `body_color` | #1a1a1a | Main text color |
| `heading_color` | #111111 | Heading color |
| `code_bg` | #f6f8fa | Code block background |
| `code_border` | #e1e4e8 | Code block border |
| `code_color` | #24292e | Code text color |
| `blockquote_border` | #dfe2e5 | Blockquote left border |
| `blockquote_color` | #6a737d | Blockquote text color |
| `link_color` | #1a73e8 | Hyperlink color |
| `table_border` | #d0d7de | Table border color |
| `table_header_bg` | #f6f8fa | Table header background |
| `hr_color` | #d0d7de | Horizontal rule color |

### Page Margins

Page margins are set via the Google Docs API after creation (requires Docs API enabled):

| Margin | Default | Notes |
|--------|---------|-------|
| Top | 36pt (0.5") | Tight margins approximate pageless mode |
| Bottom | 36pt (0.5") | |
| Left | 36pt (0.5") | |
| Right | 36pt (0.5") | |

Edit `llmtk/gdoc/styles.py` → `PAGE_STYLE` to change margins. Set `PAGE_STYLE = None` to skip.

---

## AI Agent Skills

This toolkit includes skill files for AI coding assistants so they know how to use it.

### Cursor

```bash
cp -r skills/cursor/ ~/.cursor/skills/llm-toolkit/
```

Now when you tell Cursor "make this shareable" or "push to Google Docs", it knows to use `llmtk`.

### Claude CLI (Codex)

```bash
cp -r skills/claude-cli/ ~/.codex/skills/llm-toolkit/
```

---

## Adding New Tools

The toolkit is designed to grow. Each tool follows the same pattern:

```
llmtk/
└── newtool/
    ├── __init__.py
    ├── push.py      # Output: MD → target format
    ├── pull.py      # Input: target format → MD
    └── ...
```

Register it in `llmtk/cli.py`:

```python
def _register_newtool(subparsers):
    ...

# In main():
_register_newtool(subparsers)
```

Planned tools:

- `llmtk slides` — Markdown → Google Slides
- `llmtk pdf` — Markdown → styled PDF
- `llmtk confluence` — Markdown → Confluence

---

## Related

- [PM AI Partner Framework](https://github.com/ahmedkhaledmohamed/PM-AI-Partner-Framework) — Framework for using AI as a PM thinking partner. The methodology layer; this toolkit is the shipping layer.

## License

MIT
