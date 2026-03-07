# frontend_app/views.py
"""
BharatStudio Django views.
Existing:  POST /api/drafts/
New:       POST /api/generate/video_script/
           POST /api/generate/hashtags/
           POST /api/generate/calendar/
           POST /api/generate/platform_variants/
           POST /api/generate/voice/
"""

import os
import json
import logging
import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .bedrock_service import BedrockService
from .image_service import generate_image

logger = logging.getLogger(__name__)

_USE_BEDROCK = os.getenv("USE_BEDROCK", "false").lower() in ("1", "true", "yes")
_BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "eu.amazon.nova-lite-v1:0")


# ── helpers ──────────────────────────────────────────────────────────────────

def _json_body(request):
    """Parse JSON body; raise ValueError on bad JSON."""
    return json.loads(request.body.decode("utf-8"))


def _bedrock():
    return BedrockService()


def _attach_image_to_variant(variant: dict) -> dict:
    """
    Call image_service for this variant's image_prompt.
    Adds image_b64 and image_url keys (may be None on failure).
    """
    prompt = variant.get("image_prompt") or variant.get("text", "")
    try:
        result = generate_image(prompt)
        variant["image_b64"] = result.get("b64")
        variant["image_url"] = result.get("url")
        logger.debug(
            "generate_image done — source=%s b64_len=%s",
            result.get("source"),
            len(result.get("b64") or ""),
        )
    except Exception as exc:
        logger.warning("generate_image failed for variant %s: %s", variant.get("variant_id"), exc)
        variant["image_b64"] = None
        variant["image_url"] = None
    return variant


# ── EXISTING: POST /api/drafts/ ───────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def create_draft(request):
    """
    Create a new draft.

    Body:
      { "prompt": "...", "languages": ["en","hi"],
        "content_type": "instagram_post", "tone": "casual",
        "generate_images": false }

    Response 201:
      { "draft_id": "...", "prompt": "...", "variants": [...], "status": "generated" }
    """
    try:
        data = _json_body(request)
    except (ValueError, KeyError) as exc:
        return JsonResponse({"status": "error", "error": f"Bad JSON: {exc}"}, status=400)

    prompt = data.get("prompt", "").strip()
    if not prompt:
        return JsonResponse({"status": "error", "error": "prompt is required"}, status=400)

    languages = data.get("languages", ["en", "hi"])
    generate_images = bool(data.get("generate_images", False))

    import uuid, time

    if not _USE_BEDROCK:
        # deterministic mock
        variants = [
            {
                "variant_id": f"v{i+1}",
                "lang": lang,
                "text": f"{prompt} — {lang.upper()} caption",
                "image_prompt": f"Vivid scene: {prompt}",
                "image_b64": None,
                "image_url": None,
            }
            for i, lang in enumerate(languages)
        ]
        draft = {
            "draft_id": f"mock-{int(time.time()) % 100000}",
            "prompt": prompt,
            "variants": variants,
            "status": "generated_mock",
        }
        logger.debug("create_draft mock: draft_id=%s", draft["draft_id"])
        return JsonResponse(draft, status=201)

    try:
        service = _bedrock()
        variants = service.generate_variants(prompt, languages, _BEDROCK_MODEL_ID)

        if generate_images:
            variants = [_attach_image_to_variant(v) for v in variants]
        else:
            for v in variants:
                v.setdefault("image_b64", None)
                v.setdefault("image_url", None)

        draft = {
            "draft_id": str(uuid.uuid4()),
            "prompt": prompt,
            "variants": variants,
            "status": "generated",
        }
        logger.debug("create_draft ok: draft_id=%s variants=%d", draft["draft_id"], len(variants))
        return JsonResponse(draft, status=201)

    except Exception as exc:
        logger.exception("create_draft error")
        return JsonResponse({"status": "error", "error": str(exc)}, status=500)


# ── NEW A: POST /api/generate/video_script/ ───────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def generate_video_script(request):
    """
    Generate a short video shot-list script.

    Body:
      { "prompt": "Monsoon street food in Patna", "languages": ["en","hi"] }

    Response 200:
      { "prompt": "...",
        "scripts": [{"lang":"en","video_script":"[{...}]"}, ...],
        "status": "ok" }
    """
    try:
        data = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"status": "error", "error": f"Bad JSON: {exc}"}, status=400)

    prompt = data.get("prompt", "").strip()
    languages = data.get("languages", ["en"])
    if not prompt:
        return JsonResponse({"status": "error", "error": "prompt is required"}, status=400)

    logger.debug("generate_video_script: prompt=%s languages=%s", prompt[:80], languages)

    try:
        service = _bedrock()
        results = service.generate_video_script(prompt, languages)
        # results = [{"lang": "en", "scenes": [...]}]
        scripts = [
            {"lang": r["lang"], "video_script": json.dumps(r.get("scenes", []), ensure_ascii=False)}
            for r in results
        ]
        return JsonResponse({"prompt": prompt, "scripts": scripts, "status": "ok"})
    except Exception as exc:
        logger.exception("generate_video_script error")
        return JsonResponse({"status": "error", "error": str(exc)}, status=500)


