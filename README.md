# BharatStudio — Streamlit Prototype UI

## Setup
1. python -m venv venv && source venv/bin/activate
2. pip install -r requirements.txt
3. cp .env.sample .env  # update DJANGO_API_URL and STREAMLIT_API_KEY
4. streamlit run prototype_app.py

Notes:
- Default is USE_MOCK=true which returns demo data.
- Point DJANGO_API_URL to your Django API and set STREAMLIT_API_KEY to demo token for real integration.s