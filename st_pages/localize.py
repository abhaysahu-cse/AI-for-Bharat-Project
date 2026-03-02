# st_pages/localize.py
import streamlit as st
from lib.api_client import post_localize
from lib.components import header

def page():
    header()
    st.header("Localize & Edit")
    draft = st.session_state.get("latest_draft")
    if not draft:
        st.info("Generate a draft first on the Generate tab.")
        return
    st.write("Draft ID:", draft.get("draft_id"))
    for variant in draft.get("variants", []):
        st.subheader(f"Variant {variant.get('variant_id')} — {variant.get('lang')}")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Original**")
            st.write(variant.get("text"))
        with col2:
            st.markdown("**Edit / Localize**")
            new_text = st.text_area(f"Edit {variant.get('variant_id')}", value=variant.get("text"))
            if st.button(f"Save {variant.get('variant_id')}"):
                try:
                    res = post_localize(draft.get("draft_id"), variant.get("variant_id"), new_text, variant.get("lang"))
                    st.success("Saved")
                except Exception as e:
                    st.error("Save failed: " + str(e))
