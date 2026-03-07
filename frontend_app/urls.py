# frontend_app/urls.py
from django.urls import path
from . import views
from .image_views import generate_image_view

urlpatterns = [
    path("drafts/", views.drafts_list_create, name="drafts_list_create"),
    path("drafts/<str:draft_id>/localize", views.draft_localize, name="draft_localize"),
    path("drafts/<str:draft_id>/schedule", views.draft_schedule, name="draft_schedule"),
    path("analytics/drafts/<str:draft_id>", views.draft_analytics, name="draft_analytics"),

     # ── NEW: standalone image generation endpoint ─────────────────────────────
    # POST /api/images/  { "prompt": "...", "model": "...", "save_to_s3": true }
    path("images/",                             generate_image_view,      name="generate_image"),



]