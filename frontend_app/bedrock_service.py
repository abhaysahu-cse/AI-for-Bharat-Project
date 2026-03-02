import boto3
import json
import os

REGION = os.getenv("AWS_REGION", "us-east-1")
client = boto3.client("bedrock-runtime", region_name=REGION)

def generate_caption(prompt_text: str) -> str:
    """
    Simple wrapper to call Bedrock. 
    Replace model_id below if you don't have access to the named model in your account/region.
    """
    model_id = "amazon.titan-text-express-v1"  # common low-cost draft model; change if unauthorized
    body_dict = {
        "inputText": f"Generate 3 short social media captions for: {prompt_text}. Include hashtags and emojis. Return plain text or a JSON array."
    }
    body_bytes = json.dumps(body_dict).encode("utf-8")
    resp = client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=body_bytes
    )
    raw = resp["body"].read().decode("utf-8")
    try:
        return json.loads(raw)
    except Exception:
        return raw
