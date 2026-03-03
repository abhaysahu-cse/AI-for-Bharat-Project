# st_pages/analytics.py
"""
Analytics dashboard for BharatStudio prototype.

Paste into st_pages/analytics.py (overwrite existing). This page:
 - Loads analytics for the selected draft (via lib.api_client.get_analytics or mock)
 - Shows KPI cards, time-series charts, and per-variant breakdown
 - Provides "what-if" simulation (change time, length, tone) with predicted impact
 - Suggests copy & hashtag optimizations and quick actions
 - Allows export of report (JSON / CSV)
 - Works in mock/demo mode if backend analytics are not available
"""

import streamlit as st
import time
import json
import math
import random
import csv
import io
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Tuple

from lib.components import header
from lib.api_client import get_analytics, get_recent_drafts  # get_analytics should accept draft_id or be mock-friendly

# ---------------------------
# Utilities & Mock helpers
# ---------------------------

def _now_iso():
    return datetime.utcnow().isoformat()

def _parse_iso(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.utcnow()

def _human(n: float) -> str:
    if n is None:
        return "-"
    if abs(n) < 1000:
        return str(round(n, 2))
    for unit in ["", "K", "M", "B"]:
        if abs(n) < 1000.0:
            return f"{n:3.1f}{unit}"
        n /= 1000.0
    return f"{n:.1f}T"

def _to_csv(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return ""
    output = io.StringIO()
    keys = list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=keys)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return output.getvalue()

def _download_link_text(name: str, text: str, mime="text/plain"):
    b = text.encode("utf-8")
    b64 = b64 = __import__("base64").b64encode(b).decode()
    href = f"data:{mime};base64,{b64}"
    return href

def _safe_get(d: Dict, k: str, default=None):
    return d.get(k, default) if isinstance(d, dict) else default

# Mock analytics generator (used if get_analytics fails)
def _mock_analytics_for_draft(draft_id: str, variants: List[Dict]) -> Dict:
    # create a timeline: last 14 days
    days = 14
    now = datetime.utcnow()
    timeline = []
    base_impressions = random.randint(500, 3000)
    for i in range(days):
        dt = now - timedelta(days=(days - i - 1))
        impressions = int(base_impressions * (0.8 + random.random() * 0.6))
        likes = int(impressions * (0.03 + random.random() * 0.05))
        comments = int(impressions * (0.001 + random.random() * 0.01))
        shares = int(impressions * (0.002 + random.random() * 0.008))
        timeline.append({"date": dt.date().isoformat(), "impressions": impressions, "likes": likes, "comments": comments, "shares": shares})
    # per-variant metrics
    variants_metrics = []
    for v in variants:
        impressions = int(sum([t["impressions"] for t in timeline]) / len(variants) * (0.9 + random.random() * 0.3))
        likes = int(impressions * (0.03 + random.random() * 0.04))
        ctr = round(random.uniform(0.01, 0.05), 3)
        eng_rate = round((likes + comments + shares) / impressions if impressions else 0, 3)
        hashtag_perf = [{"tag": f"tag{i}", "engagement_rate": round(random.uniform(0.02, 0.08), 3)} for i in range(1,4)]
        variants_metrics.append({
            "variant_id": v.get("variant_id"),
            "lang": v.get("lang"),
            "caption": v.get("text", ""),
            "image_prompt": v.get("image_prompt", ""),
            "impressions": impressions,
            "likes": likes,
            "comments": int(likes * 0.08),
            "shares": int(likes * 0.04),
            "engagement_rate": eng_rate,
            "ctr": ctr,
            "hashtag_performance": hashtag_perf,
            "predicted_score": round(50 + random.random() * 40, 1),
        })
    # overall KPIs
    total_impr = sum(t["impressions"] for t in timeline)
    total_likes = sum(v["likes"] for v in variants_metrics)
    kpis = {
        "impressions": total_impr,
        "likes": total_likes,
        "engagement_rate": round(sum(v["engagement_rate"] for v in variants_metrics) / len(variants_metrics), 3) if variants_metrics else 0,
        "saves": int(total_impr * 0.002),
        "ctr": round(sum(v["ctr"] for v in variants_metrics) / len(variants_metrics), 3) if variants_metrics else 0,
    }
    suggestions = [
        "Shorten the caption length for Twitter/X variants.",
        "Use 2–3 targeted hashtags focusing on location-specific tags.",
        "Post between 6–9 PM local time for better reach based on platform heuristics."
    ]
    return {"timeline": timeline, "variants": variants_metrics, "kpis": kpis, "suggestions": suggestions, "draft_id": draft_id}

# ---------------------------
# UI helpers: charts & cards
# ---------------------------

def _kpi_card(title: str, value: Any, delta: Any = None, description: str = "", as_percent: bool = False, precision: int = 2):
    """
    Robust KPI card:
      - Accepts numeric or pre-formatted string values.
      - If numeric and as_percent=True (or title contains 'rate'/'ctr'), shows percentage.
      - Falls back to showing the value string if non-numeric.
    """
    def _format_value(v):
        # numeric
        try:
            # treat booleans carefully
            if isinstance(v, bool):
                return str(v)
            n = float(v)
        except Exception:
            return str(v)  # non-numeric, show as-is

        # choose format: percent or compact human
        if as_percent or ("rate" in title.lower()) or ("ctr" in title.lower()):
            # treat n as ratio (0.03 -> 3.00%) OR absolute percent if >1 (3.0 -> 300%)
            if abs(n) <= 1:
                return f"{n * 100:.{precision}f}%"
            else:
                return f"{n:.{precision}f}%"
        else:
            # compact number using _human if available
            try:
                return _human(n)
            except Exception:
                return str(round(n, precision))

    display_value = _format_value(value)

    st.markdown(f"**{title}**")
    # render value; allow HTML for nicer size
    st.markdown(f"<h2 style='margin:0'>{display_value}</h2>", unsafe_allow_html=True)

    # delta: if numeric, color it; if string, show as-is
    if delta is not None:
        try:
            dnum = float(delta)
            color = "green" if dnum >= 0 else "red"
            st.markdown(f"<small style='color:{color}'>Δ {dnum:+}</small>", unsafe_allow_html=True)
        except Exception:
            st.markdown(f"<small>{delta}</small>", unsafe_allow_html=True)

    if description:
        st.caption(description)

def _line_chart_from_timeline(timeline: List[Dict], key: str = "impressions"):
    # convert timeline to format for st.line_chart (dict of lists)
    data = {t["date"]: t.get(key, 0) for t in timeline}
    # st.line_chart expects index by row; convert to lists
    dates = list(data.keys())
    values = [data[d] for d in dates]
    return dates, values

# Simple recommendations engine (mocked rules)
def _recommendations_for_variant(variant_metrics: Dict) -> List[str]:
    recs = []
    # length suggestion
    cap = variant_metrics.get("caption", "")
    if len(cap) > 220:
        recs.append("Caption is long — shorten to <220 chars for Instagram readability.")
    if variant_metrics.get("engagement_rate", 0) < 0.03:
        recs.append("Engagement rate is low — try stronger CTA and an emotional hook early in the caption.")
    # hashtags
    recs.append("Use 2-3 localized hashtags and 1 trending tag.")
    if variant_metrics.get("predicted_score", 0) < 60:
        recs.append("Consider using an image with higher contrast and action (food, people).")
    return recs

# ---------------------------
# Page: main
# ---------------------------

def page():
    header()
    st.title("📈 Analytics — BharatStudio Insights")

    # choose draft: prefer session latest_draft, but also allow list from recent drafts
    session_draft = st.session_state.get("latest_draft")
    drafts_list = []
    try:
        drafts_list = get_recent_drafts() or []
    except Exception:
        # ignore — will use session draft or empty
        drafts_list = drafts_list

    # normalize drafts into options
    options = []
    if session_draft:
        options.append(("session", f"Current session — {session_draft.get('draft_id', 'session')}"))
    for d in drafts_list:
        label = f"{d.get('draft_id')} — {d.get('prompt')[:60]}"
        options.append((d.get("draft_id"), label))

    if not options:
        st.info("Generate a draft on the Generate tab first. This page works best after you have generated content.")
        return

    # selection UI
    draft_choice_key = st.selectbox("Select draft for analytics", options=[o[0] for o in options], format_func=lambda k: dict(options)[k] if isinstance(dict(options), dict) and k in dict(options) else k)

    # resolve selected draft object and variants
    if draft_choice_key == "session":
        draft = session_draft
    else:
        draft = next((d for d in drafts_list if d.get("draft_id") == draft_choice_key), None)

    if not draft:
        st.error("Selected draft not found.")
        return

    draft_id = draft.get("draft_id", f"local-{int(time.time())}")
    st.markdown(f"**Draft:** `{draft_id}` — {draft.get('prompt', '')}")

    # timeframe controls
    days = st.slider("Days to show on trend charts", min_value=7, max_value=30, value=14, step=1)
    compare_with_days = st.checkbox("Show previous period (compare)", value=True)
    show_explain = st.checkbox("Show explainability / why AI suggested changes", value=True)
    st.markdown("---")

    # fetch analytics (backend or mock)
    analytics = None
    try:
        analytics = get_analytics(draft_id)
    except Exception:
        analytics = None

    if not analytics:
        # create mock analytics using variants from draft
        analytics = _mock_analytics_for_draft(draft_id, draft.get("variants", []))

    timeline = analytics.get("timeline", [])
    variants_metrics = analytics.get("variants", [])
    kpis = analytics.get("kpis", {})

    # KPI row
    st.markdown("### Key metrics")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_card("Impressions", kpis.get("impressions", 0), description="Total times content shown")
    with k2:
        _kpi_card("Likes", kpis.get("likes", 0), description="Total likes across variants")
    with k3:
        _kpi_card("Engagement rate", f"{kpis.get('engagement_rate', 0)*100:.2f}%", description="(likes+comments+shares)/impressions")
    with k4:
        _kpi_card("CTR", f"{kpis.get('ctr', 0)*100:.2f}%", description="Click-through-rate (approx)")

    st.markdown("---")

    # Time-series charts: impressions, likes, comments
    st.markdown("### Trends")
    # support date range from timeline (last N days)
    if timeline:
        # reduce timeline to requested days
        timeline_dates = [t["date"] for t in timeline]
        # pick last `days` entries
        trimmed = timeline[-days:] if len(timeline) >= days else timeline
        dates = [t["date"] for t in trimmed]
        impressions = [t["impressions"] for t in trimmed]
        likes = [t["likes"] for t in trimmed]
        comments = [t["comments"] for t in trimmed]

        # show multi-line chart
        chart_data = {
            "impressions": impressions,
            "likes": likes,
            "comments": comments
        }
        st.line_chart(data=chart_data, height=250)

        # small table
        with st.expander("Show raw timeline data"):
            st.table(trimmed)
    else:
        st.info("No timeline data available for this draft.")

    st.markdown("---")

    # Variant breakdown
    st.markdown("### Variant performance")
    if not variants_metrics:
        st.info("No variant metrics found. Generate content first.")
    else:
        # allow selecting up to 3 variants to compare
        variant_ids = [v["variant_id"] for v in variants_metrics]
        selected = st.multiselect("Select variants to show in detail (max 3)", options=variant_ids, default=variant_ids[:2])
        if len(selected) > 3:
            st.warning("Showing up to 3 variants — trimming selection.")
            selected = selected[:3]

        for v in variants_metrics:
            if v["variant_id"] in selected:
                # show compact card
                st.markdown(f"#### Variant `{v['variant_id']}` — {v.get('lang')}  (score: {v.get('predicted_score')})")
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.write(v.get("caption", "")[:400])
                    st.caption(f"Image prompt: {v.get('image_prompt', '')}")
                with c2:
                    st.metric("Impressions", _human(v.get("impressions", 0)))
                    st.metric("Likes", _human(v.get("likes", 0)))
                with c3:
                    st.metric("Engagement rate", f"{v.get('engagement_rate', 0)*100:.2f}%")
                    st.metric("CTR", f"{v.get('ctr', 0)*100:.2f}%")

                # Hashtag performance
                if v.get("hashtag_performance"):
                    st.write("Hashtag performance (simulated):")
                    for ht in v["hashtag_performance"]:
                        st.write(f"- #{ht['tag']}: engagement {ht['engagement_rate']*100:.1f}%")

                # Recommendations
                recs = _recommendations_for_variant(v)
                with st.expander("Recommendations & quick edits"):
                    for r in recs:
                        st.write("- " + r)
                    # quick edit actions
                    e1, e2 = st.columns(2)
                    with e1:
                        if st.button(f"Apply quick CTA to {v['variant_id']}", key=f"cta_{v['variant_id']}"):
                            st.success("Applied CTA (demo). Copy the text and paste into Localize to save.")
                    with e2:
                        if st.button(f"Shorten caption {v['variant_id']}", key=f"short_{v['variant_id']}"):
                            # show shortened example
                            short = v.get("caption", "")[:100] + ("…" if len(v.get("caption",""))>100 else "")
                            st.code(short)

    st.markdown("---")

    # What-if simulator: let user tweak features and see predicted change
    st.markdown("### What-if simulator (predictive)")
    sim_col1, sim_col2, sim_col3 = st.columns(3)
    with sim_col1:
        sim_tone = st.selectbox("Tone change", options=["no_change", "more_emotional", "more_professional", "shorter"], index=0)
    with sim_col2:
        sim_time = st.selectbox("Post time shift", options=["no_change", "move_to_evening", "move_to_morning"], index=0)
    with sim_col3:
        sim_hashtags = st.selectbox("Hashtag strategy", options=["no_change", "add_local_tags", "use_trending_tag"], index=0)

    if st.button("Run simulation"):
        # simple mocked prediction: apply multiplier to engagement
        base_eng = kpis.get("engagement_rate", 0) or 0.03
        multiplier = 1.0
        reasons = []
        if sim_tone == "more_emotional":
            multiplier += 0.12
            reasons.append("Emotional tone tends to increase engagement by ~12%")
        if sim_tone == "shorter":
            multiplier += 0.05
            reasons.append("Shorter captions can increase clarity (+5%)")
        if sim_time == "move_to_evening":
            multiplier += 0.08
            reasons.append("Evening posts usually get higher visibility (+8%)")
        if sim_hashtags == "add_local_tags":
            multiplier += 0.07
            reasons.append("Local hashtags improve discovery (+7%)")
        predicted = base_eng * multiplier
        st.metric("Predicted engagement rate", f"{predicted*100:.2f}%")
        with st.expander("Why this prediction?"):
            for r in reasons:
                st.write("- " + r)
            st.write("Note: This is a simulation for planning/demonstration. Real results depend on audience and creative.")

    st.markdown("---")

    # A/B test simulator (mock)
    st.markdown("### A / B test simulator")
    if st.button("Run A/B quick test (simulated)"):
        control = random.uniform(0.02, 0.05)
        variant = control * (1 + random.uniform(-0.2, 0.25))
        st.write(f"Control engagement: {control*100:.2f}%")
        st.write(f"Variant engagement: {variant*100:.2f}%")
        if variant > control:
            st.success("Variant performed better (simulated). Consider adopting changes.")
        else:
            st.info("Control remains stronger in this simulation.")

    st.markdown("---")

    # Report export
    st.markdown("### Export & report")
    rep_col1, rep_col2 = st.columns([2,1])
    with rep_col1:
        if st.button("Export full analytics JSON"):
            txt = json.dumps(analytics, ensure_ascii=False, indent=2)
            href = _download_link_text("analytics.json", txt, mime="application/json")
            st.markdown(f"[Download analytics JSON]({href})", unsafe_allow_html=True)
        if st.button("Export top-variants CSV"):
            rows = []
            for v in variants_metrics:
                rows.append({
                    "variant_id": v.get("variant_id"),
                    "lang": v.get("lang"),
                    "impressions": v.get("impressions"),
                    "likes": v.get("likes"),
                    "engagement_rate": v.get("engagement_rate"),
                    "predicted_score": v.get("predicted_score")
                })
            csv_text = _to_csv(rows)
            href = _download_link_text("variants.csv", csv_text, mime="text/csv")
            st.markdown(f"[Download variants CSV]({href})", unsafe_allow_html=True)
    with rep_col2:
        if st.button("Generate short summary (copy)"):
            summary = [
                f"Draft {draft_id}",
                f"Impressions: {_human(kpis.get('impressions',0))}",
                f"Likes: {_human(kpis.get('likes',0))}",
                f"Engagement: {kpis.get('engagement_rate',0)*100:.2f}%",
                "Top recommendation: " + (analytics.get("suggestions",[ "—"])[0])
            ]
            st.text_area("Summary (copy)", value="\n".join(summary), height=140)

    st.markdown("---")

    # Explainability & audit trail
    if show_explain:
        st.markdown("### Explainability & audit")
        with st.expander("Why did AI recommend these changes?"):
            st.write("We use heuristic signals for demo: caption length, engagement rate, local discovery signals, and platform heuristics.")
            st.write("Important signals considered (demo):")
            st.write("- Caption length vs platform limit")
            st.write("- Recent impressions / likes trend")
            st.write("- Hashtag localness score")
            st.write("- Time of day heuristics")
            st.write("For production, these signals would come from logs, model attributions, and RAG sources (cultural notes).")

    st.markdown("---")
    st.caption("Analytics page (demo mode) — values are simulated when backend is not connected. Connect your analytics endpoint to show real performance.")

# If this file is run directly for local debug
if __name__ == "__main__":
    print("This module provides an analytics page for Streamlit launcher.")