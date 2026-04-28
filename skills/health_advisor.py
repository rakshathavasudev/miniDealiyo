"""
Dealyo Skill: health_advisor  v1.0
────────────────────────────────────
Responsibility: Given a deal's risk signals, recommend specific actions.
This skill sits on TOP of the rule-based scorer in deal_health.py —
rules compute the score, Claude provides the actionable reasoning.

Separation of concerns:
  deal_health.py  →  deterministic score (fast, cheap, no LLM)
  health_advisor  →  human-quality recommendations (LLM, only when needed)
"""

import json
from skills.base import BaseSkill


class HealthAdvisorSkill(BaseSkill):
    """
    Generates specific, actionable recommendations for Yellow/Red deals.
    Only called when a deal's score drops below 80 — not on every deal.
    """

    name = "health_advisor"
    version = "1.0"
    max_tokens = 512

    @property
    def system_prompt(self) -> str:
        return """You are a senior Transaction Coordinator at Dealyo with 15 years 
of real estate closing experience. You are given a deal's risk signals and 
must produce specific, immediately actionable steps.

Your recommendations must be:
- Concrete: who to call, what to request, what deadline to set
- Prioritized: most urgent action first
- Brief: max 15 words per action

Return ONLY a valid JSON array of 2-4 action strings. No markdown, no explanation."""

    def build_prompt(self, inputs: dict) -> str:
        issues_str = "\n".join(f"- {i}" for i in inputs.get("issues", []))
        days = inputs.get("days_to_close", "unknown")

        return f"""Deal needs immediate attention.

Property: {inputs.get('address', 'unknown')}
Closing date: {inputs.get('closing_date', 'unknown')} ({days} days away)
Health status: {inputs.get('status', 'Red')}
Score: {inputs.get('score', 0)}/100

Issues detected:
{issues_str}

Return a JSON array of 2-4 specific actions a TC should take RIGHT NOW.
Example format: ["Call David Reyes at Prime Mortgage re: loan commitment — get ETA", "Request 5-day extension from seller's agent before April 28 deadline"]"""

    def parse_response(self, raw: str) -> dict:
        cleaned = self.clean_json(raw)
        actions = json.loads(cleaned)

        if not isinstance(actions, list):
            raise ValueError("Expected a JSON array of actions")

        # Normalize — ensure all items are strings
        actions = [str(a) for a in actions if a]

        return {"recommended_actions": actions}
