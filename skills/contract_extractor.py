"""
Dealyo Skill: contract_extractor  v1.0
────────────────────────────────────────
Responsibility: Extract structured key terms from real estate contract PDFs.
Uses Claude's document API (base64 PDF input).

This skill is document-modal — it accepts a PDF, not text.
build_prompt() returns a list (multimodal content block) not a string.
"""

import json
import base64
from pathlib import Path
from skills.base import BaseSkill, client


class ContractExtractorSkill(BaseSkill):
    """
    Extracts all key contract terms from a purchase agreement PDF.
    Returns structured data + a sorted deadline timeline.
    """

    name = "contract_extractor"
    version = "1.0"
    max_tokens = 2048  # PDFs need more tokens

    @property
    def system_prompt(self) -> str:
        return """You are a real estate contract analyst for Dealyo. Extract all key terms 
from purchase agreement PDFs with high precision.

Rules:
- Extract exact values — real dates, real dollar amounts, real names
- Use null for fields that are genuinely absent, not for fields you missed
- Flag any field that appears blank, ambiguous, or contradictory in missing_fields
- Return ONLY valid JSON. No markdown, no explanation."""

    SCHEMA = {
        "property_address": "full address or null",
        "purchase_price": "dollar amount or null",
        "earnest_money": "dollar amount or null",
        "closing_date": "date or null",
        "financing_contingency_date": "date or null",
        "inspection_contingency_date": "date or null",
        "appraisal_contingency_date": "date or null",
        "buyer_name": "full name or null",
        "seller_name": "full name or null",
        "buyer_agent": "name and brokerage or null",
        "seller_agent": "name and brokerage or null",
        "title_company": "name or null",
        "lender": "name or null",
        "inclusions": ["list of included items"],
        "exclusions": ["list of excluded items"],
        "repair_allowance": "dollar amount or null",
        "possession_date": "date or null",
        "special_conditions": ["any special terms or contingencies"],
        "missing_fields": ["fields that appear blank or unclear in the contract"],
    }

    def build_prompt(self, inputs: dict):
        """
        Override: returns a multimodal content list (PDF + text) instead of a string.
        The base run() method handles this transparently.
        """
        return [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": inputs["pdf_base64"],
                },
            },
            {
                "type": "text",
                "text": f"Extract all contract terms using this schema:\n{json.dumps(self.SCHEMA, indent=2)}"
            }
        ]

    def parse_response(self, raw: str) -> dict:
        cleaned = self.clean_json(raw)
        terms = json.loads(cleaned)

        # Build sorted deadline timeline from extracted dates
        timeline = []
        date_fields = {
            "inspection_contingency_date": "Inspection contingency expires",
            "financing_contingency_date": "Financing contingency expires",
            "appraisal_contingency_date": "Appraisal contingency expires",
            "possession_date": "Possession date",
            "closing_date": "Closing date",
        }
        for field, label in date_fields.items():
            val = terms.get(field)
            if val and val != "null":
                timeline.append({"date": val, "event": label})

        return {"terms": terms, "timeline": timeline}

    def run_from_file(self, pdf_path: str):
        """Convenience method — load PDF from disk and run."""
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        with open(path, "rb") as f:
            pdf_b64 = base64.standard_b64encode(f.read()).decode("utf-8")
        return self.run({"pdf_base64": pdf_b64})
