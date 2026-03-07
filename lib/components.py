# lib/components.py
"""
BharatStudio shared UI components.
All functional logic unchanged — only visual styling upgraded.
"""

import streamlit as st
import os
from typing import Dict, Any

try:
    from lib.config import USE_MOCK
except ImportError:
    USE_MOCK = True

ASSETS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
if not os.path.exists(ASSETS):
    os.makedirs(ASSETS, exist_ok=True)


# ── Inner page header (shown inside every page's content area) ────────────────
def header(show_status: bool = True):
    """
    Slim branded divider rendered at the top of each page's content area.
    Replaced the old 3-column logo+text layout with a single clean gradient bar.
    """
    badge_html = ""
    if show_status:
        if USE_MOCK:
            badge_html = (
                "<span style='background:rgba(249,115,22,0.12);border:1px solid rgba(249,115,22,0.3);"
                "color:#F97316;font-size:0.7rem;font-weight:600;padding:2px 9px;border-radius:20px;"
                "letter-spacing:0.3px;'>● Demo Mode</span>"
            )
        else:
            badge_html = (
                "<span style='background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.3);"
                "color:#10B981;font-size:0.7rem;font-weight:600;padding:2px 9px;border-radius:20px;"
                "letter-spacing:0.3px;'>● Live</span>"
            )

    st.markdown(
        f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:10px 0 12px;margin-bottom:4px;">
          <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-family:'Sora',sans-serif;font-size:1rem;font-weight:700;
                         background:linear-gradient(90deg,#F97316,#FCD34D);
                         -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                         background-clip:text;">✦ BharatStudio</span>
            <span style="font-size:0.72rem;color:#64748B;">
              Create → Localize → Optimize → Publish
            </span>
          </div>
          {badge_html}
        </div>
        <div style="height:1px;background:linear-gradient(90deg,#F97316 0%,#FCD34D 30%,
                    transparent 100%);margin-bottom:20px;opacity:0.4;"></div>
        """,
        unsafe_allow_html=True,
    )


# ── Section title ─────────────────────────────────────────────────────────────
def section_title(title: str, subtitle: str = ""):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.markdown("---")


# ── Variant card ──────────────────────────────────────────────────────────────
def variant_card(variant: Dict[str, Any], show_actions: bool = True):
    """Renders a single variant card — visual upgrade only, same fields."""
    variant_id  = variant.get("variant_id", "v?")
    lang        = variant.get("lang", "—")
    text        = variant.get("text", "")
    image_prompt= variant.get("image_prompt", "")

    st.markdown(
        f"""
        <div style="background:#1A2235;border:1px solid #242E44;border-radius:12px;
                    padding:14px 16px;margin-bottom:8px;">
          <div style="font-size:0.72rem;color:#F97316;font-weight:600;
                      letter-spacing:0.5px;margin-bottom:8px;text-transform:uppercase;">
            {lang.upper()} · Variant {variant_id}
          </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 2])
    with col1:
        st.write(text)
        if show_actions:
            a1, a2, a3 = st.columns(3)
            with a1:
                if st.button("📋 Copy", key=f"copy_{variant_id}"):
                    st.toast("Select text above and press Ctrl+C")
            with a2:
                if st.button("✏️ Edit", key=f"edit_{variant_id}"):
                    st.info("Open Localize tab to edit.")
            with a3:
                if st.button("📊 Stats", key=f"analyze_{variant_id}"):
                    st.info("Open Analytics tab.")
    with col2:
        placeholder_path = os.path.join(ASSETS, "placeholder_image.png")
        try:
            if os.path.exists(placeholder_path) and os.path.getsize(placeholder_path) > 0:
                from PIL import Image as PILImage
                with PILImage.open(placeholder_path) as img:
                    img.verify()
                with PILImage.open(placeholder_path) as img:
                    st.image(img, use_column_width=True)
            else:
                st.markdown(
                    "<div style='background:#131929;border:1px dashed #242E44;border-radius:8px;"
                    "height:90px;display:flex;align-items:center;justify-content:center;"
                    "color:#64748B;font-size:0.75rem;'>Image preview</div>",
                    unsafe_allow_html=True,
                )
        except Exception:
            st.markdown(
                "<div style='background:#131929;border:1px dashed #242E44;border-radius:8px;"
                "height:90px;display:flex;align-items:center;justify-content:center;"
                "color:#64748B;font-size:0.75rem;'>Image preview</div>",
                unsafe_allow_html=True,
            )
        if image_prompt:
            with st.expander("🎨 Image prompt"):
                st.write(image_prompt)

    st.markdown("</div>", unsafe_allow_html=True)


# ── KPI card ──────────────────────────────────────────────────────────────────
def kpi_card(title: str, value: Any, delta: Any = None):
    st.markdown(
        f"""
        <div style="background:#1A2235;border:1px solid #242E44;border-radius:10px;
                    padding:14px 16px;">
          <div style="font-size:0.72rem;color:#64748B;text-transform:uppercase;
                      letter-spacing:0.8px;margin-bottom:4px;">{title}</div>
          <div style="font-size:1.6rem;font-weight:700;color:#E2E8F0;">{value}</div>
          {'<div style="font-size:0.75rem;color:#F97316;">Δ ' + str(delta) + '</div>' if delta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Info box ──────────────────────────────────────────────────────────────────
def info_box(message: str, type_: str = "info"):
    if type_ == "success":
        st.success(message)
    elif type_ == "warning":
        st.warning(message)
    elif type_ == "error":
        st.error(message)
    else:
        st.info(message)


# ── Loading spinner ───────────────────────────────────────────────────────────
def loading_spinner(text="Processing…"):
    return st.spinner(text)