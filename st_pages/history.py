# st_pages/history.py
import streamlit as st
from lib.api_client import get_recent_drafts
from lib.components import header

def page():
    header()
    st.header("Recent Drafts")
    drafts = get_recent_drafts()
    for d in drafts:
        st.markdown(f"**{d.get('draft_id')}** — {d.get('prompt')}")
        for v in d.get("variants", []):
            st.write(f"- {v.get('lang')}: {v.get('text')[:120]}")
