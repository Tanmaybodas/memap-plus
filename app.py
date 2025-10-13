import os
from typing import Dict, Optional

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from src.models.types import Profile
from src.data.github_client import fetch_github_user
from src.data.reddit_client import fetch_reddit_user
from src.data.instagram_client import fetch_instagram_user
from src.data.web_search import web_mentions
from src.similarity.text_similarity import compare_usernames, bio_similarity
from src.similarity.image_similarity import image_similarity
from src.graph.graph_builder import build_footprint_html, build_comparison_html

# Load .env early
load_dotenv()

st.set_page_config(
    page_title="MeMap+ — Digital Footprint & Impersonation Analyzer",
    page_icon="🕸️",
    layout="wide",
)

PRIMARY = "#3B82F6"
OK = "#22c55e"
WARN = "#f59e0b"
BAD = "#ef4444"

st.markdown(
    "<h1 style='margin-bottom:0'>MeMap+</h1>"
    "<div style='color:#9CA3AF;margin-top:0'>Visual Digital Footprint & Impersonation Analyzer</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Modes")
    mode = st.radio("Select", ["Footprint", "Comparison"], index=0)
    st.markdown("---")
    st.subheader("Options")
    enable_imgs = os.getenv("ENABLE_IMAGE_SIMILARITY", "true").lower() == "true"
    st.caption(f"Image similarity: {'enabled' if enable_imgs else 'disabled'}")
    st.caption(f"Embeddings: {'enabled' if os.getenv('ENABLE_EMBEDDINGS','false').lower()=='true' else 'disabled'}")

def collect_profiles(username: str) -> Dict[str, Profile]:
    profiles: Dict[str, Profile] = {}
    gh = fetch_github_user(username)
    if gh:
        profiles["github"] = gh
    rd = fetch_reddit_user(username)
    if rd:
        profiles["reddit"] = rd
    ig = fetch_instagram_user(username)
    if ig:
        profiles["instagram"] = ig
    return profiles

def exposure_index(n_profiles: int, n_mentions: int) -> int:
    # Simple heuristic
    score = (n_profiles * 25) + (n_mentions * 10)
    return max(0, min(100, score))

def risk_badge(score: float) -> str:
    if score >= 0.8:
        return f"<span style='color:{BAD};font-weight:600'>High</span>"
    if score >= 0.6:
        return f"<span style='color:{WARN};font-weight:600'>Moderate</span>"
    return f"<span style='color:{OK};font-weight:600'>Low</span>"

def show_profiles_cards(title: str, profiles: Dict[str, Profile]):
    st.subheader(title)
    if not profiles:
        st.info("No profiles found with current configuration.")
        return
    cols = st.columns(min(3, max(1, len(profiles))))
    i = 0
    for platform, p in profiles.items():
        with cols[i % len(cols)]:
            st.markdown(f"**{platform.title()}**")
            st.write(p.display_name or p.username)
            if p.profile_url:
                st.write(p.profile_url)
            if p.bio:
                st.caption(p.bio)
        i += 1

if mode == "Footprint":
    st.subheader("Footprint Mode")
    username = st.text_input("Enter a username (e.g., octocat):", value="", placeholder="yourhandle")
    if st.button("Search") and username.strip():
        with st.spinner("Collecting profiles..."): 
            profiles = collect_profiles(username.strip())
            mentions = web_mentions(username.strip(), num_results=5)

        show_profiles_cards("Profiles", profiles)

        # Graph
        if profiles:
            html = build_footprint_html(username.strip(), profiles)
            components.html(html, height=620, scrolling=True)

        # Mentions + Exposure
        st.subheader("Web Mentions")
        if mentions:
            for m in mentions:
                st.write(f"- [{m.get('title')}]({m.get('link')})")
                if m.get("snippet"):
                    st.caption(m["snippet"]) 
        else:
            st.caption("No mentions found or Google CSE not configured.")

        idx = exposure_index(len(profiles), len(mentions))
        st.subheader("Privacy Dashboard")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Profiles Found", len(profiles))
        with c2:
            st.metric("Web Mentions", len(mentions))
        st.progress(idx / 100.0, text=f"Exposure Index: {idx}/100")

