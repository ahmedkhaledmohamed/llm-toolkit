"""Pull content from a Google Doc and convert back to markdown."""

import re
import sys
from pathlib import Path

import markdownify
from bs4 import BeautifulSoup
from googleapiclient.discovery import build

from .auth import get_credentials
from . import history


def pull_content(doc_identifier: str, output: str = None, update: bool = False) -> str:
    """Export a Google Doc as markdown.

    Args:
        doc_identifier: Google Doc URL or document ID.
        output: Optional file path to write the markdown to.
        update: If True, overwrite the original source file (from history).

    Returns:
        The markdown content as a string.
    """
    doc_id = _extract_doc_id(doc_identifier)

    creds = get_credentials()
    drive = build('drive', 'v3', credentials=creds)

    # Get doc title for display
    doc_meta = drive.files().get(fileId=doc_id, fields='name').execute()
    doc_title = doc_meta.get('name', 'Untitled')

    # Export as HTML via Drive API
    html_bytes = drive.files().export(fileId=doc_id, mimeType='text/html').execute()
    html_content = html_bytes.decode('utf-8')

    # Pre-process HTML: strip style/script/meta tags with BeautifulSoup
    # (markdownify's strip parameter keeps tag text; we need full removal)
    html_content = _preprocess_html(html_content)

    # Convert HTML to markdown
    md_content = markdownify.markdownify(
        html_content,
        heading_style="ATX",
        bullets="-",
    )

    # Clean up Google Docs artifacts
    md_content = _clean_markdown(md_content)

    # Determine output destination
    if update:
        source_path = history.find_by_id(doc_id)
        if not source_path:
            print(f'No source file found for "{doc_title}" in history.', file=sys.stderr)
            print("Use --output <file> instead.", file=sys.stderr)
            sys.exit(1)
        target = Path(source_path).expanduser().resolve()
        if not target.parent.exists():
            print(f'Source directory not found: {target.parent}', file=sys.stderr)
            print(f'Original path from history: {source_path}', file=sys.stderr)
            print("Use --output <file> instead.", file=sys.stderr)
            sys.exit(1)
        target.write_text(md_content, encoding='utf-8')
        print(f'Updated: {target}')
        print(f'From: "{doc_title}"')
    elif output:
        Path(output).write_text(md_content, encoding='utf-8')
        print(f'Saved: {output}')
        print(f'From: "{doc_title}"')
    else:
        print(md_content)

    return md_content


def _preprocess_html(html: str) -> str:
    """Remove Google Docs artifacts from HTML before markdown conversion.

    Google Docs HTML export includes <style> blocks with CSS, inline styles,
    Google-specific classes, and other elements that pollute the output.
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Remove style, script, meta, link tags entirely (including contents)
    for tag_name in ['style', 'script', 'meta', 'link']:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove empty span tags that Google Docs inserts
    for span in soup.find_all('span'):
        if not span.get_text(strip=True) and not span.find_all(True):
            span.decompose()

    # Strip all class and style attributes (they're Google-specific)
    for tag in soup.find_all(True):
        tag.attrs = {k: v for k, v in tag.attrs.items()
                     if k not in ('class', 'style', 'id')}

    return str(soup)


def _clean_markdown(md: str) -> str:
    """Clean up markdown converted from Google Docs HTML export.

    Google Docs HTML includes various artifacts (empty spans, excessive
    whitespace, non-breaking spaces, Google-specific markup) that
    markdownify doesn't fully strip.
    """
    # Replace non-breaking spaces with regular spaces
    md = md.replace('\xa0', ' ')

    # Remove zero-width spaces and other invisible unicode
    md = md.replace('\u200b', '')
    md = md.replace('\ufeff', '')

    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in md.splitlines()]
    md = '\n'.join(lines)

    # Collapse 3+ consecutive blank lines into 2
    md = re.sub(r'\n{3,}', '\n\n', md)

    # Remove empty bold/italic markers (artifacts from Google Docs spans)
    md = re.sub(r'\*\*\s*\*\*', '', md)
    md = re.sub(r'_\s*_', '', md)
    md = re.sub(r'\*\s*\*', '', md)

    # Clean up empty links
    md = re.sub(r'\[([^\]]*)\]\(\s*\)', r'\1', md)

    # Remove Google Docs image placeholder comments
    md = re.sub(r'!\[\]\([^)]*googleusercontent[^)]*\)', '', md)

    # Clean up empty table header rows (Google Docs artifact)
    # Matches rows like "|  |  |  |  |" that are just whitespace
    md = re.sub(r'^\|(?:\s*\|)+\s*$\n', '', md, flags=re.MULTILINE)

    # Normalize horizontal rules (various forms to standard ---)
    md = re.sub(r'^[\s]*[-*_]{3,}[\s]*$', '---', md, flags=re.MULTILINE)

    # Strip leading blank lines
    md = md.lstrip('\n')

    # Ensure file ends with single newline
    md = md.rstrip('\n') + '\n'

    return md


def _extract_doc_id(identifier: str) -> str:
    """Extract Google Doc ID from a URL, or return as-is if already an ID."""
    match = re.search(r'/document/d/([a-zA-Z0-9_-]+)', identifier)
    if match:
        return match.group(1)
    return identifier.strip().rstrip('/')
