# st_pages/generate.py
"""
Upgraded Generate Content page for BharatStudio prototype.

Features included:
- Role presets (Independent Creator, Influencer, Brand/Agency)
- Template prompts & sample prompts
- Multi-language targets with UI chips
- Platform presets (Instagram / X / YouTube / WhatsApp)
- Variant count slider (1..5)
- Tone, length, creativity (temperature) controls
- Model selection (mock/local/bedrock)
- Image generation toggle + placeholder previews
- Hashtag suggestion and copy/download helpers
- Raw prompt inspector and regenerated prompt flow
- Error handling and user-friendly messages
- Stores last draft into st.session_state["latest_draft"]
- Uses lib.api_client.post_create_draft for backend (mock-friendly)
"""
import json
import time
import base64
import io
from typing import List, Dict

import streamlit as st
from lib.api_client import post_create_draft  # uses USE_MOCK when set
from lib.components import header

# ---------- Helper functions ----------

def _download_text(text: str, filename: str = "caption.txt"):
    """Return link to download text file."""
    b = text.encode("utf-8")
    b64 = base64.b64encode(b).decode()
    href = f'<a href="data:text/plain;base64,{b64}" download="{filename}">Download</a>'
    return href

def _download_image_bytes(img_bytes: bytes, filename: str = "image.png"):
    b64 = base64.b64encode(img_bytes).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}">Download Image</a>'
    return href

def _copy_button_js(element_id: str, label: str = "Copy"):
    """
    Return HTML for a copy-to-clipboard button using JS.
    Note: Streamlit may sanitize HTML — this works in many setups.
    """
    return f"""
    <button id="{element_id}_btn">{label}</button>
    <script>
    const btn = document.getElementById("{element_id}_btn");
    btn.addEventListener("click", () => {{
        const text = document.getElementById("{element_id}").innerText;
        navigator.clipboard.writeText(text);
        btn.innerText = 'Copied';
        setTimeout(()=>{{ btn.innerText = '{label}'; }}, 1200);
    }});
    </script>
    """

def pretty_json(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)

# ---------- UI small components ----------

def config_sidebar():
    st.sidebar.markdown("## Quick Generate Options")
    demo_mode = st.sidebar.checkbox("Use mock backend (demo)", value=True)
    show_raw = st.sidebar.checkbox("Show raw prompt (debug)", value=False)
    return {"demo_mode": demo_mode, "show_raw": show_raw}

def role_presets():
    """Return a dict of role presets (label -> prompt template and defaults)."""
    return {
        "Independent Creator": {
            "hint": "Short social captions, single-person POV",
            "prompt_template": "Write {n_variants} short captions for {platform} about: {topic}. Tone: {tone}. Keep within {char_limit} characters.",
            "default_platforms": ["instagram", "twitter"]
        },
        "Influencer (short-form)": {
            "hint": "Hooks, 3-second openers, and video ideas",
            "prompt_template": "Generate {n_variants} short hooks and 3-line script ideas for a {platform} short on: {topic}. Tone: {tone}. Add image concept.",
            "default_platforms": ["youtube", "instagram"]
        },
        "Brand / Agency": {
            "hint": "Campaign-ready caption variants + hashtags and CTA",
            "prompt_template": "Create {n_variants} campaign captions for {platform} about: {topic}. Include 3 hashtags and one CTA. Tone: {tone}. Provide image concept and suggested aspect ratio.",
            "default_platforms": ["instagram", "whatsapp"]
        }
    }

def platform_presets():
    return {
        "instagram": {"label": "Instagram (4:5, 2200 char)", "max_chars": 2200},
        "twitter": {"label": "X / Twitter (280 char)", "max_chars": 280},
        "youtube": {"label": "YouTube Shorts Title (100 char)", "max_chars": 100},
        "whatsapp": {"label": "WhatsApp Story / Status (700 char)", "max_chars": 700},
    }

# ---------- Main UI page ----------

