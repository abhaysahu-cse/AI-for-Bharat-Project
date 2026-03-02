from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def index(request):
    return render(request, "index.html")

def generate_page(request):
    return render(request, "generate.html")

def scheduler_page(request):
    return render(request, "scheduler.html")

def video_gen_page(request):
    return render(request, "video_gen.html")

def history_page(request):
    return render(request, "history.html")

def login_page(request):
    return render(request, "login.html")

def signup_page(request):
    return render(request, "signup.html")

@csrf_exempt
def generate_ai(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            prompt = data.get("prompt", "")
            return JsonResponse({"result": f"AI Output for: {prompt}"})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    return JsonResponse({"error": "POST required"}, status=405)

def api_history(request):
    # Mock history data
    history_data = [
        {
            "id": 1,
            "topic": "Future of AI in India",
            "content_type": "YouTube Script",
            "language": "Hindi",
            "created_at": "2026-03-02T12:00:00Z",
            "generated_text": "[CAPTION] Exploring the future of AI in India... [SCENES] Scene 1..."
        }
    ]
    return JsonResponse(history_data, safe=False)

@csrf_exempt
def api_schedule(request):
    if request.method == "POST":
        return JsonResponse({"status": "success", "message": "Content scheduled"})
    return JsonResponse({"error": "POST required"}, status=405)
