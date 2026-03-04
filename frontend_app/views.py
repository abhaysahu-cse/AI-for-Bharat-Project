# frontend_app/views.py
import json
import uuid
import os
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now

from .bedrock_service import BedrockService

# Very small in-memory demo store (dev only)
_DEMO_STORE = {
    "drafts": []
}

def _make_variant(vid, lang, text):
    return {"variant_id": vid, "lang": lang, "text": text, "image_prompt": ""}

@csrf_exempt
def drafts_list_create(request):
    """
    POST /api/drafts/  -> create a draft (calls Bedrock if enabled)
    GET  /api/drafts/  -> return recent drafts
    """
    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return HttpResponseBadRequest("invalid json")

        draft_id = str(uuid.uuid4())
        prompt = payload.get("prompt", "")
        languages = payload.get("languages", ["en", "hi"])

        # If USE_BEDROCK=true in env, call Bedrock via BedrockService
        if os.getenv("USE_BEDROCK", "false").lower() in ("1", "true", "yes"):
            try:
                bedrock = BedrockService()
                # THE FIX: generate_variants returns a list directly, so we just assign it to variants
                variants = bedrock.generate_variants(
                    prompt, 
                    languages, 
                    os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0") # Updated default model
                )
                
                # normalise variant IDs if model didn't provide them
                for i, v in enumerate(variants, start=1):
                    v.setdefault("variant_id", f"v{i}")
                    v.setdefault("image_prompt", "")
                
                draft = {
                    "draft_id": draft_id,
                    "prompt": prompt,
                    "variants": variants,
                    "status": "generated",
                    "created_at": now().isoformat(),
                }
            except Exception as e:
                # If model call failed, fall back to mock and inform client
                variants = []
                for i, lang in enumerate(languages, start=1):
                    vid = f"v{i}"
                    text = f"[FALLBACK {lang}] Could not call Bedrock: {str(e)}"
                    variants.append(_make_variant(vid, lang, text))
                draft = {
                    "draft_id": draft_id,
                    "prompt": prompt,
                    "variants": variants,
                    "status": "generated_fallback",
                    "created_at": now().isoformat(),
                }
        else:
            # mock behavior (existing)
            variants = []
            for i, lang in enumerate(languages, start=1):
                vid = f"v{i}"
                text = f"[MOCK {lang}] Generated text for prompt: {prompt}"
                variants.append(_make_variant(vid, lang, text))
            draft = {
                "draft_id": draft_id,
                "prompt": prompt,
                "variants": variants,
                "status": "generated",
                "created_at": now().isoformat(),
            }

        # keep small history (append)
        _DEMO_STORE["drafts"].insert(0, draft)
        # keep only last 20
        _DEMO_STORE["drafts"] = _DEMO_STORE["drafts"][:20]
        
        return JsonResponse(draft, status=201)

    # GET -> return small list
    if request.method == "GET":
        return JsonResponse(_DEMO_STORE["drafts"], safe=False)


@csrf_exempt
def draft_localize(request, draft_id):
    """
    POST /api/drafts/<draft_id>/localize
    Body: { "variant_id": "v1", "text": "new text", "target_lang": "hi" }
    """
    if request.method != "POST":
        return JsonResponse({"detail": "method not allowed"}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return HttpResponseBadRequest("invalid json")

    variant_id = payload.get("variant_id")
    new_text = payload.get("text")
    if not variant_id or new_text is None:
        return HttpResponseBadRequest("variant_id and text required")

    # find draft
    for d in _DEMO_STORE["drafts"]:
        if d["draft_id"] == draft_id:
            for v in d["variants"]:
                if v["variant_id"] == variant_id:
                    v["text"] = new_text
                    return JsonResponse({"ok": True, "variant": v})
            # variant not found
            return JsonResponse({"ok": False, "error": "variant not found"}, status=404)

    return JsonResponse({"ok": False, "error": "draft not found"}, status=404)


@csrf_exempt
def draft_schedule(request, draft_id):
    """
    POST /api/drafts/<draft_id>/schedule
    Body: { "variant_id": "v1", "platforms": ["instagram"], "publish_time": "ISO8601" }
    """
    if request.method != "POST":
        return JsonResponse({"detail": "method not allowed"}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return HttpResponseBadRequest("invalid json")

    # simple mock schedule - just return schedule_id
    schedule_id = str(uuid.uuid4())
    return JsonResponse({"ok": True, "schedule_id": schedule_id, "status": "scheduled"}, status=201)


def draft_analytics(request, draft_id):
    """
    GET /api/analytics/drafts/<draft_id>
    Returns mock analytics structure.
    """
    # simplest: return some KPIs
    resp = {
        "draft_id": draft_id,
        "kpis": {"impressions": 1234, "likes": 120, "engagement_rate": 0.032},
        "variants": [
            {"variant_id": "v1", "lang": "en", "impressions": 800, "likes": 80, "predicted_score": 71.2},
            {"variant_id": "v2", "lang": "hi", "impressions": 434, "likes": 40, "predicted_score": 65.1},
        ],
        "timeline": [
            {"date": "2026-03-01", "impressions": 100},
            {"date": "2026-03-02", "impressions": 200},
        ],
        "suggestions": ["Shorten the caption to 100 characters", "Add 2-3 popular hashtags"],
    }
    return JsonResponse(resp)