# st_pages/history.py
"""
History / Recent Drafts page for BharatStudio prototype (final).
Drop this file into st_pages/history.py and restart Streamlit.
"""

import streamlit as st
import json
import base64
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

from lib.api_client import get_recent_drafts, get_analytics
from lib.components import header

# ----------------------------
# Helpers & utils
# ----------------------------
def _now_iso() -> str:
    return datetime.utcnow().isoformat()

def _pretty_dt(iso_ts: str) -> str:
    try:
        return datetime.fromisoformat(iso_ts).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(iso_ts)

def _excerpt(text: str, length: int = 140) -> str:
    if not text:
        return ""
    return text if len(text) <= length else text[:length].rsplit(" ", 1)[0] + "…"

def _download_json_href(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, indent=2)
    b64 = base64.b64encode(raw.encode("utf-8")).decode()
    return f"data:application/json;base64,{b64}"

def _extract_tags(text: str) -> List[str]:
    if not text:
        return []
    tags = [t for t in text.split() if t.startswith("#")]
    return list(dict.fromkeys(tags))

# ----------------------------
# Session-safe defaults
# ----------------------------
DEFAULT_STATE = {
    "history_cache": None,            # list of drafts
    "history_last_loaded": None,      # iso timestamp
    "bookmarks": {},                  # draft_id -> draft
    "history_page": 1,
    "history_page_size": 5,
    "history_sort": "newest",
    "history_search": "",
    "history_filters": {"lang": None, "platform": None},
    "last_history_action": None,
    "history_view_obj": None,         # stores a draft object to view
    "history_compare_obj": None,      # stores a draft object to compare
}

for k, v in DEFAULT_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------------
# Data loading / normalization
# ----------------------------
def load_history(force: bool = False) -> List[Dict]:
    """
    Load drafts from API (mock-friendly) and store a normalized list in session_state['history_cache'].
    Ensures unique draft_id values when duplicates appear.
    """
    if st.session_state.get("history_cache") is None or force:
        try:
            raw = get_recent_drafts() or []
        except Exception:
            raw = []

        # Normalize, ensure fields, and make draft_id unique if duplicates exist
        seen = {}
        normalized: List[Dict] = []
        for idx, d in enumerate(raw):
            nd = dict(d)  # shallow copy
            base_id = nd.get("draft_id") or f"draft-{idx+1}"
            if base_id in seen:
                seen[base_id] += 1
                nd["draft_id"] = f"{base_id}-{seen[base_id]}"
            else:
                seen[base_id] = 0
                nd["draft_id"] = base_id

            nd.setdefault("prompt", nd.get("prompt") or "—")
            nd.setdefault("variants", nd.get("variants") or [])
            nd.setdefault("created_at", nd.get("created_at") or (datetime.utcnow() - timedelta(days=idx)).isoformat())
            # derive tags from variants text
            all_text = " ".join([v.get("text", "") for v in nd["variants"]])
            nd["tags"] = _extract_tags(all_text)
            normalized.append(nd)

        st.session_state["history_cache"] = normalized
        st.session_state["history_last_loaded"] = _now_iso()

    return st.session_state.get("history_cache", [])

# ----------------------------
# Filtering / sorting / paginate
# ----------------------------
def _filter_and_search(drafts: List[Dict], search: str, lang: str = None, platform: str = None) -> List[Dict]:
    s = (search or "").strip().lower()
    out = []
    for d in drafts:
        hay = (d.get("prompt", "") + " " + " ".join([v.get("text", "") for v in d.get("variants", [])])).lower()
        if s and s not in hay:
            continue
        if lang and lang != "(any)":
            if not any(v.get("lang") == lang for v in d.get("variants", [])):
                continue
        if platform and platform != "(any)":
            if platform.lower() not in hay:
                continue
        out.append(d)
    return out

def _sort_drafts(drafts: List[Dict], mode: str) -> List[Dict]:
    if mode == "newest":
        return sorted(drafts, key=lambda d: d.get("created_at", ""), reverse=True)
    if mode == "oldest":
        return sorted(drafts, key=lambda d: d.get("created_at", ""), reverse=False)
    if mode == "most_variants":
        return sorted(drafts, key=lambda d: len(d.get("variants", [])), reverse=True)
    return drafts

