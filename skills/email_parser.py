"""
Dealyo Skill: email_parser  v1.0
─────────────────────────────────
Responsibility: Parse a raw real estate email into structured deal data.
One skill, one job. No side effects.

Versioning strategy:
  v1.0 — initial extraction schema
  v1.1 — add confidence scores per field (future)
  v2.0 — multi-email thread context (future)
"""

import json
from skills.base import BaseSkill


class EmailParserSkill(BaseSkill):
    """
    Parses raw real estate emails into structured deal intelligence.
    Powers the new@dealyo.co ingestion pipeline.
    """

    name = "email_parser"
    version = "1.0"
    max_tokens = 1024

    # ── System prompt ────────────────────────────────────────────────────────
    # Versioned here. To improve extraction, edit this prompt and bump version.
    # Old versions can be kept for A/B testing.

    @property
    def system_prompt(self) -> str:
        return """You are an expert AI Transaction Coordinator for Dealyo, a real estate 
deal automation platform. You parse raw real estate emails and extract precise, 
structured intelligence that feeds into the deal room.

Rules:
- Extract REAL names, dates, dollar amounts, document names — never generic placeholders
- Be specific: "April 28" not "upcoming deadline"  
- For missing_docs: only list docs mentioned as expected but not yet received
- For follow_up_draft: write a professional 2-3 sentence email if action needed, else ""
- Return ONLY valid JSON. No markdown, no explanation, no preamble."""

    # ── Output schema (v1.0) ─────────────────────────────────────────────────
    SCHEMA = {
        "subject_summary": "str — one clear sentence about what this email is about",
        "deal_health": "Green | Yellow | Red",
        "health_reason": "str — brief reason, max 15 words",
        "parties": ["Name — Role"],
        "documents": ["document name"],
        "deadlines": ["date: description"],
        "action_items": ["specific action needed"],
        "urgency": "Low | Medium | High",
        "missing_docs": ["expected but not received document"],
        "follow_up_draft": "str — draft follow-up email or empty string",
    }

    def build_prompt(self, inputs: dict) -> str:
        return f"""Analyze this real estate email and extract deal intelligence.

Return this exact JSON schema:
{json.dumps(self.SCHEMA, indent=2)}

EMAIL:
From: {inputs.get('sender', 'unknown')}
Subject: {inputs.get('subject', 'no subject')}
Received: {inputs.get('received_at', 'unknown')}

{inputs.get('body', '')}"""

    def parse_response(self, raw: str) -> dict:
        cleaned = self.clean_json(raw)
        parsed = json.loads(cleaned)

        # Validate required fields — raise if malformed so retry logic kicks in
        required = ["subject_summary", "deal_health", "parties", "action_items", "urgency"]
        for field in required:
            if field not in parsed:
                raise ValueError(f"Missing required field: {field}")

        # Normalize deal_health casing
        parsed["deal_health"] = parsed["deal_health"].capitalize()
        if parsed["deal_health"] not in ("Green", "Yellow", "Red"):
            parsed["deal_health"] = "Yellow"

        # Ensure lists are actually lists
        for list_field in ["parties", "documents", "deadlines", "action_items", "missing_docs"]:
            if not isinstance(parsed.get(list_field), list):
                parsed[list_field] = []

        return parsed
