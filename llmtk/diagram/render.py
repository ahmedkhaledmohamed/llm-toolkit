"""Render diagram code blocks from markdown via Kroki.io."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import requests

KROKI_URL = "https://kroki.io"

# Diagram types supported by Kroki that LLMs commonly generate
SUPPORTED_TYPES = {
    'mermaid', 'plantuml', 'graphviz', 'dot',
    'd2', 'ditaa', 'c4plantuml', 'structurizr',
    'vega', 'vegalite',
}

# Aliases — normalize to what Kroki expects
TYPE_ALIASES = {
    'dot': 'graphviz',
}

# Regex pattern for fenced code blocks with a supported diagram type
_DIAGRAM_PATTERN = re.compile(
    r'^```(' + '|'.join(SUPPORTED_TYPES) + r')[ \t]*\n(.*?)^```',
    re.MULTILINE | re.DOTALL,
)


def render_diagrams(
    md_content: str,
    source_path: str | None = None,
    fmt: str = "png",
    output_dir: str | None = None,
    inline: bool = False,
) -> list[str]:
    """Extract and render all diagram code blocks from markdown.

    Args:
        md_content: Markdown text containing diagram code blocks.
        source_path: Original file path (used for naming output files).
        fmt: Output format — 'png' or 'svg'.
        output_dir: Directory to save images. Defaults to source file's dir.
        inline: If True, replace code blocks with image references in the
                markdown and write back to source_path.

    Returns:
        List of saved image file paths.
    """
    diagrams = _extract_diagrams(md_content)

    if not diagrams:
        print("No diagram code blocks found.")
        return []

    # Determine output directory
    if output_dir:
        out_dir = Path(output_dir)
    elif source_path:
        out_dir = Path(source_path).parent
    else:
        out_dir = Path.cwd()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Determine filename stem for naming images
    stem = Path(source_path).stem if source_path else "diagram"

    saved_paths = []
    replacements = []  # (start, end, image_path) for inline mode

    print(f"Found {len(diagrams)} diagram(s). Rendering via Kroki...")

    for i, diag in enumerate(diagrams, 1):
        diagram_type = diag['type']
        source = diag['source']
        display_type = diagram_type

        # Normalize type alias
        kroki_type = TYPE_ALIASES.get(diagram_type, diagram_type)

        filename = f"{stem}-diagram-{i}.{fmt}"
        filepath = out_dir / filename

        try:
            image_bytes = _render_via_kroki(kroki_type, source, fmt)
            filepath.write_bytes(image_bytes)
            saved_paths.append(str(filepath))
            print(f"  [{i}/{len(diagrams)}] {display_type} → {filepath}")

            if inline:
                # Compute relative path from source file to image
                if source_path:
                    rel_path = Path(filepath).relative_to(
                        Path(source_path).parent
                    )
                else:
                    rel_path = filepath
                replacements.append((
                    diag['start'],
                    diag['end'],
                    f"![{stem} diagram {i}](./{rel_path})",
                ))

        except requests.HTTPError as e:
            print(f"  [{i}/{len(diagrams)}] {display_type} FAILED: {e}",
                  file=sys.stderr)
        except requests.ConnectionError:
            print(f"  [{i}/{len(diagrams)}] {display_type} FAILED: "
                  "Cannot reach kroki.io — check your network.",
                  file=sys.stderr)

    # Inline mode: replace code blocks with image references
    if inline and replacements and source_path:
        updated_md = _replace_blocks(md_content, replacements)
        Path(source_path).write_text(updated_md, encoding='utf-8')
        print(f"\nUpdated {source_path} with inline image references.")

    return saved_paths


def render_stdin(
    source: str,
    diagram_type: str,
    fmt: str = "png",
    output: str | None = None,
) -> None:
    """Render a single diagram from stdin.

    Args:
        source: Raw diagram source text.
        diagram_type: Diagram language (mermaid, plantuml, etc.).
        fmt: Output format — 'png' or 'svg'.
        output: File path to write to. If None, writes to stdout.
    """
    kroki_type = TYPE_ALIASES.get(diagram_type, diagram_type)

    if kroki_type not in SUPPORTED_TYPES and diagram_type not in TYPE_ALIASES:
        print(f"Unsupported diagram type: {diagram_type}", file=sys.stderr)
        print(f"Supported: {', '.join(sorted(SUPPORTED_TYPES))}",
              file=sys.stderr)
        sys.exit(1)

    try:
        image_bytes = _render_via_kroki(kroki_type, source, fmt)
    except requests.HTTPError as e:
        print(f"Rendering failed: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.ConnectionError:
        print("Cannot reach kroki.io — check your network.", file=sys.stderr)
        sys.exit(1)

    if output:
        Path(output).write_bytes(image_bytes)
        print(f"Saved: {output}")
    else:
        # Write binary to stdout
        sys.stdout.buffer.write(image_bytes)


def _extract_diagrams(md_content: str) -> list[dict]:
    """Find diagram code blocks in markdown.

    Returns:
        List of dicts with keys: type, source, start, end (character positions).
    """
    results = []
    for match in _DIAGRAM_PATTERN.finditer(md_content):
        results.append({
            'type': match.group(1),
            'source': match.group(2).strip(),
            'start': match.start(),
            'end': match.end(),
        })
    return results


def _render_via_kroki(diagram_type: str, source: str, fmt: str = "png") -> bytes:
    """POST diagram source to Kroki.io, return image bytes."""
    url = f"{KROKI_URL}/{diagram_type}/{fmt}"
    resp = requests.post(
        url,
        data=source.encode('utf-8'),
        headers={'Content-Type': 'text/plain'},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.content


def _replace_blocks(md_content: str, replacements: list[tuple]) -> str:
    """Replace diagram code blocks with image references.

    Args:
        md_content: Original markdown text.
        replacements: List of (start, end, image_ref) tuples,
                      in order of appearance.

    Returns:
        Updated markdown with code blocks replaced by image references.
    """
    # Process replacements in reverse order to preserve character positions
    result = md_content
    for start, end, image_ref in reversed(replacements):
        result = result[:start] + image_ref + result[end:]
    return result