def paginate(items: List[Dict], page: int, page_size: int) -> Tuple[List[Dict], int]:
    total = len(items)
    pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, pages))
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], pages

# ----------------------------
# UI components: cards, renderers
# ----------------------------
def _draft_card(draft: Dict, uid: str):
    """
    Show compact draft card. Uses uid to ensure widget keys are unique.
    """
    did = draft.get("draft_id")
    st.markdown(f"**{did}** — *{_pretty_dt(draft.get('created_at'))}*")
    st.caption(f"Prompt: {draft.get('prompt')}")
    cols = st.columns([4, 1, 1])

    with cols[0]:
        for v in draft.get("variants", []):
            lang = v.get("lang", "—")
            snippet = _excerpt(v.get("text", ""), 120)
            st.markdown(f"- **{lang}**: {snippet}")

    with cols[1]:
        # View (store the full draft object in session so we don't need to look it up by id)
        if st.button("View", key=f"view_{uid}"):
            st.session_state["history_view_obj"] = draft

    with cols[2]:
        # Bookmark toggle (keys unique by uid)
        _bookmarks = st.session_state.get("bookmarks", {})

        if draft.get("draft_id") in _bookmarks:
            if st.button("★", key=f"unbk_{uid}"):
                # ensure bookmarks dict exists then pop
                st.session_state.setdefault("bookmarks", {})
                st.session_state["bookmarks"].pop(draft.get("draft_id"), None)
                st.session_state["last_history_action"] = ("unbookmark", draft)
                st.success("Removed bookmark")
        else:
            if st.button("☆", key=f"bk_{uid}"):
                st.session_state.setdefault("bookmarks", {})
                st.session_state["bookmarks"][draft.get("draft_id")] = draft
                st.session_state["last_history_action"] = ("bookmark", draft)
                st.success("Bookmarked")

    st.markdown("---")

def _render_full_draft(draft: Dict):
    did = draft.get("draft_id")
    st.header(f"Draft: {did}")
    st.write("Prompt:", draft.get("prompt"))
    st.write("Created:", _pretty_dt(draft.get("created_at")))
    if draft.get("tags"):
        st.write("Tags:", ", ".join(draft.get("tags")))
    st.markdown("### Variants")
    for v in draft.get("variants", []):
        st.subheader(f"Variant {v.get('variant_id')} — {v.get('lang')}")
        st.code(v.get("text", ""), language="text")
        st.write("Image prompt:", v.get("image_prompt", "—"))
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("Restore to session", key=f"restore_{did}_{v.get('variant_id')}"):
                st.session_state["latest_draft"] = draft
                st.session_state["last_history_action"] = ("restore", {"draft_id": did})
                st.success("Draft restored to session (Generate & Localize).")
        with c2:
            payload = {"draft_id": did, "variant": v}
            if st.button("Export variant JSON", key=f"exportvar_{did}_{v.get('variant_id')}"):
                st.download_button("Download", data=json.dumps(payload, ensure_ascii=False, indent=2),
                                   file_name=f"{did}_{v.get('variant_id')}.json", mime="application/json")
        with c3:
            if st.button("Analytics (quick)", key=f"analytics_{did}_{v.get('variant_id')}"):
                try:
                    stats = get_analytics(did)
                    st.metric("Impressions", stats.get("impressions", 0))
                    st.metric("Likes", stats.get("likes", 0))
                    st.write("Suggestions:", stats.get("suggestions", []))
                except Exception as e:
                    st.error("Analytics fetch failed: " + str(e))

    st.markdown("### Actions")
    a1, a2, a3 = st.columns(3)
    with a1:
        href = _download_json_href(draft)
        st.markdown(f"[Download draft JSON]({href})")
    with a2:
        if st.button("Compare variants side-by-side", key=f"compare_{did}"):
            st.session_state["history_compare_obj"] = draft
    with a3:
        if st.button("Delete draft (session)", key=f"delete_{did}"):
            cache = st.session_state.get("history_cache") or []
            st.session_state["history_cache"] = [x for x in cache if x.get("draft_id") != did]
            st.session_state["last_history_action"] = ("delete", {"draft_id": did})
            st.success("Draft removed from history cache (session).")

    with st.expander("Raw draft JSON"):
        st.json(draft)

