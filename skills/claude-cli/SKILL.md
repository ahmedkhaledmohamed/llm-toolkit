---
name: llm-toolkit
description: Bridge LLM workflows to traditional tools using the llmtk CLI. Use when asked to share a document, convert to Google Doc, push to gdoc, create a shareable version, pull comments, or incorporate feedback from a shared doc.
---

# LLM Toolkit

CLI: `llmtk` — bridge LLM-generated content to traditional formats.

## Commands

```bash
llmtk gdoc push <file.md> --title "Title" --folder "Folder"
llmtk gdoc push --stdin --title "Title" < file.md
llmtk gdoc pull "<google-doc-url-or-id>"
llmtk gdoc list
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

## Workflows

**Sharing**: Save content as `.md` → run push → return URL.

**Feedback round-trip**:
1. Run `llmtk gdoc pull "<url>"` to get comments
2. For each open comment, find the quoted text in the original file and apply the feedback
3. Summarize changes made
4. Offer to re-push as an updated version

## Setup

`pip install llm-toolkit`. Requires `~/.llmtk/credentials.json` (Google OAuth).
Enable Drive API + Docs API in GCP project. First run opens browser for consent.
