# tests/test_video_script_endpoint.py
"""
Unit tests for POST /api/generate/video_script/

Run with:  pytest tests/test_video_script_endpoint.py -v
"""

import json
import os
import unittest
from unittest.mock import MagicMock, patch

# Ensure mock mode so no real AWS calls
os.environ.setdefault("USE_BEDROCK", "false")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from django.test import RequestFactory

from frontend_app.views import generate_video_script as view_generate_video_script


MOCK_SCENES = [
    {"scene": 1, "duration_seconds": 6, "shot": "Opening wide shot of street", "camera": "wide", "sfx": "ambient"},
    {"scene": 2, "duration_seconds": 8, "shot": "Close-up of steaming samosa", "camera": "close-up", "sfx": ""},
    {"scene": 3, "duration_seconds": 6, "shot": "Pan across the food stalls", "camera": "pan", "sfx": ""},
    {"scene": 4, "duration_seconds": 6, "shot": "Closing shot with CTA overlay", "camera": "wide", "sfx": "upbeat"},
]


class TestVideoScriptEndpointSchema(unittest.TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def _post(self, body: dict):
        req = self.factory.post(
            "/api/generate/video_script/",
            data=json.dumps(body).encode("utf-8"),
            content_type="application/json",
        )
        return view_generate_video_script(req)

    # ── 1. Happy path: USE_BEDROCK=false mock ──────────────────────────────

    def test_returns_200_on_valid_input(self):
        resp = self._post({"prompt": "Monsoon street food in Patna", "languages": ["en"]})
        self.assertEqual(resp.status_code, 200)

    def test_response_has_required_keys(self):
        resp = self._post({"prompt": "Monsoon street food", "languages": ["en"]})
        data = json.loads(resp.content)
        self.assertIn("prompt", data)
        self.assertIn("scripts", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "ok")

    def test_scripts_list_length_matches_languages(self):
        langs = ["en", "hi"]
        resp = self._post({"prompt": "AI in education", "languages": langs})
        data = json.loads(resp.content)
        self.assertEqual(len(data["scripts"]), len(langs))

    def test_each_script_has_lang_and_video_script_keys(self):
        resp = self._post({"prompt": "Diwali sale", "languages": ["en", "hi"]})
        data = json.loads(resp.content)
        for s in data["scripts"]:
            self.assertIn("lang", s)
            self.assertIn("video_script", s)

    def test_video_script_field_is_valid_json_string(self):
        resp = self._post({"prompt": "Street food", "languages": ["en"]})
        data = json.loads(resp.content)
        for s in data["scripts"]:
            parsed = json.loads(s["video_script"])
            self.assertIsInstance(parsed, list)

    def test_scenes_have_expected_fields(self):
        resp = self._post({"prompt": "Street food", "languages": ["en"]})
        data = json.loads(resp.content)
        scenes = json.loads(data["scripts"][0]["video_script"])
        self.assertGreater(len(scenes), 0)
        first = scenes[0]
        self.assertIn("scene", first)
        self.assertIn("shot", first)
        self.assertIn("duration_seconds", first)

    def test_prompt_echoed_in_response(self):
        prompt = "Holi festival celebrations"
        resp = self._post({"prompt": prompt, "languages": ["en"]})
        data = json.loads(resp.content)
        self.assertEqual(data["prompt"], prompt)

    # ── 2. Input validation ────────────────────────────────────────────────

    def test_missing_prompt_returns_400(self):
        resp = self._post({"languages": ["en"]})
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.content)
        self.assertEqual(data["status"], "error")

    def test_empty_prompt_returns_400(self):
        resp = self._post({"prompt": "   ", "languages": ["en"]})
        self.assertEqual(resp.status_code, 400)

    def test_bad_json_body_returns_400(self):
        req = self.factory.post(
            "/api/generate/video_script/",
            data=b"NOT JSON {{",
            content_type="application/json",
        )
        resp = view_generate_video_script(req)
        self.assertEqual(resp.status_code, 400)

    def test_languages_defaults_to_en_if_omitted(self):
        resp = self._post({"prompt": "Cricket fever"})
        data = json.loads(resp.content)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(len(data["scripts"]), 1)
        self.assertEqual(data["scripts"][0]["lang"], "en")

    # ── 3. Bedrock integration (mocked) ───────────────────────────────────

    @patch("frontend_app.views.BedrockService")
    def test_bedrock_result_is_returned_when_use_bedrock_true(self, MockBedrock):
        """When USE_BEDROCK=true, view must call bedrock service and return its scenes."""
        mock_service = MagicMock()
        mock_service.generate_video_script.return_value = [
            {"lang": "en", "scenes": MOCK_SCENES}
        ]
        MockBedrock.return_value = mock_service

        with patch.dict(os.environ, {"USE_BEDROCK": "true"}):
            resp = self._post({"prompt": "IPL opening ceremony", "languages": ["en"]})

        data = json.loads(resp.content)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(len(data["scripts"]), 1)
        scenes = json.loads(data["scripts"][0]["video_script"])
        self.assertEqual(len(scenes), len(MOCK_SCENES))

    @patch("frontend_app.views.BedrockService")
    def test_bedrock_exception_returns_500(self, MockBedrock):
        """If Bedrock raises, view must return status 500 with error message."""
        mock_service = MagicMock()
        mock_service.generate_video_script.side_effect = RuntimeError("Bedrock quota exceeded")
        MockBedrock.return_value = mock_service

        with patch.dict(os.environ, {"USE_BEDROCK": "true"}):
            resp = self._post({"prompt": "Cricket final", "languages": ["en"]})

        self.assertEqual(resp.status_code, 500)
        data = json.loads(resp.content)
        self.assertEqual(data["status"], "error")
        self.assertIn("error", data)

    # ── 4. GET request rejected ────────────────────────────────────────────

    def test_get_request_rejected(self):
        req = self.factory.get("/api/generate/video_script/")
        resp = view_generate_video_script(req)
        self.assertEqual(resp.status_code, 405)


if __name__ == "__main__":
    unittest.main()