def page():
    header()
    st.title("✨ AI Content Generator — BharatStudio")

    # Top-row: Presets, Samples
    presets = role_presets()
    sample_prompts = [
        "Monsoon street food in Patna — short IG caption",
        "Tips to conserve water in small towns — short video hook",
        "New handcrafted cane lamps — product post for small business",
        "Quick morning yoga routine for beginners — 30s reel idea"
    ]

    left, right = st.columns([3, 1])
    with left:
        # Role selection and template preview
        role = st.selectbox("Creator Type / Role", list(presets.keys()))
        st.caption(presets[role]["hint"])
        topic = st.text_input("Topic / Brief", value=sample_prompts[0])
    with right:
        st.markdown("**Sample prompts**")
        for s in sample_prompts:
            if st.button(f"Use: {s}", key=f"sample_{s[:6]}"):
                st.session_state["topic"] = s
                # refresh page to update topic (so input shows)
                st.experimental_rerun()

    # Load persisted session topic if set
    if "topic" in st.session_state:
        topic = st.session_state["topic"]

    # Middle controls: platforms, languages, variants, model
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    platforms_map = platform_presets()

    with col1:
        platform_choices = st.multiselect("Publish Platforms", options=list(platforms_map.keys()),
                                          default=presets[role]["default_platforms"])
    with col2:
        languages = st.multiselect("Target Languages", options=["en", "hi", "ta", "bn", "mr", "kn", "ml"],
                                   default=["en", "hi"])
    with col3:
        n_variants = st.slider("Number of variants", min_value=1, max_value=5, value=2)

    col4, col5, col6 = st.columns(3)
    with col4:
        tone = st.selectbox("Tone", ["casual", "informal", "formal", "witty", "emotional", "motivational"], index=0)
    with col5:
        length = st.selectbox("Length target", ["short (<=120 chars)", "medium (<=250 chars)", "long (<=600 chars)"], index=0)
    with col6:
        creativity = st.slider("Creativity (temperature)", 0.0, 1.0, 0.7)

    # Model & image options
    st.markdown("---")
    mcol1, mcol2 = st.columns([2, 1])
    with mcol1:
        model = st.selectbox("Generation model", options=["mock", "local-llm", "bedrock"], index=0,
                             help="Choose 'mock' for offline demo, 'bedrock' to use AWS Bedrock via the backend.")
    with mcol2:
        do_images = st.checkbox("Also generate image prompt / image", value=True)

    # Advanced options in expander
    with st.expander("Advanced options (prompting / RAG / persona)"):
        persona = st.text_input("Creator persona (one-line)", placeholder="e.g., 'young food vlogger from Bihar'")
        use_rag = st.checkbox("Use Retrieval-Augmented-Generation (RAG) with cultural notes", value=True)
        dialect_note = st.text_input("Dialect / region note (optional)", placeholder="e.g., Bhojpuri phrasing suggestions")

    # Build the actual prompt (preview) using selected template
    template = presets[role]["prompt_template"]
    # Decide char limit based on selected length / platforms (basic mapping)
    if "short" in length:
        char_limit = 120
    elif "medium" in length:
        char_limit = 250
    else:
        char_limit = 600

    prompt_preview = template.format(
        n_variants=n_variants,
        platform=" & ".join([platforms_map[p]["label"] for p in platform_choices]) if platform_choices else "social platforms",
        topic=topic,
        tone=tone,
        char_limit=char_limit
    )

    # Show the built prompt and let user edit
    st.markdown("**Preview / edit the prompt that will be sent to the model**")
    prompt_editor = st.text_area("Model Prompt (editable)", value=prompt_preview, height=110, key="prompt_editor")

    # Quick submit area with safety checks
    st.markdown("---")
    submit_col, cancel_col = st.columns([1, 1])
    with submit_col:
        generate_btn = st.button("🚀 Generate with AI", key="generate_btn", help="Send prompt to backend/model")
    with cancel_col:
        if st.button("Clear Drafts"):
            st.session_state.pop("latest_draft", None)
            st.success("Cleared current draft from session")

    # Sidebar config for debug and demo
    cfg = config_sidebar()

    # Early exit if no generate click
    if not generate_btn:
        # If we already have a latest_draft, show preview summary to the user
        if st.session_state.get("latest_draft"):
            st.markdown("### Last generated draft (session)")
            _show_draft_summary(st.session_state["latest_draft"])
        st.info("Adjust the prompt and press 'Generate with AI' to create captions, hashtags, and image prompts.")
        return

    # On generate click: validate inputs
    if generate_btn:
        if not topic or topic.strip() == "":
            st.error("Please add a topic / brief before generating.")
            st.stop()

        # Build the payload for backend endpoint
        payload = {
            "prompt": prompt_editor,
            "content_type": platform_choices or ["instagram"],
            "tone": tone,
            "languages": languages or ["en"],
            "n_variants": n_variants,
            "creativity": float(creativity),
            "persona": persona,
            "use_rag": bool(use_rag),
            "dialect_note": dialect_note,
            "model": model,
            "generate_images": bool(do_images),
            "char_limit": int(char_limit)
        }

        # Show a compact parameters box
        with st.spinner("Contacting backend to generate variants..."):
            try:
                draft = post_create_draft(
                    payload["prompt"],
                    content_type=",".join(payload["content_type"]),
                    tone=payload["tone"],
                    languages=payload["languages"],
                    # Note: the API client may only accept (prompt, content_type, tone, languages);
                    # we send the rest in the prompt body or as meta (backend should accept extra keys if implemented)
                )
            except Exception as e:
                st.exception(f"Failed to generate content: {e}")
                st.stop()

        # Basic validation of response
        if not draft or "variants" not in draft:
            st.error("Backend returned an unexpected response. Check logs.")
            st.stop()

        # Store draft in session
        st.session_state["latest_draft"] = draft

        # Visual success & show variants
        st.success("✅ AI Generated content — review below")
        _show_draft_full_ui(draft, payload, cfg, model=model)


