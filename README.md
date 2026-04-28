# Dealyo — AI Transaction Coordinator

An AI-native pipeline that replaces manual Transaction Coordinator work in real estate. Built as a pet project to explore how Claude skills can power real production workflows.

**Stack:** Python · FastAPI · Anthropic Claude · React · Vite

---

## What it does

Real estate deals today are managed manually — transaction coordinators track emails, chase missing documents, parse contracts, and monitor deadlines by hand. This project automates that entire workflow using Claude as the reasoning engine.

| Feature | Skill used | Description |
|---|---|---|
| Email → Deal Room | `email_parser v1.0` | Any real estate email → parties, docs, deadlines, deal health, follow-up draft |
| Missing doc detection | `doc_detector v1.0` | Identifies expected-but-missing docs and drafts follow-up emails automatically |
| Deal health scoring | `health_advisor v1.0` | Rule-based 0-100 score + Claude-powered action recommendations for at-risk deals |
| PDF contract extraction | `contract_extractor v1.0` | Upload a purchase agreement → 20+ structured fields + sorted deadline timeline |
| Email polling agent | — | Watches `new@dealyo.co` via IMAP, auto-ingests every incoming email |

---

## Claude skills architecture

All Claude calls are structured as **versioned skills** — modular, single-responsibility prompt modules that live in `skills/`.

```
skills/
  base.py                 ← BaseSkill class: versioning, retries, token tracking, timing
  email_parser.py         ← skill: raw email → structured deal data
  doc_detector.py         ← skill: detect missing docs + draft follow-up
  health_advisor.py       ← skill: recommend actions for at-risk deals
  contract_extractor.py   ← skill: PDF → contract terms + deadline timeline
  __init__.py             ← registry: single import point for all skills
  test_skills.py          ← test runner: verify all skills before starting API
```

Each skill owns exactly one Claude call and returns a typed `SkillResult` with latency, token usage, and version info. `main.py` contains zero prompts — it's pure routing.

This makes prompts independently testable, improvable without touching the API layer, and A/B testable by bumping the version number.

```python
from skills import email_parser

result = email_parser.run({
    "sender": "david@primemortgage.com",
    "subject": "Loan commitment delay",
    "body": "The underwriter needs updated pay stubs...",
})

if result.success:
    print(result.data["deal_health"])   # "Red"
    print(result.data["action_items"])  # ["Request extension from seller", ...]
    print(result.latency_ms)            # 1843
```

---

## Project structure

```
dealyo/
  backend/
    main.py               ← FastAPI routes (no prompts here)
    deal_health.py        ← rule-based scoring engine
    agent.py              ← IMAP email polling loop
    pdf_extractor.py      ← standalone PDF CLI tool
    requirements.txt
  skills/
    base.py
    email_parser.py
    doc_detector.py
    health_advisor.py
    contract_extractor.py
    __init__.py
    test_skills.py
  frontend/
    src/
      App.jsx
      components/
        EmailParser.jsx
        DealHealthCard.jsx
        PdfExtractor.jsx
  .env.example
```

---

## Quick start

### 1. Set up environment

```bash
git clone https://github.com/yourusername/dealyo
cd dealyo/backend

# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-..."
# or create backend/.env with:
# ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Install and run backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# API:   http://localhost:8000
# Docs:  http://localhost:8000/docs
```

### 3. Test all skills first

```bash
cd dealyo
python skills/test_skills.py
# Should print: All 3 skills passed. Ready to run the API.
```

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
# UI: http://localhost:5173
```

### 5. Run the email agent (optional)

```bash
# Set IMAP_HOST, IMAP_USER, IMAP_PASS in .env first
# For Gmail: use an App Password (myaccount.google.com/security)
python backend/agent.py
```

---

## API endpoints

```
GET  /                     Status + live skill versions
GET  /health               Health check
GET  /skills/versions      Which skill versions are deployed
POST /parse-email          Parse email → structured deal data   (email_parser v1.0)
POST /detect-missing-docs  Missing docs + follow-up draft       (doc_detector v1.0)
POST /advise-deal          Action recommendations for Red deals  (health_advisor v1.0)
POST /batch-parse          Parse multiple emails at once
POST /extract-pdf          Upload PDF → terms + timeline        (contract_extractor v1.0)
```

### Example — parse email

```bash
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/parse-email" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"sender":"david@primemortgage.com","subject":"Loan delay","body":"Underwriter needs updated pay stubs for Marcus Lin. Deadline April 28th."}'
```

### Example — extract PDF

```bash
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/extract-pdf" `
  -Method Post `
  -Form @{ file = Get-Item ".\sample_purchase_agreement.pdf" }
```

### Example response (`/parse-email`)

```json
{
  "subject_summary": "Lender requesting additional docs before issuing loan commitment",
  "deal_health": "Red",
  "health_reason": "Loan commitment at risk with 3 days to deadline",
  "parties": ["David Reyes — Lender (Prime Mortgage)", "Marcus Lin — Buyer"],
  "documents": ["Loan Commitment Letter", "Bank Statements", "Pay Stubs"],
  "deadlines": ["April 28: loan commitment deadline"],
  "action_items": ["Request extension from seller", "Follow up with Marcus Lin for pay stubs"],
  "urgency": "High",
  "missing_docs": ["Loan Commitment Letter"],
  "follow_up_draft": "Hi David, following up on the loan commitment for 4821 Westheimer...",
  "_skill": "email_parser",
  "_version": "1.0",
  "_latency_ms": 1843
}
```

---

## Architecture

```
new@dealyo.co (email)
       ↓
  agent.py (IMAP poll every 60s)
       ↓
  POST /parse-email
       ↓
  email_parser skill v1.0  ──→  Claude Sonnet 4
       ↓
  SkillResult { data, latency_ms, tokens }
       ↓
  deal_health.py (rule-based score)
       ↓
  health_advisor skill v1.0  ──→  Claude (only if Yellow/Red)
       ↓
  Structured JSON → Deal Room DB (Supabase — next step)
       ↓
  React dashboard
```

---

## Environment variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Email agent (optional)
IMAP_HOST=imap.gmail.com
IMAP_USER=new@dealyo.co
IMAP_PASS=your-16-char-app-password   # Gmail App Password, not your regular password
POLL_INTERVAL=60

# Frontend
VITE_API_URL=http://localhost:8000
```