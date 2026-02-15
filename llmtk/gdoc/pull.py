"""Pull comments from a Google Doc and format as markdown."""

import re
from datetime import datetime

from googleapiclient.discovery import build

from .auth import get_credentials


def pull_comments(doc_identifier: str) -> str:
    """Fetch all comments from a Google Doc and format as markdown."""
    doc_id = _extract_doc_id(doc_identifier)

    creds = get_credentials()
    drive = build('drive', 'v3', credentials=creds)

    # Get doc metadata
    doc = drive.files().get(fileId=doc_id, fields='name, webViewLink').execute()
    doc_title = doc.get('name', 'Untitled')
    doc_url = doc.get('webViewLink', '')

    # Fetch comments (including replies)
    comments_result = drive.comments().list(
        fileId=doc_id,
        fields='comments(id,content,author(displayName),quotedFileContent(value),resolved,replies(content,author(displayName)))',
    ).execute()

    comment_list = comments_result.get('comments', [])

    if not comment_list:
        print(f'No comments found on "{doc_title}"')
        return ""

    # Format as markdown
    lines = [
        f"## Feedback from: {doc_title}",
        f"> Pulled: {datetime.now().strftime('%Y-%m-%d %H:%M')} from {doc_url}",
        "",
    ]

    open_comments = [c for c in comment_list if not c.get('resolved')]
    resolved_comments = [c for c in comment_list if c.get('resolved')]

    if open_comments:
        lines.append("### Open Comments")
        lines.append("")
        for c in open_comments:
            lines.append(_format_comment(c))
        lines.append("")

    if resolved_comments:
        lines.append("### Resolved Comments")
        lines.append("")
        for c in resolved_comments:
            lines.append(_format_comment(c))
        lines.append("")

    output = '\n'.join(lines)
    print(output)
    return output


def _format_comment(comment: dict) -> str:
    """Format a single Google Doc comment as a markdown bullet."""
    author = comment.get('author', {}).get('displayName', 'Unknown')
    content = comment.get('content', '')
    quoted = comment.get('quotedFileContent', {}).get('value', '')
    resolved = comment.get('resolved', False)
    status = "resolved" if resolved else "open"

    line = f"- **{author}**"
    if quoted:
        short_quote = quoted[:100] + ('...' if len(quoted) > 100 else '')
        line += f' (on "{short_quote}")'
    line += f': "{content}" [{status}]'

    for r in comment.get('replies', []):
        r_author = r.get('author', {}).get('displayName', 'Unknown')
        r_content = r.get('content', '')
        line += f'\n  - **{r_author}** replied: "{r_content}"'

    return line


def _extract_doc_id(identifier: str) -> str:
    """Extract Google Doc ID from a URL, or return as-is if already an ID."""
    match = re.search(r'/document/d/([a-zA-Z0-9_-]+)', identifier)
    if match:
        return match.group(1)
    return identifier.strip().rstrip('/')
