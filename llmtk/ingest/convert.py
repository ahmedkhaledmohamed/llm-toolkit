"""Ingest external content (URLs, PDFs, HTML files) into clean markdown."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import html2text
import requests


JINA_READER_URL = "https://r.jina.ai/"


def ingest(source: str, output: str | None = None, local: bool = False) -> str:
    """Convert a URL, PDF, or HTML file into clean markdown.

    Args:
        source: URL, PDF file path, or HTML file path.
        output: Optional file path to write the markdown to.
        local: If True, skip Jina Reader API and use local conversion for URLs.

    Returns:
        The markdown content as a string.
    """
    source_type = _detect_source_type(source)

    if source_type == 'url':
        md_content = _ingest_url(source, local=local)
    elif source_type == 'pdf':
        md_content = _ingest_pdf(source)
    elif source_type == 'html':
        md_content = _ingest_html(source)
    else:
        print(f"Unknown source type: {source}", file=sys.stderr)
        print("Supported: URLs (http/https), .pdf files, .html/.htm files",
              file=sys.stderr)
        sys.exit(1)

    md_content = _clean_markdown(md_content)

    if output:
        Path(output).write_text(md_content, encoding='utf-8')
        print(f"Saved: {output}")
        print(f"From: {source}")
    else:
        print(md_content)

    return md_content


def _detect_source_type(source: str) -> str:
    """Detect whether the source is a URL, PDF, HTML file, or unknown."""
    if source.startswith(('http://', 'https://')):
        # URL that points to a PDF
        if source.lower().endswith('.pdf'):
            return 'pdf_url'
        return 'url'
    path = Path(source)
    if path.suffix.lower() == '.pdf':
        return 'pdf'
    if path.suffix.lower() in ('.html', '.htm'):
        return 'html'
    return 'unknown'


# --- URL ingestion ---

def _ingest_url(url: str, local: bool = False) -> str:
    """Convert a URL to markdown, using Jina Reader or local fallback."""
    if not local:
        try:
            return _ingest_url_jina(url)
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as e:
            print(f"Jina Reader failed ({e}), falling back to local...",
                  file=sys.stderr)

    return _ingest_url_local(url)


def _ingest_url_jina(url: str) -> str:
    """Fetch a URL via Jina Reader API, which returns clean markdown."""
    resp = requests.get(
        f"{JINA_READER_URL}{url}",
        headers={"Accept": "text/markdown"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def _ingest_url_local(url: str) -> str:
    """Fetch a URL directly and convert HTML to markdown locally."""
    resp = requests.get(
        url,
        headers={"User-Agent": "llmtk/0.1 (markdown ingestion)"},
        timeout=30,
    )
    resp.raise_for_status()
    return _html_to_markdown(resp.text)


# --- PDF ingestion ---

def _ingest_pdf(path: str) -> str:
    """Convert a local PDF file to markdown via pymupdf4llm."""
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    import pymupdf4llm
    md = pymupdf4llm.to_markdown(str(resolved))

    if not md or not md.strip():
        print("Warning: PDF appears to be image-only or empty. "
              "OCR is not supported yet.", file=sys.stderr)
        return ""

    return md


# --- HTML ingestion ---

def _ingest_html(path: str) -> str:
    """Convert a local HTML file to markdown."""
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    html_content = resolved.read_text(encoding='utf-8')
    return _html_to_markdown(html_content)


# --- Shared helpers ---

def _html_to_markdown(html: str) -> str:
    """Convert raw HTML string to markdown using html2text."""
    converter = html2text.HTML2Text()
    converter.body_width = 0           # Don't wrap lines
    converter.ignore_links = False
    converter.ignore_images = False
    converter.ignore_emphasis = False
    converter.protect_links = True     # Don't break long URLs
    converter.unicode_snob = True      # Use unicode instead of ASCII
    converter.skip_internal_links = True
    converter.inline_links = True
    return converter.handle(html)


def _clean_markdown(md: str) -> str:
    """Post-process markdown for LLM consumption.

    Normalizes whitespace, strips common artifacts from web pages
    and PDF extraction.
    """
    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in md.splitlines()]
    md = '\n'.join(lines)

    # Collapse 3+ consecutive blank lines into 2
    md = re.sub(r'\n{3,}', '\n\n', md)

    # Remove empty bold/italic markers
    md = re.sub(r'\*\*\s*\*\*', '', md)
    md = re.sub(r'__\s*__', '', md)

    # Clean up empty links
    md = re.sub(r'\[([^\]]*)\]\(\s*\)', r'\1', md)

    # Normalize horizontal rules
    md = re.sub(r'^[\s]*[-*_]{3,}[\s]*$', '---', md, flags=re.MULTILINE)

    # Strip leading blank lines
    md = md.lstrip('\n')

    # Ensure single trailing newline
    md = md.rstrip('\n') + '\n'

    return md
