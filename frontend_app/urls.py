# frontend_app/urls.py
"""
BharatStudio URL configuration.
Include with: path("api/", include("frontend_app.urls"))
"""

from django.urls import path

from .views import (
    create_draft,
    generate_video_script,
    generate_hashtags,
    generate_voice,
    generate_calendar,
    generate_platform_variants,
)
from .image_views import generate_image_view

urlpatterns = [
    # ── Existing ──────────────────────────────────────────
    path("drafts/", create_draft, name="create-draft"),
    path("images/", generate_image_view, name="generate-image"),

    # ── New feature endpoints ──────────────────────────────
    path("generate/video_script/",      generate_video_script,      name="generate-video-script"),
    path("generate/hashtags/",          generate_hashtags,          name="generate-hashtags"),
    path("generate/voice/",             generate_voice,             name="generate-voice"),
    path("generate/calendar/",          generate_calendar,          name="generate-calendar"),
    path("generate/platform_variants/", generate_platform_variants, name="generate-platform-variants"),
]