"""llmtk — CLI entry point.

Usage:
    llmtk gdoc push <file.md> [--title "Title"] [--folder "Folder"]
    llmtk gdoc push --stdin --title "Title"
    llmtk gdoc pull <doc-url>
    llmtk gdoc pull-content <doc-url> [--output file.md] [--update]
    llmtk gdoc list
    llmtk diagram <file.md> [--format png|svg] [--output-dir DIR] [--inline]
    llmtk diagram --stdin --type mermaid [--format png] [--output file.png]
    llmtk ingest <url|pdf|html> [--output file.md] [--local]
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime


def _register_gdoc(subparsers):
    """Register the `gdoc` tool and its subcommands."""
    gdoc = subparsers.add_parser('gdoc', help='Markdown ↔ Google Docs')
    gdoc_sub = gdoc.add_subparsers(dest='gdoc_command')

    # push
    push = gdoc_sub.add_parser('push', help='Convert MD file to Google Doc')
    push.add_argument('file', nargs='?', help='Markdown file path')
    push.add_argument('--stdin', action='store_true', help='Read markdown from stdin')
    push.add_argument('--title', '-t', help='Document title (default: filename)')
    push.add_argument('--folder', '-f', help='Google Drive folder name')

    # pull
    pull = gdoc_sub.add_parser('pull', help='Pull comments from a Google Doc')
    pull.add_argument('doc', help='Google Doc URL or document ID')

    # pull-content
    pull_content = gdoc_sub.add_parser(
        'pull-content', help='Export Google Doc content back as markdown'
    )
    pull_content.add_argument('doc', help='Google Doc URL or document ID')
    pull_content.add_argument(
        '--output', '-o', help='Write markdown to this file'
    )
    pull_content.add_argument(
        '--update', '-u', action='store_true',
        help='Overwrite the original source file (from push history)'
    )

    # list
    gdoc_sub.add_parser('list', help='List recently created docs')


def _handle_gdoc(args):
    """Handle gdoc subcommands."""
    if args.gdoc_command == 'push':
        from llmtk.gdoc.push import push_to_gdoc

        if args.stdin:
            md_content = sys.stdin.read()
            title = args.title or f"Untitled - {datetime.now().strftime('%Y-%m-%d')}"
            source = "stdin"
        elif args.file:
            md_file = Path(args.file)
            if not md_file.exists():
                print(f"File not found: {args.file}")
                sys.exit(1)
            md_content = md_file.read_text(encoding='utf-8')
            title = args.title or md_file.stem.replace('-', ' ').replace('_', ' ').title()
            source = str(md_file.resolve())
        else:
            print("Provide a file path or --stdin")
            sys.exit(1)

        push_to_gdoc(md_content, title, folder=args.folder, source=source)

    elif args.gdoc_command == 'pull':
        from llmtk.gdoc.pull import pull_comments
        pull_comments(args.doc)

    elif args.gdoc_command == 'pull-content':
        from llmtk.gdoc.pull_content import pull_content
        pull_content(args.doc, output=args.output, update=args.update)

    elif args.gdoc_command == 'list':
        from llmtk.gdoc.history import list_all
        list_all()

    else:
        print("Usage: llmtk gdoc {push|pull|pull-content|list}")
        sys.exit(1)


def _register_diagram(subparsers):
    """Register the `diagram` tool."""
    diagram = subparsers.add_parser(
        'diagram',
        help='Render diagram code blocks (mermaid, plantuml, graphviz, d2) to images',
    )
    diagram.add_argument('file', nargs='?', help='Markdown file containing diagram code blocks')
    diagram.add_argument('--stdin', action='store_true',
                         help='Read raw diagram source from stdin (requires --type)')
    diagram.add_argument('--type', '-T', dest='diagram_type',
                         help='Diagram type for stdin mode (mermaid, plantuml, graphviz, d2, ...)')
    diagram.add_argument('--format', '-f', default='png', choices=['png', 'svg'],
                         help='Output image format (default: png)')
    diagram.add_argument('--output-dir', '-d',
                         help='Directory to save images (default: same as input file)')
    diagram.add_argument('--output', '-o',
                         help='Output file path (stdin mode only)')
    diagram.add_argument('--inline', '-i', action='store_true',
                         help='Replace code blocks with image references in the source file')


def _handle_diagram(args):
    """Handle diagram subcommand."""
    from llmtk.diagram.render import render_diagrams, render_stdin

    if args.stdin:
        if not args.diagram_type:
            print("--type is required with --stdin (e.g., --type mermaid)")
            sys.exit(1)
        source = sys.stdin.read()
        if not source.strip():
            print("No input received from stdin.")
            sys.exit(1)
        render_stdin(source, args.diagram_type, fmt=args.format, output=args.output)

    elif args.file:
        md_file = Path(args.file)
        if not md_file.exists():
            print(f"File not found: {args.file}")
            sys.exit(1)
        md_content = md_file.read_text(encoding='utf-8')
        render_diagrams(
            md_content,
            source_path=str(md_file.resolve()),
            fmt=args.format,
            output_dir=args.output_dir,
            inline=args.inline,
        )
    else:
        print("Provide a file path or --stdin")
        sys.exit(1)


def _register_ingest(subparsers):
    """Register the `ingest` tool."""
    ingest_parser = subparsers.add_parser(
        'ingest',
        help='Convert URLs, PDFs, or HTML files to clean markdown for LLM context',
    )
    ingest_parser.add_argument('source', help='URL, PDF file, or HTML file to ingest')
    ingest_parser.add_argument('--output', '-o', help='Write markdown to this file')
    ingest_parser.add_argument('--local', '-l', action='store_true',
                               help='Skip Jina Reader API; use local conversion for URLs')


def _handle_ingest(args):
    """Handle ingest subcommand."""
    from llmtk.ingest.convert import ingest
    ingest(args.source, output=args.output, local=args.local)


def main():
    parser = argparse.ArgumentParser(
        prog='llmtk',
        description='LLM Toolkit — bridge LLM workflows to the traditional ways of working',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Tools:
  gdoc      Markdown ↔ Google Docs (push, pull, pull-content, list)
  diagram   Render diagram code blocks to images (mermaid, plantuml, graphviz, d2)
  ingest    Convert URLs, PDFs, or HTML files to clean markdown

Examples:
  llmtk gdoc push analysis.md --title "Q1 Analysis" --folder "Work"
  llmtk gdoc push --stdin --title "Quick Note"
  llmtk gdoc pull https://docs.google.com/document/d/1xABC.../edit
  llmtk gdoc pull-content <doc-id> --output analysis.md
  llmtk gdoc list
  llmtk diagram architecture.md
  llmtk diagram architecture.md --format svg --output-dir ./images
  llmtk diagram architecture.md --inline
  llmtk ingest https://example.com/page -o page.md
  llmtk ingest report.pdf -o report.md
  llmtk ingest page.html
        """,
    )

    subparsers = parser.add_subparsers(dest='tool')
    _register_gdoc(subparsers)

    _register_diagram(subparsers)

    _register_ingest(subparsers)

    # Add future tools here:
    # _register_slides(subparsers)
    # _register_pdf(subparsers)

    args = parser.parse_args()

    if args.tool == 'gdoc':
        _handle_gdoc(args)
    elif args.tool == 'diagram':
        _handle_diagram(args)
    elif args.tool == 'ingest':
        _handle_ingest(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == '__main__':
    main()
