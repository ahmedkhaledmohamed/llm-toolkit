"""
Post-process a Google Doc via the Docs API (Phase 2 styling).

After HTML import via Drive API (Phase 1), this module reads the doc
structure and applies precise formatting using batchUpdate requests:

  - Document layout (margins, page size / pageless)
  - Heading styles (font, size, color, spacing)
  - Body paragraph styles (font, size, line spacing)
  - Table styles (header background, borders, font size, pinned headers)
  - Blockquote styles (indent, color, italic)
  - Code block styles (font, size, background color)
"""

import sys

from googleapiclient.discovery import build

from .styles import get_styles, hex_to_rgb


# ─────────────────────────────────────────────────────────────────────────────
# Named style type mapping
# ─────────────────────────────────────────────────────────────────────────────

_HEADING_MAP = {
    "HEADING_1": "h1",
    "HEADING_2": "h2",
    "HEADING_3": "h3",
    "HEADING_4": "h4",
    "HEADING_5": "h5",
    "HEADING_6": "h6",
}

# Height for pageless simulation (very tall single page).
# 100,000 pt ≈ 1,389 inches ≈ 35 metres — enough for any document.
_PAGELESS_HEIGHT = 100000


def post_process(creds, doc_id: str):
    """Read the doc structure and apply Phase 2 styling via batchUpdate."""
    styles = get_styles()

    try:
        docs = build('docs', 'v1', credentials=creds)
    except Exception as e:
        print(f"Warning: Could not connect to Docs API: {e}", file=sys.stderr)
        return

    # Read the document structure
    try:
        doc = docs.documents().get(documentId=doc_id).execute()
    except Exception as e:
        print(f"Warning: Could not read document: {e}", file=sys.stderr)
        return

    requests = []

    # 1. Document-level styles (layout, margins, pageless)
    requests.extend(_build_document_style_requests(styles))

    # 2. Walk the body and style paragraphs + tables
    body = doc.get('body', {})
    content = body.get('content', [])

    for element in content:
        if 'paragraph' in element:
            requests.extend(
                _build_paragraph_requests(element, styles)
            )
        elif 'table' in element:
            requests.extend(
                _build_table_requests(element, styles)
            )

    if not requests:
        return

    # Execute all styling in a single batch
    try:
        docs.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests},
        ).execute()
    except Exception as e:
        print(f"Warning: Could not apply styles: {e}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────────────────────
# Document-level style requests
# ─────────────────────────────────────────────────────────────────────────────

def _build_document_style_requests(styles: dict) -> list:
    """Build updateDocumentStyle requests for layout/margins/pageless."""
    layout = styles.get("layout", {})
    margins = layout.get("margins", {})
    pageless = layout.get("pageless", False)

    doc_style = {}
    fields = []

    # Margins
    if margins.get("top") is not None:
        doc_style['marginTop'] = {'magnitude': margins['top'], 'unit': 'PT'}
        fields.append('marginTop')
    if margins.get("bottom") is not None:
        doc_style['marginBottom'] = {'magnitude': margins['bottom'], 'unit': 'PT'}
        fields.append('marginBottom')
    if margins.get("left") is not None:
        doc_style['marginLeft'] = {'magnitude': margins['left'], 'unit': 'PT'}
        fields.append('marginLeft')
    if margins.get("right") is not None:
        doc_style['marginRight'] = {'magnitude': margins['right'], 'unit': 'PT'}
        fields.append('marginRight')

    # Page size (pageless = very tall page)
    page_width = layout.get("page_width", 612)
    if pageless:
        page_height = _PAGELESS_HEIGHT
    else:
        page_height = layout.get("page_height", 792)

    doc_style['pageSize'] = {
        'width': {'magnitude': page_width, 'unit': 'PT'},
        'height': {'magnitude': page_height, 'unit': 'PT'},
    }
    fields.append('pageSize')

    if not fields:
        return []

    return [{
        'updateDocumentStyle': {
            'documentStyle': doc_style,
            'fields': ','.join(fields),
        }
    }]


# ─────────────────────────────────────────────────────────────────────────────
# Paragraph style requests
# ─────────────────────────────────────────────────────────────────────────────

def _build_paragraph_requests(element: dict, styles: dict) -> list:
    """Build styling requests for a single paragraph element."""
    requests = []
    para = element['paragraph']
    para_style = para.get('paragraphStyle', {})
    named_style = para_style.get('namedStyleType', 'NORMAL_TEXT')

    start_index = element.get('startIndex', 0)
    end_index = element.get('endIndex', start_index)

    # Skip empty paragraphs
    if start_index >= end_index:
        return []

    # Determine which style config to use
    if named_style in _HEADING_MAP:
        heading_key = _HEADING_MAP[named_style]
        heading_cfg = styles.get("headings", {}).get(heading_key, {})
        if heading_cfg:
            requests.extend(
                _style_heading(start_index, end_index, heading_cfg)
            )
    elif named_style == 'NORMAL_TEXT':
        # Check if this paragraph is inside a blockquote (detected by
        # indentation left from HTML import) or a code block (detected
        # by monospace font in the text runs).
        indent = para_style.get('indentStart', {}).get('magnitude', 0)
        is_blockquote = indent > 20  # HTML import sets ~36pt indent for blockquotes

        text_runs = _get_text_runs(para)
        is_code = _looks_like_code(text_runs)

        if is_code:
            code_cfg = styles.get("code", {})
            if code_cfg:
                requests.extend(
                    _style_code_paragraph(start_index, end_index, code_cfg)
                )
        elif is_blockquote:
            bq_cfg = styles.get("blockquote", {})
            if bq_cfg:
                requests.extend(
                    _style_blockquote(start_index, end_index, bq_cfg)
                )
        else:
            body_cfg = styles.get("body", {})
            if body_cfg:
                requests.extend(
                    _style_body_paragraph(start_index, end_index, body_cfg)
                )

    return requests


def _get_text_runs(para: dict) -> list:
    """Extract text runs from a paragraph."""
    runs = []
    for elem in para.get('elements', []):
        if 'textRun' in elem:
            runs.append(elem['textRun'])
    return runs


def _looks_like_code(text_runs: list) -> bool:
    """Detect if paragraph is a code block by checking for monospace font."""
    for run in text_runs:
        content = run.get('content', '').strip()
        if not content:
            continue
        ts = run.get('textStyle', {})
        font = ts.get('weightedFontFamily', {}).get('fontFamily', '')
        if font and any(mono in font.lower() for mono in
                        ['mono', 'courier', 'consolas', 'menlo']):
            return True
    return False


def _style_heading(start: int, end: int, cfg: dict) -> list:
    """Build requests to style a heading paragraph."""
    requests = []

    # Text style (font, size, color, bold)
    text_style = {}
    text_fields = []

    if cfg.get('font'):
        text_style['weightedFontFamily'] = {
            'fontFamily': cfg['font'],
            'weight': 700 if cfg.get('bold', True) else 400,
        }
        text_fields.append('weightedFontFamily')

    if cfg.get('size'):
        text_style['fontSize'] = {'magnitude': cfg['size'], 'unit': 'PT'}
        text_fields.append('fontSize')

    if cfg.get('color'):
        text_style['foregroundColor'] = {
            'color': {'rgbColor': hex_to_rgb(cfg['color'])}
        }
        text_fields.append('foregroundColor')

    if cfg.get('bold') is not None:
        text_style['bold'] = cfg['bold']
        text_fields.append('bold')

    if text_style:
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'textStyle': text_style,
                'fields': ','.join(text_fields),
            }
        })

    # Paragraph style (spacing)
    para_style = {}
    para_fields = []

    if cfg.get('space_before') is not None:
        para_style['spaceAbove'] = {'magnitude': cfg['space_before'], 'unit': 'PT'}
        para_fields.append('spaceAbove')

    if cfg.get('space_after') is not None:
        para_style['spaceBelow'] = {'magnitude': cfg['space_after'], 'unit': 'PT'}
        para_fields.append('spaceBelow')

    if para_style:
        requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'paragraphStyle': para_style,
                'fields': ','.join(para_fields),
            }
        })

    return requests


