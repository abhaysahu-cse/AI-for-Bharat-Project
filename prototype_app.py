# prototype_app.py
"""
BharatStudio — AI Content Platform for India
Production launcher — all pages, navigation, branding, CSS polish.
"""

import streamlit as st
import importlib
import pkgutil
import time
import os
import traceback
from typing import Dict

# ── Assets ────────────────────────────────────────────────────────────────────
try:
    from lib.asset_generator import ensure_assets_exist
    ensure_assets_exist()
except Exception as e:
    print(f"Asset generation skipped: {e}")

# ── App constants ──────────────────────────────────────────────────────────────
APP_TITLE    = "BharatStudio"
APP_TAGLINE  = "Create → Localize → Optimize → Publish"
APP_VERSION  = "v1.0"
REPO_URL     = "https://github.com/abhaysahu-cse/AI-for-Bharat-Project"

USE_MOCK        = os.environ.get("USE_MOCK", "true").lower() in ("1", "true", "yes")
DJANGO_API_URL  = os.environ.get("DJANGO_API_URL", "http://127.0.0.1:8000/api")

# ── Page map (fallback) ───────────────────────────────────────────────────────
FALLBACK_PAGE_MAP = {
    "✨ Generate":        "st_pages.generate",
    "🌐 Localize":        "st_pages.localize",
    "📅 Schedule":        "st_pages.preview_schedule",
    "🗂️ Library":         "st_pages.history",
    "📈 Analytics":       "st_pages.analytics",
}

PAGE_ICONS = {
    "generate":        "✨",
    "localize":        "🌐",
    "preview_schedule":"📅",
    "history":         "🗂️",
    "analytics":       "📈",
}

PREFERRED_ORDER = ["✨ Generate", "🌐 Localize", "📅 Schedule", "🗂️ Library", "📈 Analytics"]

# ── Page discovery ────────────────────────────────────────────────────────────
def discover_pages() -> Dict[str, str]:
    try:
        pkg = importlib.import_module("st_pages")
        pkg_path = getattr(pkg, "__path__", None)
        if not pkg_path:
            return FALLBACK_PAGE_MAP
        pages = {}
        for _, name, ispkg in pkgutil.iter_modules(pkg_path):
            if ispkg:
                continue
            icon   = PAGE_ICONS.get(name, "📄")
            label  = icon + " " + " ".join(p.capitalize() for p in name.split("_"))
            pages[label] = f"st_pages.{name}"
        ordered = {}
        for k in PREFERRED_ORDER:
            if k in pages:
                ordered[k] = pages.pop(k)
        for k in sorted(pages):
            ordered[k] = pages[k]
        return ordered or FALLBACK_PAGE_MAP
    except Exception:
        return FALLBACK_PAGE_MAP


def safe_run(module_path: str):
    start = time.perf_counter()
    try:
        mod = importlib.import_module(module_path)
    except Exception:
        return False, traceback.format_exc(), 0.0
    if not hasattr(mod, "page"):
        return False, f"Module '{module_path}' has no page() function.", 0.0
    try:
        mod.page()
        return True, None, time.perf_counter() - start
    except Exception:
        return False, traceback.format_exc(), 0.0


# ── Streamlit page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS injection ──────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&family=DM+Sans:wght@400;500&display=swap');

/* ── CSS variables ── */
:root {
    --bs-orange:   #F97316;
    --bs-orange2:  #FB923C;
    --bs-gold:     #FCD34D;
    --bs-bg:       #0B0F1A;
    --bs-surface:  #131929;
    --bs-card:     #1A2235;
    --bs-border:   #242E44;
    --bs-text:     #E2E8F0;
    --bs-muted:    #64748B;
    --bs-green:    #10B981;
    --bs-red:      #EF4444;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bs-bg) !important;
    color: var(--bs-text) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; max-width: 1200px; }
