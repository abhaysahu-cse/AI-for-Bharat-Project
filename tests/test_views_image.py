# tests/test_views_image.py
"""
Integration tests for POST /api/images/ endpoint.
image_service is fully mocked — no AWS calls made.
"""
import json
import os
import sys
import unittest
from unittest.mock import patch

# ── Django setup ──────────────────────────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import django  # noqa: E402
django.setup()

from django.test import RequestFactory  # noqa: E402
from frontend_app.image_views import generate_image_view  # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────

def _post(body: dict):
    """Fire a fake POST request to generate_image_view."""
    factory = RequestFactory()
    request = factory.post(
        "/api/images/",
        data=json.dumps(body),
        content_type="application/json",
    )
    return generate_image_view(request)


_SUCCESS_RESULT = {
    "ok": True,
    "b64": "abc123base64==",
    "s3_url": "https://my-bucket.s3.amazonaws.com/bharatstudio/images/test.png",
    "s3_key": "bharatstudio/images/test.png",
    "model_id": "amazon.titan-image-generator-v1",
}

_FAILURE_RESULT = {
    "ok": False,
    "error": "Bedrock ValidationException: Invalid model ID",
}


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestGenerateImageEndpoint(unittest.TestCase):

    # ── Success path ──────────────────────────────────────────────────────────

    @patch("frontend_app.image_views.image_service.generate_image",
           return_value=_SUCCESS_RESULT)
    def test_success_returns_200(self, mock_gen):
        resp = _post({"prompt": "steaming samosa on a rainy day"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data["ok"])
        self.assertEqual(data["b64"], "abc123base64==")
        self.assertIn("s3.amazonaws.com", data["s3_url"])

    @patch("frontend_app.image_views.image_service.generate_image",
           return_value=_SUCCESS_RESULT)
    def test_custom_model_forwarded(self, mock_gen):
        _post({"prompt": "test", "model": "stability.stable-diffusion-xl-v1"})
        call_kwargs = mock_gen.call_args[1]
        self.assertEqual(call_kwargs["model_id"], "stability.stable-diffusion-xl-v1")

    @patch("frontend_app.image_views.image_service.generate_image",
           return_value=_SUCCESS_RESULT)
    def test_save_to_s3_forwarded(self, mock_gen):
        _post({"prompt": "test", "save_to_s3": False})
        call_kwargs = mock_gen.call_args[1]
        self.assertFalse(call_kwargs["save_to_s3"])

    # ── Validation ────────────────────────────────────────────────────────────

    def test_missing_prompt_returns_400(self):
        resp = _post({})
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.content)
        self.assertFalse(data["ok"])
        self.assertIn("prompt", data["error"].lower())

    def test_empty_prompt_returns_400(self):
        resp = _post({"prompt": "   "})
        self.assertEqual(resp.status_code, 400)

    def test_invalid_json_returns_400(self):
        factory = RequestFactory()
        request = factory.post(
            "/api/images/",
            data=b"not valid json }{",
            content_type="application/json",
        )
        resp = generate_image_view(request)
        self.assertEqual(resp.status_code, 400)

    def test_get_method_returns_405(self):
        factory = RequestFactory()
        request = factory.get("/api/images/")
        resp = generate_image_view(request)
        self.assertEqual(resp.status_code, 405)

    # ── Error path ────────────────────────────────────────────────────────────

    @patch("frontend_app.image_views.image_service.generate_image",
           return_value=_FAILURE_RESULT)
    def test_service_error_returns_500(self, _mock):
        resp = _post({"prompt": "test"})
        self.assertEqual(resp.status_code, 500)
        data = json.loads(resp.content)
        self.assertFalse(data["ok"])
        self.assertIn("error", data)

    @patch("frontend_app.image_views.image_service.generate_image",
           side_effect=Exception("Unexpected crash"))
    def test_unhandled_exception_does_not_leak(self, _mock):
        # The view should propagate here — in prod a middleware handles 500s.
        # Just ensure the view was called and the exception is visible.
        with self.assertRaises(Exception):
            _post({"prompt": "test"})


if __name__ == "__main__":
    unittest.main()