def _compare_variants_side_by_side(draft: Dict):
    st.header(f"Compare variants — {draft.get('draft_id')}")
    variants = draft.get("variants", [])
    if len(variants) < 2:
        st.info("Not enough variants to compare.")
        return
    ids = [v.get("variant_id") for v in variants]
    left_id = st.selectbox("Left variant", options=ids, index=0, key=f"cmp_left_{draft.get('draft_id')}")
    right_id = st.selectbox("Right variant", options=ids, index=min(1, len(ids)-1), key=f"cmp_right_{draft.get('draft_id')}")
    left_v = next(v for v in variants if v.get("variant_id") == left_id)
    right_v = next(v for v in variants if v.get("variant_id") == right_id)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"{left_v.get('lang')} — {left_v.get('variant_id')}")
        st.write(left_v.get("text"))
        st.write("Image prompt:", left_v.get("image_prompt", "—"))
    with c2:
        st.subheader(f"{right_v.get('lang')} — {right_v.get('variant_id')}")
        st.write(right_v.get("text"))
        st.write("Image prompt:", right_v.get("image_prompt", "—"))

    with st.expander("Show simple line diff"):
        left_lines = left_v.get("text", "").splitlines()
        right_lines = right_v.get("text", "").splitlines()
        max_lines = max(len(left_lines), len(right_lines))
        rows = []
        for i in range(max_lines):
            rows.append({"left": left_lines[i] if i < len(left_lines) else "", "right": right_lines[i] if i < len(right_lines) else ""})
        st.table(rows)

