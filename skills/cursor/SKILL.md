---
name: llm-toolkit
description: Bridge LLM workflows to traditional tools using the llmtk CLI. Use when the user asks to share a document, convert markdown to Google Docs, push to gdoc, create a shareable version, get feedback on a doc, pull comments from Google Docs, or incorporate feedback. Also applies when the user says "make this shareable" or "send to Google Docs".
---

# LLM Toolkit

CLI tool `llmtk` bridges LLM-generated content to traditional formats.

## Google Docs (`llmtk gdoc`)

### Push: MD to Google Doc

Save content as a `.md` file, then:

```bash
llmtk gdoc push <file.md> --title "Title" --folder "Folder"
llmtk gdoc push --stdin --title "Title"
```

- `--title` defaults to filename if omitted
- `--folder` finds or creates a Drive folder (optional)
- `--stdin` reads markdown from stdin
- Returns the Google Doc URL

**Workflow — "make this shareable":**

1. Write final content to a clean `.md` file
2. Run push with a descriptive title
3. Return the URL to the user

### Pull: Get Feedback as Markdown

```bash
llmtk gdoc pull <google-doc-url-or-id>
```

Returns structured markdown with all comments (open + resolved), quoted text, authors, and replies.

**Workflow — "incorporate feedback":**

1. Run pull with the doc URL
2. Read the comment output
3. Apply each piece of feedback to the original file
4. Offer to push an updated version

### List Created Docs

```bash
llmtk gdoc list
```

## Setup

If auth fails, the user needs to:

1. Create `~/.llmtk/credentials.json` (Google Cloud OAuth 2.0 Desktop app)
2. Enable **Google Drive API** and **Google Docs API** in the GCP project
3. Run `pip install llm-toolkit` (or `pip install -e ~/Developer/llm-toolkit`)
4. Run any command once — browser opens for OAuth consent
