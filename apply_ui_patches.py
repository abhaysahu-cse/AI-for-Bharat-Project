#!/usr/bin/env python3
"""
apply_ui_patches.py — run this once in your project root to apply all UI polish patches.
Usage:  python apply_ui_patches.py
"""
import re, os

GRAD_HEADER = """    header()

    st.markdown(\"\"\"
    <div style='margin-bottom:20px'>
      <h1 style='font-family:Sora,sans-serif;font-size:1.8rem;font-weight:700;margin:0;
                 background:linear-gradient(90deg,#F97316,#FCD34D);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                 background-clip:text;'>{icon} {title}</h1>
      <p style='color:#64748B;margin:4px 0 0;font-size:0.88rem'>{sub}</p>
    </div>\"\"\", unsafe_allow_html=True)"""

PATCHES = {
    "st_pages/history.py": {
        "old": 'header()\n    st.title("\U0001f5c2\ufe0f Recent Drafts & Content Library")',
        "icon": "\U0001f5c2\ufe0f", "title": "Content Library",
        "sub": "Browse, search and restore your generated drafts",
        "remove_footer": "Prototype UI — built for hackathon demo",
    },
    "st_pages/preview_schedule.py": {
        "old": 'header()\n    st.title("\U0001f4c5 Preview & Schedule \u2014 BharatStudio")',
        "icon": "\U0001f4c5", "title": "Schedule & Publish",
        "sub": "Preview, optimise and schedule content across platforms",
        "remove_footer": "Prototype UI",
    },
    "st_pages/analytics.py": {
        "old": 'header()\n    st.title("\U0001f4c8 Analytics \u2014 BharatStudio Insights")',
        "icon": "\U0001f4c8", "title": "Insights & Analytics",
        "sub": "Performance metrics, trends and AI-powered recommendations",
        "remove_footer": "Analytics page (demo mode)",
    },
}

for fpath, cfg in PATCHES.items():
    if not os.path.exists(fpath):
        print(f"SKIP (not found): {fpath}")
        continue

    src = open(fpath, "r", encoding="utf-8").read()
    new_header = GRAD_HEADER.format(icon=cfg["icon"], title=cfg["title"], sub=cfg["sub"])

    # Replace st.title call
    pattern = r'header\(\)\s+st\.title\([^)]+\)'
    replaced = re.sub(pattern, new_header.strip(), src, count=1)

    if replaced == src:
        print(f"WARNING: pattern not matched in {fpath} — check manually")
    else:
        open(fpath, "w", encoding="utf-8").write(replaced)
        print(f"PATCHED: {fpath}")

# Patch prototype_app.py — remove "Loading: X — module" debug line
app_path = "prototype_app.py"
if os.path.exists(app_path):
    src = open(app_path, encoding="utf-8").read()
    # Remove the debug "Loading: page — module.path" line
    src = re.sub(r"st\.write.*Loading.*selected_module.*\n?", "", src)
    open(app_path, "w", encoding="utf-8").write(src)
    print(f"PATCHED: {app_path}")

print("\nAll patches applied. Restart Streamlit: streamlit run prototype_app.py")