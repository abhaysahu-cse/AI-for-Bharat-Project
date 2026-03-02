from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("generate/", views.generate_page, name="generate"),
    path("scheduler/", views.scheduler_page, name="scheduler"),
    path("api/generate-ai/", views.generate_ai, name="generate_ai"),
]
