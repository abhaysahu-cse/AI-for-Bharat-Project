# st_pages/preview_schedule.py
import streamlit as st
from lib.api_client import post_schedule
from lib.components import header

def page():
    header()
    st.header("Preview & Schedule")
    draft = st.session_state.get("latest_draft")
    if not draft:
        st.info("Generate a draft first.")
        return
    platforms = st.multiselect("Select platforms", ["instagram", "twitter", "youtube"], default=["instagram"])
    st.write("Preview (simulate):")
    for variant in draft.get("variants", []):
        st.markdown(f"**Variant {variant['variant_id']} — {variant['lang']}**")
        st.write(variant.get("text"))
        st.image("https://via.placeholder.com/400x225.png?text=Image+Preview", width=360)
        if st.button(f"Schedule variant {variant['variant_id']}"):
            dt = st.date_input("Publish date")
            tm = st.time_input("Publish time")
            publish_time = f"{dt.isoformat()}T{tm.isoformat()}"
            try:
                r = post_schedule(draft.get("draft_id"), variant.get("variant_id"), platforms, publish_time)
                st.success("Scheduled (demo)")
            except Exception as e:
                st.error("Schedule failed: " + str(e))
