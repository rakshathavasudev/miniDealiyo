"""
Dealyo - PDF Contract Term Extractor
Extracts key contract terms from real estate PDFs using Claude's document API.
Usage: python pdf_extractor.py contract.pdf
"""

import os
import sys
import json
import base64
import anthropic
from pathlib import Path

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM = """You are a real estate contract analyst for Dealyo. Extract all key terms 
from the provided contract PDF. Return ONLY valid JSON, no markdown."""

PROMPT = """Extract all critical terms from this real estate contract.

Return this exact JSON:
{
  "property_address": "full address",
  "purchase_price": "dollar amount",
  "earnest_money": "dollar amount",
  "closing_date": "date",
  "financing_contingency_date": "date or null",
  "inspection_contingency_date": "date or null",
  "appraisal_contingency_date": "date or null",
  "buyer_name": "full name",
  "seller_name": "full name",
  "buyer_agent": "name and brokerage or null",
  "seller_agent": "name and brokerage or null",
  "title_company": "name or null",
  "lender": "name or null",
  "inclusions": ["list of included items"],
  "exclusions": ["list of excluded items"],
  "repair_allowance": "dollar amount or null",
  "possession_date": "date or null",
  "special_conditions": ["any special terms or contingencies"],
  "missing_fields": ["fields that appear blank or unclear in the contract"]
}"""


def extract_from_pdf(pdf_path: str) -> dict:
    """Extract contract terms from a PDF using Claude's vision."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    with open(path, "rb") as f:
        pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data,
                        },
                    },
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def build_timeline(terms: dict) -> list[dict]:
    """Convert extracted terms into a sorted deadline timeline."""
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
            timeline.append({"date": val, "event": label, "field": field})

    return timeline


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <path-to-contract.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    print(f"\nExtracting terms from: {pdf_path}\n")

    terms = extract_from_pdf(pdf_path)
    print("── Extracted Terms ──────────────────────────────")
    print(json.dumps(terms, indent=2))

    print("\n── Deadline Timeline ────────────────────────────")
    timeline = build_timeline(terms)
    for item in timeline:
        print(f"  {item['date']:20s} {item['event']}")

    if terms.get("missing_fields"):
        print("\n── Missing / Unclear Fields ─────────────────────")
        for f in terms["missing_fields"]:
            print(f"  ⚠  {f}")

    # Save output
    out_path = pdf_path.replace(".pdf", "_extracted.json")
    with open(out_path, "w") as f:
        json.dump({"terms": terms, "timeline": timeline}, f, indent=2)
    print(f"\nSaved to {out_path}")
