# frontend_app/bedrock_service.py
import os
import json
import logging
import boto3
import traceback
from typing import Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class BedrockService:
    def __init__(self, region=None):
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.client = boto3.client("bedrock-runtime", region_name=self.region)

    # ── EXISTING — unchanged ──────────────────────────────────────────────────
    def invoke_model_json(self, model_id_or_arn: str, input_text: str):
        body = {
            "messages": [{"role": "user", "content": [{"text": input_text}]}],
            "inferenceConfig": {"maxTokens": 1000, "temperature": 0.7}
        }

        resp = self.client.invoke_model(
            modelId=model_id_or_arn,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body).encode("utf-8"),
        )
        raw = resp["body"].read().decode("utf-8")
        response_data = json.loads(raw)

        # Extract Nova text
        generated_text = response_data["output"]["message"]["content"][0]["text"]

        # Clean up any Markdown formatting (e.g., ```json ... ```)
        clean_text = generated_text.strip()
        if clean_text.startswith("```json"): clean_text = clean_text[7:]
        if clean_text.startswith("```"):     clean_text = clean_text[3:]
        if clean_text.endswith("```"):       clean_text = clean_text[:-3]

        return json.loads(clean_text.strip())

    # ── EXISTING — unchanged ──────────────────────────────────────────────────
    def generate_variants(self, prompt: str, languages: list, model_id: str):
        try:
            system_prompt = (
                "You are a concise social media copywriter. Return ONLY valid JSON with a 'variants' list.\n"
                "Each variant MUST include these exact keys: variant_id, lang, text, image_prompt.\n"
                "image_prompt must be a vivid visual scene (10-15 words) for an image generator.\n"
                "Format: {\"variants\": [{\"variant_id\":\"v1\",\"lang\":\"en\",\"text\":\"...\",\"image_prompt\":\"...\"}, ...]}\n"
                f"User prompt: {prompt}\n"
                f"Languages: {','.join(languages)}\n"
                "Produce 1 variant per language requested."
            )

            resp = self.invoke_model_json(model_id, system_prompt)

            if isinstance(resp, list):
                return resp
            elif isinstance(resp, dict) and "variants" in resp:
                return resp["variants"]
            else:
                return [{"variant_id": "v-err", "lang": "en", "text": f"Unexpected format: {resp}"}]

        except Exception as e:
            err_msg = traceback.format_exc()
            logger.error(f"Bedrock Service Crash:\n{err_msg}")
            return [{"variant_id": "v-crash", "lang": "en", "text": f"DEBUG TRACEBACK:\n{err_msg}"}]

    # ── NEW — generic raw invocation used by image_service.py ────────────────
    def invoke_model_raw(
        self,
        body: dict,
        model_id: Optional[str] = None,
        content_type: str = "application/json",
        accept: str = "application/json",
    ) -> dict:
        """
        Generic Bedrock invocation that accepts any pre-built body dict.
        Used by image_service (and any future model types) so all AWS calls
        go through a single, well-logged code path.

        Args:
            body:         Model-specific request dict — will be JSON-encoded.
            model_id:     Model ID or inference profile ARN.
                          Falls back to BEDROCK_MODEL_ID env var if omitted.
            content_type: MIME type for the request body.
            accept:       MIME type for the response.

        Returns:
            Parsed JSON dict from the response body, or {"raw": "<str>"}
            if the response is not valid JSON.

        Raises:
            ValueError:  if no model_id is available anywhere.
            ClientError: propagated from boto3 on AWS errors.
        """
        effective_model = model_id or os.getenv("BEDROCK_MODEL_ID", "")
        if not effective_model:
            raise ValueError(
                "No model_id provided and BEDROCK_MODEL_ID env var is not set."
            )

        try:
            response = self.client.invoke_model(
                modelId=effective_model,
                contentType=content_type,
                accept=accept,
                body=json.dumps(body).encode("utf-8"),
            )
            raw = response["body"].read().decode("utf-8")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                logger.warning(
                    "invoke_model_raw: response for '%s' is not JSON; returning {'raw': ...}",
                    effective_model,
                )
                return {"raw": raw}
        except Exception as exc:
            logger.error("invoke_model_raw failed for '%s': %s", effective_model, exc)
            raise