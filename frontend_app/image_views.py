# frontend_app/image_views.py
"""
POST /api/images/

Standalone image generation endpoint.
Accepts a prompt and optional model/S3 settings; returns b64 or S3 URL.
"""
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import image_service

logger = logging.getLogger(__name__)


@csrf_exempt
def generate_image_view(request):
    """
    POST /api/images/

    Request body (JSON):
        {
            "prompt":      "Close-up of steaming samosa on a rainy day",
            "model":       "amazon.titan-image-generator-v1",  // optional
            "save_to_s3":  true                                 // optional, default true
        }

    Response (success):
        {
            "ok":     true,
            "b64":    "<base64 PNG>",
            "s3_url": "https://...",   // null if not uploaded
            "s3_key": "images/...",    // null if not uploaded
            "model_id": "..."
        }

    Response (error):
        { "ok": false, "error": "..." }
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    # ── Parse body ──────────────────────────────────────────────────────────────
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON body"}, status=400)

    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        return JsonResponse(
            {"ok": False, "error": "'prompt' field is required"}, status=400
        )

    model_id    = payload.get("model") or None
    save_to_s3  = payload.get("save_to_s3", True)

    # ── Generate ─────────────────────────────────────────────────────────────────
    logger.info("Image generation request: model=%s prompt='%s'", model_id, prompt[:80])
    result = image_service.generate_image(
        prompt=prompt,
        model_id=model_id,
        save_to_s3=bool(save_to_s3),
    )

    status_code = 200 if result.get("ok") else 500
    return JsonResponse(result, status=status_code)