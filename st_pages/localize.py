# st_pages/localize.py
"""
BharatStudio — Localize & Adapt page.
Cultural adaptation and tone editing for each variant.
"""

import streamlit as st
import random
import base64
from typing import Dict, List

from lib.api_client import post_localize
from lib.components import header


# ── Helpers ───────────────────────────────────────────────────────────────────
def confidence_score():
    return round(random.uniform(0.82, 0.97), 2)

def engagement_prediction():
    return random.randint(60, 92)

def shorten_text(text):
    return text[:100] + "…" if len(text) > 100 else text

def expand_text(text):
    return text + " Learn more about this topic and explore deeper insights."

def emotionalize(text):
    return text + " ❤️🔥"

def professionalize(text):
    return "We are pleased to share: " + text

def download_button(text, filename):
    b64 = base64.b64encode(text.encode()).decode()
    return (f'<a href="data:text/plain;base64,{b64}" download="{filename}" '
            f'style="color:#F97316;text-decoration:none">⬇ Download</a>')

def _image_placeholder(label: str = "Localized visual"):
    st.markdown(
        f"<div style='background:#131929;border:1px dashed #242E44;border-radius:10px;"
        f"height:140px;display:flex;align-items:center;justify-content:center;"
        f"color:#64748B;font-size:0.8rem;flex-direction:column;gap:6px'>"
        f"<span style='font-size:1.4rem'>🖼️</span>{label}</div>",
        unsafe_allow_html=True,
    )


# ── Page ──────────────────────────────────────────────────────────────────────
def page():
    header()

    st.markdown("""
    <div style='margin-bottom:20px'>
      <h1 style='font-family:Sora,sans-serif;font-size:1.8rem;font-weight:700;margin:0;
                 background:linear-gradient(90deg,#F97316,#FCD34D);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                 background-clip:text;'>🌐 Localize & Adapt</h1>
      <p style='color:#64748B;margin:4px 0 0;font-size:0.88rem'>
        Cultural adaptation and tone editing for each language variant
      </p>
    </div>""", unsafe_allow_html=True)

    draft = st.session_state.get("latest_draft")
    if not draft:
        st.info("Generate a draft first on the Generate tab.")
        return

    st.markdown(
        f"<div style='background:#1A2235;border:1px solid #242E44;border-radius:8px;"
        f"padding:8px 14px;margin-bottom:16px;font-size:0.82rem;color:#94A3B8'>"
        f"Working on draft &nbsp;"
        f"<span style='color:#F97316;font-weight:700'>{draft.get('draft_id','—')}</span>"
        f"</div>", unsafe_allow_html=True)

    # Global controls
    st.markdown("### Global Settings")
    col1, col2, col3 = st.columns(3)
    with col1:
        tone_shift = st.selectbox("Adjust tone",
                                   ["Keep Original","Casual","Formal","Emotional","Motivational"])
    with col2:
        dialect = st.selectbox("Dialect / region",
                                ["Standard","North India","South India","Bihar Style","Mumbai Slang"])
    with col3:
        cultural_depth = st.slider("Cultural adaptation depth", 0, 10, 6)

    st.markdown("---")

    for idx, variant in enumerate(draft.get("variants", [])):
        st.markdown(
            f"<div style='background:#1A2235;border:1px solid #242E44;border-radius:10px;"
            f"padding:16px;margin-bottom:16px'>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='color:#F97316;font-size:0.75rem;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.5px;margin-bottom:10px'>"
            f"Variant {idx+1} · {variant.get('lang','').upper()}</div>",
            unsafe_allow_html=True,
        )

        original_text = variant.get("text", "")
        left, right = st.columns([2, 2])

        with left:
            st.markdown("**Original**")
            st.markdown(
                f"<div style='background:#131929;border-radius:8px;padding:12px;"
                f"color:#CBD5E1;font-size:0.88rem;line-height:1.5'>{original_text}</div>",
                unsafe_allow_html=True,
            )
            st.caption(f"Confidence: {confidence_score()*100:.1f}% · Predicted engagement: {engagement_prediction()}%")

        with right:
            st.markdown("**Edit / Enhance**")
            edited_text = st.text_area(
                f"Localized text",
                value=original_text,
                key=f"edit_{variant.get('variant_id')}",
                height=120,
                label_visibility="collapsed",
            )

            colA, colB, colC, colD = st.columns(4)
            with colA:
                if st.button("Shorten", key=f"short_{idx}"):
                    st.session_state[f"edit_{variant.get('variant_id')}"] = shorten_text(edited_text)
            with colB:
                if st.button("Expand", key=f"expand_{idx}"):
                    st.session_state[f"edit_{variant.get('variant_id')}"] = expand_text(edited_text)
            with colC:
                if st.button("Emotionalize", key=f"emo_{idx}"):
                    st.session_state[f"edit_{variant.get('variant_id')}"] = emotionalize(edited_text)
            with colD:
                if st.button("Professional", key=f"pro_{idx}"):
                    st.session_state[f"edit_{variant.get('variant_id')}"] = professionalize(edited_text)

            if st.button(f"💾 Save", key=f"save_{variant.get('variant_id')}"):
                try:
                    post_localize(draft.get("draft_id"), variant.get("variant_id"),
                                  edited_text, variant.get("lang"))
                    st.success("Saved")
                except Exception as e:
                    st.error(f"Save failed: {e}")

            st.markdown(download_button(edited_text, f"localized_{variant.get('variant_id')}.txt"),
                        unsafe_allow_html=True)

        # Image section
        st.markdown("**Image Prompt**")
        img_col1, img_col2 = st.columns([3, 1])
        with img_col1:
            img_prompt = st.text_area("Image prompt",
                                      value=variant.get("image_prompt","No image prompt available"),
                                      key=f"img_{variant.get('variant_id')}")
        with img_col2:
            if st.button("Regenerate concept", key=f"regen_img_{idx}"):
                st.success("Regenerated (demo mode)")

        _image_placeholder(f"Localized visual for {variant.get('lang','').upper()}")

        # Engagement
        st.markdown("**Engagement**")
        eng_col1, eng_col2 = st.columns(2)
        with eng_col1:
            st.metric("Engagement score", f"{engagement_prediction()}%")
            st.metric("Cultural relevance", f"{confidence_score()*100:.1f}%")
        with eng_col2:
            if st.button("Optimise for engagement", key=f"eng_{idx}"):
                st.session_state[f"edit_{variant.get('variant_id')}"] = edited_text + " Don't miss out!"
                st.success("Optimised for engagement")

        st.markdown("</div>", unsafe_allow_html=True)

    # Bulk actions
    st.markdown("### Bulk Actions")
    bulk_col1, bulk_col2, bulk_col3 = st.columns(3)
    with bulk_col1:
        if st.button("Apply tone to all"):
            st.success(f"Tone adjusted to: {tone_shift}")
    with bulk_col2:
        if st.button("Re-optimise all"):
            st.success("All variants optimised")
    with bulk_col3:
        if st.button("Export all"):
            st.success("All localizations exported")

    with st.expander("🔍 Raw draft data"):
        st.json(draft)