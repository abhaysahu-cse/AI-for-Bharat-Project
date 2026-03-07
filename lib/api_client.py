# lib/api_client.py
"""Robust API client for the BharatStudio Streamlit frontend.

Existing methods: ping, post_create_draft, post_localize, post_schedule,
                  get_recent_drafts, get_analytics
New methods:      post_video_script, post_hashtags, post_voice,
                  post_calendar, post_platform_variants
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

_session: Optional[requests.Session] = None


class ApiClientError(Exception):
    """Raised for API client related errors (network, http, parsing)."""


def _build_session() -> requests.Session:
    global _session
    if _session is not None:
        return _session
    session = requests.Session()
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
    session.headers.update({"Content-Type": "application/json"})
    session.headers.update(HEADERS)
    _session = session
    return _session


def _request(method: str, path: str, **kwargs) -> Any:
    session = _build_session()
    url = path if path.startswith("http") else f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
    timeout = kwargs.pop("timeout", DEFAULT_TIMEOUT)
    try:
        log.debug("API %s %s", method.upper(), url)
        resp = session.request(method=method, url=url, timeout=timeout, verify=VERIFY_SSL, **kwargs)
    except requests.RequestException as e:
        log.exception("Network error %s %s", method.upper(), url)
        raise ApiClientError(f"Network error: {e}") from e

    if not (200 <= resp.status_code < 300):
        body = None
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        log.error("HTTP %s from %s: %s", resp.status_code, url, resp.text[:200])
        raise ApiClientError(f"HTTP {resp.status_code} error from backend: {resp.text}")

    try:
        return resp.json()
    except ValueError:
        raise ApiClientError("Invalid JSON response from backend")


# ── EXISTING methods (unchanged) ──────────────────────────────────────────────

def ping() -> bool:
    if USE_MOCK:
        return True
    try:
        _request("GET", "/health")
        return True
    except ApiClientError:
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
    generate_images: bool = False,
) -> Dict[str, Any]:
    if languages is None:
        languages = ["en", "hi"]
    if metadata is None:
        metadata = {}

    if USE_MOCK:
        return {
            "draft_id": f"mock-{int(time.time()) % 10000}",
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
            "status": "generated",
        }

    payload = {
        "prompt": prompt,
        "content_type": content_type,
        "tone": tone,
        "languages": languages,
        "metadata": metadata,
        "generate_images": generate_images,
    }
    return _request("POST", "/drafts/", json=payload)


def post_localize(
    draft_id: str, variant_id: str, text: str, target_lang: str
) -> Dict[str, Any]:
    if USE_MOCK:
        return {"ok": True, "variant": {"variant_id": variant_id, "lang": target_lang, "text": text}}
    path = f"/drafts/{draft_id}/localize"
    return _request("POST", path, json={"variant_id": variant_id, "text": text, "target_lang": target_lang})


def post_schedule(
    draft_id: str,
    variant_id: str,
    platforms: List[str],
    publish_time: str,
    timezone: Optional[str] = None,
    campaign: Optional[str] = None,
) -> Dict[str, Any]:
    if USE_MOCK:
        return {"ok": True, "schedule_id": f"mock-s-{int(time.time()) % 10000}", "status": "scheduled"}
    payload = {
        "variant_id": variant_id,
        "platforms": platforms,
        "publish_time": publish_time,
        "timezone": timezone,
        "campaign": campaign,
    }
    return _request("POST", f"/drafts/{draft_id}/schedule", json=payload)


def get_recent_drafts(limit: int = 10) -> List[Dict[str, Any]]:
    if USE_MOCK:
        return [post_create_draft(f"Sample prompt {i}", languages=["en", "hi"]) for i in range(1, 4)]
    return _request("GET", f"/drafts/?limit={limit}")


def get_analytics(draft_id: str) -> Dict[str, Any]:
    if USE_MOCK:
        return {
            "timeline": [], "variants": [], "suggestions": [],
            "kpis": {"impressions": 0, "likes": 0, "engagement_rate": 0.0},
        }
    return _request("GET", f"/analytics/drafts/{draft_id}")


# ── NEW methods ───────────────────────────────────────────────────────────────

def post_video_script(
    prompt: str,
    languages: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    POST /api/generate/video_script/
    Returns {"prompt":"...","scripts":[{"lang":"en","video_script":"[...]"}],"status":"ok"}
    """
    if languages is None:
        languages = ["en"]

    if USE_MOCK:
        mock_scenes = [
            {"scene": 1, "duration_seconds": 6, "shot": f"Opening wide shot: {prompt[:40]}", "camera": "wide", "sfx": "ambient"},
            {"scene": 2, "duration_seconds": 8, "shot": "Close-up detail of main subject", "camera": "close-up", "sfx": ""},
            {"scene": 3, "duration_seconds": 6, "shot": "Action pan across scene", "camera": "pan", "sfx": ""},
            {"scene": 4, "duration_seconds": 6, "shot": "Closing shot — text overlay CTA", "camera": "wide", "sfx": "upbeat music"},
        ]
        import json
        scripts = [{"lang": lang, "video_script": json.dumps(mock_scenes)} for lang in languages]
        return {"prompt": prompt, "scripts": scripts, "status": "ok"}

    return _request("POST", "/generate/video_script/", json={"prompt": prompt, "languages": languages})


