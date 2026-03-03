# backend/frontend_app/bedrock_service.py
import os
import json
import uuid
import random
from datetime import datetime

USE_BEDROCK = os.getenv("USE_BEDROCK", "false").lower() in ("1","true","yes")

if USE_BEDROCK:
    import boto3
    bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION","us-east-1"))

def _mock_variants(prompt, languages, tone, content_type):
    # Return a simple predictable mock so Streamlit can demo without backend
    variants = []
    for i,lang in enumerate(languages, start=1):
        vid = f"v{i}"
        text = f"[MOCK {lang}] {prompt[:120]} — tone:{tone}, type:{content_type}"
        image_prompt = f"Thumbnail for {prompt} in {lang}"
        variants.append({"variant_id": vid, "lang": lang, "text": text, "image_prompt": image_prompt})
    return variants

def call_bedrock_for_json(model_id, body_dict):
    """
    Call Bedrock model endpoint and return parsed json. Assumes model returns JSON string.
    """
    body_bytes = json.dumps(body_dict).encode("utf-8")
    resp = bedrock.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=body_bytes
    )
    raw = resp["body"].read().decode("utf-8")
    # model should have returned JSON text; try parse
    try:
        return json.loads(raw)
    except Exception:
        # fallback: return raw string wrapped
        return {"raw": raw}

def generate_variants(prompt, languages=None, tone="casual", content_type="instagram_post"):
    languages = languages or ["en"]
    if not USE_BEDROCK:
        return _mock_variants(prompt, languages, tone, content_type)

    # Example: request that the model returns JSON with variants array
    model_id = os.getenv("BEDROCK_MODEL_ID", "amazon.titan-text-express-v1")
    prompt_template = {
        "instruction": "Generate content variants as JSON. EXACTLY return a JSON object like {\"variants\":[{...},...]}",
        "prompt": {
            "prompt_text": prompt,
            "tone": tone,
            "content_type": content_type,
            "languages": languages
        }
    }
    resp = call_bedrock_for_json(model_id, prompt_template)
    # Validate resp shape
    if isinstance(resp, dict) and "variants" in resp:
        return resp["variants"]
    # fallback to mock
    return _mock_variants(prompt, languages, tone, content_type)