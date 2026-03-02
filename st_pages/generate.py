# st_pages/generate.py
import streamlit as st
from lib.api_client import post_create_draft
from lib.components import header

def page():
    header()
    st.header("Generate Content")
    col1, col2 = st.columns([2, 1])
    with col1:
        prompt = st.text_area("Idea / Prompt", height=140, value="Monsoon street food in Patna — short IG caption")
        content_type = st.selectbox("Content type", ["instagram_post", "short_video", "tweet"])
        tone = st.selectbox("Tone", ["casual", "formal", "witty"])
        languages = st.multiselect("Target languages", ["en", "hi", "ta"], default=["en","hi"])
        if st.button("Generate Drafts"):
            try:
                draft = post_create_draft(prompt, content_type, tone, languages)
                st.success("Drafts generated")
                st.session_state["latest_draft"] = draft
                st.rerun()
            except Exception as e:
                st.error(f"Generate failed: {e}")
    with col2:
        st.info("Tips:\n• Mention region; • Use short phrases; • Add tone")
        if st.button("Load sample prompt"):
            st.experimental_set_query_params(p= "Monsoon samosa reel idea")
