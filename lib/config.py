# lib/config.py
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("DJANGO_API_URL", "http://127.0.0.1:8000/api")
API_KEY = os.getenv("STREAMLIT_API_KEY", "")
USE_MOCK = os.getenv("USE_MOCK", "true").lower() in ("1", "true", "yes")
TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
