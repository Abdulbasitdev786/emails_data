import os
import json
import re
from typing import Dict
from dotenv import load_dotenv
from groq import Groq
from bs4 import BeautifulSoup
import unicodedata

load_dotenv()

def llm_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY in .env file")
    return Groq(api_key=api_key)

CLIENT = llm_client()

def llm_chat(model: str, messages: list, temperature: float = 0.0, max_tokens: int = 1024) -> str:
    resp = CLIENT.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()

def clean_content(content: str) -> str:
    content = ''.join(c for c in unicodedata.normalize('NFKC', content) if unicodedata.category(c) not in ['Cf', 'Cc', 'Cn'])
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'(\d)\s*([.,]?\s*\d)', lambda m: m.group(1) + m.group(2).replace(' ', ''), content)
    return content.strip()

def get_email_content(html_path: str, text_path: str) -> str:
    content = ""
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            content = soup.get_text(separator=' ')
    elif os.path.exists(text_path):
        with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    return clean_content(content)

CLASSIFY_PROMPT = """You are an email template classifier for specific merchants.
Templates: stripe_udemyx_receipt, google_play_subscription, shophive_order_confirmation, meta_instagram_receipt, other.

Ignore decoy sections like Draft/Preview/Proforma/Projected/Forecast.

Output JSON only:
{"template": "one of the above", "confidence": 0.0-1.0}
"""

EXTRACTION_PROMPTS = {
    "stripe_udemyx_receipt": """Extract exactly this schema from the email. Ignore decoys (Draft/Preview/Proforma/Projected/Forecast). Use real values from 'Amount paid'.
Keep dates/strings verbatim (including punctuation/case). Numbers as numbers. Arrays as lists even if single.

Schema:
{
  "merchant": "UdemyX",
  "receipt_number": "####-####",
  "amount_paid_usd": 0.00,
  "date_paid": "Mon DD, YYYY",
  "payment_last4": "####",
  "line_items": [
    { "description": "string", "period": "YYYY-MM-DD—YYYY-MM-DD", "amount_usd": 0.00 }
  ]
}

Output only JSON.""",

    "google_play_subscription": """Extract exactly this schema from the email. Ignore decoys (Draft/Preview/Proforma/Projected/Forecast). Use real values from 'Total'.
Keep dates/strings verbatim (including punctuation/case). Numbers as numbers. Booleans as booleans. Arrays as lists even if single.

Schema:
{
  "merchant": "Google Play",
  "order_number": "SOP.xxxx-xxxx-xxxx-xxxxx",
  "order_date": "Mon DD, YYYY HH:MM:SS AM/PM GMT+5",
  "account_email": "name@domain",
  "item": "string",
  "price_monthly_rs": 0.00,
  "price_yearly_rs": 0.00,
  "payment_method": "Brand-####",
  "auto_renew": true,
  "tax_rs": 0.00,
  "total_rs": 0.00
}

Output only JSON.""",

    "shophive_order_confirmation": """Extract exactly this schema from the email. Ignore decoys (Draft/Preview/Proforma/Projected/Forecast). Use real values from 'Grand Total'.
Keep dates/strings verbatim (including punctuation/case). Numbers as numbers. Arrays as lists even if single.

Schema:
{
  "merchant": "Shophive",
  "order_id": "string",
  "placed_at": "Mon DD, YYYY, HH:MM:SS AM/PM",
  "customer_name": "string",
  "billing_address": "line1; city, postcode; Pakistan",
  "shipping_address": "line1; city, postcode; Pakistan",
  "phone": "03XXXXXXXXX",
  "payment_method": "Cash On Delivery",
  "cod_fee_rs": 0.00,
  "items": [
    { "name": "string", "sku": "string", "qty": 0, "unit_price_rs": 0.00, "line_total_rs": 0.00 }
  ],
  "shipping_rs": 0.00,
  "subtotal_rs": 0.00,
  "grand_total_rs": 0.00
}

Output only JSON.""",

    "meta_instagram_receipt": """Extract exactly this schema from the email. Ignore decoys (Draft/Preview/Proforma/Projected/Forecast). Use real values from 'Amount billed'.
Keep dates/strings verbatim (including punctuation/case). Numbers as numbers. Arrays as lists even if single.

Schema:
{
  "merchant": "Meta Ads",
  "amount_billed_pkr": 0.00,
  "date_range": "D Mon YYYY, HH:MM - D Mon YYYY, HH:MM",
  "product_type": "Meta ads",
  "payment_method": "Brand · ####",
  "reference": "XXXXXXXXXX",
  "campaigns": [
    { "title": "string", "amount_pkr": 0.00, "result": "Results: N,NNN Impressions" }
  ],
  "total_pkr": 0.00
}

Output only JSON.""",

    "other": """This email doesn't match any template. Output empty schema JSON: {}"""
}

VERIFY_PROMPT = """Check the extracted JSON against the schema for {{template}}.
- Types match? (numbers as numbers, booleans as booleans, strings verbatim)
- Dates/strings unchanged from email?
- Arrays present even if single?
- If issues, fix using email context, but do not invent data.

Output JSON only:
{"schema_ok": true/false, "pred": {...}}"""

def classify_template(email_content: str, model: str) -> Dict:
    messages = [
        {"role": "system", "content": CLASSIFY_PROMPT},
        {"role": "user", "content": email_content}
    ]
    raw = llm_chat(model, messages)
    try:
        return json.loads(raw)
    except:
        return {"template": "other", "confidence": 0.0}

def extract_data(email_content: str, template: str, model: str) -> Dict:
    prompt = EXTRACTION_PROMPTS.get(template, EXTRACTION_PROMPTS["other"])
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": email_content}
    ]
    raw = llm_chat(model, messages)
    try:
        return json.loads(raw)
    except:
        return {}

def verify_extraction(extracted: Dict, template: str, email_content: str, model: str) -> Dict:
    verify_filled = VERIFY_PROMPT.replace("{{template}}", template)
    messages = [
        {"role": "system", "content": verify_filled},
        {"role": "user", "content": f"Extracted: {json.dumps(extracted)}\nEmail: {email_content}"}
    ]
    raw = llm_chat(model, messages)
    try:
        return json.loads(raw)
    except:
        return {"schema_ok": False, "pred": extracted}

def process_email_pairs(email_dir: str, out_file: str, model: str):
    with open(out_file, "w", encoding="utf-8") as out:
        email_id = 1
        files = sorted([f for f in os.listdir(email_dir) if f.endswith('.html') or f.endswith('.txt')])
        processed = set()
        for filename in files:
            base, ext = os.path.splitext(filename)
            if base in processed:
                continue
            html_path = os.path.join(email_dir, f"{base}.html")
            text_path = os.path.join(email_dir, f"{base}.txt")
            content = get_email_content(html_path, text_path)
            if not content:
                continue

            classification = classify_template(content, model)
            template = classification.get("template", "other")

            extracted = extract_data(content, template, model)
            verified = verify_extraction(extracted, template, content, model)

            result = {
                "id": email_id,
                "template": template,
                "pred": verified.get("pred", {})
            }

            out.write(json.dumps(result) + "\n")
            print(f"Processed {base} → {template}")
            processed.add(base)
            email_id += 1

if __name__ == "__main__":
    MODEL = os.getenv("MODEL_CLASSIFY", "openai/gpt-oss-120b")
    process_email_pairs("emails/", "predictions.jsonl", MODEL)