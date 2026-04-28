"""
Dealyo - AI Transaction Coordinator API
All Claude calls go through versioned skills in /skills.
main.py is pure routing — no prompts live here.
"""

import os
import sys
import base64

# Fix path FIRST — skills/ is at dealyo/skills/, one level up from dealyo/backend/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from skills import (
    email_parser,
    doc_detector,
    health_advisor,
    contract_extractor,
    SKILL_VERSIONS,
)

app = FastAPI(title="Dealyo AI Pipeline", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class EmailInput(BaseModel):
    subject: str = ""
    sender: str = ""
    body: str
    received_at: Optional[str] = None


@app.get("/")
def root():
    return {"status": "Dealyo AI Pipeline running", "version": "2.0.0", "skills": SKILL_VERSIONS}


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/skills/versions")
def skill_versions():
    return {"versions": SKILL_VERSIONS, "model": "claude-sonnet-4-20250514"}


@app.post("/parse-email")
def parse_email(payload: EmailInput):
    result = email_parser.run({
        "sender": payload.sender,
        "subject": payload.subject,
        "body": payload.body,
        "received_at": payload.received_at or datetime.utcnow().isoformat(),
    })
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return {**result.data, "_skill": result.skill_name, "_version": result.skill_version, "_latency_ms": result.latency_ms}


@app.post("/detect-missing-docs")
def detect_missing_docs(payload: EmailInput):
    result = doc_detector.run({
        "sender": payload.sender,
        "subject": payload.subject,
        "body": payload.body,
    })
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return {**result.data, "_skill": result.skill_name, "_version": result.skill_version, "_latency_ms": result.latency_ms}


@app.post("/batch-parse")
def batch_parse(emails: list[EmailInput]):
    results = []
    for em in emails:
        result = email_parser.run({
            "sender": em.sender, "subject": em.subject,
            "body": em.body, "received_at": em.received_at or datetime.utcnow().isoformat(),
        })
        if result.success:
            results.append({"status": "ok", "data": result.data})
        else:
            results.append({"status": "error", "error": result.error})
    return results


@app.post("/advise-deal")
def advise_deal(payload: dict):
    result = health_advisor.run(payload)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return {**result.data, "_skill": result.skill_name, "_version": result.skill_version, "_latency_ms": result.latency_ms}


@app.post("/extract-pdf")
async def extract_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    pdf_b64 = base64.standard_b64encode(contents).decode("utf-8")
    result = contract_extractor.run({"pdf_base64": pdf_b64})
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return {**result.data, "_skill": result.skill_name, "_version": result.skill_version, "_latency_ms": result.latency_ms}
