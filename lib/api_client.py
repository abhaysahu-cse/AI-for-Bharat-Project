# lib/api_client.py
import requests
from .config import API_BASE, API_KEY, TIMEOUT, USE_MOCK
import logging

log = logging.getLogger("api_client")
HEADERS = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}

def post_create_draft(prompt, content_type="instagram_post", tone="casual", languages=None):
    if languages is None:
        languages = ["en", "hi"]
    if USE_MOCK:
        return {
            "draft_id": "mock-d1",
            "prompt": prompt,
            "variants": [
                {"variant_id": "v1", "lang": "en", "text": f"{prompt} — short caption (EN)", "image_prompt": "street food close-up"},
                {"variant_id": "v2", "lang": "hi", "text": f"{prompt} — संक्षिप्त कैप्शन (HI)", "image_prompt": "सड़क का खाना"}
            ],
            "status": "generated"
        }
    try:
        resp = requests.post(f"{API_BASE}/drafts/", json={
            "prompt": prompt, "content_type": content_type, "tone": tone, "languages": languages
        }, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log.exception("Create draft failed")
        raise

def post_localize(draft_id, variant_id, text, target_lang):
    if USE_MOCK:
        return {"ok": True, "variant": {"variant_id": variant_id, "lang": target_lang, "text": text}}
    resp = requests.post(f"{API_BASE}/drafts/{draft_id}/localize", json={
        "variant_id": variant_id, "text": text, "target_lang": target_lang
    }, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def post_schedule(draft_id, variant_id, platforms, publish_time):
    if USE_MOCK:
        return {"ok": True, "schedule_id": "mock-s1", "status": "scheduled"}
    resp = requests.post(f"{API_BASE}/drafts/{draft_id}/schedule", json={
        "variant_id": variant_id, "platforms": platforms, "publish_time": publish_time
    }, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def get_recent_drafts(limit=10):
    if USE_MOCK:
        return [post_create_draft(f"Sample prompt {i}") for i in range(1,4)]
    resp = requests.get(f"{API_BASE}/drafts/?limit={limit}", headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def get_analytics(draft_id):
    if USE_MOCK:
        return {"impressions": 1200, "likes": 150, "shares": 10, "suggestions": ["Shorten caption for Tamil"] }
    resp = requests.get(f"{API_BASE}/analytics/drafts/{draft_id}", headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()
