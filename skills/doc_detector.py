"""
Dealyo Skill: doc_detector  v1.0
─────────────────────────────────
Responsibility: Detect missing documents in a deal and draft follow-up emails.
Focused skill — does NOT score deal health or extract parties.

Versioning strategy:
  v1.0 — detect missing docs from email context
  v1.1 — cross-reference against deal room document checklist (future)
  v2.0 — detect docs from PDF attachments (future)
"""

import json
from skills.base import BaseSkill


# Standard documents required for a residential real estate closing
STANDARD_CHECKLIST = [
    "Purchase Agreement",
    "Earnest Money Receipt",
    "Inspection Report",
    "Loan Commitment Letter",
    "Appraisal Report",
    "Title Commitment",
    "HOA Disclosure",
    "Seller Disclosure",
    "Final Walkthrough Confirmation",
    "Closing Disclosure",
]


class DocDetectorSkill(BaseSkill):
    """
    Detects missing documents from email context.
    Returns missing docs, urgency, and a ready-to-send follow-up draft.
    """

    name = "doc_detector"
    version = "1.0"
    max_tokens = 768

    @property
    def system_prompt(self) -> str:
        return """You are a document compliance specialist for Dealyo, a real estate 
transaction platform. Your only job is to identify missing documents and draft 
follow-up requests to obtain them.

Be precise: only flag documents explicitly mentioned as missing, overdue, or not yet received.
Do not flag documents that haven't been mentioned at all.
Return ONLY valid JSON. No markdown, no preamble."""

    SCHEMA = {
        "missing_docs": ["document name that is explicitly missing or overdue"],
        "doc_status": {
            "document name": "missing | pending | received"
        },
        "follow_up_required": "bool",
        "follow_up_recipient": "name and role of who to follow up with, or empty string",
        "follow_up_draft": "professional 2-3 sentence follow-up email, or empty string",
        "urgency": "Low | Medium | High",
        "deadline": "specific deadline date if mentioned, or empty string",
    }

    def build_prompt(self, inputs: dict) -> str:
        checklist_str = "\n".join(f"- {doc}" for doc in STANDARD_CHECKLIST)

        return f"""Analyze this real estate email for missing or overdue documents.

Standard document checklist for reference:
{checklist_str}

Return this exact JSON:
{json.dumps(self.SCHEMA, indent=2)}

EMAIL:
From: {inputs.get('sender', 'unknown')}
Subject: {inputs.get('subject', 'no subject')}

{inputs.get('body', '')}"""

    def parse_response(self, raw: str) -> dict:
        cleaned = self.clean_json(raw)
        parsed = json.loads(cleaned)

        if not isinstance(parsed.get("missing_docs"), list):
            parsed["missing_docs"] = []

        if not isinstance(parsed.get("doc_status"), dict):
            parsed["doc_status"] = {}

        parsed["follow_up_required"] = bool(parsed.get("follow_up_required", False))

        return parsed
