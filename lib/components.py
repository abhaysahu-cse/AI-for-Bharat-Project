# lib/components.py
import streamlit as st
from PIL import Image
import os

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")

def header():
    logo_path = os.path.join(ASSETS, "logo.png")
    try:
        st.image(logo_path, width=140)
    except Exception:
        st.markdown("### BharatStudio (Prototype UI)")
    st.markdown("### BharatStudio (Prototype UI)\nCreate → Localize → Schedule", unsafe_allow_html=True)
