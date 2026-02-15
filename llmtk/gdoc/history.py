"""Track created Google Docs for the `list` command."""

import json
from pathlib import Path
from datetime import datetime

HISTORY_FILE = Path.home() / '.llmtk' / 'gdoc_history.json'


def save(doc_id: str, title: str, source: str, url: str):
    """Append a created doc to the history file."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    history = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            history = json.load(f)

    history.append({
        'id': doc_id,
        'title': title,
        'source': source,
        'url': url,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
    })

    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def list_all():
    """Print recently created Google Docs."""
    if not HISTORY_FILE.exists():
        print("No documents created yet.")
        return

    with open(HISTORY_FILE) as f:
        history = json.load(f)

    if not history:
        print("No documents created yet.")
        return

    print(f"Recent documents ({len(history)}):\n")
    for entry in reversed(history[-20:]):
        print(f"  {entry['date']}  {entry['title']}")
        print(f"  {entry['url']}")
        print(f"  Source: {entry['source']}")
        print()
