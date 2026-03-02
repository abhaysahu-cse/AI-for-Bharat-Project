from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("generate/", views.generate_page, name="generate"),
    path("scheduler/", views.scheduler_page, name="scheduler"),
    path("video-gen/", views.video_gen_page, name="video_gen"),
    path("history/", views.history_page, name="history"),
    path("login/", views.login_page, name="login"),
    path("signup/", views.signup_page, name="signup"),
    path("api/generate-ai/", views.generate_ai, name="generate_ai"),
    path("api/history/", views.api_history, name="api_history"),
    path("api/schedule/", views.api_schedule, name="api_schedule"),
]
