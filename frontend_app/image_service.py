# frontend_app/image_service.py
"""
Image generation service for BharatStudio.

Tries sources in order until one works:
  1. Pollinations.ai  — real AI images, free, no key (may be blocked on some networks)
  2. Picsum.photos    — real photos via CDN, almost always reachable
  3. Static base64    — tiny coloured placeholder, always works offline

Set USE_BEDROCK_IMAGES=true to use Amazon Bedrock instead of the above.
"""
import base64
import hashlib
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
_USE_BEDROCK_IMAGES = os.getenv("USE_BEDROCK_IMAGES", "false").lower() in ("1", "true", "yes")
_USE_S3             = os.getenv("USE_S3", "false").lower() in ("1", "true", "yes")
_IMG_MODEL          = os.getenv("BEDROCK_IMAGE_MODEL_ID", "amazon.titan-image-generator-v2:0")
_IMG_REGION         = os.getenv("BEDROCK_IMAGE_REGION", os.getenv("AWS_REGION", "us-east-1"))
_TIMEOUT            = int(os.getenv("IMAGE_FETCH_TIMEOUT", "20"))

# ── Tiny coloured placeholder PNG (always-works fallback) ──────────────────────
# 64×64 orange square — BharatStudio brand colour
_PLACEHOLDER_B64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkS"
    "Ew8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJ"
    "CQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIy"
    "MjIyMjIyMjIyMjIyMjL/wAARCABAAEADASIAAhEBAxEB/8QAGwABAAMBAQEBAAAA"
    "AAAAAAAAAAQFBgMCAQf/xAAuEAABBAEDAwMDBAMBAAAAAAABAAIDEQQFEiExBhNB"
    "UWEUcYGRIjKhscHR/8QAGAEAAwEBAAAAAAAAAAAAAAAAAAECAwT/xAAiEQADAAID"
    "AAMBAQAAAAAAAAAAAQIDERIhMUETUWH/2gAMAwEAAhEDEQA/APuaIiAIiIAiIgCI"
    "iAIiIAiIgCIiAIiIAiIgCIiAIiIAiIgCIiAIiIAiIgCIiAIiIAiIgCIiAIiIAiI"
    "gCIiAIiIAiIgCIiAIiIAiIgCIiAIiIAiIgCIiAIiIAiIgCIiAIiIAiIgCIiAIiIA"
    "iIgCIiAIiIAiIgP/2Q=="
)


# ── Helper: fetch URL → bytes ─────────────────────────────────────────────────

