# st_pages/analytics.py
import streamlit as st
from lib.api_client import get_analytics
from lib.components import header

def page():
    header()
    st.header("Analytics")
    draft = st.session_state.get("latest_draft")
    if not draft:
        st.info("Generate a draft first (Go to Generate Content).")
        return
    draft_id = draft.get("draft_id")
    st.write("Draft ID:", draft_id)
    try:
        stats = get_analytics(draft_id)
    except Exception as e:
        st.error(f"Could not fetch analytics: {e}")
        return
    col1, col2, col3 = st.columns(3)
    col1.metric("Impressions", stats.get("impressions", 0))
    col2.metric("Likes", stats.get("likes", 0))
    col3.metric("Shares", stats.get("shares", 0))
    st.subheader("AI suggestions / insights")
    for s in stats.get("suggestions", []):
        st.write("•", s)
    timeline = stats.get("timeline")
    if timeline and isinstance(timeline, list):
        st.subheader("Engagement timeline")
        try:
            st.line_chart(timeline)
        except Exception:
            st.write("Timeline present but can't render chart in demo.")
    st.markdown("---")
    st.caption("Tip: After scheduling a post in Preview & Schedule, come back here to see mock analytics.")
