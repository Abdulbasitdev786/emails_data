import os
import json
from typing import List, Dict
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

def llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY in .env file")
    client = Groq(api_key=api_key)
    return client

CLIENT = llm()

def llm_chat(model: str, messages: List[Dict[str, str]], temperature: float = 0.0, max_tokens: int = 800) -> str:
    resp = CLIENT.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()

CLASSIFY_PROMPT = """You are an email classifier.
Categories: invoice/bill, shipping/order, calendar_invite, newsletter, other.

Output JSON only:
{"category": "...", "confidence": 0.0-1.0}
"""

EXTRACTION_PROMPTS = {
    "invoice/bill": """Extract schema:
{"vendor":"", "invoice_total":"", "invoice_date":""}""",
    "shipping/order": """Extract schema:
{"order_id":"", "ship_date":"", "carrier":""}""",
    "calendar_invite": """Extract schema:
{"event_title":"", "event_date":"", "organizer":""}""",
    "newsletter": """Extract schema:
{"newsletter_name":"", "topic":"", "date":""}""",
    "other": """Extract schema:
{"summary":""}""",
}

VERIFY_PROMPT = """Check the JSON.
- Does it match schema? (true/false)
- If not, fix it.

Output only JSON:
{"schema_ok": true/false, "data": {...}}"""

def classify_email(email_text: str, model: str) -> Dict:
    messages = [
        {"role": "system", "content": CLASSIFY_PROMPT},
        {"role": "user", "content": email_text}
    ]
    raw = llm_chat(model, messages)
    try:
        return json.loads(raw)
    except:
        return {"category": "other", "confidence": 0.0}

def extract_email(email_text: str, category: str, model: str) -> Dict:
    schema_prompt = EXTRACTION_PROMPTS.get(category, EXTRACTION_PROMPTS["other"])
    messages = [
        {"role": "system", "content": schema_prompt},
        {"role": "user", "content": email_text}
    ]
    raw = llm_chat(model, messages)
    try:
        return json.loads(raw)
    except:
        return {}

def verify_schema(extracted: Dict, model: str) -> Dict:
    messages = [
        {"role": "system", "content": VERIFY_PROMPT},
        {"role": "user", "content": json.dumps(extracted)}
    ]
    raw = llm_chat(model, messages)
    try:
        return json.loads(raw)
    except:
        return {"schema_ok": False, "data": extracted}

def process_emails(in_file: str, out_file: str, model: str):
    with open(in_file, "r", encoding="utf-8") as f:
        emails = json.load(f)

    with open(out_file, "w", encoding="utf-8") as out:
        for idx, email in enumerate(emails):
            email_text = email.get("body", "")
            email_id = email.get("id", f"email_{idx}")

            classification = classify_email(email_text, model)
            category = classification.get("category", "other")

            extracted = extract_email(email_text, category, model)
            verified = verify_schema(extracted, model)

            result = {
                "email_id": email_id,
                "category": category,
                "confidence": classification.get("confidence", 0.0),
                "schema_ok": verified.get("schema_ok", False),
                "data": verified.get("data", {})
            }

            out.write(json.dumps(result) + "\n")
            print(f"[{idx+1}] Processed {email_id} → {category}")

if __name__ == "__main__":
    MODEL = os.getenv("MODEL_CLASSIFY", "openai/gpt-oss-120b")
    process_emails("emails.json", "result.jsonl", MODEL)
