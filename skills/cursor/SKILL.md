---
name: llm-toolkit
description: Bridge LLM workflows to traditional tools using the llmtk CLI. Use when the user asks to share a document, convert markdown to Google Docs, push to gdoc, create a shareable version, get feedback on a doc, pull comments, pull content back from Google Docs, render diagrams from markdown, or incorporate feedback. Also applies when the user says "make this shareable", "send to Google Docs", or "render diagrams".
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

### Pull Content: Google Doc back to Markdown

```bash
llmtk gdoc pull-content "<google-doc-url-or-id>"                  # print to stdout
llmtk gdoc pull-content "<google-doc-url-or-id>" --output file.md # save to file
llmtk gdoc pull-content "<google-doc-url-or-id>" --update         # overwrite original source
```

- Exports via Drive API HTML export, then converts to clean markdown
- `--update` looks up the original source file from push history and overwrites it
- Strips Google Docs CSS artifacts, normalizes tables and whitespace

### List Created Docs

```bash
llmtk gdoc list
```

## Diagrams (`llmtk diagram`)

### Render diagrams from markdown

```bash
llmtk diagram <file.md>                          # render all diagram blocks to PNG
llmtk diagram <file.md> --format svg             # SVG output
llmtk diagram <file.md> --output-dir ./images    # save to specific directory
llmtk diagram <file.md> --inline                 # replace code blocks with image refs
echo "graph LR; A-->B" | llmtk diagram --stdin --type mermaid -o flow.png
```

- Extracts fenced code blocks tagged as `mermaid`, `plantuml`, `graphviz`, `dot`, `d2`, `ditaa`, `c4plantuml`, `structurizr`
- Renders via Kroki.io API (zero local dependencies, supports 20+ diagram types)
- `--inline` replaces diagram code blocks with `![](./path.png)` image references in-place
- Output files named `{stem}-diagram-{n}.{format}`
- Ignores non-diagram code blocks (python, bash, etc.)

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

### "Sync edits back" / "Pull content"

1. Run `llmtk gdoc pull-content "<url>" --output updated.md` (or `--update` to overwrite original)
2. Diff against the original markdown to see what collaborators changed
3. Merge changes as needed

### "Render diagrams" / "Generate diagram images"

1. Run `llmtk diagram <file.md>` to render all diagram code blocks
2. Use `--inline` to replace code blocks with image references for sharing
3. Use `--format svg` for scalable vector output

### Full round-trip example

```
User: "make this shareable"
-> Save to analysis.md
-> llmtk gdoc push analysis.md --title "Q1 Analysis" --folder "Work"
-> Return URL

User: "incorporate the feedback from that doc"
-> llmtk gdoc pull "<url>"
-> Read comments, apply each to analysis.md
-> Show changes summary
-> Offer to re-push as "Q1 Analysis (v2)"

User: "sync their edits back"
-> llmtk gdoc pull-content "<url>" --update
-> Original file updated with collaborator edits

User: "render the diagrams in this doc"
-> llmtk diagram architecture.md --output-dir ./images
-> 4 PNGs created
```

## Setup

If auth fails, the user needs to:

1. Create `~/.llmtk/credentials.json` (Google Cloud OAuth 2.0 Desktop app)
2. Enable **Google Drive API** and **Google Docs API** in the GCP project
3. Run `pip install llm-toolkit` (or `pip install -e ~/Developer/llm-toolkit`)
4. Run any command once — browser opens for OAuth consent

Diagram rendering requires network access (Kroki.io API) but no additional setup.
