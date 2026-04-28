"""
Dealyo Skills Registry
──────────────────────
Single import point for all skills.
Add new skills here. Version history tracked here.

Usage:
    from skills import email_parser, doc_detector, health_advisor, contract_extractor

    result = email_parser.run({"body": "...", "sender": "...", "subject": "..."})
    if result.success:
        print(result.data["deal_health"])
"""

from skills.email_parser import EmailParserSkill
from skills.doc_detector import DocDetectorSkill
from skills.health_advisor import HealthAdvisorSkill
from skills.contract_extractor import ContractExtractorSkill

# ── Singleton instances (shared across requests) ──────────────────────────
# Skills are stateless — safe to share.

email_parser       = EmailParserSkill()
doc_detector       = DocDetectorSkill()
health_advisor     = HealthAdvisorSkill()
contract_extractor = ContractExtractorSkill()

# ── Version manifest ──────────────────────────────────────────────────────
# Used by /skills/versions endpoint for observability.

SKILL_VERSIONS = {
    s.name: s.version
    for s in [email_parser, doc_detector, health_advisor, contract_extractor]
}

__all__ = [
    "email_parser",
    "doc_detector",
    "health_advisor",
    "contract_extractor",
    "SKILL_VERSIONS",
]
