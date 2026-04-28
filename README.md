# Dealyo — AI Transaction Coordinator

AI-native pipeline that replaces manual Transaction Coordinator work.
Built with **Claude (Anthropic)**, FastAPI, and React.

---

## What this does

| Feature | Description |
|---|---|
| **Email → Deal Room** | Paste any real estate email → Claude extracts parties, docs, deadlines, health score, and drafts follow-ups |
| **Deal Health Engine** | Rule-based scoring (0-100) + Claude recommendations for at-risk deals |
| **PDF Contract Extractor** | Upload a purchase agreement → Claude extracts all key terms and builds a deadline timeline |
| **Email Polling Agent** | Watches `new@dealyo.co` via IMAP, auto-ingests and flags missing docs |

---

## Quick start

### 1. Clone and set up environment

```bash
git clone https://github.com/yourusername/dealyo
cd dealyo
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY
```

### 2. Run the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# API running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev
# UI at http://localhost:5173
```

### 4. Run the email agent (optional)

```bash
cd backend
# Set IMAP_USER, IMAP_PASS in .env
python agent.py
```

---

## API endpoints

```
POST /parse-email          Parse a single email → structured deal data
POST /batch-parse          Parse multiple emails at once
POST /detect-missing-docs  Only check for missing docs + draft follow-up
POST /extract-pdf          Upload PDF → extract contract terms + timeline
GET  /health               Health check
```

### Example request

```bash
curl -X POST http://localhost:8000/parse-email \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "david@primemortgage.com",
    "subject": "Loan commitment delay",
    "body": "The underwriter needs 2 more items before issuing the loan commitment..."
  }'
```

### Example response

```json
{
  "subject_summary": "Lender requesting additional documents before issuing loan commitment",
  "deal_health": "Red",
  "health_reason": "Loan commitment at risk with 3 days to deadline",
  "parties": ["David Reyes — Lender (Prime Mortgage)", "Marcus Lin — Buyer"],
  "documents": ["Loan Commitment Letter", "Bank Statements", "Pay Stubs"],
  "deadlines": ["April 28: loan commitment deadline"],
  "action_items": [
    "Request 5-7 day extension from seller",
    "Follow up with Marcus Lin for bank statements and pay stubs"
  ],
  "urgency": "High",
  "missing_docs": ["Loan Commitment Letter"],
  "follow_up_draft": "Hi David, following up on the loan commitment for 4821 Westheimer. Could you confirm the exact documents needed from Marcus and the earliest you can issue once received? We may need to request a short extension — please advise."
}
```

---

## Architecture

```
new@dealyo.co (email)
       ↓
  agent.py (IMAP poll)
       ↓
POST /parse-email
       ↓
  Claude Sonnet 4 (extraction prompt)
       ↓
  Structured JSON → Deal Room DB
       ↓
  deal_health.py (scoring engine)
       ↓
  Frontend dashboard
```

---

## Tech stack

- **AI**: Anthropic Claude (`claude-sonnet-4-20250514`) via Python SDK
- **Backend**: FastAPI + Uvicorn
- **Frontend**: React + Vite
- **Email**: IMAP polling (Gmail compatible)
- **PDF**: Claude document API (base64 PDF input)
