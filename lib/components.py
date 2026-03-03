# lib/components.py

import streamlit as st
import os
from typing import Dict, Any
from PIL import Image

# Import config safely - no dotenv loading here
try:
    from lib.config import USE_MOCK
except ImportError:
    USE_MOCK = True

# Use absolute path for assets
ASSETS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))

# Ensure assets directory exists
if not os.path.exists(ASSETS):
    os.makedirs(ASSETS, exist_ok=True)


# -----------------------------
# Header / Top Navigation Bar
# -----------------------------
def header(show_status: bool = True):
    """
    Robust header with safe image loading.
    Never crashes even if logo is missing or corrupted.
    """
    col1, col2, col3 = st.columns([1, 4, 1])

    with col1:
        logo_path = os.path.join(ASSETS, "logo.png")
        logo_loaded = False
        
        # Safe image loading with multiple checks
        if os.path.exists(logo_path):
            try:
                # Check file size (must be > 0 bytes)
                file_size = os.path.getsize(logo_path)
                if file_size > 0:
                    # Verify image integrity with PIL
                    with Image.open(logo_path) as img:
                        img.verify()
                    # If verification passed, load and display
                    with Image.open(logo_path) as img:
                        st.image(img, width=110)
                        logo_loaded = True
            except Exception as e:
                # Log error but don't crash
                st.caption("⚠️ Logo")
        
        # Fallback to text if image failed
        if not logo_loaded:
            st.markdown("**BS**")  # BharatStudio initials

    with col2:
        st.markdown(
            """
            <h2 style='margin-bottom:0'>BharatStudio</h2>
            <small style='color:gray'>Create → Localize → Schedule → Analyze</small>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        if show_status:
            if USE_MOCK:
                st.markdown(
                    "<span style='color:orange;font-weight:bold'>🟠 MOCK MODE</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<span style='color:green;font-weight:bold'>🟢 LIVE BACKEND</span>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")


# -----------------------------
# Section Title
# -----------------------------
def section_title(title: str, subtitle: str = ""):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.markdown("---")


# -----------------------------
# Variant Card (Enhanced)
# -----------------------------
def variant_card(variant: Dict[str, Any], show_actions: bool = True):
    variant_id = variant.get("variant_id", "v?")
    lang = variant.get("lang", "—")
    text = variant.get("text", "")
    image_prompt = variant.get("image_prompt", "")

    st.markdown(f"### 🌐 Variant `{variant_id}` — {lang.upper()}")

    col1, col2 = st.columns([3, 2])

    with col1:
        st.write(text)

        if show_actions:
            action_col1, action_col2, action_col3 = st.columns(3)

            with action_col1:
                if st.button("📋 Copy Text", key=f"copy_{variant_id}"):
                    st.toast("Copy manually (Ctrl+C) — Clipboard API demo only.")

            with action_col2:
                if st.button("✏ Edit", key=f"edit_{variant_id}"):
                    st.info("Open Localize tab to edit this variant.")

            with action_col3:
                if st.button("📊 Analyze", key=f"analyze_{variant_id}"):
                    st.info("Open Analytics tab for performance insights.")

    with col2:
        placeholder_path = os.path.join(ASSETS, "placeholder_image.png")
        # Safe image loading
        if os.path.exists(placeholder_path):
            try:
                file_size = os.path.getsize(placeholder_path)
                if file_size > 0:
                    with Image.open(placeholder_path) as img:
                        img.verify()
                    with Image.open(placeholder_path) as img:
                        st.image(img, use_column_width=True)
                else:
                    st.info("Image preview placeholder")
            except Exception:
                st.info("Image preview placeholder")
        else:
            st.info("Image preview placeholder")

        if image_prompt:
            with st.expander("🎨 Image Prompt"):
                st.write(image_prompt)

    st.markdown("---")


# -----------------------------
# KPI Card Component
# -----------------------------
def kpi_card(title: str, value: Any, delta: Any = None):
    st.markdown(f"**{title}**")
    st.markdown(f"<h3 style='margin:0'>{value}</h3>", unsafe_allow_html=True)
    if delta:
        st.caption(f"Δ {delta}")


# -----------------------------
# Info Box
# -----------------------------
def info_box(message: str, type_: str = "info"):
    if type_ == "success":
        st.success(message)
    elif type_ == "warning":
        st.warning(message)
    elif type_ == "error":
        st.error(message)
    else:
        st.info(message)


# -----------------------------
# Loading Wrapper
# -----------------------------
def loading_spinner(text="Processing..."):
    return st.spinner(text)