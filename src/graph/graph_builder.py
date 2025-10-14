from typing import Dict
import networkx as nx
from pyvis.network import Network
from src.models.types import Profile

# Colors for platforms
_PLATFORM_COLORS = {
    "github": "#22c55e",
    "reddit": "#f97316",
    "instagram": "#a855f7",
    "twitter": "#60a5fa",
    "mentions": "#60a5fa",
}

def _edge_color(score: float) -> str:
    if score >= 0.8:
        return "#22c55e"  # green
    if score >= 0.6:
        return "#f59e0b"  # yellow
    return "#ef4444"      # red

def _edge_label(score: float, friendly: bool) -> str:
    pct = f"{int(score * 100)}%"
    if not friendly:
        return pct
    if score >= 0.8:
        return f"{pct} — Strong"
    if score >= 0.6:
        return f"{pct} — Medium"
    return f"{pct} — Weak"

def _inject_overlay(html: str, legend_html: str) -> str:
    # Inject a small legend overlay before </body>
    overlay_css = """
    <style>
      .memap-legend {
        position: fixed;
        right: 18px;
        bottom: 18px;
        background: rgba(17,24,39,0.92);
        color: #E5E7EB;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 10px 12px;
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
        font-size: 12px;
        z-index: 9999;
        max-width: 300px;
        line-height: 1.35;
      }
      .memap-legend .row { display:flex; gap:8px; align-items:center; margin:6px 0; }
      .memap-legend .chip { width:14px; height:14px; border-radius:9999px; display:inline-block; }
      .memap-legend .chip.edge { width:28px; height:4px; border-radius:2px; }
      .memap-legend .title { font-weight:600; margin-bottom:6px; }
      .memap-legend hr { border: none; border-top: 1px solid #374151; margin: 8px 0; }
    </style>
    """
    injection = f"""{overlay_css}
    <div class="memap-legend">
      {legend_html}
    </div>
    """
    return html.replace("</body>", f"{injection}</body>")

def build_footprint_html(
    central_label: str,
    profiles: Dict[str, Profile],
    friendly: bool = True
) -> str:
    G = nx.Graph()
    # Center node
    G.add_node(central_label, color="#6366f1", shape="dot", size=25, label=central_label)

    # Platform nodes
    for platform, prof in profiles.items():
        color = _PLATFORM_COLORS.get(platform, "#94a3b8")
        bio_text = prof.bio[:50] + "..." if prof.bio and len(prof.bio) > 50 else prof.bio or "No bio available"
        title = f"Platform: {platform.title()}\nUsername: {prof.username}\nBio: {bio_text}\nFollowers: {prof.followers or 'Unknown'}"
        node_id = f"{platform}:{prof.username}"

        G.add_node(node_id, 
                  color=color, 
                  size=18, 
                  title=title,
                  label=f"{platform.title()}\n@{prof.username}",
                  shape="dot")
        G.add_edge(central_label, node_id, color="#64748b", width=3)

    net = Network(height="650px", width="100%", bgcolor="#0f172a", font_color="#e2e8f0")
    net.from_nx(G)
    net.set_options("""
{
  "nodes": { 
    "font": { 
      "color": "#e2e8f0", 
      "size": 16 
    },
    "borderWidth": 2,
    "borderColor": "#1e293b",
    "shadow": {
      "enabled": true,
      "color": "rgba(0,0,0,0.3)",
      "size": 10,
      "x": 5,
      "y": 5
    }
  },
  "edges": {
    "color": { "color": "#64748b" },
    "smooth": { "type": "dynamic" },
    "font": { "size": 12, "strokeWidth": 0 },
    "shadow": {
      "enabled": true,
      "color": "rgba(0,0,0,0.2)"
    }
  },
  "physics": {
    "barnesHut": { 
      "gravitationalConstant": -12000, 
      "centralGravity": 0.1, 
      "springLength": 180, 
      "springConstant": 0.04 
    },
    "stabilization": true
  },
  "interaction": {
    "hover": true,
    "hoverConnectedEdges": true,
    "selectConnectedEdges": false
  }
}
""")
    html = net.generate_html(notebook=False)

    legend = f"""
      <div class="title">How to read</div>
      <div class="row"><span class="chip" style="background:#6366f1"></span> Center = {central_label}</div>
      <div class="row"><span class="chip" style="background:#22c55e"></span> GitHub</div>
      <div class="row"><span class="chip" style="background:#a855f7"></span> Instagram</div>
      <div class="row"><span class="chip" style="background:#f97316"></span> Reddit</div>
      <div class="row"><span class="chip" style="background:#60a5fa"></span> Twitter</div>
      <hr/>
      <div class="row">Nodes = accounts. Center node is the searched identity.</div>
      <div class="row">Edges = connections from identity to platform profiles.</div>
      <div class="row">Hover a node for: display name, bio, followers, and profile link.</div>
    """
    return _inject_overlay(html, legend)