[data-testid="stDecoration"] { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F1626 0%, #0B0F1A 100%) !important;
    border-right: 1px solid var(--bs-border) !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

/* ── Sidebar logo area ── */
.bs-logo-block {
    background: linear-gradient(135deg, #F97316 0%, #FB923C 50%, #FCD34D 100%);
    padding: 18px 20px 14px;
    margin: 0 0 6px 0;
    border-radius: 0 0 16px 0;
}
.bs-logo-title {
    font-family: 'Sora', sans-serif;
    font-size: 1.45rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.5px;
    margin: 0;
    line-height: 1.2;
}
.bs-logo-tag {
    font-size: 0.68rem;
    color: rgba(255,255,255,0.75);
    margin: 3px 0 0;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* ── Nav radio buttons ── */
[data-testid="stRadio"] label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
    color: var(--bs-muted) !important;
    padding: 6px 10px !important;
    border-radius: 8px !important;
    transition: all 0.15s !important;
    cursor: pointer !important;
}
[data-testid="stRadio"] label:hover {
    color: var(--bs-text) !important;
    background: var(--bs-card) !important;
}
[data-testid="stRadio"] [data-checked="true"] label,
[data-testid="stRadio"] input:checked + div label {
    color: var(--bs-orange) !important;
    background: rgba(249,115,22,0.1) !important;
    font-weight: 600 !important;
}

/* ── Sidebar section labels ── */
.bs-section {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--bs-muted);
    padding: 14px 10px 4px;
}

/* ── Status badge ── */
.bs-badge-live {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(16,185,129,0.12);
    border: 1px solid rgba(16,185,129,0.3);
    color: var(--bs-green);
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 20px;
}
.bs-badge-mock {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(249,115,22,0.12);
    border: 1px solid rgba(249,115,22,0.3);
    color: var(--bs-orange);
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 20px;
}
.bs-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.bs-dot-green { background: var(--bs-green); box-shadow: 0 0 6px var(--bs-green); }
.bs-dot-orange { background: var(--bs-orange); animation: pulse-orange 1.5s infinite; }
@keyframes pulse-orange { 0%,100%{opacity:1;} 50%{opacity:0.4;} }

/* ── Main header bar ── */
.bs-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 16px;
    border-bottom: 1px solid var(--bs-border);
    margin-bottom: 20px;
}
.bs-topbar-title {
    font-family: 'Sora', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    background: linear-gradient(90deg, #F97316, #FCD34D);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
}
.bs-topbar-tag {
    font-size: 0.75rem;
    color: var(--bs-muted);
    margin-top: 2px;
}
.bs-version {
    font-size: 0.7rem;
    color: var(--bs-muted);
    background: var(--bs-card);
    border: 1px solid var(--bs-border);
    padding: 3px 8px;
    border-radius: 6px;
}

/* ── Quick action buttons ── */
.stButton button {
    background: var(--bs-card) !important;
    color: var(--bs-text) !important;
    border: 1px solid var(--bs-border) !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    transition: all 0.15s !important;
    width: 100% !important;
    text-align: left !important;
}
.stButton button:hover {
    background: var(--bs-border) !important;
    border-color: var(--bs-orange) !important;
    color: var(--bs-orange) !important;
}

/* ── Page load success bar ── */
.stSuccess {
    background: rgba(16,185,129,0.08) !important;
    border: 1px solid rgba(16,185,129,0.2) !important;
    border-radius: 8px !important;
    color: var(--bs-green) !important;
    font-size: 0.78rem !important;
}

/* ── Page error ── */
.stError {
    background: rgba(239,68,68,0.08) !important;
    border: 1px solid rgba(239,68,68,0.2) !important;
    border-radius: 8px !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: var(--bs-card) !important;
    border: 1px solid var(--bs-border) !important;
    border-radius: 8px !important;
    color: var(--bs-text) !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--bs-orange) !important;
    box-shadow: 0 0 0 2px rgba(249,115,22,0.15) !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    color: var(--bs-muted) !important;
    border-radius: 8px 8px 0 0 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--bs-orange) !important;
    border-bottom-color: var(--bs-orange) !important;
    font-weight: 600 !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: var(--bs-card) !important;
    border: 1px solid var(--bs-border) !important;
    border-radius: 10px !important;
    padding: 12px !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: var(--bs-card) !important;
    border: 1px solid var(--bs-border) !important;
    border-radius: 10px !important;
}

/* ── Chat messages ── */
[data-testid="chat-message-container"] {
    background: var(--bs-surface) !important;
    border: 1px solid var(--bs-border) !important;
    border-radius: 12px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bs-bg); }
::-webkit-scrollbar-thumb { background: var(--bs-border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--bs-muted); }

/* ── Divider ── */
hr { border-color: var(--bs-border) !important; }

/* ── Page loading text (hide the debug module path) ── */
.bs-hidden { display: none !important; }

/* ── Sidebar env pill ── */
.bs-env-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.72rem;
    color: var(--bs-muted);
    padding: 3px 0;
}
.bs-env-val { color: var(--bs-text); font-size: 0.72rem; }

