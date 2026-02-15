---
name: llm-toolkit
description: Bridge LLM workflows to traditional tools using the llmtk CLI. Use when asked to share a document, convert to Google Doc, push to gdoc, create a shareable version, pull comments, or incorporate feedback from a shared doc.
---

# LLM Toolkit

CLI: `llmtk` — bridge LLM-generated content to traditional formats.

## Commands

Push markdown to Google Doc:

```bash
llmtk gdoc push <file.md> --title "Title" --folder "Folder"
llmtk gdoc push --stdin --title "Title" < file.md
```

Pull comments as markdown:

```bash
llmtk gdoc pull <google-doc-url-or-id>
```

List created docs:

```bash
llmtk gdoc list
```

## Workflow

**Sharing**: Save content as `.md` -> run push -> return URL.

**Feedback**: Run pull with doc URL -> read comments -> apply to original file.

## Setup

Requires `~/.llmtk/credentials.json` (Google OAuth 2.0 Desktop).
First run opens browser for consent. Needs Drive API + Docs API enabled.

```bash
pip install llm-toolkit
```
