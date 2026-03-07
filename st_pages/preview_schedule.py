# st_pages/preview_schedule.py
"""
Preview & Schedule page — upgraded.

Features:
- Multi-platform previews (Instagram / X / YouTube / WhatsApp)
- Character counters and platform-specific rules
- Image/video preview and attachments
- Suggested posting times per platform
- Timezone selection and human-friendly scheduling info
- Single-variant schedule & bulk schedule
- Conflict detection & warnings (session-scoped)
- Export scheduled items to CSV
- Schedule history (session)
- Undo last schedule (session)
- UTM/campaign tags & CTA templates
- Save/Load as draft (session)
- Calls lib.api_client.post_schedule(...) to schedule (supports mock mode)
"""

import streamlit as st
from datetime import datetime, timedelta, date, time as dt_time
from typing import List, Dict, Any
import csv
import io
import uuid
import textwrap

from lib.api_client import post_schedule, get_recent_drafts, get_analytics
from lib.components import header

# ---- Platform configuration ----
PLATFORM_RULES = {
    "instagram": {"label": "Instagram", "max_chars": 2200, "aspect": "4:5", "suggest_hours": [18, 20, 21]},
    "twitter": {"label": "X / Twitter", "max_chars": 280, "aspect": "n/a", "suggest_hours": [12, 18]},
    "youtube": {"label": "YouTube Shorts", "max_chars": 100, "aspect": "9:16", "suggest_hours": [17, 19]},
    "whatsapp": {"label": "WhatsApp", "max_chars": 700, "aspect": "16:9", "suggest_hours": [20, 21]}
}

CTA_TEMPLATES = [
    "Learn more",
    "Shop now",
    "Sign up",
    "Watch now",
    "Book a demo"
]

DEFAULT_TIMEZONE = "UTC"

# ---- Helpers ----

def _now_utc():
    return datetime.utcnow()

def _format_dt_for_display(dt_obj: datetime):
    return dt_obj.strftime("%Y-%m-%d %H:%M")

def _human_readable_delta(target_dt: datetime):
    now = _now_utc()
    delta = target_dt - now
    if delta.total_seconds() < 0:
        return "in the past"
    days = delta.days
    hours = delta.seconds // 3600
    if days > 0:
        return f"in {days} day(s) {hours} hr"
    if hours > 0:
        return f"in {hours} hr(s)"
    minutes = delta.seconds // 60
    return f"in {minutes} min(s)"

def _csv_of_scheduled_items(items: List[Dict[str, Any]]):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["schedule_id", "draft_id", "variant_id", "platforms", "publish_time", "status", "caption"])
    for s in items:
        writer.writerow([s.get("id"), s.get("draft_id"), s.get("variant_id"), "|".join(s.get("platforms", [])),
                         s.get("publish_time"), s.get("status"), s.get("caption", "")])
    return output.getvalue()

def _generate_local_schedule_id():
    return f"local-{uuid.uuid4().hex[:8]}"

def _suggest_times_for_platform(platform: str, days_ahead: int = 7):
    """Return list of suggested datetimes (UTC) for the next N days based on heuristic hours."""
    hours = PLATFORM_RULES.get(platform, {}).get("suggest_hours", [18])
    suggestions = []
    today = date.today()
    for d in range(0, days_ahead):
        for h in hours:
            dt_obj = datetime.combine(today + timedelta(days=d), dt_time(hour=h, minute=0))
            suggestions.append(dt_obj)
    return suggestions

# ---- Session helpers (store scheduled items in session for demo/undo/history) ----

if "scheduled_items" not in st.session_state:
    st.session_state["scheduled_items"] = []  # list of dicts
if "last_action" not in st.session_state:
    st.session_state["last_action"] = None

def add_scheduled_item(item: Dict[str, Any]):
    st.session_state["scheduled_items"].append(item)
    st.session_state["last_action"] = {"type": "add", "item": item}

def remove_scheduled_item(schedule_id: str):
    for i, it in enumerate(st.session_state["scheduled_items"]):
        if it.get("id") == schedule_id:
            removed = st.session_state["scheduled_items"].pop(i)
            st.session_state["last_action"] = {"type": "remove", "item": removed}
            return removed
    return None

