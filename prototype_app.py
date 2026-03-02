import streamlit as st
from importlib import import_module

PAGE_MAP = {
    "Generate Content": "st_pages.generate",
    "Localize & Edit": "st_pages.localize",
    "Preview & Schedule": "st_pages.preview_schedule",
    "History": "st_pages.history",
    "Analytics": "st_pages.analytics"
}

st.set_page_config(page_title="BharatStudio Prototype", layout="wide")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", list(PAGE_MAP.keys()))

module = import_module(PAGE_MAP[page])
module.page()