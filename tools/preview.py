#!/usr/bin/env python3
"""
preview.py — Open the newsletter HTML in the default browser for review.

Usage:
    python tools/preview.py
"""

import os
import sys
import webbrowser
from pathlib import Path

HTML_PATH = ".tmp/newsletter_final.html"


def preview():
    if not os.path.exists(HTML_PATH):
        sys.exit(f"Error: {HTML_PATH} not found. Run render_html.py first.")

    abs_path = Path(HTML_PATH).resolve()
    url = abs_path.as_uri()

    webbrowser.open(url)

    print(f"Newsletter preview opened in browser: {abs_path}")
    print()
    print("=" * 60)
    print("REVIEW REQUIRED")
    print("=" * 60)
    print("Please review the newsletter in your browser.")
    print("Check:")
    print("  - Layout and formatting look correct")
    print("  - Images/infographics are rendering")
    print("  - Text content is accurate and well-written")
    print("  - No obvious errors or awkward phrasing")
    print()
    print("Once approved, run: python tools/send_email.py")
    print("=" * 60)


if __name__ == "__main__":
    preview()
