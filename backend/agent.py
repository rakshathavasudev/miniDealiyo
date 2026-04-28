"""
Dealyo - Email Polling Agent
Watches new@dealyo.co via IMAP, feeds emails into the parse pipeline,
and auto-triggers follow-ups for missing documents.
Run with: python agent.py
"""

import os
import imaplib
import email
import time
import json
import logging
import httpx
from email.header import decode_header
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("dealyo-agent")

API_BASE = os.environ.get("DEALYO_API", "http://localhost:8000")
IMAP_HOST = os.environ.get("IMAP_HOST", "imap.gmail.com")
IMAP_USER = os.environ.get("IMAP_USER", "new@dealyo.co")
IMAP_PASS = os.environ.get("IMAP_PASS", "")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))  # seconds


def decode_str(s):
    if not s:
        return ""
    decoded, enc = decode_header(s)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(enc or "utf-8", errors="replace")
    return decoded


def get_body(msg):
    """Extract plain text body from email."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return ""


def fetch_unseen_emails():
    """Connect to IMAP and fetch unseen emails."""
    emails = []
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(IMAP_USER, IMAP_PASS)
        mail.select("inbox")

        _, data = mail.search(None, "UNSEEN")
        for num in data[0].split():
            _, raw = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(raw[0][1])
            emails.append({
                "subject": decode_str(msg["Subject"]),
                "sender": decode_str(msg["From"]),
                "body": get_body(msg),
                "received_at": msg["Date"],
                "uid": num.decode(),
            })
            # Mark as seen
            mail.store(num, "+FLAGS", "\\Seen")

        mail.logout()
    except Exception as e:
        log.error(f"IMAP error: {e}")
    return emails


def process_email(em: dict):
    """Send one email to the parse API and log the result."""
    try:
        resp = httpx.post(f"{API_BASE}/parse-email", json={
            "subject": em["subject"],
            "sender": em["sender"],
            "body": em["body"],
            "received_at": em["received_at"],
        }, timeout=30)
        resp.raise_for_status()
        result = resp.json()

        log.info(f"[{result['deal_health']}] {em['subject'][:60]}")
        log.info(f"  Parties: {result['parties']}")
        log.info(f"  Deadlines: {result['deadlines']}")
        log.info(f"  Action items: {result['action_items']}")

        if result.get("missing_docs"):
            log.warning(f"  MISSING DOCS: {result['missing_docs']}")
            if result.get("follow_up_draft"):
                log.info(f"  FOLLOW-UP QUEUED:\n{result['follow_up_draft']}")
                # TODO: send via SendGrid / SMTP

        # TODO: write to your DB here (Supabase, Postgres, etc.)
        save_to_deal_room(em, result)

    except Exception as e:
        log.error(f"Failed to process email '{em['subject']}': {e}")


def save_to_deal_room(raw_email: dict, parsed: dict):
    """Placeholder: persist to database / deal room."""
    # In production: upsert to Supabase/Postgres
    # For demo: write to local JSONL file
    record = {
        "ingested_at": datetime.utcnow().isoformat(),
        "raw": raw_email,
        "parsed": parsed,
    }
    with open("deal_room.jsonl", "a") as f:
        f.write(json.dumps(record) + "\n")
    log.info(f"  Saved to deal_room.jsonl")


def run():
    log.info(f"Dealyo email agent started. Polling {IMAP_USER} every {POLL_INTERVAL}s")
    while True:
        log.info("Checking for new emails…")
        emails = fetch_unseen_emails()
        if emails:
            log.info(f"Found {len(emails)} new email(s)")
            for em in emails:
                process_email(em)
        else:
            log.info("No new emails.")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