def undo_last_action():
    act = st.session_state.get("last_action")
    if not act:
        st.info("Nothing to undo.")
        return
    if act["type"] == "add":
        # remove that item
        sid = act["item"]["id"]
        remove_scheduled_item(sid)
        st.success("Undid last schedule action.")
    elif act["type"] == "remove":
        st.session_state["scheduled_items"].append(act["item"])
        st.success("Restored last removed scheduled item.")
    st.session_state["last_action"] = None

# ---- Preview rendering ----

def _render_instagram_preview(caption: str, image_url: str = None):
    st.markdown("<div style='border-radius:8px; padding:12px; background:#111; color: #fff;'>", unsafe_allow_html=True)
    st.markdown(f"**Instagram Preview — {len(caption)} chars**")
    if image_url:
        st.image(image_url, width=360)
    else:
        st.image("https://via.placeholder.com/360x450.png?text=Instagram+Preview", width=360)
    st.write(caption)
    st.markdown("</div>", unsafe_allow_html=True)

def _render_x_preview(caption: str):
    st.markdown("<div style='border-left: 4px solid #1DA1F2; padding:10px;'>", unsafe_allow_html=True)
    st.write("**X / Twitter Preview**")
    st.write(caption)
    st.markdown("</div>", unsafe_allow_html=True)

def _render_youtube_preview(title: str, thumb_url: str = None):
    st.markdown("<div style='border:1px solid #333; padding:8px; border-radius:6px;'>", unsafe_allow_html=True)
    st.write("**YouTube Shorts Preview**")
    if thumb_url:
        st.image(thumb_url, width=320)
    else:
        st.image("https://via.placeholder.com/320x180.png?text=YouTube+Thumbnail", width=320)
    st.write(f"**Title:** {title}")
    st.markdown("</div>", unsafe_allow_html=True)

def _render_whatsapp_preview(caption: str):
    st.markdown("<div style='background:#0f9d58; padding:10px; color:white; border-radius:6px;'>", unsafe_allow_html=True)
    st.write("**WhatsApp Status Preview**")
    st.write(caption)
    st.markdown("</div>", unsafe_allow_html=True)

# ---- Validation ----

def _validate_schedule_time(publish_dt: datetime) -> (bool, str):
    # simple validation: must be at least 2 minutes in future
    now = _now_utc()
    if publish_dt < now + timedelta(minutes=1):
        return False, "Publish time must be at least 1 minute in the future."
    return True, ""

def _detect_conflict(publish_dt: datetime, platforms: List[str]) -> List[Dict[str, Any]]:
    conflicts = []
    for s in st.session_state["scheduled_items"]:
        # if same time and overlapping platforms -> conflict
        try:
            existing_dt = datetime.fromisoformat(s["publish_time"])
        except Exception:
            # stored as display string — ignore
            continue
        if existing_dt == publish_dt and any(p in s.get("platforms", []) for p in platforms):
            conflicts.append(s)
    return conflicts

# ---- Main Page ----