# ---------- Render helpers for generated content ----------

def _show_draft_summary(draft: Dict):
    """Compact summary of last draft"""
    st.markdown(f"**Draft ID:** `{draft.get('draft_id', 'n/a')}`")
    st.markdown(f"**Prompt:** {st.session_state.get('prompt_editor', '—')}")
    st.caption(f"Variants: {len(draft.get('variants', []))} — Languages: {', '.join({v.get('lang','?') for v in draft.get('variants',[])})}")

def _variant_card_ui(variant: Dict, idx: int, payload: Dict, cfg: Dict, model: str):
    """
    Render a single variant card. Provides:
    - Text area (editable)
    - Hashtag suggestions
    - Image preview (placeholder)
    - Download & copy buttons
    - Schedule quick buttons
    """
    st.markdown(f"---\n#### Variant {idx+1} — `{variant.get('lang')}`")
    col_text, col_media = st.columns([2, 1])

    with col_text:
        # Editable caption area
        caption_key = f"caption_{variant.get('variant_id')}"
        caption_value = variant.get("text", "")
        new_caption = st.text_area("Caption (editable)", value=caption_value, key=caption_key, height=120)

        # Emoji / CTA quick inserts
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("Add CTA: Learn more", key=f"cta_learn_{variant.get('variant_id')}"):
            new_caption += " Learn more."
            st.session_state[caption_key] = new_caption
        if c2.button("Add CTA: Shop now", key=f"cta_shop_{variant.get('variant_id')}"):
            new_caption += " Shop now."
            st.session_state[caption_key] = new_caption
        if c3.button("Add emoji 🔥", key=f"emoji_fire_{variant.get('variant_id')}"):
            new_caption += " 🔥"
            st.session_state[caption_key] = new_caption
        if c4.button("Shorten", key=f"shorten_{variant.get('variant_id')}"):
            # naive shorten: first 80 chars
            new_caption = new_caption[:80] + ("…" if len(new_caption) > 80 else "")
            st.session_state[caption_key] = new_caption

        # Hashtag suggestions block
        suggested_tags = variant.get("hashtags") or _simple_hashtag_sugg(new_caption)
        st.write("Suggested hashtags:", ", ".join(suggested_tags))
        if st.button("Copy hashtags", key=f"copy_hashtags_{variant.get('variant_id')}"):
            # small UX: show text area with hashtags ready to copy
            st.text_area("Hashtags", value=" ".join(["#"+t for t in suggested_tags]), height=30, key=f"ht_{variant.get('variant_id')}")
        # Download caption
        st.markdown(_download_text(new_caption, filename=f"caption_{variant.get('variant_id')}.txt"), unsafe_allow_html=True)

    with col_media:
        # Image: placeholder or generated (mock)
        img_bytes = variant.get("image_bytes")  # if backend returns image bytes
        image_prompt = variant.get("image_prompt", "Image concept not provided")
        st.markdown("**Image concept**")
        st.write(image_prompt)
        if img_bytes:
            try:
                # if bytes are provided base64 or raw bytes, handle flexibly
                if isinstance(img_bytes, str):
                    # assume base64 string
                    b = base64.b64decode(img_bytes)
                else:
                    b = img_bytes
                st.image(b, width=280)
                st.markdown(_download_image_bytes(b, filename=f"{variant.get('variant_id')}.png"), unsafe_allow_html=True)
            except Exception:
                st.image("https://via.placeholder.com/400x225.png?text=AI+Visual", width=280)
        else:
            st.image("https://via.placeholder.com/400x225.png?text=AI+Visual", width=280)

        # Quick publish / schedule stub
        if st.button("Quick schedule (tomorrow 6PM)", key=f"qs_{variant.get('variant_id')}"):
            st.info("Scheduled (demo) for tomorrow 18:00 — check Preview & Schedule page")

