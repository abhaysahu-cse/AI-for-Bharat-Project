# frontend_app/bedrock_service.py
import os
import json
import logging
import traceback
from datetime import date, timedelta
from typing import Optional

import boto3

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_USE_BEDROCK = os.getenv("USE_BEDROCK", "false").lower() in ("1", "true", "yes")


class BedrockService:
    def __init__(self, region=None):
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.client = boto3.client("bedrock-runtime", region_name=self.region)

    # ── EXISTING — unchanged ──────────────────────────────────────────────────
    def invoke_model_json(self, model_id_or_arn: str, input_text: str, max_tokens: int = 1000):
        """Invoke Nova-style model, parse and return JSON. max_tokens param added."""
        body = {
            "messages": [{"role": "user", "content": [{"text": input_text}]}],
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0.7}
        }
        resp = self.client.invoke_model(
            modelId=model_id_or_arn,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body).encode("utf-8"),
        )
        raw = resp["body"].read().decode("utf-8")
        response_data = json.loads(raw)
        generated_text = response_data["output"]["message"]["content"][0]["text"]
        clean_text = generated_text.strip()
        if clean_text.startswith("```json"): clean_text = clean_text[7:]
        if clean_text.startswith("```"):     clean_text = clean_text[3:]
        if clean_text.endswith("```"):       clean_text = clean_text[:-3]
        return json.loads(clean_text.strip())

    # ── EXISTING — unchanged ──────────────────────────────────────────────────
    def generate_variants(self, prompt: str, languages: list, model_id: str):
        try:
            lang_str = ",".join(languages)
            system_prompt = (
                "You are a concise social media copywriter. Return ONLY valid JSON with a 'variants' list.\n"
                "Each variant MUST include these exact keys: variant_id, lang, text, image_prompt.\n"
                "image_prompt must be a vivid visual scene (10-15 words) for an image generator.\n"
                "Format: {\"variants\": [{\"variant_id\":\"v1\",\"lang\":\"en\",\"text\":\"...\","
                "\"image_prompt\":\"...\"}, ...]}\n"
                f"User prompt: {prompt}\n"
                f"Languages: {lang_str}\n"
                "Produce 1 variant per language requested."
            )
            resp = self.invoke_model_json(model_id, system_prompt)
            if isinstance(resp, list):
                return resp
            elif isinstance(resp, dict) and "variants" in resp:
                return resp["variants"]
            else:
                return [{"variant_id": "v-err", "lang": "en", "text": f"Unexpected format: {resp}"}]
        except Exception:
            err_msg = traceback.format_exc()
            logger.error("Bedrock Service Crash:\n%s", err_msg)
            return [{"variant_id": "v-crash", "lang": "en", "text": f"DEBUG TRACEBACK:\n{err_msg}"}]

    # ── EXISTING — unchanged ──────────────────────────────────────────────────
    def invoke_model_raw(self, body: dict, model_id: Optional[str] = None,
                         content_type: str = "application/json",
                         accept: str = "application/json") -> dict:
        """Generic low-level Bedrock invocation used by image_service.py."""
        effective_model = model_id or os.getenv("BEDROCK_MODEL_ID", "")
        if not effective_model:
            raise ValueError("No model_id provided and BEDROCK_MODEL_ID env var is not set.")
        try:
            response = self.client.invoke_model(
                modelId=effective_model, contentType=content_type,
                accept=accept, body=json.dumps(body).encode("utf-8"),
            )
            raw = response["body"].read().decode("utf-8")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"raw": raw}
        except Exception as exc:
            logger.error("invoke_model_raw failed for model '%s': %s", effective_model, exc)
            raise

    # ── NEW: A — Video Script Generator ──────────────────────────────────────
    def generate_video_script(self, prompt: str, languages: list,
                               model_id: str = None) -> list:
        """
        Generate a shot-list video script for each requested language.

        Returns:
            [{"lang": "en", "scenes": [{"scene":1, "duration_seconds":6,
              "shot":"...", "camera":"wide|close-up|pan", "sfx":"optional"}]}]
        """
        effective_model = model_id or os.getenv(
            "BEDROCK_MODEL_ID_VIDEO",
            os.getenv("BEDROCK_MODEL_ID", "eu.amazon.nova-lite-v1:0"),
        )
        mock_scenes = [
            {"scene": 1, "duration_seconds": 6,
             "shot": f"Opening wide shot: {prompt[:50]}", "camera": "wide", "sfx": "ambient"},
            {"scene": 2, "duration_seconds": 8,
             "shot": "Close-up detail of main subject", "camera": "close-up", "sfx": ""},
            {"scene": 3, "duration_seconds": 6,
             "shot": "Action pan revealing full scene", "camera": "pan", "sfx": ""},
            {"scene": 4, "duration_seconds": 6,
             "shot": "Closing shot with text overlay CTA", "camera": "wide", "sfx": "upbeat music"},
        ]

        if not _USE_BEDROCK:
            return [{"lang": lang, "scenes": mock_scenes} for lang in languages]

        results = []
        for lang in languages:
            sys_prompt = (
                f"You are a concise video script writer for short social videos (6-30s).\n"
                f"Write a vivid 4-6 scene video script for this topic: {prompt}\n"
                f"Language for shot descriptions: {lang}\n"
                "Rules:\n"
                "- Each scene must have a SPECIFIC, VIVID shot description (not generic words)\n"
                "- duration_seconds must be a number between 6 and 10\n"
                "- camera must be one of: close-up, wide, pan, overhead, tracking\n"
                "- sfx is optional ambient sound (empty string if none)\n"
                "Return ONLY a raw JSON object — no markdown, no explanation.\n"
                "Example of GOOD output (fill with real content about the topic, not these words):\n"
                "{\"scenes\":["
                "{\"scene\":1,\"duration_seconds\":6,\"shot\":\"Steam rising from a hot tawa as golden samosas sizzle in oil\",\"camera\":\"close-up\",\"sfx\":\"sizzling oil sound\"},"
                "{\"scene\":2,\"duration_seconds\":8,\"shot\":\"Busy Patna street stall at dusk, crowds holding umbrellas in monsoon rain\",\"camera\":\"wide\",\"sfx\":\"rain and crowd noise\"},"
                "{\"scene\":3,\"duration_seconds\":6,\"shot\":\"Vendor's hands expertly folding a kachori, flour dusted fingers\",\"camera\":\"overhead\",\"sfx\":\"\"},"
                "{\"scene\":4,\"duration_seconds\":6,\"shot\":\"Happy customers biting into chaat, expressions of delight\",\"camera\":\"tracking\",\"sfx\":\"upbeat folk music\"}"
                "]}"
            )
            try:
                resp = self.invoke_model_json(effective_model, sys_prompt, max_tokens=800)
                scenes = resp.get("scenes", resp) if isinstance(resp, dict) else resp
                results.append({"lang": lang, "scenes": scenes})
            except Exception as e:
                logger.error("generate_video_script lang=%s: %s", lang, e)
                results.append({"lang": lang, "scenes": mock_scenes})
        return results

    # ── NEW: B — Hashtag Optimizer ────────────────────────────────────────────
    def generate_hashtags(self, caption: str, platform: str = "instagram",
                          languages: list = None, model_id: str = None) -> dict:
        """
        Generate platform-optimised hashtags with a heuristic engagement score.

        Returns:
            {"hashtags": [{"tag":"#X","reason":"..."}], "predicted_engagement": 75}
        """
        effective_model = model_id or os.getenv(
            "BEDROCK_MODEL_ID_HASHTAGS",
            os.getenv("BEDROCK_MODEL_ID", "eu.amazon.nova-lite-v1:0"),
        )
        languages = languages or ["en"]

        def _mock_tags():
            words = [w.strip(".,!?#@") for w in caption.split() if len(w) > 4][:6]
            return [{"tag": f"#{w.capitalize()}", "reason": "derived from caption"} for w in words]

        if not _USE_BEDROCK:
            return {"hashtags": _mock_tags(), "predicted_engagement": 72}

        sys_prompt = (
            f"You are a social media hashtag expert for {platform}.\n"
            f"Generate 6-8 optimised hashtags for this caption: {caption}\n"
            "Return ONLY valid JSON — no markdown:\n"
            "{\"hashtags\":[{\"tag\":\"#Example\",\"reason\":\"why this tag works\"}]}"
        )
        try:
            resp = self.invoke_model_json(effective_model, sys_prompt, max_tokens=500)
            hashtags = resp.get("hashtags", []) if isinstance(resp, dict) else []
        except Exception as e:
            logger.error("generate_hashtags error: %s", e)
            hashtags = _mock_tags()

        # Heuristic engagement score (0-99)
        n_tags    = len(hashtags)
        cap_len   = len(caption)
        len_score = 100 if 80 <= cap_len <= 200 else max(40, 100 - abs(cap_len - 140) // 3)
        tag_score = 100 if 4 <= n_tags <= 8 else max(50, 100 - abs(n_tags - 6) * 8)
        predicted = max(10, min(99, round(len_score * 0.4 + tag_score * 0.6)))

        return {"hashtags": hashtags, "predicted_engagement": predicted}

    # ── NEW: D — Content Calendar ─────────────────────────────────────────────
    def generate_content_calendar(self, topic: str, platforms: list,
                                  days: int = 7, model_id: str = None) -> list:
        """
        Generate a scheduled content calendar.

        Returns:
            [{"date":"2026-03-07","platform":"instagram","caption":"...",
              "image_prompt":"...","time":"18:00"}]
        """
        effective_model = model_id or os.getenv("BEDROCK_MODEL_ID", "eu.amazon.nova-lite-v1:0")
        start_date = date.today()
        DEFAULT_TIMES = {
            "instagram": "18:00", "twitter": "12:30",
            "youtube": "17:00",   "whatsapp": "20:00", "linkedin": "09:00",
        }

        def _mock_calendar():
            items = []
            for i in range(days):
                plat = platforms[i % len(platforms)]
                items.append({
                    "date": (start_date + timedelta(days=i)).isoformat(),
                    "platform": plat,
                    "caption": f"Day {i+1}: Engaging post about {topic}",
                    "image_prompt": f"Vibrant visual for {topic}, day {i+1}",
                    "time": DEFAULT_TIMES.get(plat, "18:00"),
                })
            return items

        if not _USE_BEDROCK:
            return _mock_calendar()

        plat_str   = ", ".join(platforms)
        sys_prompt = (
            f"You are a social media content strategist.\n"
            f"Create a {days}-day content calendar for topic: {topic}\n"
            f"Platforms: {plat_str}\n"
            f"Start date: {start_date.isoformat()}\n"
            "Return ONLY valid JSON array — no markdown:\n"
            "[{\"date\":\"YYYY-MM-DD\",\"platform\":\"instagram\","
            "\"caption\":\"...\",\"image_prompt\":\"...\",\"time\":\"18:00\"}]"
        )
        try:
            resp = self.invoke_model_json(effective_model, sys_prompt, max_tokens=1500)
            items = resp if isinstance(resp, list) else resp.get("items", resp.get("calendar", []))
            for item in items:
                item.setdefault("time", DEFAULT_TIMES.get(item.get("platform", ""), "18:00"))
            return items
        except Exception as e:
            logger.error("generate_content_calendar error: %s", e)
            return _mock_calendar()

    # ── NEW: E — Platform Variants ────────────────────────────────────────────
    def generate_platform_variants(self, prompt: str, languages: list,
                                   platforms: list, model_id: str = None) -> list:
        """
        Generate platform-optimised captions per platform × language combination.

        Returns:
            [{"platform":"instagram","lang":"en","caption":"...","cta":"..."}]
        """
        effective_model = model_id or os.getenv("BEDROCK_MODEL_ID", "eu.amazon.nova-lite-v1:0")

        if not _USE_BEDROCK:
            return [
                {"platform": p, "lang": l,
                 "caption": f"[MOCK] {p.upper()} caption for: {prompt} ({l.upper()})",
                 "cta": "Learn more"}
                for p in platforms for l in languages
            ]

        lang_str   = ", ".join(languages)
        plat_str   = ", ".join(platforms)
        sys_prompt = (
            f"You are a platform-aware social media writer.\n"
            f"Write optimised captions for: {prompt}\n"
            f"Languages: {lang_str}  |  Platforms: {plat_str}\n"
            "Character limits: Twitter 280, Instagram aim <=150, LinkedIn 700, YouTube 100.\n"
            "Return ONLY valid JSON array — no markdown:\n"
            "[{\"platform\":\"instagram\",\"lang\":\"en\",\"caption\":\"...\",\"cta\":\"optional CTA\"}]"
        )
        try:
            resp = self.invoke_model_json(effective_model, sys_prompt, max_tokens=1200)
            variants = (resp if isinstance(resp, list)
                        else resp.get("platform_variants", resp.get("variants", [])))
            return variants
        except Exception as e:
            logger.error("generate_platform_variants error: %s", e)
            return [{"platform": p, "lang": l, "caption": f"Error: {e}", "cta": ""}
                    for p in platforms for l in languages]