def post_hashtags(
    caption: str,
    platform: str = "instagram",
    languages: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    POST /api/generate/hashtags/
    Returns {"hashtags":[{"tag":"#X","score":85,"reason":"..."}],"predicted_engagement":82,...}
    """
    if languages is None:
        languages = ["en"]

    if USE_MOCK:
        words = [w.strip(".,!?#@") for w in caption.split() if len(w) > 4][:6]
        hashtags = [
            {"tag": f"#{w.capitalize()}", "score": max(50, 90 - i * 7), "reason": "derived from caption"}
            for i, w in enumerate(words)
        ]
        return {
            "caption": caption,
            "platform": platform,
            "hashtags": hashtags,
            "predicted_engagement": 72,
            "status": "ok",
        }

    return _request(
        "POST", "/generate/hashtags/",
        json={"caption": caption, "platform": platform, "languages": languages},
    )


def post_voice(
    text: str,
    lang: str = "en",
    voice: Optional[str] = None,
) -> Dict[str, Any]:
    """
    POST /api/generate/voice/
    Returns {"status":"ok","audio_base64":"<base64-mp3>","mime":"audio/mpeg"}
    """
    if USE_MOCK:
        return {
            "status": "ok",
            "audio_base64": None,
            "mime": "audio/mpeg",
            "note": "mock mode — no audio generated",
        }
    payload = {"text": text, "lang": lang}
    if voice:
        payload["voice"] = voice
    return _request("POST", "/generate/voice/", json=payload)


def post_calendar(
    topic: str,
    platforms: Optional[List[str]] = None,
    days: int = 7,
) -> Dict[str, Any]:
    """
    POST /api/generate/calendar/
    Returns {"topic":"...","start_date":"...","items":[{date,platform,caption,image_prompt,time}],"status":"ok"}
    """
    if platforms is None:
        platforms = ["instagram", "twitter"]

    if USE_MOCK:
        from datetime import date, timedelta
        default_times = {"instagram": "18:00", "twitter": "12:30", "youtube": "17:00",
                         "whatsapp": "20:00", "linkedin": "09:00"}
        today = date.today()
        items = [
            {
                "date": (today + timedelta(days=i)).isoformat(),
                "platform": platforms[i % len(platforms)],
                "caption": f"Day {i+1}: Engaging post about {topic}",
                "image_prompt": f"Visual for {topic}, day {i+1}",
                "time": default_times.get(platforms[i % len(platforms)], "18:00"),
            }
            for i in range(days)
        ]
        return {"topic": topic, "start_date": today.isoformat(), "items": items, "status": "ok"}

    return _request(
        "POST", "/generate/calendar/",
        json={"topic": topic, "platforms": platforms, "days": days},
    )


def post_platform_variants(
    prompt: str,
    languages: Optional[List[str]] = None,
    platforms: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    POST /api/generate/platform_variants/
    Returns {"platform_variants":[{platform,lang,caption,cta}],"status":"ok"}
    """
    if languages is None:
        languages = ["en"]
    if platforms is None:
        platforms = ["instagram", "twitter", "linkedin", "youtube"]

    if USE_MOCK:
        variants = [
            {
                "platform": p,
                "lang": l,
                "caption": f"[MOCK] {p.upper()} caption for: {prompt} ({l.upper()})",
                "cta": "Learn more",
            }
            for p in platforms
            for l in languages
        ]
        return {"platform_variants": variants, "status": "ok"}

    return _request(
        "POST", "/generate/platform_variants/",
        json={"prompt": prompt, "languages": languages, "platforms": platforms},
    )


def debug_fetch_all():
    return {"ping": ping(), "recent": get_recent_drafts(limit=3)}