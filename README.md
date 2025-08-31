Project: Agentic AI — Email extraction, classification & verification pipeline

Purpose: Turn messy inbox emails into clean, structured JSON for analysis or downstream systems

Dataset included:

emails.json — 55 redacted sample emails
emails.jsonl — same dataset, one JSON object per line (ready for pipelines)

What the pipeline does (high-level):

Redacts sensitive details (emails, phone numbers, card-like numbers)

Classifies each email into one of: invoice/bill, shipping/order, calendar_invite, newsletter, other

Extracts structured fields per category (invoice totals, order IDs, meeting times, etc.)

Runs a verification/fix step (self-check → correct common schema problems)

Outputs one JSONL line per email:
{"email_id":"...","category":"...","confidence":0.0,"schema_ok":true/false,"data":{...}}

Why this is useful:

Saves time: automates manual reading + tagging of emails

Makes data analysis possible: invoices & orders become searchable, sortable, and aggregatable

Safer: PII is redacted before analysis or sharing

Included prompts:

prompts.md contains the exact classification, per-category extraction, and verification prompts used in experiments

Prompts are structured: role headers, delimiters, and strict JSON-only output instructions

Files in this repo (what to open first):

index.py — main pipeline (Groq-compatible variant included)

emails.json — demo dataset (human-like, redacted; contains “Abdul Basit” in greetings)

emails.jsonl — newline-delimited version for streaming/processing

prompts.md — all prompt templates used for classification/extraction/verification

report.md — short summary of results, failure cases, and fixes

Quick start (run locally):

Install dependencies: pip install groq python-dotenv

Create .env with your Groq key:

GROQ_API_KEY=your_key_here

optionally set models: MODEL_CLASSIFY, MODEL_EXTRACT, MODEL_VERIFY (defaults are in index.py)

Run the pipeline:

python index.py --in emails.json --out emails.jsonl

Add --limit 10 to test with a subset

Model guidance & pitfalls:

Use a currently supported Groq model (openai/gpt-oss-120b)
