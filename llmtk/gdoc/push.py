"""Push markdown content to Google Docs."""

import sys

import markdown as md_lib
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

from .auth import get_credentials
from .styles import HTML_TEMPLATE, PAGE_STYLE, get_styles
from . import history


def md_to_html(md_content: str) -> str:
    """Convert markdown to styled HTML ready for Google Docs import."""
    extensions = [
        'markdown.extensions.extra',
        'markdown.extensions.toc',
        'markdown.extensions.sane_lists',
        'markdown.extensions.smarty',
    ]

    html_body = md_lib.markdown(md_content, extensions=extensions)
    styles = get_styles()
    return HTML_TEMPLATE.format(content=html_body, **styles)


def push_to_gdoc(md_content: str, title: str, folder: str = None, source: str = "stdin"):
    """Upload markdown content as a styled Google Doc. Returns (doc_id, doc_url)."""
    html_content = md_to_html(md_content)

    creds = get_credentials()
    drive = build('drive', 'v3', credentials=creds)

    # Resolve folder
    parent_id = None
    if folder:
        parent_id = _find_or_create_folder(drive, folder)

    # Upload HTML as Google Doc
    file_metadata = {
        'name': title,
        'mimeType': 'application/vnd.google-apps.document',
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]

    media = MediaInMemoryUpload(
        html_content.encode('utf-8'),
        mimetype='text/html',
        resumable=True,
    )

    result = drive.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink',
    ).execute()

    doc_url = result.get('webViewLink')
    doc_id = result.get('id')

    # Apply page style (tight margins for near-pageless look)
    if PAGE_STYLE:
        _apply_page_style(creds, doc_id)

    history.save(doc_id, title, source, doc_url)

    print(f'Created: "{title}"')
    print(f"URL: {doc_url}")

    return doc_id, doc_url


def _apply_page_style(creds, doc_id: str):
    """Set page margins via Docs API for a near-pageless layout."""
    try:
        docs = build('docs', 'v1', credentials=creds)
        docs.documents().batchUpdate(
            documentId=doc_id,
            body={
                'requests': [{
                    'updateDocumentStyle': {
                        'documentStyle': {
                            'marginTop': {'magnitude': PAGE_STYLE['margin_top'], 'unit': 'PT'},
                            'marginBottom': {'magnitude': PAGE_STYLE['margin_bottom'], 'unit': 'PT'},
                            'marginLeft': {'magnitude': PAGE_STYLE['margin_left'], 'unit': 'PT'},
                            'marginRight': {'magnitude': PAGE_STYLE['margin_right'], 'unit': 'PT'},
                        },
                        'fields': 'marginTop,marginBottom,marginLeft,marginRight',
                    }
                }]
            }
        ).execute()
    except Exception as e:
        print(f"Warning: Could not set page style: {e}", file=sys.stderr)


def _find_or_create_folder(drive, folder_name: str) -> str:
    """Find existing Drive folder by name, or create one."""
    query = (
        f"name = '{folder_name}' and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )
    results = drive.files().list(q=query, fields='files(id, name)', pageSize=1).execute()
    files = results.get('files', [])

    if files:
        return files[0]['id']

    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    folder = drive.files().create(body=folder_metadata, fields='id').execute()
    print(f'Created folder: "{folder_name}"')
    return folder['id']
