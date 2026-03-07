# tests/test_image_service.py
"""
Unit tests for frontend_app/image_service.py.
All AWS calls are mocked — no real credentials needed.
"""
import base64
import json
import os
import sys
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

# ── Make frontend_app importable from tests/ ──────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Force mock mode off so we exercise the Bedrock path in tests
os.environ.setdefault("USE_BEDROCK", "true")
os.environ.setdefault("AWS_REGION",  "eu-north-1")
os.environ.setdefault("BEDROCK_IMAGE_MODEL_ID", "amazon.titan-image-generator-v1")

from frontend_app import image_service  # noqa: E402 (import after env setup)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fake_png_bytes() -> bytes:
    """Return a minimal valid 1×1 PNG for testing."""
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhf"
        "DwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )


def _titan_response(image_bytes: bytes) -> dict:
    """Build a fake Titan Image Generator response body."""
    return {"images": [base64.b64encode(image_bytes).decode("utf-8")]}


def _stability_response(image_bytes: bytes) -> dict:
    """Build a fake Stability AI response body."""
    return {"artifacts": [{"base64": base64.b64encode(image_bytes).decode("utf-8")}]}


def _mock_bedrock_response(body_dict: dict) -> MagicMock:
    """Wrap a dict in a mock that mimics boto3 invoke_model response."""
    raw = json.dumps(body_dict).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp["body"].read.return_value = raw
    return mock_resp


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestBuildRequestBody(unittest.TestCase):
    """_build_request_body selects the right schema per model."""

    def test_titan_schema(self):
        body = image_service._build_request_body("test", "amazon.titan-image-generator-v1")
        self.assertEqual(body["taskType"], "TEXT_IMAGE")
        self.assertIn("textToImageParams", body)
        self.assertEqual(body["textToImageParams"]["text"], "test")

    def test_stability_schema(self):
        body = image_service._build_request_body("test", "stability.stable-diffusion-xl-v1")
        self.assertIn("text_prompts", body)
        self.assertEqual(body["text_prompts"][0]["text"], "test")

    def test_unknown_model_falls_back_to_titan(self):
        body = image_service._build_request_body("test", "some.unknown-model-v1")
        self.assertIn("taskType", body)


class TestExtractImageBytes(unittest.TestCase):
    """_extract_image_bytes parses each model's response shape."""

    def test_titan_extraction(self):
        png = _fake_png_bytes()
        resp = _titan_response(png)
        result = image_service._extract_image_bytes(resp, "amazon.titan-image-generator-v1")
        self.assertEqual(result, png)

    def test_stability_extraction(self):
        png = _fake_png_bytes()
        resp = _stability_response(png)
        result = image_service._extract_image_bytes(resp, "stability.stable-diffusion-xl-v1")
        self.assertEqual(result, png)

    def test_titan_no_images_raises(self):
        with self.assertRaises(ValueError) as ctx:
            image_service._extract_image_bytes({"images": []}, "amazon.titan-image-generator-v1")
        self.assertIn("no images", str(ctx.exception).lower())

    def test_stability_no_artifacts_raises(self):
        with self.assertRaises(ValueError):
            image_service._extract_image_bytes({"artifacts": []}, "stability.stable-diffusion-xl-v1")


class TestGenerateImageMockMode(unittest.TestCase):
    """When USE_BEDROCK=false, generate_image returns a placeholder."""

    def setUp(self):
        self._orig = image_service._USE_BEDROCK
        image_service._USE_BEDROCK = False

    def tearDown(self):
        image_service._USE_BEDROCK = self._orig

    def test_returns_placeholder(self):
        result = image_service.generate_image("some prompt")
        self.assertTrue(result["ok"])
        self.assertEqual(result["b64"], image_service._PLACEHOLDER_B64)
        self.assertTrue(result.get("mock"))
        self.assertIsNone(result.get("s3_url"))


