# st_pages/generate.py
"""
BharatStudio — Generate page.
Chat-style draft interface + 5 AI feature panels.
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
    "chat_history":  [],
    "latest_draft":  None,
    "bs_images":     True,
    "bs_languages":  ["en", "hi"],
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── helpers ───────────────────────────────────────────────────────────────────
def _b64_to_bytes(b64: Optional[str]) -> Optional[bytes]:
    if not b64:
        return None
    try:
        return base64.b64decode(b64)
    except Exception:
        return None


def _platform_icon(platform: str) -> str:
    return {"instagram":"📸","twitter":"🐦","linkedin":"💼","youtube":"▶️","whatsapp":"💬"}.get(platform.lower(),"📱")


def _score_bar(score: int, label: str = ""):
    color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"
    st.markdown(
        f"""<div style="margin:8px 0">
          <div style="display:flex;justify-content:space-between;margin-bottom:3px">
            <small style="color:#94a3b8">{label}</small>
            <small style="color:{color};font-weight:700">{score}/100</small>
          </div>
          <div style="background:#1e293b;border-radius:6px;height:8px">
            <div style="background:{color};height:8px;border-radius:6px;width:{score}%"></div>
          </div>
        </div>""", unsafe_allow_html=True)


def _panel_title(icon: str, title: str, subtitle: str):
    st.markdown(f"""
    <div style='margin-bottom:14px'>
      <div style='font-size:1.1rem;font-weight:700;color:#E2E8F0'>{icon} {title}</div>
      <div style='font-size:0.8rem;color:#64748B;margin-top:3px'>{subtitle}</div>
    </div>""", unsafe_allow_html=True)


# ── Draft card renderer ───────────────────────────────────────────────────────
def _render_card(variant: Dict[str, Any], turn_key: str, idx: int):
    v_id = variant.get("variant_id", f"v{idx}")
    lang = variant.get("lang", "—")
    text = variant.get("text", "")
    image_b64 = variant.get("image_b64")
    image_url  = variant.get("image_url")

    lang_flags = {"en":"🇬🇧","hi":"🇮🇳","ta":"🇮🇳","te":"🇮🇳","bn":"🇮🇳","mr":"🇮🇳","gu":"🇮🇳"}
    flag = lang_flags.get(lang, "🌐")

    st.markdown(
        f"<div style='background:#1A2235;border:1px solid #242E44;border-radius:10px;"
        f"padding:12px 14px;margin-bottom:8px'>"
        f"<div style='color:#F97316;font-size:0.72rem;font-weight:700;letter-spacing:0.5px;"
        f"margin-bottom:8px;text-transform:uppercase'>{flag} {lang.upper()} · {v_id}</div>",
        unsafe_allow_html=True)

    st.write(text)

    tags = [w for w in text.split() if w.startswith("#")]
    if tags:
        st.markdown(" ".join(
            f"<span style='background:#1e3a5f;color:#93c5fd;padding:2px 8px;"
            f"border-radius:12px;font-size:0.78em'>{t}</span>" for t in tags
        ), unsafe_allow_html=True)

    img_col, dl_col = st.columns([3, 1])
    with img_col:
        img_bytes = _b64_to_bytes(image_b64)
        if img_bytes:
            st.image(img_bytes, use_column_width=True)
        elif image_url:
            st.image(image_url, use_column_width=True)
    with dl_col:
        if img_bytes:
            st.download_button("⬇ Image", data=img_bytes,
                               file_name=f"image_{turn_key}_{v_id}.png", mime="image/png",
                               key=f"dl_img_{turn_key}_{v_id}_{idx}")
        st.download_button("⬇ Caption", data=text.encode("utf-8"),
                           file_name=f"caption_{turn_key}_{v_id}.txt", mime="text/plain",
                           key=f"dl_cap_{turn_key}_{v_id}_{idx}")

    with st.expander("✏️ Edit caption", expanded=False):
        edited = st.text_area("Caption", value=text, height=100,
                              key=f"edit_{turn_key}_{v_id}_{idx}")
        if edited != text:
            variant["text"] = edited

    st.markdown("</div>", unsafe_allow_html=True)


# ── Panel: Video Script ───────────────────────────────────────────────────────
def _panel_video_script():
    _panel_title("🎬", "Video Script Generator",
                 "Generate a shot-list script for short social videos (6–30 s)")

    draft = st.session_state.get("latest_draft")
    v_prompt = st.text_input("Topic / prompt",
                              value=draft.get("prompt","") if draft else "", key="vs_prompt")
    v_langs  = st.multiselect("Languages", ["en","hi","ta","te","bn"], default=["en"], key="vs_langs")

    if st.button("Generate video script", key="btn_video_script"):
        if not v_prompt.strip():
            st.warning("Please enter a prompt.")
            return
        with st.spinner("Generating script…"):
            try:
                result = post_video_script(v_prompt.strip(), v_langs)
            except Exception as exc:
                st.error(f"Error: {exc}"); return

        if result.get("status") == "error":
            st.error(result.get("error", "Unknown error")); return

        for s in result.get("scripts", []):
            lang = s.get("lang","—")
            raw  = s.get("video_script","[]")
            try:
                scenes = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                scenes = [{"scene":1,"shot":raw}]

            st.markdown(
                f"<div style='background:#131929;border:1px solid #242E44;border-radius:8px;"
                f"padding:12px;margin:8px 0'>"
                f"<div style='color:#F97316;font-weight:700;margin-bottom:8px'>"
                f"{lang.upper()} — {len(scenes)} scenes</div>", unsafe_allow_html=True)

            for sc in scenes:
                shot = sc.get("shot", sc.get("description",""))
                cam  = sc.get("camera","")
                sfx  = sc.get("sfx","")
                st.markdown(
                    f"**Scene {sc.get('scene','?')}** "
                    f"<span style='color:#F97316;font-size:0.78em'>{sc.get('duration_seconds','?')}s · {cam}</span>"
                    f"<br><span style='color:#CBD5E1'>{shot}</span>"
                    + (f"<br><span style='color:#64748B;font-size:0.75em'>🔊 {sfx}</span>" if sfx else ""),
                    unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇ Download .txt",
                    data="\n".join(f"Scene {sc.get('scene')}: {sc.get('shot',sc.get('description',''))}"
                                   for sc in scenes).encode("utf-8"),
                    file_name=f"script_{lang}.txt", mime="text/plain",
                    key=f"dl_script_{lang}_{int(time.time())}")
            with c2:
                st.download_button("⬇ Download .json",
                    data=json.dumps(scenes, ensure_ascii=False, indent=2).encode("utf-8"),
                    file_name=f"script_{lang}.json", mime="application/json",
                    key=f"dl_script_json_{lang}_{int(time.time())}")
        st.success("Done!")


# ── Panel: Hashtag Optimizer ──────────────────────────────────────────────────
def _panel_hashtags():
    _panel_title("#️⃣", "Hashtag Optimizer",
                 "Platform-optimised hashtags with predicted engagement score")

    draft = st.session_state.get("latest_draft")
    caption_default = draft["variants"][0].get("text","") if draft and draft.get("variants") else ""

    h_caption  = st.text_area("Caption to optimise", value=caption_default, height=80, key="ht_caption")
    h_platform = st.selectbox("Platform",
                               ["instagram","twitter","linkedin","youtube","whatsapp"], key="ht_platform")

    if st.button("Suggest hashtags", key="btn_hashtags"):
        if not h_caption.strip():
            st.warning("Please enter a caption."); return
        with st.spinner("Generating hashtags…"):
            try:
                result = post_hashtags(h_caption.strip(), h_platform)
            except Exception as exc:
                st.error(f"Error: {exc}"); return

        if result.get("status") == "error":
            st.error(result.get("error","Unknown error")); return

        hashtags   = result.get("hashtags",[])
        engagement = result.get("predicted_engagement",0)
        _score_bar(engagement, "Predicted engagement score")

        if hashtags:
            st.markdown(" ".join(
                f"<span style='background:#1e3a5f;color:#93c5fd;padding:4px 12px;"
                f"border-radius:20px;font-size:0.82em;display:inline-block;margin:3px'>"
                f"{h['tag']}</span>" for h in hashtags), unsafe_allow_html=True)

            with st.expander("Why these hashtags?"):
                for h in hashtags:
                    st.write(f"**{h['tag']}** — {h.get('reason','')}")

            tags_str = " ".join(h["tag"] for h in hashtags)
            st.text_area("Copy all hashtags", value=tags_str, height=60,
                         key=f"ht_copy_{int(time.time())}")
            if st.button("Insert into caption", key=f"ht_insert_{int(time.time())}"):
                st.text_area("Updated caption", value=h_caption.strip()+"\n\n"+tags_str,
                             height=120, key="ht_updated")
        st.success("Done!")


# ── Panel: Voice Caption ──────────────────────────────────────────────────────
def _panel_voice():
    _panel_title("🔊", "Voice Caption",
                 "Generate an MP3 voice clip of a caption via Amazon Polly")

    draft = st.session_state.get("latest_draft")
    text_default = ""
    lang_default = "en"
    if draft and draft.get("variants"):
        first = draft["variants"][0]
        text_default = first.get("text","")
        lang_default = first.get("lang","en")

    vc_text  = st.text_area("Caption text", value=text_default, height=80, key="vc_text")
    vc_lang  = st.selectbox("Language code", ["en","hi","ta","te","bn","mr","gu"],
                             index=["en","hi","ta","te","bn","mr","gu"].index(lang_default)
                                   if lang_default in ["en","hi","ta","te","bn","mr","gu"] else 0,
                             key="vc_lang")
    vc_voice = st.text_input("Polly voice ID (leave blank for default)", value="",
                              placeholder="e.g. Raveena, Joanna, Aditi", key="vc_voice")

    if st.button("🔊 Generate voice", key="btn_voice"):
        if not vc_text.strip():
            st.warning("Please enter text."); return
        with st.spinner("Calling Amazon Polly…"):
            try:
                result = post_voice(vc_text.strip(), lang=vc_lang, voice=vc_voice or None)
            except Exception as exc:
                st.error(f"Error: {exc}"); return

        if result.get("status") == "error":
            st.error(result.get("error","Unknown error")); return

        note = result.get("note","")
        if note:
            st.info(note)

        audio_bytes = _b64_to_bytes(result.get("audio_base64"))
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")
            st.download_button("⬇ Download MP3", data=audio_bytes,
                               file_name="caption_voice.mp3", mime="audio/mpeg",
                               key=f"dl_mp3_{int(time.time())}")
        else:
            st.info("No audio returned — ensure IAM Polly permissions are set.")
        st.success("Done!")


# ── Panel: Content Calendar ───────────────────────────────────────────────────
def _panel_calendar():
    _panel_title("📅", "Content Calendar",
                 "Generate a scheduled publishing plan and export as CSV")

    draft = st.session_state.get("latest_draft")
    cc_topic     = st.text_input("Topic", value=draft.get("prompt","") if draft else "", key="cc_topic")
    cc_days      = st.selectbox("Days", [7,14,30], key="cc_days")
    cc_platforms = st.multiselect("Platforms",
                                   ["instagram","twitter","linkedin","youtube","whatsapp"],
                                   default=["instagram","twitter"], key="cc_platforms")

    if st.button("Generate calendar", key="btn_calendar"):
        if not cc_topic.strip():
            st.warning("Please enter a topic."); return
        with st.spinner("Generating calendar…"):
            try:
                result = post_calendar(cc_topic.strip(), cc_platforms, cc_days)
            except Exception as exc:
                st.error(f"Error: {exc}"); return

        if result.get("status") == "error":
            st.error(result.get("error","Unknown error")); return

        items = result.get("items",[])
        st.markdown(f"**{len(items)} posts planned from {result.get('start_date','')}**")

        rows_html = "".join(
            f"<tr style='border-bottom:1px solid #1E293B'>"
            f"<td style='padding:6px 10px;color:#94A3B8'>{it.get('date','')}</td>"
            f"<td style='padding:6px 10px'>{_platform_icon(it.get('platform',''))} {it.get('platform','')}</td>"
            f"<td style='padding:6px 10px;color:#94A3B8'>{it.get('time','')}</td>"
            f"<td style='padding:6px 10px;color:#CBD5E1'>"
            + ((it.get('caption','')[:80]+'…') if len(it.get('caption',''))>80 else it.get('caption',''))
            + "</td></tr>"
            for it in items)
        st.markdown(
            f"<div style='background:#131929;border:1px solid #242E44;border-radius:8px;overflow:hidden;margin:8px 0'>"
            f"<table style='width:100%;font-size:0.82em;border-collapse:collapse'>"
            f"<thead><tr style='background:#1A2235;color:#F97316'>"
            f"<th style='text-align:left;padding:8px 10px'>Date</th>"
            f"<th style='text-align:left;padding:8px 10px'>Platform</th>"
            f"<th style='text-align:left;padding:8px 10px'>Time</th>"
            f"<th style='text-align:left;padding:8px 10px'>Caption</th>"
            f"</tr></thead><tbody>{rows_html}</tbody></table></div>",
            unsafe_allow_html=True)

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["date","platform","caption","image_prompt","time"])
        writer.writeheader()
        for it in items:
            writer.writerow({k: it.get(k,"") for k in ["date","platform","caption","image_prompt","time"]})
        st.download_button("⬇ Export CSV", data=buf.getvalue().encode("utf-8"),
                           file_name=f"calendar_{cc_days}d.csv", mime="text/csv",
                           key=f"dl_cal_{int(time.time())}")

        with st.expander("Create drafts from calendar"):
            st.warning("This will POST each calendar item as a new draft.")
            if st.button("Confirm — create all drafts", key=f"cc_create_{int(time.time())}"):
                created = 0
                for it in items:
                    try:
                        post_create_draft(it.get("caption", "calendar item"), languages=["en"])
                        created += 1
                    except Exception:
                        pass
                st.success(f"Created {created} draft(s).")
        st.success("Done!")


# ── Panel: Platform Variants ──────────────────────────────────────────────────
def _panel_platform_variants():
    _panel_title("📱", "Platform Variants",
                 "Generate optimised captions per platform and language")

    draft = st.session_state.get("latest_draft")
    pv_prompt = st.text_input("Prompt / topic",
                               value=draft.get("prompt","") if draft else "", key="pv_prompt")
    lang_default = list({v.get("lang","en") for v in draft.get("variants",[])}) if draft else ["en"]
    pv_langs  = st.multiselect("Languages", ["en","hi","ta","te","bn","mr","gu"],
                                default=lang_default or ["en"], key="pv_langs")
    pv_plats  = st.multiselect("Platforms",
                                ["instagram","twitter","linkedin","youtube","whatsapp"],
                                default=["instagram","twitter","linkedin"], key="pv_plats")

    if st.button("Generate platform variants", key="btn_pv"):
        if not pv_prompt.strip():
            st.warning("Please enter a prompt."); return
        if not pv_plats:
            st.warning("Select at least one platform."); return
        with st.spinner("Generating variants…"):
            try:
                result = post_platform_variants(pv_prompt.strip(), pv_langs, pv_plats)
            except Exception as exc:
                st.error(f"Error: {exc}"); return

        if result.get("status") == "error":
            st.error(result.get("error","Unknown error")); return

        by_plat: Dict[str, List] = {}
        for v in result.get("platform_variants",[]):
            by_plat.setdefault(v.get("platform","?"), []).append(v)

        for plat, pvs in by_plat.items():
            st.markdown(
                f"<div style='background:#131929;border:1px solid #242E44;border-radius:8px;"
                f"padding:12px;margin:8px 0'>"
                f"<div style='color:#F97316;font-weight:700;margin-bottom:10px'>"
                f"{_platform_icon(plat)} {plat.capitalize()}</div>",
                unsafe_allow_html=True)
            for pv in pvs:
                lang    = pv.get("lang","—")
                caption = pv.get("caption","")
                cta     = pv.get("cta","")
                chars   = len(caption)
                limits  = {"twitter":280,"youtube":100}
                if limits.get(plat) and chars > limits[plat]:
                    st.warning(f"{lang.upper()}: {chars}/{limits[plat]} chars — over limit")
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.text_area(f"{lang.upper()} — {chars} chars",
                                 value=caption + (f"\n\n{cta}" if cta else ""),
                                 height=80, key=f"pv_{plat}_{lang}_{int(time.time())}")
                with c2:
                    if st.button("Add to draft", key=f"pv_add_{plat}_{lang}_{int(time.time())}"):
                        if st.session_state.get("latest_draft"):
                            st.session_state["latest_draft"]["variants"].append({
                                "variant_id": f"pv-{plat}-{lang}", "lang": lang,
                                "text": caption, "image_prompt": pv_prompt,
                                "image_b64": None, "image_url": None,
                            })
                            st.success("Added.")
                        else:
                            st.warning("No active draft.")
            st.markdown("</div>", unsafe_allow_html=True)
        st.success("Done!")


# ── Main ──────────────────────────────────────────────────────────────────────
def page():
    header()

    st.markdown("""
    <div style='margin-bottom:20px'>
      <h1 style='font-family:Sora,sans-serif;font-size:1.8rem;font-weight:700;margin:0;
                 background:linear-gradient(90deg,#F97316,#FCD34D);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                 background-clip:text;'>✨ Generate Content</h1>
      <p style='color:#64748B;margin:4px 0 0;font-size:0.88rem'>
        Create multilingual social media drafts, scripts, hashtags, and more
      </p>
    </div>""", unsafe_allow_html=True)

    with st.expander("⚙️ Settings", expanded=False):
        s1, s2 = st.columns(2)
        with s1:
            st.session_state["bs_languages"] = st.multiselect(
                "Languages", ["en","hi","ta","te","bn","mr","gu"],
                default=st.session_state["bs_languages"], key="settings_langs")
        with s2:
            st.session_state["bs_images"] = st.checkbox(
                "Generate images", value=st.session_state["bs_images"], key="settings_images")

    tabs = st.tabs(["💬 Draft","🎬 Video Script","#️⃣ Hashtags","🔊 Voice","📅 Calendar","📱 Platform Variants"])

    with tabs[0]:
        st.markdown("#### Generate social media drafts")
        for turn in st.session_state["chat_history"]:
            role = turn.get("role","assistant")
            with st.chat_message(role):
                if role == "user":
                    st.write(turn["content"])
                else:
                    st.write(turn.get("content",""))
                    d = turn.get("draft")
                    if d:
                        tk = d.get("draft_id", str(id(d)))
                        for i, v in enumerate(d.get("variants",[])):
                            _render_card(v, tk, i)

        user_input = st.chat_input("Describe your post (e.g. Monsoon street food in Patna)…")
        if user_input:
            st.session_state["chat_history"].append({"role":"user","content":user_input})
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
                        st.session_state["chat_history"].append({"role":"assistant","content":f"Error: {exc}"})
                        return
                st.session_state["latest_draft"] = draft
                tk  = draft.get("draft_id", str(int(time.time())))
                msg = f"Generated **{len(draft.get('variants',[]))} variant(s)** for: *{user_input}*"
                st.write(msg)
                for i, v in enumerate(draft.get("variants",[])):
                    _render_card(v, tk, i)
                st.session_state["chat_history"].append({"role":"assistant","content":msg,"draft":draft})

        if st.session_state["chat_history"]:
            if st.button("🗑 Clear chat", key="clear_chat"):
                st.session_state["chat_history"] = []
                st.rerun()

    with tabs[1]: _panel_video_script()
    with tabs[2]: _panel_hashtags()
    with tabs[3]: _panel_voice()
    with tabs[4]: _panel_calendar()
    with tabs[5]: _panel_platform_variants()