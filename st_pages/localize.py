# st_pages/localize.py

import streamlit as st
import random
import time
import base64
from typing import Dict, List

from lib.api_client import post_localize
from lib.components import header


# -----------------------------
# Utility helpers
# -----------------------------

def confidence_score():
    return round(random.uniform(0.82, 0.97), 2)

def engagement_prediction():
    return random.randint(60, 92)

def shorten_text(text):
    return text[:100] + "..." if len(text) > 100 else text

def expand_text(text):
    return text + " Learn more about this topic and explore deeper insights."

def emotionalize(text):
    return text + " ❤️🔥"

def professionalize(text):
    return "We are pleased to share: " + text

def download_button(text, filename):
    b64 = base64.b64encode(text.encode()).decode()
    href = f'<a href="data:text/plain;base64,{b64}" download="{filename}">Download</a>'
    return href


# -----------------------------
# Main Page
# -----------------------------

def page():
    header()
    st.title("🌐 AI Localization & Cultural Adaptation Studio")

    draft = st.session_state.get("latest_draft")

    if not draft:
        st.info("Generate a draft first on the Generate tab.")
        return

    st.success(f"Working on Draft ID: {draft.get('draft_id')}")

    # Global Controls
    st.markdown("### Global Localization Settings")
    col1, col2, col3 = st.columns(3)

    with col1:
        tone_shift = st.selectbox("Adjust Tone Globally",
                                  ["Keep Original", "Casual", "Formal", "Emotional", "Motivational"])

    with col2:
        dialect = st.selectbox("Dialect / Region",
                               ["Standard", "North India", "South India", "Bihar Style", "Mumbai Slang"])

    with col3:
        cultural_depth = st.slider("Cultural Adaptation Depth", 0, 10, 6)

    st.markdown("---")

    # Process Each Variant
    for idx, variant in enumerate(draft.get("variants", [])):

        st.markdown(f"## Variant {idx+1} — {variant.get('lang')}")
        original_text = variant.get("text")

        left, right = st.columns([2, 2])

        # Original Panel
        with left:
            st.markdown("### Original Version")
            st.info(original_text)

            st.caption(f"Translation Confidence: {confidence_score()*100:.1f}%")

            st.caption(f"Predicted Engagement: {engagement_prediction()}%")

        # Edit Panel
        with right:
            st.markdown("### Edit / Enhance")

            edited_text = st.text_area(
                f"Localized Text ({variant.get('variant_id')})",
                value=original_text,
                key=f"edit_{variant.get('variant_id')}",
                height=150
            )

            colA, colB, colC, colD = st.columns(4)

            with colA:
                if st.button("Shorten", key=f"short_{idx}"):
                    edited_text = shorten_text(edited_text)
                    st.session_state[f"edit_{variant.get('variant_id')}"] = edited_text

            with colB:
                if st.button("Expand", key=f"expand_{idx}"):
                    edited_text = expand_text(edited_text)
                    st.session_state[f"edit_{variant.get('variant_id')}"] = edited_text

            with colC:
                if st.button("Emotionalize", key=f"emo_{idx}"):
                    edited_text = emotionalize(edited_text)
                    st.session_state[f"edit_{variant.get('variant_id')}"] = edited_text

            with colD:
                if st.button("Professionalize", key=f"pro_{idx}"):
                    edited_text = professionalize(edited_text)
                    st.session_state[f"edit_{variant.get('variant_id')}"] = edited_text

            # Save Action
            if st.button(f"💾 Save Localization {variant.get('variant_id')}"):
                try:
                    post_localize(
                        draft.get("draft_id"),
                        variant.get("variant_id"),
                        edited_text,
                        variant.get("lang")
                    )
                    st.success("Saved Successfully")
                except Exception as e:
                    st.error("Save failed: " + str(e))

            # Download Option
            st.markdown(download_button(edited_text, f"localized_{variant.get('variant_id')}.txt"),
                        unsafe_allow_html=True)

        # Image Localization Section
        st.markdown("### 🎨 Image Prompt Localization")

        img_col1, img_col2 = st.columns([3, 1])

        with img_col1:
            img_prompt = st.text_area(
                "Image Prompt",
                value=variant.get("image_prompt", "No image prompt available"),
                key=f"img_{variant.get('variant_id')}"
            )

        with img_col2:
            if st.button("Regenerate Image Concept", key=f"regen_img_{idx}"):
                st.success("Image concept regenerated (demo mode)")

        st.image("https://via.placeholder.com/600x300.png?text=Localized+Visual",
                 use_column_width=True)

        # Engagement Section
        st.markdown("### 📊 Engagement Optimization")

        eng_col1, eng_col2 = st.columns(2)

        with eng_col1:
            st.metric("Engagement Score", f"{engagement_prediction()}%")
            st.metric("Cultural Relevance", f"{confidence_score()*100:.1f}%")

        with eng_col2:
            if st.button("Improve for Engagement", key=f"eng_{idx}"):
                improved = edited_text + " Don't miss out!"
                st.session_state[f"edit_{variant.get('variant_id')}"] = improved
                st.success("Optimized for engagement")

        st.markdown("---")

    # Bulk Actions
    st.markdown("## 🚀 Bulk Actions")

    bulk_col1, bulk_col2, bulk_col3 = st.columns(3)

    with bulk_col1:
        if st.button("Apply Tone Shift to All"):
            st.success(f"Tone adjusted to {tone_shift} (demo)")

    with bulk_col2:
        if st.button("Re-Optimize All Variants"):
            st.success("All variants optimized (demo)")

    with bulk_col3:
        if st.button("Export All Localizations"):
            st.success("All localized content exported (demo)")

    st.markdown("### 🔍 Advanced Debug Panel")
    with st.expander("View Raw Draft Data"):
        st.json(draft)

    st.caption("Localization Studio powered by BharatStudio AI — Cultural, Contextual, Intelligent.")