/* ── Footer ── */
.bs-footer {
    font-size: 0.7rem;
    color: var(--bs-muted);
    text-align: center;
    padding: 16px 0 8px;
    border-top: 1px solid var(--bs-border);
    margin-top: 24px;
}
.bs-footer a { color: var(--bs-orange); text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# ── Page map ──────────────────────────────────────────────────────────────────
PAGE_MAP     = discover_pages()
PAGE_TITLES  = list(PAGE_MAP.keys())

# Default to Generate (first page)
if "current_page" not in st.session_state:
    st.session_state["current_page"] = PAGE_TITLES[0]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # Logo block
    st.markdown("""
    <div class="bs-logo-block">
      <div class="bs-logo-title">✦ BharatStudio</div>
      <div class="bs-logo-tag">AI Creator Platform · India-First</div>
    </div>
    """, unsafe_allow_html=True)

    # Status badge
    if USE_MOCK:
        st.markdown("""
        <div style="padding: 8px 12px;">
          <span class="bs-badge-mock">
            <span class="bs-dot bs-dot-orange"></span> Demo Mode
          </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="padding: 8px 12px;">
          <span class="bs-badge-live">
            <span class="bs-dot bs-dot-green"></span> Live Backend
          </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="bs-section">Navigate</div>', unsafe_allow_html=True)

    # Find default index
    default_idx = 0
    for i, t in enumerate(PAGE_TITLES):
        if "generate" in t.lower() or "Generate" in t:
            default_idx = i
            break

    page_choice = st.radio(
        "nav",
        PAGE_TITLES,
        index=default_idx,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown('<div class="bs-section">Quick Actions</div>', unsafe_allow_html=True)

    if st.button("🔄  Refresh page"):
        st.rerun()

    if st.button("↩️  Restore last draft"):
        st.success("Use Library → Restore to session.")

    # Environment info
    st.markdown("---")
    st.markdown('<div class="bs-section">Environment</div>', unsafe_allow_html=True)
    api_short = DJANGO_API_URL.replace("http://", "").replace("https://", "")
    st.markdown(f"""
    <div class="bs-env-row">
      <span>API</span>
      <span class="bs-env-val" style="color:#F97316;font-size:0.68rem">{api_short}</span>
    </div>
    <div class="bs-env-row">
      <span>Version</span>
      <span class="bs-env-val">{APP_VERSION}</span>
    </div>
    """, unsafe_allow_html=True)

    # Debug toggle
    st.markdown("---")
    show_debug = st.checkbox("Debug panel", value=False)


# ── Top bar ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0F1626 0%,#1A2235 100%);
            border:1px solid #242E44;border-radius:14px;padding:20px 26px;
            margin-bottom:20px;">
  <div style="font-family:'Sora',sans-serif;font-size:1.55rem;font-weight:700;
              background:linear-gradient(90deg,#F97316,#FCD34D);
              -webkit-background-clip:text;-webkit-text-fill-color:transparent;
              background-clip:text;margin-bottom:6px;">
    ✦ BharatStudio — AI Content Studio for India's Creators
  </div>
  <div style="font-size:1rem;color:#94A3B8;font-weight:400;">
    Generate multilingual social media content in seconds.
  </div>
</div>
""", unsafe_allow_html=True)

# ── Run selected page ─────────────────────────────────────────────────────────
selected_module = PAGE_MAP.get(page_choice, "st_pages.generate")

ok, err, load_time = safe_run(selected_module)

if ok:
    st.markdown(
        f"<div style='position:fixed;bottom:12px;right:18px;font-size:0.65rem;"
        f"color:#334155;z-index:999'>⚡ {load_time*1000:.0f} ms</div>",
        unsafe_allow_html=True,
    )
else:
    st.error("Failed to load this page.")
    st.code(err, language="python")
    st.info("Check the error above, fix the page module, then click Refresh.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="bs-footer">
  BharatStudio — AI-powered content for India's creators &nbsp;·&nbsp;
  <a href="{REPO_URL}" target="_blank">GitHub</a>
  &nbsp;·&nbsp; {APP_VERSION}
</div>
""", unsafe_allow_html=True)

# ── Debug panel ───────────────────────────────────────────────────────────────
if show_debug:
    with st.expander("🔧 Debug: session state"):
        st.json({k: repr(v) for k, v in st.session_state.items()})
    with st.expander("🔧 Debug: environment"):
        st.json({"DJANGO_API_URL": DJANGO_API_URL, "USE_MOCK": USE_MOCK, "PAGE_MAP": PAGE_MAP})
    if st.button("⚠️ Clear session (debug only)"):
        st.session_state.clear()
        st.rerun()