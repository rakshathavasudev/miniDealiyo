"""
Dealyo - Deal Health Scoring Engine
Aggregates signals from emails, documents, and timelines
to compute a Green/Yellow/Red health score for each deal.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
import anthropic
import os
import json

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


@dataclass
class DealSignals:
    """All observable signals for a single deal."""
    address: str
    closing_date: date

    # Document signals
    required_docs: list[str] = field(default_factory=list)
    received_docs: list[str] = field(default_factory=list)

    # Email signals (from parser)
    email_urgencies: list[str] = field(default_factory=list)   # Low/Medium/High per email
    overdue_deadlines: list[str] = field(default_factory=list)
    upcoming_deadlines: list[str] = field(default_factory=list)  # within 72h

    # Manual flags
    lender_flag: bool = False
    title_flag: bool = False
    inspection_flag: bool = False


@dataclass
class HealthScore:
    status: str          # Green | Yellow | Red
    score: int           # 0-100
    reasons: list[str]
    recommended_actions: list[str]
    computed_at: str


def compute_health(signals: DealSignals) -> HealthScore:
    """
    Rule-based + AI-assisted deal health computation.
    Rules run first for speed; Claude provides nuanced reasoning.
    """
    score = 100
    reasons = []
    actions = []

    # ── Rule-based scoring ─────────────────────────────────────────────────
    missing = [d for d in signals.required_docs if d not in signals.received_docs]
    if missing:
        penalty = min(len(missing) * 15, 40)
        score -= penalty
        reasons.append(f"{len(missing)} required document(s) missing: {', '.join(missing)}")
        actions.append(f"Follow up on: {', '.join(missing)}")

    if signals.overdue_deadlines:
        score -= len(signals.overdue_deadlines) * 20
        reasons.append(f"{len(signals.overdue_deadlines)} deadline(s) overdue")
        actions.append("Immediately address overdue contingencies")

    if signals.upcoming_deadlines:
        score -= len(signals.upcoming_deadlines) * 5
        reasons.append(f"{len(signals.upcoming_deadlines)} deadline(s) within 72 hours")

    high_urgency_count = signals.email_urgencies.count("High")
    if high_urgency_count:
        score -= high_urgency_count * 10
        reasons.append(f"{high_urgency_count} high-urgency email thread(s) unresolved")

    if signals.lender_flag:
        score -= 15
        reasons.append("Lender flagged an issue")
        actions.append("Contact lender immediately")

    if signals.title_flag:
        score -= 20
        reasons.append("Title issue detected")
        actions.append("Resolve title exception before closing")

    days_to_close = (signals.closing_date - date.today()).days
    if days_to_close < 0:
        score -= 30
        reasons.append("Closing date has passed — deal may be in default")
    elif days_to_close <= 3 and score < 90:
        score -= 10
        reasons.append(f"Only {days_to_close} day(s) until closing with open items")

    score = max(0, score)

    # ── Determine status ───────────────────────────────────────────────────
    if score >= 80:
        status = "Green"
    elif score >= 50:
        status = "Yellow"
    else:
        status = "Red"

    # ── Claude adds nuanced reasoning for non-green deals ─────────────────
    if status != "Green" and reasons:
        try:
            ai_actions = _get_ai_recommendations(signals, reasons, status)
            actions = ai_actions or actions
        except Exception:
            pass  # Fall back to rule-based actions

    return HealthScore(
        status=status,
        score=score,
        reasons=reasons,
        recommended_actions=actions,
        computed_at=datetime.utcnow().isoformat(),
    )


def _get_ai_recommendations(signals: DealSignals, issues: list[str], status: str) -> list[str]:
    """Ask Claude for specific recommended actions given the deal's issues."""
    prompt = f"""A real estate deal has health status: {status}

Property: {signals.address}
Closing date: {signals.closing_date}
Days to closing: {(signals.closing_date - date.today()).days}

Issues detected:
{chr(10).join(f'- {i}' for i in issues)}

Return a JSON array of 2-4 specific, actionable steps a transaction coordinator should take RIGHT NOW.
Each action should be concrete (who to call, what to request, what deadline to set).
Return ONLY the JSON array, no markdown."""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


# ── Example usage ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    signals = DealSignals(
        address="4821 Westheimer Rd, Houston TX",
        closing_date=date(2025, 5, 3),
        required_docs=[
            "Purchase Agreement",
            "Inspection Report",
            "Loan Commitment Letter",
            "Title Commitment",
            "HOA Disclosure",
        ],
        received_docs=["Purchase Agreement", "HOA Disclosure"],
        email_urgencies=["High", "Medium"],
        overdue_deadlines=["Loan commitment (Apr 25)"],
        upcoming_deadlines=["Inspection contingency (Apr 29)"],
        lender_flag=True,
    )

    result = compute_health(signals)
    print(f"\nDeal: {signals.address}")
    print(f"Health: {result.status} (score: {result.score}/100)")
    print(f"\nReasons:")
    for r in result.reasons:
        print(f"  - {r}")
    print(f"\nRecommended actions:")
    for a in result.recommended_actions:
        print(f"  → {a}")
