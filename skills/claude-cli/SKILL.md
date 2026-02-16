---
name: llm-toolkit
description: Bridge LLM workflows to traditional tools using the llmtk CLI. Use when asked to share a document, convert to Google Doc, push to gdoc, create a shareable version, pull comments, pull content back, render diagrams, or incorporate feedback from a shared doc.
---

# LLM Toolkit

CLI: `llmtk` — bridge LLM-generated content to traditional formats.

## Commands

```bash
# Google Docs
llmtk gdoc push <file.md> --title "Title" --folder "Folder"
llmtk gdoc push --stdin --title "Title" < file.md
llmtk gdoc pull "<google-doc-url-or-id>"
llmtk gdoc pull-content "<url-or-id>" --output file.md
llmtk gdoc pull-content "<url-or-id>" --update
llmtk gdoc list

# Diagrams
llmtk diagram <file.md>                        # render all diagram blocks to PNG
llmtk diagram <file.md> --format svg           # SVG output
llmtk diagram <file.md> --inline               # replace code blocks with image refs
echo "graph LR; A-->B" | llmtk diagram --stdin --type mermaid -o flow.png
```

Always quote URLs (they contain `?` which zsh interprets).

## Pull Output Format

```
## Feedback from: Doc Title
> Pulled: 2026-02-15 from https://docs.google.com/...

### Open Comments
- **Author** (on "quoted text..."): "comment" [open]
  - **Author** replied: "reply"
```

## Diagrams

Supports: mermaid, plantuml, graphviz, dot, d2, ditaa, c4plantuml, structurizr.
Renders via Kroki.io API (zero local dependencies). Output: `{stem}-diagram-{n}.{format}`.

## Workflows

**Sharing**: Save content as `.md` -> run push -> return URL.

**Feedback round-trip**:
1. Run `llmtk gdoc pull "<url>"` to get comments
2. For each open comment, find the quoted text in the original file and apply the feedback
3. Summarize changes made
4. Offer to re-push as an updated version

**Sync edits back**: `llmtk gdoc pull-content "<url>" --update` overwrites original source file.

**Render diagrams**: `llmtk diagram file.md` extracts and renders all diagram code blocks. Use `--inline` to replace blocks with image references.

## Setup

`pip install llm-toolkit`. Requires `~/.llmtk/credentials.json` (Google OAuth).
Enable Drive API + Docs API in GCP project. First run opens browser for consent.
Diagrams require network (Kroki.io) but no additional auth.