def page():
    header()

    st.markdown("""
    <div style='margin-bottom:20px'>
      <h1 style='font-family:Sora,sans-serif;font-size:1.8rem;font-weight:700;margin:0;
                 background:linear-gradient(90deg,#F97316,#FCD34D);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                 background-clip:text;'>📅 Schedule & Publish</h1>
      <p style='color:#64748B;margin:4px 0 0;font-size:0.88rem'>Preview, optimise and schedule content across platforms</p>
    </div>""", unsafe_allow_html=True)

    draft = st.session_state.get("latest_draft")
    if not draft:
        st.info("Generate a draft first on the Generate tab.")
        return

    st.markdown("## Select platforms")
    platforms = st.multiselect("Select platforms to preview/publish", options=list(PLATFORM_RULES.keys()), default=["instagram"])

    st.markdown("---")
    st.markdown("## Preview & variants")

    # Show each variant with platform-specific preview
    variants = draft.get("variants", [])
    for vi, variant in enumerate(variants):
        st.markdown(f"### Variant {vi+1} — `{variant.get('variant_id')}` — {variant.get('lang')}")
        caption = variant.get("text", "")
        image_prompt = variant.get("image_prompt", "")
        image_preview_url = variant.get("image_url") if variant.get("image_url") else None

        # quick UI: platform toggles per variant
        pv_cols = st.columns([2, 1])
        with pv_cols[0]:
            st.write("Caption (editable)")
            cap_key = f"preview_caption_{variant.get('variant_id')}"
            if cap_key not in st.session_state:
                st.session_state[cap_key] = caption
            edited_caption = st.text_area("Edit caption", value=st.session_state[cap_key], key=cap_key, height=100)
            
            st.write("Image concept:", image_prompt)
            if image_preview_url:
                st.image(image_preview_url, width=240)
            else:
                st.image("https://via.placeholder.com/240x135.png?text=Media+Preview", width=240)

            # CTA and UTM fields
            c1, c2 = st.columns(2)
            with c1:
                cta = st.selectbox("CTA (optional)", options=["", *CTA_TEMPLATES], key=f"cta_{variant.get('variant_id')}")
            with c2:
                campaign = st.text_input("Campaign / UTM tag", value="", key=f"camp_{variant.get('variant_id')}")

            # Social meta preview toggles
            meta_col = st.columns(3)
            char_len = len(edited_caption)
            st.write(f"Character count: {char_len} / max across selected platforms")
            max_allowed = max(PLATFORM_RULES[p]["max_chars"] for p in platforms) if platforms else 2200
            if char_len > max_allowed:
                st.warning(f"Caption exceeds max for selected platforms ({max_allowed} chars). Consider shortening.")

        with pv_cols[1]:
            # Show per-platform preview cards
            st.markdown("**Platform Previews**")
            for p in platforms:
                if p == "instagram":
                    _render_instagram_preview(edited_caption, image_preview_url)
                elif p == "twitter":
                    _render_x_preview(edited_caption)
                elif p == "youtube":
                    # map caption -> title if too long
                    title = edited_caption if len(edited_caption) <= 100 else edited_caption[:97] + "..."
                    _render_youtube_preview(title, image_preview_url)
                elif p == "whatsapp":
                    _render_whatsapp_preview(edited_caption)

        # Suggested posting times
        st.markdown("**Suggested posting times**")
        suggestion_list = []
        for p in platforms:
            suggestion_list.extend(_suggest_times_for_platform(p, days_ahead=3))
        # unique and sorted
        suggestion_list = sorted({dt for dt in suggestion_list})
        suggest_strs = [f"{_format_dt_for_display(dt)} (UTC)" for dt in suggestion_list[:8]]
        st.write(", ".join(suggest_strs))

        # Scheduling controls
        st.markdown("**Schedule this variant**")
        sched_col1, sched_col2, sched_col3 = st.columns([2,1,1])
        with sched_col1:
            publish_date = st.date_input("Publish date", value=date.today(), key=f"date_{variant.get('variant_id')}")
            publish_time = st.time_input("Publish time", value=dt_time(hour=18, minute=0), key=f"time_{variant.get('variant_id')}")
        with sched_col2:
            tz = st.selectbox("Timezone (display only)", options=[DEFAULT_TIMEZONE, "UTC", "Asia/Kolkata", "Asia/Kathmandu"], index=0, key=f"tz_{variant.get('variant_id')}")
        with sched_col3:
            bulk_platforms = st.multiselect("Platforms", options=list(PLATFORM_RULES.keys()), default=platforms, key=f"plat_{variant.get('variant_id')}")

        # Compute publish datetime (naively treat timezone as display label — conversion left to backend)
        publish_dt = datetime.combine(publish_date, publish_time)
        valid, msg = _validate_schedule_time(publish_dt)
        if not valid:
            st.error(msg)

        # Conflict detection
        conflicts = _detect_conflict(publish_dt, bulk_platforms)
        if conflicts:
            st.warning(f"Conflict detected: {len(conflicts)} existing scheduled item(s) at this time for overlapping platforms.")

        # Quick schedule & batch schedule buttons
        btn_col1, btn_col2, btn_col3 = st.columns([1,1,1])
        with btn_col1:
            if st.button(f"Schedule variant {variant.get('variant_id')}", key=f"sch_btn_{variant.get('variant_id')}"):
                # call backend scheduling endpoint
                try:
                    payload_platforms = bulk_platforms or platforms or ["instagram"]
                    publish_iso = publish_dt.isoformat()
                    res = post_schedule(draft.get("draft_id"), variant.get("variant_id"), payload_platforms, publish_iso)
                    # create a local schedule record for display
                    local_id = res.get("schedule_id") if res and isinstance(res, dict) and res.get("schedule_id") else _generate_local_schedule_id()
                    scheduled = {
                        "id": local_id,
                        "draft_id": draft.get("draft_id"),
                        "variant_id": variant.get("variant_id"),
                        "platforms": payload_platforms,
                        "publish_time": publish_iso,
                        "caption": edited_caption,
                        "status": res.get("status") if res and isinstance(res, dict) and res.get("status") else "scheduled",
                        "meta": {"cta": cta, "campaign": campaign}
                    }
                    add_scheduled_item(scheduled)
                    st.success(f"Scheduled {variant.get('variant_id')} for {publish_iso}")
                except Exception as e:
                    st.exception(f"Scheduling failed: {e}")

        with btn_col2:
            if st.button(f"Bulk schedule variant {variant.get('variant_id')} for all suggested", key=f"bulk_sch_{variant.get('variant_id')}"):
                # schedule for each suggested time (capped)
                scheduled_count = 0
                for dtobj in suggestion_list[:3]:
                    try:
                        publish_iso = dtobj.isoformat()
                        res = post_schedule(draft.get("draft_id"), variant.get("variant_id"), bulk_platforms or platforms, publish_iso)
                        local_id = res.get("schedule_id") if res and isinstance(res, dict) and res.get("schedule_id") else _generate_local_schedule_id()
                        scheduled = {
                            "id": local_id,
                            "draft_id": draft.get("draft_id"),
                            "variant_id": variant.get("variant_id"),
                            "platforms": bulk_platforms or platforms,
                            "publish_time": publish_iso,
                            "caption": edited_caption,
                            "status": "scheduled",
                            "meta": {"cta": cta, "campaign": campaign}
                        }
                        add_scheduled_item(scheduled)
                        scheduled_count += 1
                    except Exception:
                        continue
                st.success(f"Bulk scheduled {scheduled_count} items (demo)")

        with btn_col3:
            if st.button(f"Preview analytics for {variant.get('variant_id')}", key=f"an_{variant.get('variant_id')}"):
                try:
                    stats = get_analytics(draft.get("draft_id"))
                    st.metric("Impressions (sim)", stats.get("impressions", 0))
                    st.metric("Likes (sim)", stats.get("likes", 0))
                except Exception as e:
                    st.write("Analytics unavailable:", e)

        st.markdown("---")

    # ---- Scheduled items panel ----
    st.markdown("## Scheduled items (session)")
    if not st.session_state["scheduled_items"]:
        st.info("No scheduled items yet. Use the schedule buttons above.")
    else:
        for s in st.session_state["scheduled_items"]:
            st.markdown(f"**{s['id']}** — Variant `{s['variant_id']}` → {', '.join(s['platforms'])} @ {s['publish_time']}")
            s_col1, s_col2, s_col3 = st.columns([2,1,1])
            with s_col1:
                st.write(textwrap.shorten(s.get("caption", ""), width=120))
            with s_col2:
                if st.button("Cancel", key=f"cancel_{s['id']}"):
                    removed = remove_scheduled_item(s["id"])
                    st.success(f"Canceled schedule {s['id']} (demo)")
            with s_col3:
                if st.button("Edit", key=f"edit_{s['id']}"):
                    st.info("Edit action not implemented in demo — open generate/localize, modify and reschedule if needed.")

    # ---- Utilities: export, undo, CSV ----
    st.markdown("---")
    util_col1, util_col2, util_col3 = st.columns(3)
    with util_col1:
        if st.button("Export scheduled to CSV"):
            csv_data = _csv_of_scheduled_items(st.session_state["scheduled_items"])
            st.download_button("Download CSV", data=csv_data, file_name="scheduled_items.csv", mime="text/csv")
    with util_col2:
        if st.button("Undo last scheduling action"):
            undo_last_action()
    with util_col3:
        if st.button("Clear all scheduled (session)"):
            st.session_state["scheduled_items"] = []
            st.success("Cleared scheduled items (session)")

    # ---- Tips & best posting times (educational) ----
    st.markdown("### Scheduling Tips")
    st.markdown("""
    - Instagram: Post when your audience is active (evenings and weekends).  
    - X / Twitter: Midday & evening for higher engagement.  
    - YouTube Shorts: Early evenings and weekend slots.  
    - Use the platform previews to check caption length and thumbnail.  
    """)
    # small "I love you" easter egg (user asked for "I love you just")
    if st.checkbox("Show secret message (I love you)"):
        st.balloons()
        st.success("I love you — keep building great content! ❤️")

    # Debug / raw inspector
    if st.checkbox("Show raw scheduled items (debug)"):
        st.json(st.session_state["scheduled_items"])