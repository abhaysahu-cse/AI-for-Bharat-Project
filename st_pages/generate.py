# st_pages/generate.py
"""
BharatStudio — AI Assistant for Creators
Clean ChatGPT/Claude-style chat interface.
- Messages flow top → bottom
- Fixed prompt bar at bottom
- Full creator assistant (not just captions)
- No clutter
"""
import json
import base64
from typing import List, Dict

import streamlit as st
from lib.api_client import post_create_draft

# ─────────────────────────────────────────────────────────────
#  STYLES — dark, minimal, ChatGPT-like
# ─────────────────────────────────────────────────────────────
STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"] {
    background: #212121 !important;
    font-family: 'Inter', sans-serif !important;
    color: #ececec !important;
}

[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stStatusWidget"], footer, #MainMenu { display: none !important; }

[data-testid="block-container"] { padding: 0 !important; max-width: 100% !important; }
[data-testid="stMain"] > div { padding: 0 !important; }

/* TOP BAR */
.bs-topbar {
    position: fixed; top: 0; left: 0; right: 0; height: 52px;
    background: #212121; border-bottom: 1px solid #2f2f2f;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 24px; z-index: 1000;
}
.bs-logo { font-size: 15px; font-weight: 600; color: #fff; }
.bs-logo span { color: #f97316; }
.bs-model-badge {
    background: #2f2f2f; border-radius: 20px; padding: 4px 14px;
    font-size: 12px; color: #8e8ea0; border: 1px solid #3a3a3a;
}

/* CHAT SCROLL AREA */
.bs-chat-area {
    margin-top: 52px;
    padding-bottom: 170px;
    min-height: calc(100vh - 52px);
}

/* WELCOME */
.bs-welcome {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; min-height: calc(100vh - 220px);
    text-align: center; padding: 40px 20px;
}
.bs-welcome h2 {
    font-size: 26px; font-weight: 600; color: #ececec;
    margin-bottom: 8px; letter-spacing: -0.3px;
}
.bs-welcome p { font-size: 14px; color: #8e8ea0; line-height: 1.6; margin-bottom: 32px; }

/* USER MESSAGE */
.bs-msg-user {
    display: flex; justify-content: flex-end;
    padding: 16px 24px 0; max-width: 820px; margin: 0 auto; width: 100%;
}
.bs-bubble {
    background: #2f2f2f; border-radius: 18px 18px 4px 18px;
    padding: 12px 18px; max-width: 72%;
    font-size: 15px; line-height: 1.6; color: #ececec;
}

/* AI MESSAGE */
.bs-msg-ai {
    padding: 20px 24px 0; max-width: 820px; margin: 0 auto; width: 100%;
}
.bs-ai-label {
    display: flex; align-items: center; gap: 8px;
    font-size: 13px; font-weight: 500; color: #8e8ea0; margin-bottom: 14px;
}
.bs-ai-icon {
    width: 22px; height: 22px; border-radius: 50%;
    background: linear-gradient(135deg, #f97316, #fbbf24);
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; flex-shrink: 0;
}

/* VARIANT CARD */
.bs-card {
    background: #2a2a2a; border: 1px solid #333; border-radius: 14px;
    padding: 20px; margin-bottom: 10px;
    transition: border-color 0.2s;
}
.bs-card:hover { border-color: #484848; }
.bs-card-top {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 12px;
}
.bs-lang-tag {
    background: #1c1c1c; border: 1px solid #3a3a3a; border-radius: 20px;
    padding: 3px 12px; font-size: 11px; font-weight: 600;
    color: #f97316; text-transform: uppercase; letter-spacing: 0.5px;
}
.bs-card-num { font-size: 11px; color: #4a4a4a; }
.bs-caption {
    font-size: 15px; line-height: 1.75; color: #d4d4d4;
    border-left: 2px solid #f97316; padding-left: 14px;
    margin-bottom: 12px; white-space: pre-wrap;
}
.bs-concept {
    font-size: 12px; color: #5a5a5a; background: #1e1e1e;
    border-radius: 8px; padding: 10px 14px; margin-bottom: 12px;
}
.bs-hashtags { display: flex; flex-wrap: wrap; gap: 6px; }
.bs-hashtag {
    background: #1e1e1e; border: 1px solid #333; border-radius: 20px;
    padding: 3px 11px; font-size: 12px; color: #8e8ea0;
}

/* ACTION ROW */
.bs-actions {
    max-width: 820px; margin: 4px auto 0; padding: 0 24px 24px;
    display: flex; align-items: center; gap: 8px;
}

/* DIVIDER */
.bs-sep { border: none; border-top: 1px solid #2a2a2a; margin: 4px 0 0; }

/* BOTTOM BAR */
.bs-bottom {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: #212121;
    padding: 10px 20px 20px; z-index: 999;
}
.bs-input-wrap {
    max-width: 720px; margin: 0 auto;
    background: #2f2f2f; border: 1px solid #3a3a3a; border-radius: 16px;
    padding: 4px 6px 4px 16px; display: flex; align-items: flex-end; gap: 6px;
    transition: border-color 0.2s;
}
.bs-input-wrap:focus-within { border-color: #f97316 !important; }

[data-testid="stTextArea"] label { display: none !important; }
[data-testid="stTextArea"] { flex: 1; }
[data-testid="stTextArea"] textarea {
    background: transparent !important; border: none !important;
    box-shadow: none !important; color: #ececec !important;
    font-family: 'Inter', sans-serif !important; font-size: 15px !important;
    resize: none !important; padding: 11px 0 !important; min-height: 24px !important;
}
[data-testid="stTextArea"] textarea::placeholder { color: #555 !important; }

/* Send button — only the last column button gets orange */
.bs-send-col .stButton > button {
    background: #f97316 !important; border: none !important;
    border-radius: 10px !important; width: 40px !important; height: 40px !important;
    font-size: 18px !important; color: #fff !important; padding: 0 !important;
    margin-bottom: 5px !important; line-height: 1 !important;
    transition: background 0.15s, transform 0.1s !important;
}
.bs-send-col .stButton > button:hover {
    background: #ea6c0a !important; transform: scale(1.06) !important;
}

/* Settings expander */
.bs-settings-wrap { max-width: 720px; margin: 0 auto 6px; }
[data-testid="stExpander"] { background: transparent !important; border: none !important; }
[data-testid="stExpander"] details { background: transparent !important; border: none !important; }
[data-testid="stExpander"] summary { font-size: 12px !important; color: #555 !important; padding: 2px 0 !important; }
[data-testid="stExpander"] summary:hover { color: #ececec !important; }

/* Widgets in settings */
[data-testid="stMultiSelect"] > div > div,
[data-testid="stSelectbox"] > div > div {
    background: #2a2a2a !important; border-color: #3a3a3a !important; color: #ececec !important;
}

/* Edit expander inside card */
.bs-edit-wrap [data-testid="stExpander"] summary { color: #555 !important; font-size: 12px !important; }

/* Spinner */
[data-testid="stSpinner"] > div > div { border-top-color: #f97316 !important; }

/* Download button */
[data-testid="stDownloadButton"] > button {
    background: #2a2a2a !important; border: 1px solid #3a3a3a !important;
    color: #ececec !important; border-radius: 8px !important; font-size: 12px !important;
}

/* Misc stButton overrides */
.stButton > button {
    background: #2a2a2a !important; border: 1px solid #3a3a3a !important;
    color: #ececec !important; border-radius: 8px !important; font-size: 13px !important;
    transition: border-color 0.15s !important;
}
.stButton > button:hover { border-color: #f97316 !important; color: #f97316 !important; }

/* IMAGE PREVIEW inside variant card */
.bs-img-wrap { border-radius: 10px; overflow: hidden; margin-bottom: 14px; border: 1px solid #333; }
.bs-img-label { font-size: 11px; color: #555; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
[data-testid="stImage"] img { border-radius: 10px !important; border: 1px solid #333 !important; width: 100% !important; }
</style>
"""

# ─────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────
LANGUAGES = {
    "en": "English", "hi": "हिंदी", "ta": "தமிழ்",
    "bn": "বাংলা",  "mr": "मराठी", "te": "తెలుగు",
    "kn": "ಕನ್ನಡ",  "ml": "മലയാളം",
}

SUGGESTIONS = [
    ("🌧️ Monsoon street food caption",
     "Short, catchy Instagram post",
     "Write a catchy Instagram caption about monsoon street food in Patna"),
    ("🎬 YouTube Shorts hook",
     "3-line opening for a food reel",
     "Write the best 3-line opening hook for a YouTube Shorts video on street food"),
    ("🏮 Product launch post",
     "Small business · handcraft launch",
     "Write an Instagram + WhatsApp post to launch a new handcrafted cane lamp collection"),
    ("📈 Content strategy ideas",
     "5 ideas for a regional food brand",
     "Give me 5 creative Instagram content ideas for a regional food brand trying to grow"),
]

# ─────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────
def _tags(text: str) -> List[str]:
    stops = set("the a an is are was were in on at to of and or for with by it its this that".split())
    words = [w.strip(".,!?:;#🌧️🍵🔥✨💡🎬📈🏮—–'\"").lower() for w in text.split()]
    seen, out = set(), []
    for w in words:
        if len(w) > 3 and w not in stops and w not in seen:
            seen.add(w); out.append(w)
    return out[:5]

def _pretty(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)

# ─────────────────────────────────────────────────────────────
#  Render one variant card
# ─────────────────────────────────────────────────────────────
def _render_card(variant: Dict, idx: int):
    lang    = variant.get("lang", "en")
    lname   = LANGUAGES.get(lang, lang.upper())
    text    = variant.get("text", "")
    concept = variant.get("image_prompt", "")
    hashtags = variant.get("hashtags") or _tags(text)
    vid     = variant.get("variant_id", f"v{idx+1}")

    tag_html  = "".join(f'<span class="bs-hashtag">#{t}</span>' for t in hashtags)
    conc_html = (f'<div class="bs-concept">🎨 {concept}</div>' if concept else "")

    st.markdown(f"""
<div class="bs-card">
    <div class="bs-card-top">
        <span class="bs-lang-tag">{lname}</span>
        <span class="bs-card-num">variant {idx+1} · {vid}</span>
    </div>
    <div class="bs-caption">{text}</div>
    {conc_html}
    <div class="bs-hashtags">{tag_html}</div>
</div>""", unsafe_allow_html=True)

    # ── IMAGE DISPLAY ────────────────────────────────────────────────────────
    image_b64 = variant.get("image_b64") or ""
    image_url = variant.get("image_url") or ""
    if image_b64:
        try:
            img_bytes = base64.b64decode(image_b64)
            img_col, act_col = st.columns([2, 1])
            with img_col:
                st.markdown('<div class="bs-img-wrap">', unsafe_allow_html=True)
                st.image(img_bytes, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with act_col:
                st.markdown('<p class="bs-img-label">Generated visual</p>', unsafe_allow_html=True)
                st.download_button(
                    label="⬇ Image",
                    data=img_bytes,
                    file_name=f"variant_{vid}.png",
                    mime="image/png",
                    key=f"img_dl_{vid}_{idx}",
                    use_container_width=True,
                )
                if image_url:
                    st.markdown(f'<a href="{image_url}" target="_blank" style="font-size:11px;color:#f97316;">🔗 S3 link</a>', unsafe_allow_html=True)
        except Exception as img_err:
            st.caption(f"Image preview unavailable: {img_err}")

    # Edit expander
    st.markdown('<div class="bs-edit-wrap">', unsafe_allow_html=True)
    with st.expander("✏️ Edit caption"):
        edited = st.text_area("", value=text, height=90,
                              key=f"edit_{vid}_{idx}", label_visibility="collapsed")
        if st.button("Save", key=f"save_{vid}_{idx}"):
            variant["text"] = edited
            st.toast("Saved ✓", icon="✅")
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  Render one AI response block
# ─────────────────────────────────────────────────────────────
def _render_ai_block(draft: Dict):
    st.markdown("""
<div class="bs-msg-ai">
    <div class="bs-ai-label">
        <div class="bs-ai-icon">✦</div>
        BharatStudio
    </div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div style="max-width:820px;margin:0 auto;padding:0 24px;">', unsafe_allow_html=True)

    variants = draft.get("variants", [])
    if not variants:
        st.markdown('<p style="color:#8e8ea0;font-size:14px;">No output returned. Please try again.</p>',
                    unsafe_allow_html=True)
    else:
        for i, v in enumerate(variants):
            _render_card(v, i)

    st.markdown('</div>', unsafe_allow_html=True)

    # Action row
    st.markdown('<div class="bs-actions">', unsafe_allow_html=True)
    a1, a2, a3 = st.columns([1, 1, 5])
    with a1:
        st.download_button("⬇ Export",
            data=_pretty(draft),
            file_name=f"draft_{draft.get('draft_id','x')}.json",
            mime="application/json",
            key=f"dl_{draft.get('draft_id','x')}_{id(draft)}")
    with a2:
        if st.button("🔄 Retry", key=f"retry_{id(draft)}"):
            hist = st.session_state.get("bs_history", [])
            # Remove last AI turn so user can resend
            if hist and hist[-1]["role"] == "ai":
                hist.pop()
            st.rerun()
    with a3:
        st.caption(f"`{draft.get('draft_id','—')}` · {draft.get('status','—')}")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<hr class="bs-sep"/>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  PAGE ENTRY POINT
# ─────────────────────────────────────────────────────────────
def page():
    st.markdown(STYLES, unsafe_allow_html=True)

    # Top bar
    st.markdown("""
<div class="bs-topbar">
    <div class="bs-logo">Bharat<span>Studio</span></div>
    <div class="bs-model-badge">amazon.nova-lite · eu-north-1</div>
</div>""", unsafe_allow_html=True)

    # Session init
    if "bs_history"  not in st.session_state: st.session_state["bs_history"]  = []
    if "bs_langs"    not in st.session_state: st.session_state["bs_langs"]    = ["en", "hi"]
    if "bs_tone"     not in st.session_state: st.session_state["bs_tone"]     = "casual"
    if "bs_platforms"not in st.session_state: st.session_state["bs_platforms"]= ["instagram"]
    if "bs_n"        not in st.session_state: st.session_state["bs_n"]        = 2
    if "bs_images"   not in st.session_state: st.session_state["bs_images"]   = True

    history = st.session_state["bs_history"]

    # ── CHAT AREA ──────────────────────────────────
    st.markdown('<div class="bs-chat-area">', unsafe_allow_html=True)

    if not history:
        # Welcome + suggestion cards
        st.markdown("""
<div class="bs-welcome">
    <h2>What can I create for you?</h2>
    <p>Captions · Scripts · Hooks · Campaign ideas<br>
    in English, Hindi and regional Indian languages.</p>
</div>""", unsafe_allow_html=True)

        st.markdown('<div style="max-width:640px;margin:-40px auto 0;padding:0 20px;">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        for i, (title, sub, pval) in enumerate(SUGGESTIONS):
            with (c1 if i % 2 == 0 else c2):
                if st.button(f"{title}\n\n{sub}", key=f"sug_{i}", use_container_width=True):
                    st.session_state["bs_prefill"] = pval
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        for turn in history:
            if turn["role"] == "user":
                st.markdown(f"""
<div class="bs-msg-user">
    <div class="bs-bubble">{turn["content"]}</div>
</div>""", unsafe_allow_html=True)
            else:
                _render_ai_block(turn["content"])

    st.markdown('</div>', unsafe_allow_html=True)  # end chat area

    # ── FIXED BOTTOM BAR ───────────────────────────
    st.markdown('<div class="bs-bottom">', unsafe_allow_html=True)

    # Collapsed settings
    st.markdown('<div class="bs-settings-wrap">', unsafe_allow_html=True)
    with st.expander("⚙️  Languages · Tone · Platforms"):
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1:
            st.session_state["bs_langs"] = st.multiselect(
                "Languages", list(LANGUAGES.keys()),
                default=st.session_state["bs_langs"],
                format_func=lambda x: LANGUAGES[x], key="sl_lang")
        with s2:
            opts = ["casual", "witty", "formal", "emotional", "motivational"]
            st.session_state["bs_tone"] = st.selectbox(
                "Tone", opts,
                index=opts.index(st.session_state["bs_tone"]), key="sl_tone")
        with s3:
            st.session_state["bs_platforms"] = st.multiselect(
                "Platforms", ["instagram","twitter","youtube","whatsapp"],
                default=st.session_state["bs_platforms"], key="sl_plat")
        with s4:
            st.session_state["bs_n"] = st.slider(
                "Variants", 1, 5, st.session_state["bs_n"], key="sl_n")
        with s5:
            st.session_state["bs_images"] = st.checkbox(
                "Generate images", value=st.session_state.get("bs_images", True),
                key="sl_images", help="Attach an AI-generated image to each variant")
    st.markdown('</div>', unsafe_allow_html=True)

    # Input bar
    prefill = st.session_state.pop("bs_prefill", "")
    st.markdown('<div class="bs-input-wrap">', unsafe_allow_html=True)
    left_col, right_col = st.columns([12, 1])
    with left_col:
        user_input = st.text_area(
            "msg", value=prefill,
            placeholder="Ask me to write a caption, script, hook, campaign idea…",
            height=52, key="bs_inp", label_visibility="collapsed")
    with right_col:
        st.markdown('<div class="bs-send-col">', unsafe_allow_html=True)
        send = st.button("↑", key="bs_send")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)  # end input-wrap

    st.markdown(
        '<p style="text-align:center;font-size:11px;color:#3a3a3a;margin-top:6px;">'
        'Always review AI output before publishing.</p>',
        unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # end bs-bottom

    # ── SEND LOGIC ─────────────────────────────────
    if send:
        text = (user_input or "").strip()
        if not text:
            st.toast("Type something first.", icon="⚠️")
            return

        history.append({"role": "user", "content": text})

        langs  = st.session_state["bs_langs"]  or ["en", "hi"]
        tone   = st.session_state["bs_tone"]
        plats  = st.session_state["bs_platforms"] or ["instagram"]
        n      = st.session_state["bs_n"]

        with st.spinner("Generating…"):
            try:
                enriched = (
                    f"{text}\n"
                    f"Tone: {tone}. Platforms: {', '.join(plats)}. "
                    f"Produce {n} variants."
                )
                draft = post_create_draft(
                    enriched,
                    content_type=",".join(plats),
                    tone=tone,
                    languages=langs,
                    generate_images=st.session_state.get("bs_images", True),
                )
                history.append({"role": "ai", "content": draft})
            except Exception as e:
                history.append({"role": "ai", "content": {
                    "draft_id": "error", "status": "error",
                    "variants": [{"variant_id": "v1", "lang": "en",
                                  "text": f"Error: {e}", "image_prompt": ""}]
                }})
        st.rerun()


if __name__ == "__main__":
    print("Run via: streamlit run prototype_app.py")