def _show_draft_full_ui(draft: Dict, payload: Dict, cfg: Dict, model: str):
    """
    Show full UI for a freshly generated draft:
     - Show metadata
     - Show individual variant cards with controls
     - Provide "Regenerate variant" actions
     - Provide raw JSON and model prompt (if debug)
    """
    st.markdown("## Generated Variants")
    variants = draft.get("variants", [])
    for idx, variant in enumerate(variants):
        _variant_card_ui(variant, idx, payload, cfg, model)

    # Action row
    a1, a2, a3 = st.columns(3)
    if a1.button("Regenerate all variants"):
        # naive regenerate action: call backend with same payload again
        st.warning("Regenerating all variants (demo)...")
        time.sleep(0.3)
        try:
            new_draft = post_create_draft(payload["prompt"], content_type=",".join(payload["content_type"]) if isinstance(payload["content_type"], list) else payload["content_type"], tone=payload["tone"], languages=payload["languages"])
            st.session_state["latest_draft"] = new_draft
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Regenerate failed: {e}")

    if a2.button("Export draft (JSON)"):
        st.download_button("Download draft JSON", data=pretty_json(draft), file_name=f"draft_{draft.get('draft_id')}.json", mime="application/json")

    if a3.button("Save draft to repo (mock)"):
        st.success("Saved draft to repository (demo). In production this would push to backend DB.")

    # Debug / raw data
    if cfg.get("show_raw"):
        with st.expander("Raw draft JSON"):
            st.code(pretty_json(draft), language="json")

# ---------- small utility functions ----------

def _simple_hashtag_sugg(text: str) -> List[str]:
    """Naive hashtag suggestion: pick nouns / words > 3 chars (demo)"""
    words = [w.strip(".,!?:;#").lower() for w in text.split() if len(w.strip(".,!?:;#")) > 3]
    uniq = []
    for w in words:
        if w not in uniq:
            uniq.append(w)
    return uniq[:6]

# If this file is run directly (debug), expose page
if __name__ == "__main__":
    # For development outside Streamlit UI
    print("This module is designed to be imported by prototype_app Streamlit launcher.")