def _style_body_paragraph(start: int, end: int, cfg: dict) -> list:
    """Build requests to style a normal body paragraph."""
    requests = []

    # Text style
    text_style = {}
    text_fields = []

    if cfg.get('font'):
        text_style['weightedFontFamily'] = {
            'fontFamily': cfg['font'],
            'weight': 400,
        }
        text_fields.append('weightedFontFamily')

    if cfg.get('size'):
        text_style['fontSize'] = {'magnitude': cfg['size'], 'unit': 'PT'}
        text_fields.append('fontSize')

    if cfg.get('color'):
        text_style['foregroundColor'] = {
            'color': {'rgbColor': hex_to_rgb(cfg['color'])}
        }
        text_fields.append('foregroundColor')

    if text_style:
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'textStyle': text_style,
                'fields': ','.join(text_fields),
            }
        })

    # Paragraph style
    para_style = {}
    para_fields = []

    if cfg.get('line_spacing'):
        # Docs API uses percentage (115 = 1.15x)
        para_style['lineSpacing'] = cfg['line_spacing'] * 100
        para_fields.append('lineSpacing')

    if cfg.get('space_after') is not None:
        para_style['spaceBelow'] = {'magnitude': cfg['space_after'], 'unit': 'PT'}
        para_fields.append('spaceBelow')

    if para_style:
        requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'paragraphStyle': para_style,
                'fields': ','.join(para_fields),
            }
        })

    return requests


