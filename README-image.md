# BharatStudio — Image Generation

## Overview

BharatStudio now supports AI image generation via Amazon Bedrock.
Per-variant image prompts are automatically turned into visuals when
`generate_images: true` is included in the draft creation request.

---

## New files

| File | Purpose |
|------|---------|
| `frontend_app/image_service.py` | Bedrock image generation + S3 upload |
| `frontend_app/s3_service.py` | S3 upload helper |
| `frontend_app/image_views.py` | `POST /api/images/` endpoint |
| `tests/test_image_service.py` | Unit tests (fully mocked) |
| `tests/test_views_image.py` | Endpoint integration tests (fully mocked) |

---

## Environment variables

Add these to your `.env` (never commit real values):

```properties
# ── Bedrock image model ──────────────────────────────────────────────────────
# First-party Amazon model — no Marketplace subscription needed:
BEDROCK_IMAGE_MODEL_ID=amazon.titan-image-generator-v1

# If you want Stability AI (requires Marketplace subscription):
# BEDROCK_IMAGE_MODEL_ID=stability.stable-diffusion-xl-v1

# ── S3 storage (optional) ────────────────────────────────────────────────────
USE_S3=false                   # set to "true" to upload images to S3
S3_BUCKET_NAME=my-bharatstudio-bucket
S3_PREFIX=bharatstudio/images  # key prefix inside the bucket
S3_PUBLIC=false                # true = public-read ACL; false = presigned URL
S3_URL_EXPIRY=3600             # presigned URL lifetime in seconds

# ── Already set (no changes needed) ─────────────────────────────────────────
USE_BEDROCK=true
AWS_REGION=eu-north-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

---

## IAM permissions required

Attach this policy to the IAM user / role running the backend:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvoke",
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/amazon.titan-image-generator-v1",
        "arn:aws:bedrock:*::foundation-model/stability.stable-diffusion-xl-v1",
        "arn:aws:bedrock:eu-north-1:<ACCOUNT_ID>:inference-profile/*"
      ]
    },
    {
      "Sid": "S3ImageStorage",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::my-bharatstudio-bucket/*"
    }
  ]
}
```

Replace `<ACCOUNT_ID>` and `my-bharatstudio-bucket` with real values.

---

## API usage

### Generate image standalone

```bash
curl -X POST http://127.0.0.1:8000/api/images/ \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Close-up of steaming samosa on a rainy monsoon street in Patna",
    "model": "amazon.titan-image-generator-v1",
    "save_to_s3": false
  }'
```

Response:
```json
{
  "ok": true,
  "b64": "<base64 PNG>",
  "s3_url": null,
  "s3_key": null,
  "model_id": "amazon.titan-image-generator-v1"
}
```

### Generate draft with images attached

```powershell
$body = @{
  prompt          = "Monsoon street food in Patna"
  languages       = @("en", "hi")
  generate_images = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/drafts/" `
  -Method POST -Body $body -ContentType "application/json"
```

Each variant in the response will include:
```json
{
  "variant_id": "v1",
  "lang": "en",
  "text": "...",
  "image_prompt": "Close-up of ...",
  "image_url": "https://...",
  "image_b64": "<base64>"
}
```

---

## Running tests

```bash
# Unit tests (no AWS creds needed — all mocked)
pytest tests/test_image_service.py -v

# Endpoint integration tests (Django + mocked image_service)
pytest tests/test_views_image.py -v

# All tests
pytest tests/ -v
```

---

## Supported models

| Model ID | Notes |
|----------|-------|
| `amazon.titan-image-generator-v1` | ✅ First-party, no Marketplace OTP |
| `amazon.titan-image-generator-v2:0` | ✅ First-party, higher quality |
| `stability.stable-diffusion-xl-v1` | ⚠️ Requires Marketplace subscription (OTP issue for Indian cards) |

For Indian AWS accounts with RBI OTP restrictions, use `amazon.titan-image-generator-v1`.

---

## How the image flow works

```
POST /api/drafts/ {generate_images: true}
        │
        ▼
  BedrockService.generate_variants()   ← text captions
        │
        ▼  (for each variant with image_prompt)
  image_service.generate_image()
        │
        ├─ USE_BEDROCK=false → placeholder PNG (mock)
        │
        └─ USE_BEDROCK=true  → Bedrock invoke_model
                │
                ├─ USE_S3=true  → s3_service.upload_bytes_to_s3() → s3_url
                └─ USE_S3=false → base64 inline → image_b64
```