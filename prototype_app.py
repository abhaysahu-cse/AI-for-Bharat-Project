# prototype_app.py
"""
Product-ish Streamlit launcher for the BharatStudio prototype.

Features:
- Top header with title, version, mode (mock vs real)
- Sidebar with logo, navigation, quick actions, and repo link
- Dynamic discovery of pages inside `st_pages` package (automatically picks up new pages)
- Safe import and error display for pages (traceback in UI)
- Page load timing and simple smoke-test runner (if available)
- Debug toggle to show session state & config
"""

import streamlit as st
import importlib
import pkgutil
import time
import os
import traceback
from typing import Dict, List

# Ensure assets exist before anything else
try:
    from lib.asset_generator import ensure_assets_exist
    ensure_assets_exist()
except Exception as e:
    print(f"Warning: Asset generation failed: {e}")

# ---- Config / constants ----
APP_TITLE = "BharatStudio Prototype"
APP_SUB = "Create → Localize → Schedule"
APP_VERSION = "v0.9-proto"
REPO_URL = "https://github.com/abhaysahu-cse/AI-for-Bharat-Project"
LOGO_PATH = "logo.png"  # keep a logo in repo root / lib assets or change path

# Optional: prefer lib.config if present
USE_MOCK = os.environ.get("USE_MOCK", "true").lower() in ("1", "true", "yes")
DJANGO_API_URL = os.environ.get("DJANGO_API_URL", "http://127.0.0.1:8000/api")

# Fallback static map (keeps compatibility with your previous code)
FALLBACK_PAGE_MAP = {
    "Generate Content": "st_pages.generate",
    "Localize & Edit": "st_pages.localize",
    "Preview & Schedule": "st_pages.preview_schedule",
    "History": "st_pages.history",
    "Analytics": "st_pages.analytics",
}

# ---- Helpers ----

def discover_st_pages() -> Dict[str, str]:
    """
    Discover modules under the st_pages package and return a mapping:
      friendly_name -> import_path

    If discovery fails, return FALLBACK_PAGE_MAP.
    """
    try:
        pkg = importlib.import_module("st_pages")
        pkg_path = getattr(pkg, "__path__", None)
        if not pkg_path:
            return FALLBACK_PAGE_MAP

        pages = {}
        # iterate modules under st_pages
        for finder, name, ispkg in pkgutil.iter_modules(pkg_path):
            if ispkg:
                continue
            import_path = f"st_pages.{name}"
            # Friendly label: convert underscore to Title Case
            label = " ".join(part.capitalize() for part in name.split("_"))
            pages[label] = import_path

        # Keep a deterministic order: sensible default ordering if present
        preferred_order = ["Generate Content", "Localize & Edit", "Preview & Schedule", "History", "Analytics"]
        ordered = {}
        # first add preferred if present
        for k in preferred_order:
            if k in pages:
                ordered[k] = pages.pop(k)
        # add the rest
        for k in sorted(pages.keys()):
            ordered[k] = pages[k]
        # If discovery produced nothing, fallback
        return ordered if ordered else FALLBACK_PAGE_MAP
    except Exception:
        return FALLBACK_PAGE_MAP

def safe_import_and_run(module_path: str):
    """
    Import module_path and call module.page() if present.
    Returns tuple (ok:bool, err:str or None, load_time:float)
    """
    start = time.perf_counter()
    try:
        module = importlib.import_module(module_path)
    except Exception as e:
        return False, f"ImportError: {e}\n\n{traceback.format_exc()}", 0.0

    if not hasattr(module, "page"):
        return False, f"Module '{module_path}' has no page() function.", 0.0

    try:
        module.page()
        took = time.perf_counter() - start
        return True, None, took
    except Exception as e:
        return False, f"RuntimeError while running {module_path}.page():\n\n{traceback.format_exc()}", 0.0

# ---- UI Layout ----

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")

# Sidebar: logo + navigation + quick actions
with st.sidebar:
    # logo if exists
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=160)
    st.markdown(f"## {APP_TITLE}")
    st.markdown(APP_SUB)
    st.caption(f"{APP_VERSION} • mode: {'mock' if USE_MOCK else 'live'}")

    st.markdown("---")
    st.markdown("### Navigation")

