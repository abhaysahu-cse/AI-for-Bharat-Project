# lib/api_client.py
"""Robust API client used by the Streamlit frontend to talk to your Django backend.

Design goals:
- Retry transient network errors
- Central session and headers
- Mock-mode fallback (USE_MOCK env)
- Helpful logging + consistent exceptions
"""

from __future__ import annotations
import os
import time
import logging
from typing import Any, Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import API_BASE, API_KEY, TIMEOUT, USE_MOCK, VERIFY_SSL

log = logging.getLogger("lib.api_client")
log.setLevel(logging.INFO)

HEADERS = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
DEFAULT_TIMEOUT = TIMEOUT or 10.0

# Configure session with retries
_session: Optional[requests.Session] = None


class ApiClientError(Exception):
    """Raised for API client related errors (network, http, parsing)."""


def _build_session() -> requests.Session:
    global _session
    if _session is not None:
        return _session

    session = requests.Session()
    # sensible retry: backoff on idempotent methods and on connection errors
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        backoff_factor=0.8,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # default headers (can be overridden per-call)
    session.headers.update({"Content-Type": "application/json"})
    session.headers.update(HEADERS)

    _session = session
    return _session


def _request(method: str, path: str, **kwargs) -> Any:
    """
    Low-level request wrapper.
    Returns JSON on success, raises ApiClientError on problems.
    """
    session = _build_session()
    url = path if path.startswith("http") else f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
    timeout = kwargs.pop("timeout", DEFAULT_TIMEOUT)

    try:
        log.debug("API %s %s kwargs=%s", method.upper(), url, {k: v for k, v in kwargs.items() if k != "json"})
        resp = session.request(method=method, url=url, timeout=timeout, verify=VERIFY_SSL, **kwargs)
    except requests.RequestException as e:
        log.exception("Network error while calling %s %s", method.upper(), url)
        raise ApiClientError(f"Network error: {e}") from e

    # HTTP-level handling
    if not (200 <= resp.status_code < 300):
        body = None
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        log.error("HTTP %s error from %s: %s - %s", resp.status_code, url, resp.text[:200], body)
        raise ApiClientError(f"HTTP {resp.status_code} error from backend: {resp.text}")

    # parse JSON response
    try:
        return resp.json()
    except ValueError:
        log.error("Failed to parse JSON response from %s: %s", url, resp.text[:250])
        raise ApiClientError("Invalid JSON response from backend")


# ---------------------------
# High-level API methods used by Streamlit pages
# ---------------------------

def ping() -> bool:
    """Simple health check (calls /health or /ping if available)."""
    if USE_MOCK:
        return True
    try:
        _request("GET", "/health")
        return True
    except ApiClientError:
        # try alternate
        try:
            _request("GET", "/ping")
            return True
        except ApiClientError:
            return False


def post_create_draft(
    prompt: str,
    content_type: str = "instagram_post",
    tone: str = "casual",
    languages: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    generate_images: bool = False,              # ← NEW: triggers image per variant
) -> Dict[str, Any]:
    """
    Create a new draft via backend.
    Returns dict: {draft_id, prompt, variants: [{variant_id, lang, text,
    image_prompt, image_b64, image_url}], status}
    """
    if languages is None:
        languages = ["en", "hi"]
    if metadata is None:
        metadata = {}

    if USE_MOCK:
        # deterministic sample for demo & predictable tests
        return {
            "draft_id": f"mock-{int(time.time())%10000}",
            "prompt": prompt,
            "variants": [
                {
                    "variant_id": f"v{i+1}",
                    "lang": lang,
                    "text": f"{prompt} — short caption ({lang.upper()})",
                    "image_prompt": f"{lang} street food",
                    "image_b64": None,
                    "image_url": None,
                }
                for i, lang in enumerate(languages)
            ],
            "status": "generated"
        }

    payload = {
        "prompt":          prompt,
        "content_type":    content_type,
        "tone":            tone,
        "languages":       languages,
        "metadata":        metadata,
        "generate_images": generate_images,     # ← forwarded to Django views.py
    }
    return _request("POST", "/drafts/", json=payload)


def post_localize(draft_id: str, variant_id: str, text: str, target_lang: str) -> Dict[str, Any]:
    """
    Localize / edit a variant.
    Returns updated variant object.
    """
    if USE_MOCK:
        return {"ok": True, "variant": {"variant_id": variant_id, "lang": target_lang, "text": text}}

    path = f"/drafts/{draft_id}/localize"
    payload = {"variant_id": variant_id, "text": text, "target_lang": target_lang}
    return _request("POST", path, json=payload)


def post_schedule(draft_id: str, variant_id: str, platforms: List[str], publish_time: str,
                  timezone: Optional[str] = None, campaign: Optional[str] = None) -> Dict[str, Any]:
    """
    Schedule a variant for publishing.
    publish_time should be ISO-8601 string. timezone optional.
    Returns schedule object.
    """
    if USE_MOCK:
        return {"ok": True, "schedule_id": f"mock-s-{int(time.time())%10000}", "status": "scheduled"}

    payload = {
        "variant_id":   variant_id,
        "platforms":    platforms,
        "publish_time": publish_time,
        "timezone":     timezone,
        "campaign":     campaign
    }
    path = f"/drafts/{draft_id}/schedule"
    return _request("POST", path, json=payload)


def get_recent_drafts(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch recent drafts (for History page).
    """
    if USE_MOCK:
        return [post_create_draft(f"Sample prompt {i}", languages=["en", "hi"]) for i in range(1, 4)]

    path = f"/drafts/?limit={limit}"
    return _request("GET", path)


def get_analytics(draft_id: str) -> Dict[str, Any]:
    """
    Fetch analytics for a draft.
    Expected backend shape:
      { timeline: [...], variants: [...], kpis: {...}, suggestions: [...] }
    """
    if USE_MOCK:
        return {"timeline": [], "variants": [], "kpis": {"impressions": 0, "likes": 0, "engagement_rate": 0.0}, "suggestions": []}

    path = f"/analytics/drafts/{draft_id}"
    return _request("GET", path)


# convenience wrapper for debugging
def debug_fetch_all():
    """Run common endpoints and return a dict — useful for smoke tests."""
    return {
        "ping": ping(),
        "recent": get_recent_drafts(limit=3) if not USE_MOCK else get_recent_drafts(3)
    }