else:
    st.subheader("Comparison Mode")
    c1, c2 = st.columns(2)
    with c1:
        user_a = st.text_input("User A", value="", placeholder="e.g., tanmaybodas")
    with c2:
        user_b = st.text_input("User B", value="", placeholder="e.g., tanmaybodas_")

    if st.button("Compare") and user_a.strip() and user_b.strip():
        ua = user_a.strip()
        ub = user_b.strip()
        with st.spinner("Fetching and comparing..."):
            profiles_a = collect_profiles(ua)
            profiles_b = collect_profiles(ub)

            # Platform similarity
            platform_scores: Dict[str, float] = {}
            for platform in set(list(profiles_a.keys()) + list(profiles_b.keys())):
                pa = profiles_a.get(platform)
                pb = profiles_b.get(platform)
                if pa and pb:
                    user_sim = compare_usernames(pa.username, pb.username)
                    bio_sim = bio_similarity(pa.bio, pb.bio)
                    # Weight usernames and bios
                    platform_scores[platform] = (0.5 * user_sim) + (0.5 * bio_sim)

            # Overall metrics
            overall_username = compare_usernames(ua, ub)
            # Average bio similarity where both bios exist
            bio_sims = []
            for platform in platform_scores:
                pa = profiles_a.get(platform)
                pb = profiles_b.get(platform)
                if pa and pb and pa.bio and pb.bio:
                    bio_sims.append(bio_similarity(pa.bio, pb.bio))
            overall_bio = sum(bio_sims) / len(bio_sims) if bio_sims else 0.0

            shared = len([p for p in platform_scores.keys()])
            total_unique = len(set(list(profiles_a.keys()) + list(profiles_b.keys())))
            mutual_presence = (shared / total_unique) if total_unique else 0.0

            img_sim_val: Optional[float] = None
            if enable_imgs:
                # Try image sim only across shared platforms first; fallback to main GH avatars
                candidates = []
                for platform in platform_scores:
                    pa = profiles_a.get(platform)
                    pb = profiles_b.get(platform)
                    if pa and pb and pa.avatar_url and pb.avatar_url:
                        candidates.append((pa.avatar_url, pb.avatar_url))
                if not candidates:
                    # fallback: try github avatars if present
                    ga, gb = profiles_a.get("github"), profiles_b.get("github")
                    if ga and gb and ga.avatar_url and gb.avatar_url:
                        candidates.append((ga.avatar_url, gb.avatar_url))
                if candidates:
                    img_sim_val = image_similarity(candidates[0][0], candidates[0][1])

            # Impersonation likelihood (heuristic)
            # 40% bio, 30% username, 20% mutual presence, 10% image similarity (if any)
            imp_like = (0.4 * overall_bio) + (0.3 * overall_username) + (0.2 * mutual_presence) + (0.1 * (img_sim_val or 0.0))
            imp_like = max(0.0, min(1.0, imp_like))

        # Metrics panel
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Bio Similarity", f"{int(overall_bio*100)}%")
        with m2:
            st.metric("Username Similarity", f"{int(overall_username*100)}%")
        with m3:
            st.metric("Mutual Platform Presence", f"{int(mutual_presence*100)}%")
        with m4:
            if img_sim_val is not None:
                st.metric("Profile Image Similarity", f"{int(img_sim_val*100)}%")
            else:
                st.metric("Profile Image Similarity", "N/A")

        st.markdown(f"Risk Level: {risk_badge(imp_like)} — Impersonation Likelihood {int(imp_like*100)}%", unsafe_allow_html=True)

        # Insights
        st.subheader("AI Insights")
        insights = []
        if overall_bio >= 0.8:
            insights.append("Bio content highly similar — possible impersonation.")
        elif overall_bio >= 0.6:
            insights.append("Bios show notable overlap — investigate.")
        if overall_username >= 0.9:
            insights.append("Usernames nearly identical — typical impersonation pattern.")
        elif overall_username >= 0.75:
            insights.append("Usernames share a strong root — could be related accounts.")
        if mutual_presence >= 0.5:
            insights.append("Strong mutual platform presence detected.")
        if img_sim_val is not None:
            if img_sim_val >= 0.8:
                insights.append("Profile images look very similar.")
            elif img_sim_val >= 0.6:
                insights.append("Profile images share some visual similarity.")

        if insights:
            for i in insights:
                st.write(f"- {i}")
        else:
            st.caption("No strong signals detected with current data.")

        # Graph
        html = build_comparison_html(ua, ub, profiles_a, profiles_b, platform_scores)
        components.html(html, height=620, scrolling=True)

st.markdown(
    "<div style='color:#6B7280;margin-top:2rem'>Note: Data is best-effort from public sources. "
    "APIs may rate-limit; app degrades gracefully when a source is unavailable.</div>",
    unsafe_allow_html=True,
)