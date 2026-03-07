# st_pages/generate.py
"""
BharatStudio — Generate page.
ChatGPT-style dark chat interface + 5 new AI feature panels:
  A. Video Script Generator
  B. Hashtag Optimizer
  C. Voice Caption (TTS)
  D. Content Calendar
  E. Platform Variants
"""

import streamlit as st
import json
import base64
import time
import io
import csv
from typing import List, Dict, Any, Optional

from lib.api_client import (
    post_create_draft,
    post_video_script,
    post_hashtags,
    post_voice,
    post_calendar,
    post_platform_variants,
)
from lib.components import header

# ── session state defaults ────────────────────────────────────────────────────

_DEFAULTS = {
    "chat_history":  [],       # list of {role, content, draft?, images?}
    "latest_draft":  None,
    "bs_images":     True,
    "bs_languages":  ["en", "hi"],
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── helpers ───────────────────────────────────────────────────────────────────

def _b64_to_bytes(b64: Optional[str]) -> Optional[bytes]:
    """Safely decode a base64 string; return None on failure."""
    if not b64:
        return None
    try:
        return base64.b64decode(b64)
    except Exception:
        return None


def _platform_icon(platform: str) -> str:
    icons = {
        "instagram": "📸",
        "twitter": "🐦",
        "linkedin": "💼",
        "youtube": "▶️",
        "whatsapp": "💬",
    }
    return icons.get(platform.lower(), "📱")


def _score_bar(score: int, label: str = ""):
    """Render a small colored score bar 0-100."""
    color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"
    st.markdown(
        f"""
        <div style="margin:4px 0">
          <small>{label}</small>
          <div style="background:#1e293b;border-radius:6px;height:10px;width:100%">
            <div style="background:{color};height:10px;border-radius:6px;width:{score}%"></div>
          </div>
          <small style="color:{color};font-weight:600">{score}/100</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Draft card renderer ───────────────────────────────────────────────────────

def _render_card(variant: Dict[str, Any], turn_key: str, idx: int):
    """Render a single variant card with image + download buttons."""
    v_id = variant.get("variant_id", f"v{idx}")
    lang = variant.get("lang", "—")
    text = variant.get("text", "")
    image_b64 = variant.get("image_b64")
    image_url  = variant.get("image_url")

    lang_flags = {"en": "🇬🇧", "hi": "🇮🇳", "ta": "🇮🇳", "te": "🇮🇳", "bn": "🇮🇳", "mr": "🇮🇳", "gu": "🇮🇳"}
    flag = lang_flags.get(lang, "🌐")

    st.markdown(
        f"<div style='color:#94a3b8;font-size:0.85em;margin-bottom:4px'>"
        f"{flag} <b>{lang.upper()}</b> &nbsp; variant {v_id}</div>",
        unsafe_allow_html=True,
    )
    st.write(text)

    # hashtags (present if text contains #)
    tags = [w for w in text.split() if w.startswith("#")]
    if tags:
        st.markdown(
            " ".join(
                f"<span style='background:#1e40af;color:#bfdbfe;padding:2px 7px;"
                f"border-radius:12px;font-size:0.78em'>{t}</span>"
                for t in tags
            ),
            unsafe_allow_html=True,
        )

    img_col, dl_col = st.columns([3, 1])
    with img_col:
        img_bytes = _b64_to_bytes(image_b64)
        if img_bytes:
            st.image(img_bytes, use_column_width=True)
        elif image_url:
            st.image(image_url, use_column_width=True)

    with dl_col:
        if img_bytes:
            st.download_button(
                "⬇ Image",
                data=img_bytes,
                file_name=f"image_{turn_key}_{v_id}.png",
                mime="image/png",
                key=f"dl_img_{turn_key}_{v_id}_{idx}",
            )
        st.download_button(
            "⬇ Caption",
            data=text.encode("utf-8"),
            file_name=f"caption_{turn_key}_{v_id}.txt",
            mime="text/plain",
            key=f"dl_cap_{turn_key}_{v_id}_{idx}",
        )

    with st.expander("✏️ Edit caption", expanded=False):
        edited = st.text_area(
            "Caption", value=text, height=100,
            key=f"edit_{turn_key}_{v_id}_{idx}",
        )
        if edited != text:
            variant["text"] = edited


# ── Panel A: Video Script ─────────────────────────────────────────────────────

def _panel_video_script():
    st.markdown("### 🎬 A — Video Script Generator")
    st.caption("Generate a shot-list script for short social videos (6–30 s).")

    draft = st.session_state.get("latest_draft")
    prompt_default = draft.get("prompt", "") if draft else ""

    v_prompt = st.text_input("Topic / prompt", value=prompt_default, key="vs_prompt")
    v_langs  = st.multiselect("Languages", ["en", "hi", "ta", "te", "bn"], default=["en"], key="vs_langs")

    if st.button("Generate video script", key="btn_video_script"):
        if not v_prompt.strip():
            st.warning("Please enter a prompt.")
            return
        with st.spinner("Generating script…"):
            try:
                result = post_video_script(v_prompt.strip(), v_langs)
            except Exception as exc:
                st.error(f"Error: {exc}")
                return

        if result.get("status") == "error":
            st.error(result.get("error", "Unknown error"))
            return

        scripts = result.get("scripts", [])
        for s in scripts:
            lang = s.get("lang", "—")
            raw  = s.get("video_script", "[]")
            try:
                scenes = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                scenes = [{"scene": 1, "shot": raw}]

            st.markdown(f"**{lang.upper()} script** — {len(scenes)} scene(s)")
            for sc in scenes:
                dur  = sc.get("duration_seconds", "?")
                shot = sc.get("shot", "")
                cam  = sc.get("camera", "")
                sfx  = sc.get("sfx", "")
                st.markdown(
                    f"- **Scene {sc.get('scene','?')}** ({dur}s) `{cam}` — {shot}"
                    + (f" 🔊 *{sfx}*" if sfx else "")
                )

            # copy / download buttons
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button(
                    "⬇ Download script .txt",
                    data="\n".join(
                        f"Scene {sc.get('scene')}: {sc.get('shot','')}" for sc in scenes
                    ).encode("utf-8"),
                    file_name=f"script_{lang}.txt",
                    mime="text/plain",
                    key=f"dl_script_{lang}_{int(time.time())}",
                )
            with dl_col2:
                st.download_button(
                    "⬇ Download script .json",
                    data=json.dumps(scenes, ensure_ascii=False, indent=2).encode("utf-8"),
                    file_name=f"script_{lang}.json",
                    mime="application/json",
                    key=f"dl_script_json_{lang}_{int(time.time())}",
                )

        st.success("Done!")


# ── Panel B: Hashtag Optimizer ────────────────────────────────────────────────

def _panel_hashtags():
    st.markdown("### #️⃣ B — Hashtag Optimizer")
    st.caption("Generate platform-optimised hashtags with predicted engagement score.")

    draft = st.session_state.get("latest_draft")
    caption_default = ""
    if draft and draft.get("variants"):
        caption_default = draft["variants"][0].get("text", "")

    h_caption  = st.text_area("Caption to optimise", value=caption_default, height=80, key="ht_caption")
    h_platform = st.selectbox("Platform", ["instagram", "twitter", "linkedin", "youtube", "whatsapp"], key="ht_platform")

    if st.button("Suggest hashtags", key="btn_hashtags"):
        if not h_caption.strip():
            st.warning("Please enter a caption.")
            return
        with st.spinner("Generating hashtags…"):
            try:
                result = post_hashtags(h_caption.strip(), h_platform)
            except Exception as exc:
                st.error(f"Error: {exc}")
                return

        if result.get("status") == "error":
            st.error(result.get("error", "Unknown error"))
            return

        hashtags   = result.get("hashtags", [])
        engagement = result.get("predicted_engagement", 0)

        _score_bar(engagement, "Predicted engagement")

        if hashtags:
            # pill-style display
            pills_html = " ".join(
                f"<span style='background:#1e3a5f;color:#93c5fd;padding:3px 10px;"
                f"border-radius:14px;font-size:0.82em;margin:2px;display:inline-block'>"
                f"{h['tag']}"
                f"<span style='color:#64748b;font-size:0.75em'> {h.get('score','')}</span>"
                f"</span>"
                for h in hashtags
            )
            st.markdown(pills_html, unsafe_allow_html=True)

            # reasons expander
            with st.expander("Why these hashtags?"):
                for h in hashtags:
                    st.write(f"**{h['tag']}** — {h.get('reason','')}")

            # copy all tags as a string
            tags_str = " ".join(h["tag"] for h in hashtags)
            st.text_area(
                "Copy all hashtags",
                value=tags_str,
                height=68,
                key=f"ht_copy_{int(time.time())}",
            )

            # Insert into caption helper
            if st.button("Insert hashtags into caption", key=f"ht_insert_{int(time.time())}"):
                new_caption = h_caption.strip() + "\n\n" + tags_str
                st.text_area("Updated caption", value=new_caption, height=120, key="ht_updated")

        st.success("Done!")


# ── Panel C: Voice Caption ────────────────────────────────────────────────────

def _panel_voice():
    st.markdown("### 🔊 C — Voice Caption (TTS)")
    st.caption("Generate an MP3 voice clip of a caption via Amazon Polly.")

    draft = st.session_state.get("latest_draft")
    text_default = ""
    lang_default = "en"
    if draft and draft.get("variants"):
        first = draft["variants"][0]
        text_default = first.get("text", "")
        lang_default = first.get("lang", "en")

    vc_text   = st.text_area("Caption text", value=text_default, height=80, key="vc_text")
    vc_lang   = st.selectbox("Language code", ["en", "hi", "ta", "te", "bn", "mr", "gu"],
                              index=["en","hi","ta","te","bn","mr","gu"].index(lang_default)
                                    if lang_default in ["en","hi","ta","te","bn","mr","gu"] else 0,
                              key="vc_lang")
    vc_voice  = st.text_input(
        "Polly voice ID (leave blank for default)",
        value="",
        placeholder="e.g. Raveena, Joanna, Aditi",
        key="vc_voice",
    )

    if st.button("🔊 Generate voice", key="btn_voice"):
        if not vc_text.strip():
            st.warning("Please enter text.")
            return
        with st.spinner("Calling Amazon Polly…"):
            try:
                result = post_voice(vc_text.strip(), lang=vc_lang, voice=vc_voice or None)
            except Exception as exc:
                st.error(f"Error: {exc}")
                return

        if result.get("status") == "error":
            st.error(result.get("error", "Unknown error"))
            return

        note = result.get("note", "")
        if note:
            st.info(note)

        audio_b64 = result.get("audio_base64")
        audio_bytes = _b64_to_bytes(audio_b64)

        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")
            st.download_button(
                "⬇ Download MP3",
                data=audio_bytes,
                file_name="caption_voice.mp3",
                mime="audio/mpeg",
                key=f"dl_mp3_{int(time.time())}",
            )
            st.caption(
                "Production note: store audio in S3 and return a signed URL "
                "instead of embedding base64 for large-scale use."
            )
        else:
            st.info("No audio returned (mock mode or Polly disabled).")

        st.success("Done!")


# ── Panel D: Content Calendar ─────────────────────────────────────────────────

def _panel_calendar():
    st.markdown("### 📅 D — Content Calendar Generator")
    st.caption("Generate a scheduled content calendar and export as CSV.")

    draft = st.session_state.get("latest_draft")
    topic_default = draft.get("prompt", "") if draft else ""

    cc_topic      = st.text_input("Topic", value=topic_default, key="cc_topic")
    cc_days       = st.selectbox("Days", [7, 14, 30], key="cc_days")
    cc_platforms  = st.multiselect(
        "Platforms",
        ["instagram", "twitter", "linkedin", "youtube", "whatsapp"],
        default=["instagram", "twitter"],
        key="cc_platforms",
    )

    if st.button("Generate calendar", key="btn_calendar"):
        if not cc_topic.strip():
            st.warning("Please enter a topic.")
            return
        with st.spinner("Generating calendar…"):
            try:
                result = post_calendar(cc_topic.strip(), cc_platforms, cc_days)
            except Exception as exc:
                st.error(f"Error: {exc}")
                return

        if result.get("status") == "error":
            st.error(result.get("error", "Unknown error"))
            return

        items = result.get("items", [])
        st.markdown(f"**{len(items)} items — starting {result.get('start_date','')}**")

        # table display
        rows_html = "".join(
            f"<tr>"
            f"<td style='padding:4px 8px'>{it.get('date','')}</td>"
            f"<td style='padding:4px 8px'>{_platform_icon(it.get('platform',''))} {it.get('platform','')}</td>"
            f"<td style='padding:4px 8px'>{it.get('time','')}</td>"
            f"<td style='padding:4px 8px'>{(it.get('caption','')[:80] + '…') if len(it.get('caption',''))>80 else it.get('caption','')}</td>"
            f"</tr>"
            for it in items
        )
        st.markdown(
            f"<table style='width:100%;font-size:0.82em;border-collapse:collapse'>"
            f"<thead><tr style='color:#94a3b8'>"
            f"<th style='text-align:left;padding:4px 8px'>Date</th>"
            f"<th style='text-align:left;padding:4px 8px'>Platform</th>"
            f"<th style='text-align:left;padding:4px 8px'>Time</th>"
            f"<th style='text-align:left;padding:4px 8px'>Caption</th>"
            f"</tr></thead><tbody>{rows_html}</tbody></table>",
            unsafe_allow_html=True,
        )

        # CSV export
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["date","platform","caption","image_prompt","time"])
        writer.writeheader()
        for it in items:
            writer.writerow({k: it.get(k,"") for k in ["date","platform","caption","image_prompt","time"]})
        st.download_button(
            "⬇ Export CSV",
            data=buf.getvalue().encode("utf-8"),
            file_name=f"calendar_{cc_days}d.csv",
            mime="text/csv",
            key=f"dl_cal_{int(time.time())}",
        )

        # "Create Drafts" helper
        with st.expander("Create drafts from calendar items (confirm first)"):
            st.warning("This will POST each calendar item as a new draft. Confirm?")
            if st.button("Confirm — create all drafts", key=f"cc_create_{int(time.time())}"):
                created = 0
                for it in items:
                    try:
                        post_create_draft(
                            it.get("caption", it.get("image_prompt", "calendar item")),
                            languages=["en"],
                        )
                        created += 1
                    except Exception:
                        pass
                st.success(f"Created {created} draft(s).")

        st.success("Done!")


# ── Panel E: Platform Variants ────────────────────────────────────────────────

def _panel_platform_variants():
    st.markdown("### 📱 E — Platform Variants")
    st.caption("Generate optimised captions per platform and language.")

    draft = st.session_state.get("latest_draft")
    prompt_default = draft.get("prompt", "") if draft else ""
    lang_default   = list({v.get("lang","en") for v in draft.get("variants",[])} if draft else ["en"])

    pv_prompt = st.text_input("Prompt / topic", value=prompt_default, key="pv_prompt")
    pv_langs  = st.multiselect("Languages", ["en","hi","ta","te","bn","mr","gu"],
                                default=lang_default or ["en"], key="pv_langs")
    pv_plats  = st.multiselect(
        "Platforms",
        ["instagram","twitter","linkedin","youtube","whatsapp"],
        default=["instagram","twitter","linkedin"],
        key="pv_plats",
    )

    if st.button("Generate platform variants", key="btn_pv"):
        if not pv_prompt.strip():
            st.warning("Please enter a prompt.")
            return
        if not pv_plats:
            st.warning("Select at least one platform.")
            return
        with st.spinner("Generating variants…"):
            try:
                result = post_platform_variants(pv_prompt.strip(), pv_langs, pv_plats)
            except Exception as exc:
                st.error(f"Error: {exc}")
                return

        if result.get("status") == "error":
            st.error(result.get("error", "Unknown error"))
            return

        variants  = result.get("platform_variants", [])
        # group by platform
        by_plat: Dict[str, List] = {}
        for v in variants:
            by_plat.setdefault(v.get("platform","?"), []).append(v)

        for plat, pvs in by_plat.items():
            icon = _platform_icon(plat)
            st.markdown(f"#### {icon} {plat.capitalize()}")
            for pv in pvs:
                lang    = pv.get("lang","—")
                caption = pv.get("caption","")
                cta     = pv.get("cta","")
                chars   = len(caption)

                # char limit warnings
                limits  = {"twitter": 280, "youtube": 100}
                limit   = limits.get(plat)
                if limit and chars > limit:
                    st.warning(f"{lang.upper()}: {chars}/{limit} chars — over limit!")

                c1, c2 = st.columns([5, 1])
                with c1:
                    st.text_area(
                        f"{lang.upper()} — {chars} chars",
                        value=caption + (f"\n\n{cta}" if cta else ""),
                        height=80,
                        key=f"pv_{plat}_{lang}_{int(time.time())}",
                    )
                with c2:
                    if cta:
                        st.caption(f"CTA: {cta}")
                    if st.button(
                        "Add to draft",
                        key=f"pv_add_{plat}_{lang}_{int(time.time())}",
                    ):
                        if st.session_state.get("latest_draft"):
                            st.session_state["latest_draft"]["variants"].append({
                                "variant_id": f"pv-{plat}-{lang}",
                                "lang": lang,
                                "text": caption,
                                "image_prompt": pv_prompt,
                                "image_b64": None,
                                "image_url": None,
                            })
                            st.success("Added to current draft.")
                        else:
                            st.warning("No active draft — generate one first.")

        st.success("Done!")


# ── Main chat interface ───────────────────────────────────────────────────────

def page():
    header()
    st.title("✨ BharatStudio — Generate")

    # ── Settings expander ─────────────────────────────────────────────────────
    with st.expander("⚙️ Settings", expanded=False):
        s1, s2 = st.columns(2)
        with s1:
            st.session_state["bs_languages"] = st.multiselect(
                "Languages",
                ["en","hi","ta","te","bn","mr","gu"],
                default=st.session_state["bs_languages"],
                key="settings_langs",
            )
        with s2:
            st.session_state["bs_images"] = st.checkbox(
                "Generate images",
                value=st.session_state["bs_images"],
                key="settings_images",
            )

    # ── AI Feature tabs ───────────────────────────────────────────────────────
    tabs = st.tabs(["💬 Draft", "🎬 Video Script", "#️⃣ Hashtags", "🔊 Voice", "📅 Calendar", "📱 Platform Variants"])

    # ── Tab 0: Chat / Draft generation ───────────────────────────────────────
    with tabs[0]:
        st.markdown("#### Generate social media drafts")

        # replay chat history
        for turn in st.session_state["chat_history"]:
            role = turn.get("role", "assistant")
            with st.chat_message(role):
                if role == "user":
                    st.write(turn["content"])
                else:
                    st.write(turn.get("content", ""))
                    draft = turn.get("draft")
                    if draft:
                        turn_key = draft.get("draft_id", str(id(draft)))
                        variants = draft.get("variants", [])
                        for i, v in enumerate(variants):
                            _render_card(v, turn_key, i)
                        st.caption(
                            f"`{turn_key}` · {draft.get('status','')}"
                        )

        # chat input
        user_input = st.chat_input("Describe your post (e.g. Monsoon street food in Patna)…")
        if user_input:
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Generating…"):
                    try:
                        draft = post_create_draft(
                            prompt=user_input,
                            languages=st.session_state["bs_languages"],
                            generate_images=st.session_state["bs_images"],
                        )
                    except Exception as exc:
                        st.error(f"Error: {exc}")
                        st.session_state["chat_history"].append(
                            {"role": "assistant", "content": f"Error: {exc}"}
                        )
                        return

                st.session_state["latest_draft"] = draft
                turn_key = draft.get("draft_id", str(int(time.time())))
                msg = f"Generated **{len(draft.get('variants',[]))} variant(s)** for: *{user_input}*"
                st.write(msg)
                for i, v in enumerate(draft.get("variants", [])):
                    _render_card(v, turn_key, i)
                st.caption(f"`{turn_key}` · {draft.get('status','')}")

                st.session_state["chat_history"].append(
                    {"role": "assistant", "content": msg, "draft": draft}
                )

        if st.session_state["chat_history"]:
            if st.button("🗑 Clear chat", key="clear_chat"):
                st.session_state["chat_history"] = []
                st.rerun()

    # ── Tabs 1-5: Feature panels ───────────────────────────────────────────────
    with tabs[1]:
        _panel_video_script()

    with tabs[2]:
        _panel_hashtags()

    with tabs[3]:
        _panel_voice()

    with tabs[4]:
        _panel_calendar()

    with tabs[5]:
        _panel_platform_variants()