# backend/frontend_app/models.py
from django.db import models
import uuid

class Draft(models.Model):
    draft_id = models.CharField(max_length=64, primary_key=True, default=uuid.uuid4)
    prompt = models.TextField()
    content_type = models.CharField(max_length=64, default="instagram_post")
    tone = models.CharField(max_length=32, default="casual")
    status = models.CharField(max_length=32, default="generated")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.draft_id} - {self.prompt[:40]}"

class Variant(models.Model):
    variant_id = models.CharField(max_length=64, primary_key=True)
    draft = models.ForeignKey(Draft, related_name="variants", on_delete=models.CASCADE)
    lang = models.CharField(max_length=12, default="en")
    text = models.TextField()
    image_prompt = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=32, default="generated")

    def __str__(self):
        return f"{self.variant_id} ({self.lang})"

class Schedule(models.Model):
    schedule_id = models.CharField(max_length=64, primary_key=True, default=uuid.uuid4)
    draft = models.ForeignKey(Draft, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    platform = models.CharField(max_length=64)
    publish_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=32, default="scheduled")