def build_comparison_html(
    user_a: str,
    user_b: str,
    profiles_a: Dict[str, Profile],
    profiles_b: Dict[str, Profile],
    platform_scores: Dict[str, float],
    friendly: bool = True
) -> str:
    G = nx.Graph()

    # Use internal ids but show the real usernames as labels
    root_a = "__memap_root_a__"
    root_b = "__memap_root_b__"

    G.add_node(root_a, color="#6366f1", shape="dot", size=25, title=user_a, label=user_a, x=-250, y=0, fixed=True)
    G.add_node(root_b, color="#8b5cf6", shape="dot", size=25, title=user_b, label=user_b, x=250, y=0, fixed=True)

    # Side clusters with slight vertical stacking
    y_a = -120
    for platform, prof in profiles_a.items():
        node_id = f"A:{platform}"
        bio_text = prof.bio[:30] + "..." if prof.bio and len(prof.bio) > 30 else prof.bio or "No bio"
        title = f"User A - {platform.title()}\nUsername: {prof.username}\nBio: {bio_text}"
        
        G.add_node(node_id, 
                  color=_PLATFORM_COLORS.get(platform, "#94a3b8"),
                  size=18,
                  title=title,
                  x=-380,
                  y=y_a,
                  fixed=False,
                  label=f"A: {platform.title()}\n@{prof.username}",
                  shape="dot")
        G.add_edge(root_a, node_id, color="#64748b", width=2)
        y_a += 120

    y_b = -120
    for platform, prof in profiles_b.items():
        node_id = f"B:{platform}"
        bio_text = prof.bio[:30] + "..." if prof.bio and len(prof.bio) > 30 else prof.bio or "No bio"
        title = f"User B - {platform.title()}\nUsername: {prof.username}\nBio: {bio_text}"
        
        G.add_node(node_id, 
                  color=_PLATFORM_COLORS.get(platform, "#94a3b8"),
                  size=18,
                  title=title,
                  x=380,
                  y=y_b,
                  fixed=False,
                  label=f"B: {platform.title()}\n@{prof.username}",
                  shape="dot")
        G.add_edge(root_b, node_id, color="#64748b", width=2)
        y_b += 120

    # Cross links with labels and thickness by strength
    for platform, score in platform_scores.items():
        if platform in profiles_a and platform in profiles_b:
            label = _edge_label(score, friendly)
            G.add_edge(
                f"A:{platform}",
                f"B:{platform}",
                color=_edge_color(score),
                width=max(2, 1 + (score * 6)),
                label=label,
                font={"size": 12, "align": "top"},
                title=f"{platform.capitalize()} similarity: {int(score*100)}%"
            )

    net = Network(height="700px", width="100%", bgcolor="#0f172a", font_color="#e2e8f0")
    net.from_nx(G)
    net.set_options("""
{
  "nodes": { 
    "font": { 
      "color": "#e2e8f0", 
      "size": 16 
    },
    "borderWidth": 2,
    "borderColor": "#1e293b",
    "shadow": {
      "enabled": true,
      "color": "rgba(0,0,0,0.3)",
      "size": 10,
      "x": 5,
      "y": 5
    }
  },
  "edges": {
    "smooth": { "type": "dynamic" },
    "font": { "size": 12, "align": "top", "strokeWidth": 0 },
    "shadow": {
      "enabled": true,
      "color": "rgba(0,0,0,0.2)"
    }
  },
  "physics": {
    "enabled": true,
    "barnesHut": { 
      "gravitationalConstant": -8000, 
      "centralGravity": 0.1, 
      "springLength": 180, 
      "springConstant": 0.04 
    },
    "stabilization": true
  },
  "interaction": {
    "hover": true,
    "hoverConnectedEdges": true,
    "selectConnectedEdges": false
  }
}
""")
    html = net.generate_html(notebook=False)

    legend = f"""
      <div class="title">How to read</div>
      <div class="row"><span class="chip" style="background:#6366f1"></span> Left cluster = {user_a}</div>
      <div class="row"><span class="chip" style="background:#8b5cf6"></span> Right cluster = {user_b}</div>
      <hr/>
      <div class="row"><span class="chip edge" style="background:#22c55e"></span> Green line = Strong match (≥80%)</div>
      <div class="row"><span class="chip edge" style="background:#f59e0b"></span> Yellow line = Medium (60–79%)</div>
      <div class="row"><span class="chip edge" style="background:#ef4444"></span> Red line = Weak (&lt;60%)</div>
      <div class="row">Edge label shows similarity % and plain-language strength.</div>
    """
    return _inject_overlay(html, legend)