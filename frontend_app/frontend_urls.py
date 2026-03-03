# backend/frontend_app/frontend_urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("generate/", views.generate_page, name="generate"),
    path("history/", views.history_page, name="history"),
    path("scheduler/", views.scheduler_page, name="scheduler"),
    # add others if you want: /video/, /analytics/ etc.
]