# Discover pages
PAGE_MAP = discover_st_pages()
PAGE_TITLES = list(PAGE_MAP.keys())

# Sidebar navigation (radio)
with st.sidebar:
    page_choice = st.radio("Go to", PAGE_TITLES, index=0)

    st.markdown("---")
    st.markdown("### Quick actions")
    if st.button("🔁 Reload app (soft)"):
        st.experimental_rerun()

    # Restore latest draft action
    if st.button("↩️ Restore latest draft to session"):
        # a simple convenience: instruct user how to restore via History/Generate
        st.toast = None
        st.success("Restored: (demo) — copy a draft from History → Restore to use in Generate/Localize.")
        # If you want a real restore hook, the History page already sets st.session_state['latest_draft']
        # We cannot magically create a draft here without backend, so we just inform the user.

    # Smoke test runner (optional)
    try:
        # check if st_pages.test_pages module exists and exposes run_smoke_tests()
        test_mod = importlib.import_module("st_pages.test_pages")
        if hasattr(test_mod, "run_smoke_tests"):
            if st.button("▶️ Run smoke tests"):
                st.info("Running smoke tests (see console/logs and results below)...")
                try:
                    results = test_mod.run_smoke_tests()
                    st.success("Smoke tests completed (see result object below).")
                    st.json(results)
                except Exception as e:
                    st.error(f"Smoke tests failed: {e}")
        else:
            st.write("")  # no-op placeholder
    except Exception:
        # no test module => ignore
        pass

    st.markdown("---")
    st.markdown("### Environment")
    st.markdown(f"- API: `{DJANGO_API_URL}`")
    st.markdown(f"- Mock mode: **{USE_MOCK}**")

    st.markdown("---")
    st.markdown("### Links")
    st.markdown(f"- [GitHub repo]({REPO_URL})")
    st.markdown("- [Submission instructions](#)")

    st.markdown("---")
    # small debug toggles
    show_debug = st.checkbox("Show debug data", value=False)

# Top header (main area)
title_col, badge_col = st.columns([8, 2])
with title_col:
    st.title(APP_TITLE)
    st.write(APP_SUB)
with badge_col:
    st.markdown(f"**{APP_VERSION}**")
    st.markdown(f"Mode: **{'mock' if USE_MOCK else 'live'}**")
    if st.button("Help"):
        st.info("Use the left navigation to jump between pages. Generate → Localize → Preview → Schedule → Analytics.")

st.markdown("---")

# Running the selected page
selected_module = PAGE_MAP.get(page_choice)
st.write(f"Loading: **{page_choice}** — `{selected_module}`")

# Global safety wrapper - catch all exceptions
try:
    ok, err, load_time = safe_import_and_run(selected_module)
    if ok:
        st.success(f"Page loaded in {load_time*1000:.0f} ms")
    else:
        st.error("Failed to load page.")
        st.code(err, language="python")
        st.warning("Check error trace above, fix page module, then click Reload app.")
except Exception as e:
    st.error("⚠️ Page failed to load - Critical Error")
    st.exception(e)
    st.info("The page encountered an unexpected error. Please check the logs and try reloading.")

# Footer area with small utilities
st.markdown("---")
footer_col1, footer_col2 = st.columns([3, 1])
with footer_col1:
    st.caption("Prototype UI — built for hackathon demo. Keep backend running (Django) for full features.")
    st.markdown(f"[Open repo]({REPO_URL}) • Version: {APP_VERSION}")
with footer_col2:
    if st.button("Clear session (debug)"):
        # careful: do not destroy necessary state unintentionally
        st.session_state.clear()
        st.experimental_rerun()

# Debug panel: show session state & minimal env when asked
if show_debug:
    st.markdown("### Debug: session_state")
    st.json({k: repr(v) for k, v in st.session_state.items()})
    st.markdown("### Debug: environment")
    st.json({
        "DJANGO_API_URL": DJANGO_API_URL,
        "USE_MOCK": USE_MOCK,
        "PAGE_MAP": PAGE_MAP
    })