class TestGenerateImageSuccess(unittest.TestCase):
    """Happy-path: Bedrock returns a valid Titan response; S3 disabled."""

    def setUp(self):
        self._orig_bedrock = image_service._USE_BEDROCK
        self._orig_s3      = image_service._USE_S3
        image_service._USE_BEDROCK = True
        image_service._USE_S3      = False

    def tearDown(self):
        image_service._USE_BEDROCK = self._orig_bedrock
        image_service._USE_S3      = self._orig_s3

    @patch("frontend_app.image_service._bedrock_client")
    def test_success_no_s3(self, mock_client_factory):
        png     = _fake_png_bytes()
        resp    = _titan_response(png)
        raw_str = json.dumps(resp).encode("utf-8")

        mock_body = MagicMock()
        mock_body.read.return_value = raw_str

        mock_client = MagicMock()
        mock_client.invoke_model.return_value = {"body": mock_body}
        mock_client_factory.return_value = mock_client

        result = image_service.generate_image(
            "steaming samosa on a rainy day",
            model_id="amazon.titan-image-generator-v1",
            save_to_s3=False,
        )

        self.assertTrue(result["ok"])
        self.assertIsNone(result["s3_url"])
        # b64 should decode back to original bytes
        self.assertEqual(base64.b64decode(result["b64"]), png)
        mock_client.invoke_model.assert_called_once()


class TestGenerateImageS3Upload(unittest.TestCase):
    """S3 upload path: result includes s3_url."""

    def setUp(self):
        self._orig_bedrock = image_service._USE_BEDROCK
        self._orig_s3      = image_service._USE_S3
        image_service._USE_BEDROCK = True
        image_service._USE_S3      = True

    def tearDown(self):
        image_service._USE_BEDROCK = self._orig_bedrock
        image_service._USE_S3      = self._orig_s3

    @patch("frontend_app.image_service.s3_service.upload_bytes_to_s3")
    @patch("frontend_app.image_service._bedrock_client")
    def test_s3_url_present(self, mock_client_factory, mock_upload):
        png     = _fake_png_bytes()
        raw_str = json.dumps(_titan_response(png)).encode("utf-8")

        mock_body = MagicMock()
        mock_body.read.return_value = raw_str

        mock_client = MagicMock()
        mock_client.invoke_model.return_value = {"body": mock_body}
        mock_client_factory.return_value = mock_client

        mock_upload.return_value = "https://my-bucket.s3.amazonaws.com/bharatstudio/images/test.png"

        result = image_service.generate_image(
            "monsoon street food",
            model_id="amazon.titan-image-generator-v1",
            save_to_s3=True,
        )

        self.assertTrue(result["ok"])
        self.assertIsNotNone(result["s3_url"])
        self.assertIn("s3.amazonaws.com", result["s3_url"])
        mock_upload.assert_called_once()


class TestGenerateImageS3Failure(unittest.TestCase):
    """If S3 upload fails, fall back to inline base64 instead of erroring."""

    def setUp(self):
        self._orig_bedrock = image_service._USE_BEDROCK
        self._orig_s3      = image_service._USE_S3
        image_service._USE_BEDROCK = True
        image_service._USE_S3      = True

    def tearDown(self):
        image_service._USE_BEDROCK = self._orig_bedrock
        image_service._USE_S3      = self._orig_s3

    @patch("frontend_app.image_service.s3_service.upload_bytes_to_s3",
           side_effect=Exception("S3 bucket not found"))
    @patch("frontend_app.image_service._bedrock_client")
    def test_s3_error_returns_b64_fallback(self, mock_client_factory, _mock_upload):
        png     = _fake_png_bytes()
        raw_str = json.dumps(_titan_response(png)).encode("utf-8")

        mock_body = MagicMock()
        mock_body.read.return_value = raw_str

        mock_client = MagicMock()
        mock_client.invoke_model.return_value = {"body": mock_body}
        mock_client_factory.return_value = mock_client

        result = image_service.generate_image("test", save_to_s3=True)

        # Still ok — b64 inline fallback
        self.assertTrue(result["ok"])
        self.assertIsNotNone(result["b64"])
        self.assertIsNone(result["s3_url"])


class TestGenerateImageBedrockError(unittest.TestCase):
    """Bedrock ClientError after 2 retries returns ok=False."""

    def setUp(self):
        self._orig = image_service._USE_BEDROCK
        image_service._USE_BEDROCK = True

    def tearDown(self):
        image_service._USE_BEDROCK = self._orig

    @patch("frontend_app.image_service._bedrock_client")
    def test_client_error_after_retries(self, mock_client_factory):
        from botocore.exceptions import ClientError

        error = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid model"}},
            "InvokeModel",
        )
        mock_client = MagicMock()
        mock_client.invoke_model.side_effect = error
        mock_client_factory.return_value = mock_client

        result = image_service.generate_image("test prompt")

        self.assertFalse(result["ok"])
        self.assertIn("error", result)
        # Should have attempted twice
        self.assertEqual(mock_client.invoke_model.call_count, 2)


if __name__ == "__main__":
    unittest.main()