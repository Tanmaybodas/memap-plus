from typing import Dict, Optional
import networkx as nx
from pyvis.network import Network
from src.models.types import Profile

_PLATFORM_COLORS = {
    "github": "#22c55e",
    "reddit": "#f97316",
    "instagram": "#a855f7",
    "mentions": "#60a5fa",
}

def _edge_color(score: float) -> str:
    if score >= 0.8:
        return "#22c55e"  # green
    if score >= 0.6:
        return "#f59e0b"  # yellow
    return "#ef4444"      # red

def build_footprint_html(central_label: str, profiles: Dict[str, Profile]) -> str:
    G = nx.Graph()
    G.add_node(central_label, color="#3B82F6", shape="dot", size=18)
    for platform, prof in profiles.items():
        label = f"{platform}: {prof.username}"
        color = _PLATFORM_COLORS.get(platform, "#94a3b8")
        G.add_node(label, color=color, shape="dot", size=12, title=(prof.bio or ""))
        G.add_edge(central_label, label)

    net = Network(height="600px", width="100%", bgcolor="#0B1220", font_color="#E5E7EB")
    net.from_nx(G)
    net.set_options("""
    const options = {
      nodes: { font: { color: '#E5E7EB' } },
      edges: { color: { color: '#64748b' } },
      physics: { stabilization: true }
    };
    """)
    return net.generate_html(notebook=False)

def build_comparison_html(user_a: str, user_b: str, profiles_a: Dict[str, Profile], profiles_b: Dict[str, Profile], platform_scores: Dict[str, float]) -> str:
    G = nx.Graph()
    G.add_node("User A", color="#60a5fa", shape="dot", size=18, title=user_a)
    G.add_node("User B", color="#f59e0b", shape="dot", size=18, title=user_b)

    for platform, prof in profiles_a.items():
        label = f"A:{platform}"; title = f"{prof.username}\n{prof.bio or ''}"
        G.add_node(label, color=_PLATFORM_COLORS.get(platform, "#94a3b8"), size=12, title=title)
        G.add_edge("User A", label)
    for platform, prof in profiles_b.items():
        label = f"B:{platform}"; title = f"{prof.username}\n{prof.bio or ''}"
        G.add_node(label, color=_PLATFORM_COLORS.get(platform, "#94a3b8"), size=12, title=title)
        G.add_edge("User B", label)

    for platform, score in platform_scores.items():
        if platform in profiles_a and platform in profiles_b:
            G.add_edge(f"A:{platform}", f"B:{platform}", color=_edge_color(score), width=1 + (score * 4))

    net = Network(height="600px", width="100%", bgcolor="#0B1220", font_color="#E5E7EB")
    net.from_nx(G)
    net.set_options("""
    const options = {
      nodes: { font: { color: '#E5E7EB' } },
      edges: { color: { color: '#64748b' } },
      physics: { stabilization: true }
    };
    """)
    return net.generate_html(notebook=False)