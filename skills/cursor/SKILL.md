---
name: llm-toolkit
description: Bridge LLM workflows to traditional tools using the llmtk CLI. Use when the user asks to share a document, convert markdown to Google Docs, push to gdoc, create a shareable version, get feedback on a doc, pull comments from Google Docs, or incorporate feedback. Also applies when the user says "make this shareable" or "send to Google Docs".
---

# LLM Toolkit

CLI tool `llmtk` bridges LLM-generated content to traditional formats.

## Google Docs (`llmtk gdoc`)

### Push: MD to Google Doc

```bash
llmtk gdoc push <file.md> --title "Title" --folder "Folder"
llmtk gdoc push --stdin --title "Title"
```

- `--title` defaults to filename if omitted
- `--folder` finds or creates a Drive folder (optional)
- `--stdin` reads markdown from stdin
- Returns the Google Doc URL
- Always quote URLs in commands (they contain `?` which zsh interprets)

### Pull: Get Feedback as Markdown

```bash
llmtk gdoc pull "<google-doc-url-or-id>"
```

Returns structured markdown like:

```
## Feedback from: Q1 Analysis
> Pulled: 2026-02-15 07:41 from https://docs.google.com/...

### Open Comments
- **John Smith** (on "reduced latency by 40%"): "Can you add the baseline number?" [open]
  - **Sarah Lee** replied: "agreed, we need the before/after"
- **Sarah Lee** (on "team allocation"): "Missing the infra team" [open]

### Resolved Comments
- **John Smith** (on "P99 at 187ms"): "Looks good" [resolved]
```

### List Created Docs

```bash
llmtk gdoc list
```

## Workflows

### "Make this shareable" / "Push to Google Docs"

1. Save the content as a clean `.md` file (strip internal notes, draft markers)
2. Run `llmtk gdoc push <file> --title "Descriptive Title" --folder "Folder"`
3. Return the Google Doc URL to the user

### "Incorporate feedback" / "Pull comments"

1. Ask the user for the Google Doc URL (or check `llmtk gdoc list` for recent docs)
2. Run `llmtk gdoc pull "<url>"` and capture the output
3. For each open comment:
   - Find the quoted text in the original markdown file
   - Apply the feedback (edit, add detail, restructure as requested)
   - Note what was changed
4. Present a summary of changes made
5. Ask if the user wants to push the updated version back: `llmtk gdoc push <file> --title "Title (v2)"`

### Full round-trip example

```
User: "make this shareable"
→ Save to analysis.md
→ llmtk gdoc push analysis.md --title "Q1 Analysis" --folder "Work"
→ Return URL

User: "incorporate the feedback from that doc"
→ llmtk gdoc pull "<url>"
→ Read comments, apply each to analysis.md
→ Show changes summary
→ Offer to re-push as "Q1 Analysis (v2)"
```

## Setup

If auth fails, the user needs to:

1. Create `~/.llmtk/credentials.json` (Google Cloud OAuth 2.0 Desktop app)
2. Enable **Google Drive API** and **Google Docs API** in the GCP project
3. Run `pip install llm-toolkit` (or `pip install -e ~/Developer/llm-toolkit`)
4. Run any command once — browser opens for OAuth consent
