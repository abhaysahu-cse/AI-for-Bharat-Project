# frontend_app/s3_service.py
"""
S3 upload helpers for BharatStudio.
Reads all config from environment variables — no secrets in code.

Required env vars:
    S3_BUCKET_NAME  — target bucket
    AWS_REGION      — e.g. eu-north-1
Optional:
    S3_PREFIX       — key prefix, e.g. "images/" (default: "bharatstudio/")
    S3_PUBLIC       — "true" to set public-read ACL (default: false → presigned URL)
    S3_URL_EXPIRY   — presigned URL expiry in seconds (default: 3600)
"""
import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# ── Config from env ────────────────────────────────────────────────────────────
_BUCKET      = os.getenv("S3_BUCKET_NAME", "")
_REGION      = os.getenv("AWS_REGION", "us-east-1")
_PREFIX      = os.getenv("S3_PREFIX", "bharatstudio/")
_PUBLIC      = os.getenv("S3_PUBLIC", "false").lower() in ("1", "true", "yes")
_URL_EXPIRY  = int(os.getenv("S3_URL_EXPIRY", "3600"))


def _s3_client():
    """Return a boto3 S3 client using the default credential chain."""
    return boto3.client("s3", region_name=_REGION)


def upload_bytes_to_s3(
    bytes_data: bytes,
    key: str,
    content_type: str = "image/png",
    bucket: Optional[str] = None,
) -> str:
    """
    Upload raw bytes to S3 and return a URL.

    Args:
        bytes_data:   Raw bytes to upload (e.g. PNG image).
        key:          S3 object key (relative, prefix is prepended automatically).
        content_type: MIME type for the object (default: image/png).
        bucket:       Override bucket name (defaults to S3_BUCKET_NAME env var).

    Returns:
        Public URL string if S3_PUBLIC=true, otherwise a pre-signed URL.

    Raises:
        ValueError: if bucket name is not configured.
        ClientError: propagated from boto3 on upload failure.
    """
    target_bucket = bucket or _BUCKET
    if not target_bucket:
        raise ValueError(
            "S3_BUCKET_NAME env var is not set. "
            "Set it or pass bucket= explicitly."
        )

    full_key = f"{_PREFIX.rstrip('/')}/{key.lstrip('/')}" if _PREFIX else key
    client   = _s3_client()

    put_kwargs = {
        "Bucket":      target_bucket,
        "Key":         full_key,
        "Body":        bytes_data,
        "ContentType": content_type,
    }
    if _PUBLIC:
        put_kwargs["ACL"] = "public-read"

    logger.info("Uploading %d bytes to s3://%s/%s", len(bytes_data), target_bucket, full_key)
    client.put_object(**put_kwargs)

    if _PUBLIC:
        url = f"https://{target_bucket}.s3.{_REGION}.amazonaws.com/{full_key}"
        logger.info("Uploaded (public): %s", url)
        return url

    # Generate presigned URL for private buckets
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": target_bucket, "Key": full_key},
        ExpiresIn=_URL_EXPIRY,
    )
    logger.info("Uploaded (presigned, expiry=%ds): %s", _URL_EXPIRY, url)
    return url