# ── NEW B: POST /api/generate/hashtags/ ───────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def generate_hashtags(request):
    """
    Generate platform-optimised hashtags with engagement score.

    Body:
      { "caption": "...", "platform": "instagram", "languages": ["en"] }

    Response 200:
      { "caption": "...", "platform": "instagram",
        "hashtags": [{"tag":"#X","score":85,"reason":"..."}],
        "predicted_engagement": 82, "status": "ok" }
    """
    try:
        data = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"status": "error", "error": f"Bad JSON: {exc}"}, status=400)

    caption = data.get("caption", "").strip()
    platform = data.get("platform", "instagram")
    languages = data.get("languages", ["en"])
    if not caption:
        return JsonResponse({"status": "error", "error": "caption is required"}, status=400)

    logger.debug("generate_hashtags: platform=%s caption_len=%d", platform, len(caption))

    try:
        service = _bedrock()
        result = service.generate_hashtags(caption, platform, languages)
        # add score field per tag (use index-based heuristic if not present)
        hashtags = result.get("hashtags", [])
        for i, h in enumerate(hashtags):
            h.setdefault("score", max(50, 95 - i * 5))
        return JsonResponse({
            "caption": caption,
            "platform": platform,
            "hashtags": hashtags,
            "predicted_engagement": result.get("predicted_engagement", 70),
            "status": "ok",
        })
    except Exception as exc:
        logger.exception("generate_hashtags error")
        return JsonResponse({"status": "error", "error": str(exc)}, status=500)


# ── NEW C: POST /api/generate/voice/ ─────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def generate_voice(request):
    """
    Convert caption to MP3 audio via Amazon Polly.

    Body:
      { "text": "...", "lang": "hi", "voice": "Raveena" }

    Response 200:
      { "status": "ok", "audio_base64": "<base64-mp3>", "mime": "audio/mpeg" }
    """
    try:
        data = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"status": "error", "error": f"Bad JSON: {exc}"}, status=400)

    text = data.get("text", "").strip()
    lang = data.get("lang", "en")
    voice = data.get("voice") or ("Raveena" if lang == "hi" else "Joanna")

    if not text:
        return JsonResponse({"status": "error", "error": "text is required"}, status=400)

    logger.debug("generate_voice: lang=%s voice=%s text_len=%d", lang, voice, len(text))

    if not _USE_BEDROCK:
        # Return a 1-second silent MP3 stub (44 bytes minimal valid)
        silent_b64 = (
            "SUQzAwAAAAAAFlRJVDIAAAAMAAAAU2lsZW5jZSAxcwAA"
            "//uSwAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAAB"
        )
        return JsonResponse({
            "status": "ok",
            "audio_base64": silent_b64,
            "mime": "audio/mpeg",
            "note": "mock — Polly disabled (USE_BEDROCK=false)",
        })

    try:
        from .tts_service import synthesize_speech
        audio_bytes = synthesize_speech(text, voice=voice, output_format="mp3")
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return JsonResponse({"status": "ok", "audio_base64": audio_b64, "mime": "audio/mpeg"})
    except Exception as exc:
        logger.exception("generate_voice error")
        return JsonResponse({"status": "error", "error": str(exc)}, status=500)


# ── NEW D: POST /api/generate/calendar/ ──────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def generate_calendar(request):
    """
    Generate a content calendar.

    Body:
      { "topic": "...", "platforms": ["instagram","twitter"], "days": 7 }

    Response 200:
      { "topic": "...", "start_date": "YYYY-MM-DD",
        "items": [{date, platform, caption, image_prompt, time},...],
        "status": "ok" }
    """
    try:
        data = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"status": "error", "error": f"Bad JSON: {exc}"}, status=400)

    topic = data.get("topic", "").strip()
    platforms = data.get("platforms", ["instagram", "twitter"])
    days = int(data.get("days", 7))
    if not topic:
        return JsonResponse({"status": "error", "error": "topic is required"}, status=400)
    days = max(1, min(days, 30))

    logger.debug("generate_calendar: topic=%s days=%d platforms=%s", topic[:80], days, platforms)

    try:
        from datetime import date
        service = _bedrock()
        items = service.generate_content_calendar(topic, platforms, days)
        return JsonResponse({
            "topic": topic,
            "start_date": date.today().isoformat(),
            "items": items,
            "status": "ok",
        })
    except Exception as exc:
        logger.exception("generate_calendar error")
        return JsonResponse({"status": "error", "error": str(exc)}, status=500)


# ── NEW E: POST /api/generate/platform_variants/ ─────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def generate_platform_variants(request):
    """
    Generate platform-optimised captions per platform x language.

    Body:
      { "prompt": "...", "languages": ["en","hi"],
        "platforms": ["instagram","twitter","linkedin","youtube"] }

    Response 200:
      { "platform_variants": [{platform, lang, caption, cta},...],
        "status": "ok" }
    """
    try:
        data = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"status": "error", "error": f"Bad JSON: {exc}"}, status=400)

    prompt = data.get("prompt", "").strip()
    languages = data.get("languages", ["en"])
    platforms = data.get("platforms", ["instagram", "twitter", "linkedin", "youtube"])
    if not prompt:
        return JsonResponse({"status": "error", "error": "prompt is required"}, status=400)

    logger.debug(
        "generate_platform_variants: prompt=%s languages=%s platforms=%s",
        prompt[:80], languages, platforms,
    )

    try:
        service = _bedrock()
        variants = service.generate_platform_variants(prompt, languages, platforms)
        return JsonResponse({"platform_variants": variants, "status": "ok"})
    except Exception as exc:
        logger.exception("generate_platform_variants error")
        return JsonResponse({"status": "error", "error": str(exc)}, status=500)