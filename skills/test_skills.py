"""
Dealyo Skills — Test Runner
Run this to verify all skills work before starting the API.

Usage:
    cd dealyo
    python skills/test_skills.py
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../backend/.env"))

from skills import email_parser, doc_detector, health_advisor, SKILL_VERSIONS

# ── Color output ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):  print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}")
def info(msg): print(f"  {YELLOW}→{RESET} {msg}")


def test_email_parser():
    print(f"\n{BOLD}1. email_parser v{email_parser.version}{RESET}")
    result = email_parser.run({
        "sender": "david.reyes@primemortgage.com",
        "subject": "Loan commitment delay — 4821 Westheimer",
        "body": (
            "Hi, the underwriter needs updated pay stubs and 12-month bank statements "
            "for Marcus Lin before we can issue the loan commitment. "
            "We estimate 5-7 business days. The current deadline is April 28th "
            "so we may need a short extension from the seller. Please advise."
        ),
    })
    if result.success:
        ok(f"Success ({result.latency_ms}ms)")
        ok(f"deal_health = {result.data['deal_health']}")
        ok(f"parties = {result.data['parties']}")
        ok(f"urgency = {result.data['urgency']}")
        ok(f"missing_docs = {result.data.get('missing_docs', [])}")
    else:
        fail(f"Failed: {result.error}")
    return result.success


def test_doc_detector():
    print(f"\n{BOLD}2. doc_detector v{doc_detector.version}{RESET}")
    result = doc_detector.run({
        "sender": "jennifer.walsh@houstonhomes.com",
        "subject": "Inspection report — still waiting",
        "body": (
            "We scheduled the inspection at 4821 Westheimer on April 18th "
            "with TrustCheck Inspections but have NOT received the report yet. "
            "The inspection contingency expires April 29th. "
            "Can someone follow up? Buyer Marcus Lin is getting anxious."
        ),
    })
    if result.success:
        ok(f"Success ({result.latency_ms}ms)")
        ok(f"missing_docs = {result.data['missing_docs']}")
        ok(f"follow_up_required = {result.data['follow_up_required']}")
        if result.data.get("follow_up_draft"):
            ok(f"follow_up_draft = {result.data['follow_up_draft'][:80]}...")
    else:
        fail(f"Failed: {result.error}")
    return result.success


def test_health_advisor():
    print(f"\n{BOLD}3. health_advisor v{health_advisor.version}{RESET}")
    result = health_advisor.run({
        "address": "4821 Westheimer Rd, Houston TX",
        "closing_date": "2025-05-03",
        "status": "Red",
        "score": 35,
        "days_to_close": 6,
        "issues": [
            "Loan commitment overdue (deadline April 25)",
            "Inspection report not received",
            "Lender flagged missing documents",
        ],
    })
    if result.success:
        ok(f"Success ({result.latency_ms}ms)")
        for action in result.data["recommended_actions"]:
            ok(f"action: {action}")
    else:
        fail(f"Failed: {result.error}")
    return result.success


def main():
    print(f"\n{BOLD}Dealyo Skills Test Runner{RESET}")
    print(f"Skill versions: {SKILL_VERSIONS}")
    print("─" * 50)

    results = [
        test_email_parser(),
        test_doc_detector(),
        test_health_advisor(),
    ]

    passed = sum(results)
    total = len(results)
    print(f"\n{'─' * 50}")
    if passed == total:
        print(f"{GREEN}{BOLD}All {total} skills passed.{RESET} Ready to run the API.")
    else:
        print(f"{RED}{BOLD}{passed}/{total} skills passed.{RESET} Check errors above.")
    print()


if __name__ == "__main__":
    main()