# ----------------------------
# Page main
# ----------------------------
def page():
    header()

    st.markdown("""
    <div style='margin-bottom:20px'>
      <h1 style='font-family:Sora,sans-serif;font-size:1.8rem;font-weight:700;margin:0;
                 background:linear-gradient(90deg,#F97316,#FCD34D);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                 background-clip:text;'>🗂️ Content Library</h1>
      <p style='color:#64748B;margin:4px 0 0;font-size:0.88rem'>Browse, search and restore your generated drafts</p>
    </div>""", unsafe_allow_html=True)

    # Controls row
    ctrl1, ctrl2, ctrl3 = st.columns([2, 3, 2])
    with ctrl1:
        if st.button("Reload history"):
            load_history(force=True)
            st.experimental_rerun()
    with ctrl2:
        st.session_state["history_search"] = st.text_input("Search drafts (prompt, text, hashtags)", value=st.session_state.get("history_search", ""), key="history_search_input")
    with ctrl3:
        st.session_state["history_sort"] = st.selectbox("Sort", options=["newest", "oldest", "most_variants"], index=["newest","oldest","most_variants"].index(st.session_state.get("history_sort", "newest")))
        st.session_state["history_page_size"] = st.selectbox("Page size", options=[5,10,20], index=[5,10,20].index(st.session_state.get("history_page_size", 5)))

    # Filters
    all_cache = load_history()
    # gather languages
    all_langs = sorted({v.get("lang") for d in all_cache for v in d.get("variants", []) if v.get("lang")})
    fcol1, fcol2, fcol3 = st.columns([1,1,1])
    with fcol1:
        selected_lang = st.selectbox("Filter by language", options=["(any)", *all_langs], index=0)
        lang_filter = None if selected_lang == "(any)" else selected_lang
    with fcol2:
        all_platforms = ["(any)", "instagram", "twitter", "youtube", "whatsapp"]
        selected_platform = st.selectbox("Filter by platform keyword", options=all_platforms, index=0)
        plat_filter = None if selected_platform == "(any)" else selected_platform
    with fcol3:
        if st.button("Bookmark all visible"):
            # bookmark all visible after filtering/pagination below
            st.session_state["last_history_action"] = ("bookmark_bulk", None)
            # actual bookmarking performed after page_items computed

    st.markdown("---")

    # Apply search / filters / sort
    drafts = load_history()
    filtered = _filter_and_search(drafts, st.session_state.get("history_search", ""), lang_filter, plat_filter)
    sorted_list = _sort_drafts(filtered, st.session_state.get("history_sort", "newest"))

    st.write(f"Showing {len(sorted_list)} results (last loaded: {st.session_state.get('history_last_loaded')})")

    # paginate
    page = st.session_state.get("history_page", 1)
    page_size = st.session_state.get("history_page_size", 5)
    page_items, total_pages = paginate(sorted_list, page, page_size)

    # If we requested bookmark all visible, add them now
    if st.session_state.get("last_history_action") and st.session_state["last_history_action"][0] == "bookmark_bulk":
        for d in page_items:
            st.session_state["bookmarks"][d["draft_id"]] = d
        st.session_state["last_history_action"] = ("bookmark_bulk_done", len(page_items))
        st.success(f"Bookmarked {len(page_items)} drafts on this page.")

    # Render page items (use unique uid derived from draft_id + index)
    for idx, d in enumerate(page_items):
        uid = f"{d.get('draft_id')}_{idx}"
        _draft_card(d, uid)

    # Pagination controls
    p1, p2, p3, p4 = st.columns([1,1,1,2])
    with p1:
        if st.button("Prev", key="hist_prev") and page > 1:
            st.session_state["history_page"] = page - 1
            st.experimental_rerun()
    with p2:
        st.write(f"Page {page} / {total_pages}")
    with p3:
        if st.button("Next", key="hist_next") and page < total_pages:
            st.session_state["history_page"] = page + 1
            st.experimental_rerun()
    with p4:
        st.write(" ")

    # Sidebar bookmarks
    st.sidebar.markdown("### 📌 Bookmarks")
    if st.session_state["bookmarks"]:
        for bid, bd in st.session_state["bookmarks"].items():
            st.sidebar.markdown(f"- **{bid}** — {bd.get('prompt')[:40]}")
            if st.sidebar.button(f"Open {bid}", key=f"openbk_{bid}"):
                st.session_state["history_view_obj"] = bd
    else:
        st.sidebar.info("No bookmarks yet — mark drafts with ☆")

    # Undo last action
    if st.session_state.get("last_history_action"):
        la = st.session_state["last_history_action"]
        if st.button("Undo last action"):
            act = la[0]
            if act == "bookmark":
                did = la[1].get("draft_id")
                st.session_state["bookmarks"].pop(did, None)
            elif act == "unbookmark":
                st.session_state["bookmarks"][la[1].get("draft_id")] = la[1]
            elif act == "delete":
                st.info("Cannot undo delete in demo mode.")
            st.session_state["last_history_action"] = None
            st.experimental_rerun()

    # handle view / compare
    view_obj = st.session_state.get("history_view_obj")
    if view_obj:
        _render_full_draft(view_obj)
        if st.button("Close view"):
            st.session_state["history_view_obj"] = None
            st.experimental_rerun()
        return

    compare_obj = st.session_state.get("history_compare_obj")
    if compare_obj:
        _compare_variants_side_by_side(compare_obj)
        if st.button("Close compare"):
            st.session_state["history_compare_obj"] = None
            st.experimental_rerun()
        return

    # Footer utilities
    st.markdown("---")
    u1, u2, u3 = st.columns(3)
    with u1:
        if st.button("Export visible page to JSON"):
            st.download_button("Download JSON", data=json.dumps(page_items, ensure_ascii=False, indent=2),
                               file_name=f"history_page_{page}.json", mime="application/json")
    with u2:
        if st.button("Export ALL history to JSON"):
            st.download_button("Download all", data=json.dumps(drafts, ensure_ascii=False, indent=2),
                               file_name="history_all.json", mime="application/json")
    with u3:
        if st.button("Clear history cache"):
            st.session_state["history_cache"] = None
            st.session_state["history_last_loaded"] = None
            st.success("Cleared history cache. Reload to fetch again.")

    # timeline optional
    if st.checkbox("Show timeline (simple)"):
        counts = {}
        for d in drafts:
            day = d.get("created_at", "")[:10]
            counts[day] = counts.get(day, 0) + 1
        days = sorted(counts.keys())
        values = [counts[d] for d in days]
        st.bar_chart({"dates": days, "counts": values})

    st.caption("Tip: Use Restore → Generate to continue editing a draft. Bookmarks survive the session.")