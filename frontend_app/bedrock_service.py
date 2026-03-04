# frontend_app/bedrock_service.py
import os
import json
import logging
import boto3
import traceback

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class BedrockService:
    def __init__(self, region=None):
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.client = boto3.client("bedrock-runtime", region_name=self.region)

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
        if clean_text.startswith("```"): clean_text = clean_text[3:]
        if clean_text.endswith("```"): clean_text = clean_text[:-3]
        
        return json.loads(clean_text.strip())

    def generate_variants(self, prompt: str, languages: list, model_id: str):
        try:
            system_prompt = (
                "You are a concise social media copywriter. Return ONLY valid JSON with a 'variants' list.\n"
                "Format: {\"variants\": [{\"variant_id\":\"v1\",\"lang\":\"en\",\"text\":\"...\"}, ...]}\n"
                f"User prompt: {prompt}\n"
                f"Languages: {','.join(languages)}\n"
                "Produce 1 variant per language requested."
            )
            
            resp = self.invoke_model_json(model_id, system_prompt)
            
            # Safely normalize the payload to a list
            if isinstance(resp, list):
                return resp
            elif isinstance(resp, dict) and "variants" in resp:
                return resp["variants"]
            else:
                return [{"variant_id": "v-err", "lang": "en", "text": f"Unexpected format: {resp}"}]
                
        except Exception as e:
            # If the service crashes, it returns the exact error line as the variant text
            err_msg = traceback.format_exc()
            logger.error(f"Bedrock Service Crash:\n{err_msg}")
            return [{"variant_id": "v-crash", "lang": "en", "text": f"DEBUG TRACEBACK:\n{err_msg}"}]