def _style_code_paragraph(start: int, end: int, cfg: dict) -> list:
    """Build requests to style a code block paragraph."""
    requests = []

    text_style = {}
    text_fields = []

    if cfg.get('font'):
        text_style['weightedFontFamily'] = {
            'fontFamily': cfg['font'],
            'weight': 400,
        }
        text_fields.append('weightedFontFamily')

    if cfg.get('size'):
        text_style['fontSize'] = {'magnitude': cfg['size'], 'unit': 'PT'}
        text_fields.append('fontSize')

    if cfg.get('color'):
        text_style['foregroundColor'] = {
            'color': {'rgbColor': hex_to_rgb(cfg['color'])}
        }
        text_fields.append('foregroundColor')

    if cfg.get('background'):
        text_style['backgroundColor'] = {
            'color': {'rgbColor': hex_to_rgb(cfg['background'])}
        }
        text_fields.append('backgroundColor')

    if text_style:
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'textStyle': text_style,
                'fields': ','.join(text_fields),
            }
        })

    return requests


def _style_blockquote(start: int, end: int, cfg: dict) -> list:
    """Build requests to style a blockquote paragraph."""
    requests = []

    # Text style
    text_style = {}
    text_fields = []

    if cfg.get('color'):
        text_style['foregroundColor'] = {
            'color': {'rgbColor': hex_to_rgb(cfg['color'])}
        }
        text_fields.append('foregroundColor')

    if cfg.get('italic') is not None:
        text_style['italic'] = cfg['italic']
        text_fields.append('italic')

    if text_style:
        requests.append({
            'updateTextStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'textStyle': text_style,
                'fields': ','.join(text_fields),
            }
        })

    # Paragraph style
    para_style = {}
    para_fields = []

    if cfg.get('indent') is not None:
        para_style['indentStart'] = {'magnitude': cfg['indent'], 'unit': 'PT'}
        para_fields.append('indentStart')

    if cfg.get('space_before') is not None:
        para_style['spaceAbove'] = {'magnitude': cfg['space_before'], 'unit': 'PT'}
        para_fields.append('spaceAbove')

    if cfg.get('space_after') is not None:
        para_style['spaceBelow'] = {'magnitude': cfg['space_after'], 'unit': 'PT'}
        para_fields.append('spaceBelow')

    if para_style:
        requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': start, 'endIndex': end},
                'paragraphStyle': para_style,
                'fields': ','.join(para_fields),
            }
        })

    return requests


