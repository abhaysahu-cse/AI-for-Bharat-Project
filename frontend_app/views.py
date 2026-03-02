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

@csrf_exempt
def generate_ai(request):
    if request.method == "POST":
        data = json.loads(request.body)
        prompt = data.get("prompt", "")
        return JsonResponse({"result": f"AI Output for: {prompt}"})
