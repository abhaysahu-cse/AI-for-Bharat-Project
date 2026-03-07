# frontend_app/tts_service.py
"""
Text-to-speech via Amazon Polly.

Usage:
    from frontend_app.tts_service import synthesize_speech
    audio_bytes = synthesize_speech("Hello world", voice="Joanna", output_format="mp3")

Production note: store returned bytes in S3 and return a signed URL instead of
embedding base64 in the API response. For demo purposes, base64 in-response is fine.
"""

import os
import logging
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

# Sensible voice defaults per language code
_VOICE_DEFAULTS: dict = {
    "hi":  os.getenv("POLLY_VOICE_HI",  "Raveena"),
    "en":  os.getenv("POLLY_VOICE_EN",  "Joanna"),
    "ta":  os.getenv("POLLY_VOICE_TA",  "Aditi"),    # Hindi neural also covers Devanagari; Tamil not yet in Polly
    "te":  os.getenv("POLLY_VOICE_TE",  "Aditi"),
    "bn":  os.getenv("POLLY_VOICE_BN",  "Aditi"),
    "mr":  os.getenv("POLLY_VOICE_MR",  "Aditi"),
    "gu":  os.getenv("POLLY_VOICE_GU",  "Aditi"),
    "default": os.getenv("POLLY_VOICE", "Joanna"),
}

_OUTPUT_FORMAT = os.getenv("POLLY_OUTPUT_FORMAT", "mp3")   # mp3 | ogg_vorbis | pcm

# Neural voices support prosody much better — enable if your account has access
_ENGINE = os.getenv("POLLY_ENGINE", "standard")  # standard | neural


def _get_voice(lang: str, explicit_voice: Optional[str] = None) -> str:
    """Resolve a Polly voice name: explicit override > lang default > global default."""
    if explicit_voice:
        return explicit_voice
    return _VOICE_DEFAULTS.get(lang, _VOICE_DEFAULTS["default"])


def synthesize_speech(
    text: str,
    lang: str = "en",
    voice: Optional[str] = None,
    output_format: str = _OUTPUT_FORMAT,
    region: Optional[str] = None,
    use_ssml: bool = False,
) -> bytes:
    """
    Call Amazon Polly and return raw audio bytes.

    Args:
        text:          Plain text (or SSML markup if use_ssml=True).
        lang:          BCP-47 language hint, used to pick a default voice.
        voice:         Explicit Polly voice ID (overrides lang-based default).
        output_format: 'mp3', 'ogg_vorbis', or 'pcm'.
        region:        AWS region override (falls back to AWS_REGION env var).
        use_ssml:      If True, text is treated as SSML.

    Returns:
        Raw audio bytes.

    Raises:
        RuntimeError: if Polly call fails.
    """
    effective_region = region or os.getenv("POLLY_REGION", os.getenv("AWS_REGION", "us-east-1"))
    effective_voice  = _get_voice(lang, voice)
    text_type        = "ssml" if use_ssml else "text"

    polly = boto3.client("polly", region_name=effective_region)

    kwargs: dict = {
        "Text":         text,
        "TextType":     text_type,
        "OutputFormat": output_format,
        "VoiceId":      effective_voice,
        "Engine":       _ENGINE,
    }

    logger.debug(
        "Polly synthesize: voice=%s engine=%s format=%s text_len=%d",
        effective_voice, _ENGINE, output_format, len(text),
    )

    try:
        response = polly.synthesize_speech(**kwargs)
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        # Neural not available for this voice → fall back to standard
        if error_code in ("InvalidSampleRateException", "UnsupportedPlsSpeechMarkTypeException") \
                or "neural" in str(exc).lower():
            logger.warning("Neural engine failed (%s), retrying with standard engine.", exc)
            kwargs["Engine"] = "standard"
            try:
                response = polly.synthesize_speech(**kwargs)
            except (BotoCoreError, ClientError) as inner:
                raise RuntimeError(f"Polly synthesize_speech failed: {inner}") from inner
        else:
            raise RuntimeError(f"Polly ClientError ({error_code}): {exc}") from exc
    except BotoCoreError as exc:
        raise RuntimeError(f"Polly BotoCoreError: {exc}") from exc

    # AudioStream is a StreamingBody — read it all
    audio_bytes: bytes = response["AudioStream"].read()
    logger.debug("Polly returned %d audio bytes", len(audio_bytes))
    return audio_bytes