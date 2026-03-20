#!/usr/bin/env python3
"""
send_email.py — Send the newsletter via Gmail API with OAuth2.

Usage:
    python tools/send_email.py
    python tools/send_email.py --group friends
    python tools/send_email.py --to recipient@example.com --subject "Custom Subject"

Reads sender identity from:  config/newsletter_style.json
Reads recipients from:        config/recipients.json
"""

import argparse
import base64
import json
import os
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

import html2text
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.compose"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
HTML_PATH = ".tmp/newsletter_final.html"
CONTENT_PATH = ".tmp/newsletter_content.json"
STYLE_CONFIG = "config/newsletter_style.json"
RECIPIENTS_CONFIG = "config/recipients.json"


def load_style() -> dict:
    with open(STYLE_CONFIG) as f:
        return json.load(f)


def load_recipients(group: str = None) -> list:
    """Return list of {name, email} dicts for the given group (or default_group)."""
    with open(RECIPIENTS_CONFIG) as f:
        config = json.load(f)
    target_group = group or config.get("default_group", "self")
    recipients = config.get("groups", {}).get(target_group)
    if not recipients:
        sys.exit(f"Error: Recipient group '{target_group}' not found in {RECIPIENTS_CONFIG}")
    return recipients


def get_gmail_service():
    """Authenticate and return Gmail API service, handling scope upgrades automatically."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                sys.exit(
                    f"Error: {CREDENTIALS_FILE} not found.\n"
                    "Download it from Google Cloud Console → APIs & Services → Credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def build_email(
    to_list: list,
    subject: str,
    html_content: str,
    sender_name: str,
    sender_email: str,
) -> dict:
    """Build a MIME email with HTML and plain-text fallback."""
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((sender_name, sender_email))
    msg["To"] = ", ".join(formataddr((r["name"], r["email"])) for r in to_list)
    msg["Subject"] = subject

    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    plain_text = converter.handle(html_content)

    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return {"raw": raw}


def save_draft(service, email_body):
    result = service.users().drafts().create(
        userId="me", body={"message": email_body}
    ).execute()
    return result.get("id", "unknown")


def send_email(to: str = None, group: str = None, subject: str = None, send: bool = False):
    if not os.path.exists(HTML_PATH):
        sys.exit(f"Error: {HTML_PATH} not found. Run render_html.py first.")

    style = load_style()
    sender_name = style.get("sender_name", "Newsletter")
    sender_email = style.get("sender_email", "")
    newsletter_name = style.get("newsletter_name", "Newsletter")
    subject_prefix = style.get("subject_prefix", "")

    if to:
        recipients = [{"name": to, "email": to}]
    else:
        recipients = load_recipients(group)

    with open(HTML_PATH) as f:
        html_content = f.read()

    if subject is None:
        subject = newsletter_name
        if os.path.exists(CONTENT_PATH):
            with open(CONTENT_PATH) as f:
                content = json.load(f)
            headline = content.get("headline", "")
            topic = content.get("topic", "")
            if headline:
                subject = headline
            elif topic:
                subject = f"{newsletter_name}: {topic}"

    if subject_prefix:
        subject = f"{subject_prefix} {subject}"

    print(f"From:    {sender_name} <{sender_email}>")
    print(f"To:      {', '.join(r['email'] for r in recipients)}")
    print(f"Subject: {subject}")
    print("Authenticating with Gmail...")

    service = get_gmail_service()
    email_body = build_email(recipients, subject, html_content, sender_name, sender_email)

    try:
        if send:
            result = service.users().messages().send(userId="me", body=email_body).execute()
            print(f"\nEmail sent successfully!")
            print(f"  Message ID: {result.get('id', 'unknown')}")
            print(f"  Sent to {len(recipients)} recipient(s)")
        else:
            draft_id = save_draft(service, email_body)
            print(f"\nDraft saved to Gmail!")
            print(f"  Draft ID: {draft_id}")
            print(f"  Open Gmail → Drafts to review, then send manually.")
            print(f"\n  To send directly next time, run:")
            print(f"  python3 tools/send_email.py --send")
    except HttpError as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send newsletter via Gmail")
    parser.add_argument("--to", help="Single recipient email (bypasses recipients.json)")
    parser.add_argument("--group", help="Recipient group from recipients.json (default: default_group)")
    parser.add_argument("--subject", help="Email subject (defaults to newsletter headline)")
    parser.add_argument("--send", action="store_true", help="Actually send the email (default: save as draft)")
    args = parser.parse_args()
    send_email(args.to, args.group, args.subject, args.send)