def _fetch_url(url: str, timeout: int = _TIMEOUT) -> Optional[bytes]:
    """Fetch a URL and return raw bytes, or None on any error."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 BharatStudio/1.0",
                "Accept":     "image/png,image/jpeg,image/*",
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = resp.read()
                logger.info("Fetched %d bytes from %s", len(data), url[:60])
                return data
            logger.warning("HTTP %d from %s", resp.status, url[:60])
            return None
    except (urllib.error.URLError, OSError) as exc:
        logger.warning("Network error fetching %s: %s", url[:60], exc)
        return None


# ── Source 1: Pollinations.ai (real AI images) ────────────────────────────────

def _via_pollinations(prompt: str) -> Optional[bytes]:
    """
    Call Pollinations.ai — free AI image generation, no key needed.
    May be blocked on some corporate / college networks.
    """
    encoded = urllib.parse.quote(prompt[:200], safe="")
    url     = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true&seed=42"
    logger.info("Trying Pollinations.ai...")
    return _fetch_url(url, timeout=30)


# ── Source 2: Picsum.photos (real photos, CDN, very reliable) ─────────────────

def _via_picsum(prompt: str) -> Optional[bytes]:
    """
    Use picsum.photos — a public photo CDN (Lorem Picsum).
    Deterministic seed from prompt so same prompt → same image.
    Always accessible; used as reliable fallback when AI APIs are blocked.
    """
    # Derive a stable seed from the prompt so results are consistent
    seed = int(hashlib.md5(prompt.encode()).hexdigest(), 16) % 1000
    url  = f"https://picsum.photos/seed/{seed}/512/512"
    logger.info("Trying Picsum.photos (seed=%d)...", seed)
    return _fetch_url(url, timeout=15)


# ── Source 3: Static placeholder (always works) ───────────────────────────────

def _via_placeholder() -> bytes:
    """Return a small static branded PNG. Zero network calls."""
    logger.warning("All image sources failed — using static placeholder.")
    return base64.b64decode(_PLACEHOLDER_B64)


# ── Bedrock path (optional, opt-in) ───────────────────────────────────────────

def _via_bedrock(prompt: str, model_id: str) -> Optional[bytes]:
    try:
        import boto3
        from botocore.exceptions import ClientError

        client = boto3.client("bedrock-runtime", region_name=_IMG_REGION)
        mid    = model_id.lower()

        if "titan" in mid or "nova-canvas" in mid:
            body = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {"text": prompt},
                "imageGenerationConfig": {
                    "numberOfImages": 1, "height": 512, "width": 512, "cfgScale": 8.0,
                },
            }
        elif "stability" in mid:
            body = {
                "text_prompts": [{"text": prompt, "weight": 1.0}],
                "cfg_scale": 10, "steps": 30, "width": 512, "height": 512, "samples": 1,
            }
        else:
            body = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {"text": prompt},
                "imageGenerationConfig": {"numberOfImages": 1, "height": 512, "width": 512},
            }

        for attempt in range(1, 3):
            try:
                resp      = client.invoke_model(
                    modelId=model_id, contentType="application/json",
                    accept="application/json", body=json.dumps(body).encode(),
                )
                resp_dict = json.loads(resp["body"].read().decode())
                images    = resp_dict.get("images") or []
                if images:
                    return base64.b64decode(images[0])
                artifacts = resp_dict.get("artifacts") or []
                if artifacts:
                    return base64.b64decode(artifacts[0]["base64"])
                logger.warning("Bedrock returned empty image list")
                return None
            except ClientError as exc:
                logger.warning("Bedrock attempt %d: %s", attempt, exc.response["Error"]["Message"])
                if attempt < 2:
                    time.sleep(1)
    except Exception as exc:
        logger.warning("Bedrock image error: %s", exc)
    return None


# ── S3 upload ─────────────────────────────────────────────────────────────────

def _try_s3(image_bytes: bytes, key: str) -> Optional[str]:
    try:
        from . import s3_service
        return s3_service.upload_bytes_to_s3(image_bytes, key)
    except Exception as exc:
        logger.warning("S3 upload failed: %s", exc)
        return None


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_image(
    prompt: str,
    model_id: Optional[str] = None,
    save_to_s3: bool = True,
    s3_key: Optional[str] = None,
) -> dict:
    """
    Generate an image from a text prompt.

    Tries sources in order:
      Bedrock (if USE_BEDROCK_IMAGES=true) → Picsum.photos → Placeholder

    Note: Pollinations.ai is skipped (HTTP 530 on this network).

    Returns:
        {
            "ok":     True,
            "b64":    "<base64 string>",
            "s3_url": "https://..." or None,
            "s3_key": "images/..."  or None,
            "source": "bedrock" | "picsum" | "placeholder",
        }
    """
    image_bytes: Optional[bytes] = None
    source = "placeholder"

    # ── 1. Bedrock (opt-in via USE_BEDROCK_IMAGES=true) ───────────────────────
    if _USE_BEDROCK_IMAGES:
        image_bytes = _via_bedrock(prompt, model_id or _IMG_MODEL)
        if image_bytes:
            source = "bedrock"
        else:
            logger.warning("Bedrock failed, falling back to Picsum.")

    # ── 2. Picsum.photos (reliable CDN, works on all networks) ───────────────
    if image_bytes is None:
        image_bytes = _via_picsum(prompt)
        if image_bytes:
            source = "picsum"

    # ── 3. Static placeholder (always works offline) ──────────────────────────
    if image_bytes is None:
        image_bytes = _via_placeholder()
        source      = "placeholder"

    b64_str = base64.b64encode(image_bytes).decode("utf-8")
    result  = {
        "ok":     True,
        "b64":    b64_str,
        "s3_url": None,
        "s3_key": None,
        "source": source,
    }

    # ── Optional S3 upload ────────────────────────────────────────────────────
    if (save_to_s3 and _USE_S3) or len(image_bytes) > 512 * 1024:
        key              = s3_key or f"images/{int(time.time() * 1000)}.png"
        url              = _try_s3(image_bytes, key)
        result["s3_url"] = url
        result["s3_key"] = key if url else None

    logger.info("generate_image done — source=%s b64_len=%d", source, len(b64_str))
    return result