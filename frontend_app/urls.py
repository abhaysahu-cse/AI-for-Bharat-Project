# frontend_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("drafts/", views.drafts_list_create, name="drafts_list_create"),
    path("drafts/<str:draft_id>/localize", views.draft_localize, name="draft_localize"),
    path("drafts/<str:draft_id>/schedule", views.draft_schedule, name="draft_schedule"),
    path("analytics/drafts/<str:draft_id>", views.draft_analytics, name="draft_analytics"),
]