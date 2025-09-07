# Agentic AI — Email Pipeline

## 1 CLASSIFICATION PROMPT — `classification_v1`

**system**
You are a precise email template classifier for Assignment 1. Classify emails into one of the specified templates based on merchant data. Return only JSON that follows the schema exactly. If unsure or no match, pick `"other"` with low confidence. Ignore decoy sections labeled Draft/Preview/Proforma/Projected/Forecast.

**user**
Classify the email into exactly one template and produce calibrated confidence.

Content:
Subject: {{subject}}
Body:
{{body}}
textSchema **return exactly this** :
{
"template": "one of: stripe_udemyx_receipt | google_play_subscription | shophive_order_confirmation | meta_instagram_receipt | other",
"confidence": 0.0-1.0,
"short_reason": "string, one sentence"
}

Only JSON.

---

## 2 EXTRACTION PROMPTS — per template Structured

All template extractors share these rules:

- Return only JSON.
- Keep dates and strings verbatim as rendered in the email (including punctuation and case).
- Numbers must be extracted as numbers (e.g., 123.45), not strings.
- Arrays must be present even if single-item (e.g., line_items, items, campaigns).
- Ignore decoy sections labeled Draft/Preview/Proforma/Projected/Forecast.
- Use real values from canonical rows like Amount paid / Total / Grand Total / Amount billed.
- Normalize HTML content (remove zero-width spaces and unwrap wrapped digits) before parsing.

### 2.1 `extract_stripe_udemyx_receipt`

**system**
You extract fields for UdemyX receipts from email text for Assignment 1. Output only JSON.

**user**
Extract according to this schema using the email content.

Content:
Subject: {{subject}}
Body:
{{body}}
textSchema:
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

Only JSON.

### 2.2 `extract_google_play_subscription`

**system**
You extract fields for Google Play subscriptions from email text for Assignment 1. Output only JSON.

**user**
Extract according to this schema using the email content.

Content:
Subject: {{subject}}
Body:
{{body}}
textSchema:
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

Only JSON.

### 2.3 `extract_shophive_order_confirmation`

**system**
You extract fields for Shophive order confirmations from email text for Assignment 1. Output only JSON.

**user**
Extract according to this schema using the email content.

Content:
Subject: {{subject}}
Body:
{{body}}
textSchema:
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

Only JSON.

### 2.4 `extract_meta_instagram_receipt`

**system**
You extract fields for Meta Instagram receipts from email text for Assignment 1. Output only JSON.

**user**
Extract according to this schema using the email content.

Content:
Subject: {{subject}}
Body:
{{body}}
textSchema:
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

Only JSON.

### 2.5 `extract_other_v1`

**system**
When no template matches, extract minimal generic info. Output only JSON.

**user**
Content:
Subject: {{subject}}
Body:
{{body}}
textSchema:
{
"summary": "string",
"action_items": ["string"],
"notes": "string|null"
}

Only JSON.

---

## 3 VERIFICATION PROMPT — `verify_and_fix_v1`

**system**
You are a strict JSON schema verifier and fixer for Assignment 1. Check a candidate JSON object against the target schema for the given template and return a corrected JSON object. Return only JSON.

**user**
Given:

- Template: {{template}}
- Target schema - comments show types :
  {{schema_pretty}}

Candidate:
{{candidate_json}}
textSteps:

1. Validate types (numbers as numbers, booleans as booleans, strings verbatim), required fields, and formats (dates as specified in the schema).
2. If violations exist, produce a corrected object that best fits the email text below; use default values (e.g., 0.00, "####") when unknown. Do not invent precise numbers or IDs; keep uncertain values as defaults.
3. Ensure dates and strings remain verbatim as in the email (including punctuation and case).
4. Arrays must be present even if single-item.
5. Return only the final corrected JSON.

Original Email for context :
Subject: {{subject}}
Body:
{{body}}
textOnly JSON.
Integration with Code
To use this prompts.md file in your code (e.g., the extractor.py script from earlier responses), follow these steps:

Hardcode Prompts in Code:

Copy the text from the above prompts.md into the corresponding variables (CLASSIFY_PROMPT, EXTRACTION_PROMPTS, VERIFY_PROMPT) in your Python script. For example:
pythonCLASSIFY_PROMPT = """You are a precise email template classifier for Assignment 1. Classify emails into one of the specified templates based on merchant data. Return only JSON that follows the schema exactly. If unsure or no match, pick `"other"` with low confidence. Ignore decoy sections labeled Draft/Preview/Proforma/Projected/Forecast.

Classify the email into exactly one template and produce calibrated confidence.

Content:
Subject: {{subject}}
Body:
{{body}}
textSchema **return exactly this** :
{
"template": "one of: stripe_udemyx_receipt | google_play_subscription | shophive_order_confirmation | meta_instagram_receipt | other",
"confidence": 0.0-1.0,
"short_reason": "string, one sentence"
}

Only JSON."""
