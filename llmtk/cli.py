"""llmtk — CLI entry point.

Usage:
    llmtk gdoc push <file.md> [--title "Title"] [--folder "Folder"]
    llmtk gdoc push --stdin --title "Title"
    llmtk gdoc pull <doc-url>
    llmtk gdoc list
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
            source = str(args.file)
        else:
            print("Provide a file path or --stdin")
            sys.exit(1)

        push_to_gdoc(md_content, title, folder=args.folder, source=source)

    elif args.gdoc_command == 'pull':
        from llmtk.gdoc.pull import pull_comments
        pull_comments(args.doc)

    elif args.gdoc_command == 'list':
        from llmtk.gdoc.history import list_all
        list_all()

    else:
        print("Usage: llmtk gdoc {push|pull|list}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog='llmtk',
        description='LLM Toolkit — bridge LLM workflows to the traditional ways of working',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Tools:
  gdoc    Markdown ↔ Google Docs (push, pull comments, list)

Examples:
  llmtk gdoc push analysis.md --title "Q1 Analysis" --folder "Work"
  llmtk gdoc push --stdin --title "Quick Note"
  llmtk gdoc pull https://docs.google.com/document/d/1xABC.../edit
  llmtk gdoc list
        """,
    )

    subparsers = parser.add_subparsers(dest='tool')
    _register_gdoc(subparsers)

    # Add future tools here:
    # _register_slides(subparsers)
    # _register_pdf(subparsers)

    args = parser.parse_args()

    if args.tool == 'gdoc':
        _handle_gdoc(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == '__main__':
    main()