# ─────────────────────────────────────────────────────────────────────────────
# Table style requests
# ─────────────────────────────────────────────────────────────────────────────

def _build_table_requests(element: dict, styles: dict) -> list:
    """Build styling requests for a table element."""
    requests = []
    table = element['table']
    table_cfg = styles.get("table", {})

    if not table_cfg:
        return []

    rows = table.get('tableRows', [])

    for row_idx, row in enumerate(rows):
        cells = row.get('tableCells', [])
        is_header = (row_idx == 0)

        for cell in cells:
            cell_start = cell.get('startIndex', 0)
            cell_end = cell.get('endIndex', cell_start)

            if cell_start >= cell_end:
                continue

            # Cell style (background for headers, padding, borders)
            cell_style = {}
            cell_fields = []

            if is_header and table_cfg.get('header_background'):
                cell_style['backgroundColor'] = {
                    'color': {'rgbColor': hex_to_rgb(table_cfg['header_background'])}
                }
                cell_fields.append('backgroundColor')

            if table_cfg.get('cell_padding') is not None:
                padding = {'magnitude': table_cfg['cell_padding'], 'unit': 'PT'}
                cell_style['paddingTop'] = padding
                cell_style['paddingBottom'] = padding
                cell_style['paddingLeft'] = padding
                cell_style['paddingRight'] = padding
                cell_fields.extend([
                    'paddingTop', 'paddingBottom', 'paddingLeft', 'paddingRight'
                ])

            if table_cfg.get('border_color') and table_cfg.get('border_width'):
                border = {
                    'color': {'color': {'rgbColor': hex_to_rgb(table_cfg['border_color'])}},
                    'width': {'magnitude': table_cfg['border_width'], 'unit': 'PT'},
                    'dashStyle': 'SOLID',
                }
                cell_style['borderTop'] = border
                cell_style['borderBottom'] = border
                cell_style['borderLeft'] = border
                cell_style['borderRight'] = border
                cell_fields.extend([
                    'borderTop', 'borderBottom', 'borderLeft', 'borderRight'
                ])

            if cell_style:
                requests.append({
                    'updateTableCellStyle': {
                        'tableStartLocation': {'index': element.get('startIndex', 0)},
                        'tableCellLocation': {
                            'tableStartLocation': {'index': element.get('startIndex', 0)},
                            'rowIndex': row_idx,
                            'columnIndex': cells.index(cell),
                        },
                        'tableCellStyle': cell_style,
                        'fields': ','.join(cell_fields),
                    }
                })

            # Text style inside cells
            text_style = {}
            text_fields = []

            if table_cfg.get('font_size'):
                text_style['fontSize'] = {
                    'magnitude': table_cfg['font_size'], 'unit': 'PT'
                }
                text_fields.append('fontSize')

            if is_header and table_cfg.get('header_bold'):
                text_style['bold'] = True
                text_fields.append('bold')

            if text_style:
                # Apply to all text in the cell
                for content_elem in cell.get('content', []):
                    if 'paragraph' in content_elem:
                        p_start = content_elem.get('startIndex', 0)
                        p_end = content_elem.get('endIndex', p_start)
                        if p_start < p_end:
                            requests.append({
                                'updateTextStyle': {
                                    'range': {
                                        'startIndex': p_start,
                                        'endIndex': p_end,
                                    },
                                    'textStyle': text_style,
                                    'fields': ','.join(text_fields),
                                }
                            })

    # Pin header rows
    if table_cfg.get('pin_header_rows') and rows:
        requests.append({
            'pinTableHeaderRows': {
                'tableStartLocation': {'index': element.get('startIndex', 0)},
                'pinnedHeaderRowsCount': 1,
            }
        })

    return requests
