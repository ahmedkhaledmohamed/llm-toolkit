# LLM Toolkit — Agent Context

## What This Is

A Python CLI toolkit (`llmtk`) that bridges LLM workflows to traditional tools.
Markdown is the universal interchange format. Each tool converts between markdown
and a traditional format (Google Docs, Slides, PDF, Confluence, etc.).

## Architecture

```
llmtk/
├── cli.py              # Top-level CLI, delegates to tool subcommands
└── gdoc/               # First tool: Markdown ↔ Google Docs
    ├── auth.py          # Google OAuth (shared across tools)
    ├── push.py          # MD → HTML → Google Doc
    ├── pull.py          # Google Doc comments → MD
    ├── styles.py        # CSS styles + HTML template
    └── history.py       # Track created docs
```

## Adding a New Tool

1. Create `llmtk/newtool/` with `__init__.py`, `push.py`, `pull.py`
2. Register in `cli.py` with `_register_newtool()` and `_handle_newtool()`
3. Reuse `llmtk/gdoc/auth.py` for Google API auth
4. Update `skills/` templates if the new tool needs agent awareness

## Conventions

- CLI namespace: `llmtk <tool> <command>` (e.g., `llmtk gdoc push`)
- Config dir: `~/.llmtk/` (credentials, tokens, style overrides)
- Auth tokens per-service in `~/.llmtk/`
- Lazy imports in `cli.py` — only import tool modules when that tool is invoked
- Non-fatal errors for optional features (e.g., page style) — always create the doc
- Styles are CSS-based, injected into HTML before Google Docs import

## Dependencies

- `markdown` — MD → HTML conversion
- `google-auth-oauthlib` + `google-api-python-client` — Google APIs
- Python >= 3.9
