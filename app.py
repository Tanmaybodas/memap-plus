import os
from typing import Dict, Optional
import requests

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
from pyvis.network import Network

# Load .env early
load_dotenv()

st.set_page_config(
    page_title="MeMap+ — Digital Footprint & Impersonation Analyzer",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Modern color palette
PRIMARY = "#6366f1"  # Indigo
PRIMARY_DARK = "#4f46e5"
SECONDARY = "#8b5cf6"  # Violet
ACCENT = "#06b6d4"  # Cyan
SUCCESS = "#10b981"  # Emerald
WARNING = "#f59e0b"  # Amber
DANGER = "#ef4444"  # Red
DARK = "#1f2937"  # Gray-800
LIGHT = "#f9fafb"  # Gray-50
NEUTRAL = "#6b7280"  # Gray-500

# Custom CSS for modern UI
st.markdown("""
<style>
    /* Global Styles */
    .main {
        padding: 2rem 1rem;
    }
    
    /* Header Styling */
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 20px 40px rgba(99, 102, 241, 0.3);
    }
    
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(45deg, #ffffff, #e0e7ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .main-subtitle {
        font-size: 1.2rem;
        margin-top: 0.5rem;
        opacity: 0.9;
        font-weight: 400;
    }
    
    /* Card Styling */
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
        margin-bottom: 1.5rem;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.6);
    }
    
    /* Input Styling */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #e5e7eb;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
        border-radius: 10px;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* Alert Styling */
    .stAlert {
        border-radius: 12px;
        border-left: 4px solid;
    }
    
    /* Spinner Styling */
    .stSpinner {
        border: 3px solid #f3f4f6;
        border-top: 3px solid #6366f1;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Risk Badge Styling */
    .risk-high {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4);
    }
    
    .risk-moderate {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
    }
    
    .risk-low {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
    }
    
    /* Profile Card Styling */
    .profile-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .profile-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    
    .platform-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
        margin-bottom: 1rem;
    }
    
    .github-icon { background: linear-gradient(135deg, #22c55e, #16a34a); }
    .reddit-icon { background: linear-gradient(135deg, #f97316, #ea580c); }
    .instagram-icon { background: linear-gradient(135deg, #a855f7, #9333ea); }
</style>
""", unsafe_allow_html=True)

# Modern Header
st.markdown(
    """
    <div class="main-header">
        <h1 class="main-title">MeMap+</h1>
        <p class="main-subtitle">Advanced Digital Footprint & Impersonation Analyzer</p>
    </div>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.markdown("### 🎯 Analysis Mode")
    mode = st.radio(
        "Choose your analysis type:", 
        ["🔍 Footprint Analysis", "⚖️ Comparison Analysis"], 
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Settings")
    enable_imgs = os.getenv("ENABLE_IMAGE_SIMILARITY", "true").lower() == "true"
    enable_emb = os.getenv('ENABLE_EMBEDDINGS','false').lower()=='true'
    friendly_graph = st.checkbox("Beginner-friendly graph labels", value=True)
    use_api_backend = st.checkbox("Use API backend (FastAPI)", value=True)
    api_base_url = st.text_input("API Base URL", value=os.getenv("API_BASE_URL", "http://localhost:8000"), help="FastAPI server base URL")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Image Analysis", "✅" if enable_imgs else "❌")
    with col2:
        st.metric("AI Embeddings", "✅" if enable_emb else "❌")
    
    st.markdown("---")
    
    st.markdown("### 📊 Features")
    st.markdown("")
    st.markdown("• **Multi-platform Analysis**")
    st.markdown("• **Real-time Similarity Detection**")
    st.markdown("• **Visual Network Graphs**")
    st.markdown("• **Privacy Risk Assessment**")
    st.markdown("• **AI-Powered Insights**")
    
    st.markdown("---")
    
    st.markdown("### 💡 Tips")
    st.info("💡 **Pro Tip:** Enable API keys in environment variables for enhanced data collection and analysis accuracy.")

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
        return f"<span class='risk-high'>HIGH RISK</span>"
    if score >= 0.6:
        return f"<span class='risk-moderate'>MODERATE</span>"
    return f"<span class='risk-low'>LOW RISK</span>"

def show_profiles_cards(title: str, profiles: Dict[str, Profile]):
    st.markdown(f"### 📱 {title}")
    if not profiles:
        st.info("🔍 No profiles found with current configuration. Try enabling API keys for better results.")
        return
    
    cols = st.columns(min(3, max(1, len(profiles))))
    platform_icons = {
        "github": "🐙",
        "reddit": "🤖", 
        "instagram": "📸"
    }
    
    i = 0
    for platform, p in profiles.items():
        with cols[i % len(cols)]:
            icon = platform_icons.get(platform, "🌐")
            
            # Create a styled profile card
            st.markdown(
                f"""
                <div class="profile-card">
                    <div class="platform-icon {platform}-icon">
                        {icon}
                    </div>
                    <h4 style="margin: 0; color: #1f2937;">{platform.title()}</h4>
                    <h3 style="margin: 0.5rem 0; color: #6366f1;">{p.display_name or p.username}</h3>
                    {f'<p style="color: #6b7280; font-size: 0.9rem; margin: 0.5rem 0;">{p.bio}</p>' if p.bio else ''}
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Add the profile link using Streamlit's native markdown
            if p.profile_url:
                st.markdown(f"**🔗 [View {platform.title()} Profile]({p.profile_url})**")
        i += 1

def graph_from_api(nodes, edges) -> str:
    net = Network(height="650px", width="100%", bgcolor="#0f172a", font_color="#e2e8f0")
    for n in nodes:
        nid = n.get("id")
        label = n.get("label", nid)
        group = n.get("group")
        meta = n.get("meta") or {}
        title_parts = []
        if meta.get("display_name"):
            title_parts.append(str(meta.get("display_name")))
        if meta.get("bio"):
            title_parts.append(str(meta.get("bio")))
        if meta.get("url"):
            title_parts.append(str(meta.get("url")))
        title = "\n".join(title_parts)
        net.add_node(nid, label=label, title=title, group=group)
    for e in edges:
        net.add_edge(e.get("source"), e.get("target"), title=e.get("label"), value=e.get("weight"))
    net.set_options("""
{
  "nodes": { "font": { "color": "#e2e8f0" } },
  "edges": { "color": { "color": "#64748b" } }
}
""")
    return net.generate_html(notebook=False)

if "Footprint" in mode:
    st.markdown("### 🔍 Digital Footprint Analysis")
    st.markdown("Discover and analyze a user's digital presence across multiple platforms.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        username = st.text_input(
            "Enter username to analyze:", 
            value="", 
            placeholder="e.g., octocat, john_doe",
            help="Enter a username without @ symbol"
        )
    with col2:
        search_clicked = st.button("🔍 Analyze", type="primary", use_container_width=True)
    
    if search_clicked and username.strip():
        with st.spinner(""):
            profiles = {}
            mentions = []
            used_api = False
            if use_api_backend:
                try:
                    r = requests.get(f"{api_base_url}/footprint", params={"username": username.strip()}, timeout=30)
                    r.raise_for_status()
                    data = r.json()
                    html = graph_from_api(data.get("nodes", []), data.get("edges", []))
                    components.html(html, height=650, scrolling=True)
                    used_api = True
                    # Also fetch local profiles so the profile cards populate
                    profiles = collect_profiles(username.strip())
                except Exception as e:
                    st.warning(f"API unavailable, falling back to local: {e}")
            if not used_api:
                profiles = collect_profiles(username.strip())
                html = build_footprint_html(username.strip(), profiles, friendly=friendly_graph)
                components.html(html, height=650, scrolling=True)
            # mentions shown regardless
            mentions = web_mentions(username.strip(), num_results=5)

        show_profiles_cards("Profiles", profiles)

        # Profiles cards only if we have local profiles
        if profiles:
            show_profiles_cards("Profiles", profiles)

        # Privacy Dashboard
        st.markdown("### 📊 Privacy Exposure Dashboard")
        
        idx = exposure_index(len(profiles), len(mentions))
        
        # Enhanced metrics with better styling
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h2 style="color: #6366f1; margin: 0;">{len(profiles)}</h2>
                    <p style="margin: 0; color: #6b7280;">Platform Profiles</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <h2 style="color: #8b5cf6; margin: 0;">{len(mentions)}</h2>
                    <p style="margin: 0; color: #6b7280;">Web Mentions</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col3:
            risk_color = DANGER if idx >= 70 else WARNING if idx >= 40 else SUCCESS
            st.markdown(
                f"""
                <div class="metric-card">
                    <h2 style="color: {risk_color}; margin: 0;">{idx}%</h2>
                    <p style="margin: 0; color: #6b7280;">Exposure Index</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Enhanced progress bar
        st.markdown(f"**Overall Privacy Risk Level: {idx}%**")
        st.progress(idx / 100.0, text=f"Exposure Index: {idx}/100")
        
        # Risk interpretation
        if idx >= 70:
            st.error("⚠️ **High Risk**: Significant digital footprint detected. Consider privacy settings review.")
        elif idx >= 40:
            st.warning("⚡ **Moderate Risk**: Moderate digital presence. Monitor your online visibility.")
        else:
            st.success("✅ **Low Risk**: Minimal digital footprint. Good privacy practices maintained.")
        
        # Web Mentions Section
        if mentions:
            st.markdown("### 🌐 Web Mentions")
            for i, m in enumerate(mentions, 1):
                with st.expander(f"📄 {m.get('title', 'Untitled')} - Mention #{i}"):
                    st.markdown(f"**🔗 [Open Link]({m.get('link')})**")
                    if m.get("snippet"):
                        st.markdown(f"*{m['snippet']}*")
        else:
            st.info("🔍 No web mentions found. This could be due to limited search results or Google CSE not configured.")

else:
    st.markdown("### ⚖️ Impersonation Comparison Analysis")
    st.markdown("Compare two users to detect potential impersonation or account similarities.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 👤 User A")
        user_a = st.text_input(
            "Username A:", 
            value="", 
            placeholder="e.g., tanmaybodas",
            key="user_a",
            help="First user to analyze"
        )
    with col2:
        st.markdown("#### 👤 User B")
        user_b = st.text_input(
            "Username B:", 
            value="", 
            placeholder="e.g., tanmaybodas_",
            key="user_b",
            help="Second user to compare"
        )

    compare_clicked = st.button("⚖️ Compare Users", type="primary", use_container_width=True)
    
    if compare_clicked and user_a.strip() and user_b.strip():
        ua = user_a.strip()
        ub = user_b.strip()
        with st.spinner(""):
            used_api = False
            profiles_a = {}
            profiles_b = {}
            if use_api_backend:
                try:
                    r = requests.get(f"{api_base_url}/compare", params={"user_a": ua, "user_b": ub}, timeout=45)
                    r.raise_for_status()
                    data = r.json()
                    html_api = graph_from_api(data.get("nodes", []), data.get("edges", []))
                    components.html(html_api, height=650, scrolling=True)
                    used_api = True
                except Exception as e:
                    st.warning(f"API unavailable, falling back to local: {e}")
            if not used_api:
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

        # Enhanced metrics panel
        st.markdown("### 📊 Similarity Analysis Results")
        
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            bio_color = DANGER if overall_bio >= 0.8 else WARNING if overall_bio >= 0.6 else SUCCESS
            st.markdown(
                f"""
                <div class="metric-card">
                    <h2 style="color: {bio_color}; margin: 0;">{int(overall_bio*100)}%</h2>
                    <p style="margin: 0; color: #6b7280;">Bio Similarity</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with m2:
            user_color = DANGER if overall_username >= 0.9 else WARNING if overall_username >= 0.75 else SUCCESS
            st.markdown(
                f"""
                <div class="metric-card">
                    <h2 style="color: {user_color}; margin: 0;">{int(overall_username*100)}%</h2>
                    <p style="margin: 0; color: #6b7280;">Username Similarity</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with m3:
            presence_color = DANGER if mutual_presence >= 0.8 else WARNING if mutual_presence >= 0.5 else SUCCESS
            st.markdown(
                f"""
                <div class="metric-card">
                    <h2 style="color: {presence_color}; margin: 0;">{int(mutual_presence*100)}%</h2>
                    <p style="margin: 0; color: #6b7280;">Platform Presence</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with m4:
            if img_sim_val is not None:
                img_color = DANGER if img_sim_val >= 0.8 else WARNING if img_sim_val >= 0.6 else SUCCESS
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <h2 style="color: {img_color}; margin: 0;">{int(img_sim_val*100)}%</h2>
                        <p style="margin: 0; color: #6b7280;">Image Similarity</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <h2 style="color: #6b7280; margin: 0;">N/A</h2>
                        <p style="margin: 0; color: #6b7280;">Image Similarity</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Risk Assessment
        st.markdown("### ⚠️ Risk Assessment")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Risk Level:** {risk_badge(imp_like)}", unsafe_allow_html=True)
            st.markdown(f"**Impersonation Likelihood:** {int(imp_like*100)}%")
        with col2:
            if imp_like >= 0.8:
                st.error("🚨 **HIGH ALERT**\nStrong impersonation indicators detected!")
            elif imp_like >= 0.6:
                st.warning("⚠️ **MODERATE RISK**\nSome concerning similarities found.")
            else:
                st.success("✅ **LOW RISK**\nMinimal impersonation indicators.")

        # Enhanced AI Insights
        st.markdown("### 🤖 AI-Powered Insights")
        
        insights = []
        insight_icons = []
        
        if overall_bio >= 0.8:
            insights.append("Bio content highly similar — possible impersonation.")
            insight_icons.append("🔴")
        elif overall_bio >= 0.6:
            insights.append("Bios show notable overlap — investigate further.")
            insight_icons.append("🟡")
            
        if overall_username >= 0.9:
            insights.append("Usernames nearly identical — typical impersonation pattern.")
            insight_icons.append("🔴")
        elif overall_username >= 0.75:
            insights.append("Usernames share a strong root — could be related accounts.")
            insight_icons.append("🟡")
            
        if mutual_presence >= 0.5:
            insights.append("Strong mutual platform presence detected.")
            insight_icons.append("🔵")
            
        if img_sim_val is not None:
            if img_sim_val >= 0.8:
                insights.append("Profile images look very similar.")
                insight_icons.append("🔴")
            elif img_sim_val >= 0.6:
                insights.append("Profile images share some visual similarity.")
                insight_icons.append("🟡")

        if insights:
            for i, (insight, icon) in enumerate(zip(insights, insight_icons)):
                st.markdown(
                    f"""
                    <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #6366f1;">
                        <p style="margin: 0; font-weight: 500;">{icon} {insight}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("🔍 No strong impersonation signals detected with current data. This is a good sign!")
            
        # Additional recommendations
        st.markdown("### 💡 Recommendations")
        if imp_like >= 0.7:
            st.markdown(
                """
                - **Immediate Action Required**: Report potential impersonation
                - **Document Evidence**: Screenshot all similar profiles
                - **Platform Reporting**: Use platform-specific reporting tools
                - **Legal Consultation**: Consider legal advice if significant harm
                """
            )
        elif imp_like >= 0.4:
            st.markdown(
                """
                - **Monitor Closely**: Keep an eye on both accounts
                - **Gather Evidence**: Document any suspicious behavior
                - **Report if Needed**: Report if impersonation is confirmed
                """
            )
        else:
            st.markdown(
                """
                - **Low Risk**: Continue normal monitoring
                - **Good Practices**: Maintain unique usernames across platforms
                """
            )

        # Graph (local only)
        if not use_api_backend:
            html = build_comparison_html(ua, ub, profiles_a, profiles_b, platform_scores, friendly=friendly_graph)
            components.html(html, height=650, scrolling=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #6b7280; margin-top: 2rem; padding: 1rem; background: #f8fafc; border-radius: 12px;">
        <h4 style="color: #6366f1; margin-bottom: 0.5rem;">🔒 Privacy & Security Notice</h4>
        <p style="margin: 0; font-size: 0.9rem;">
            Data analysis is performed using publicly available information only. 
            APIs may rate-limit; the application gracefully handles unavailable sources. 
            No private data is stored or transmitted.
        </p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; opacity: 0.8;">
            MeMap+ v1.0 | Built with ❤️ for digital security awareness
        </p>
    </div>
    """,
    unsafe_allow_html=True
)