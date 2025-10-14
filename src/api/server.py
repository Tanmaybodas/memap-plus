from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from src.models.types import Profile
from src.data.github_client import fetch_github_user
from src.data.reddit_client import fetch_reddit_user
from src.data.instagram_client import fetch_instagram_user
from src.data.twitter_client import fetch_twitter_user
from src.similarity.text_similarity import compare_usernames, bio_similarity


class Node(BaseModel):
    id: str
    label: str
    group: Optional[str] = None
    meta: Optional[Dict] = None


class Edge(BaseModel):
    source: str
    target: str
    weight: Optional[float] = None
    label: Optional[str] = None


class GraphResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


app = FastAPI(title="MeMap+ API", version="1.0.0")


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
    tw = fetch_twitter_user(username)
    if tw:
        profiles["twitter"] = tw
    return profiles


def _handle_candidates_from_name(full_name: str, max_candidates: int = 30) -> List[str]:
    name = full_name.strip()
    if not name:
        return []
    parts = [p for p in name.lower().replace("\t", " ").split(" ") if p]
    joined = "".join(parts)
    dashed = "-".join(parts)
    dotted = ".".join(parts)
    underscored = "_".join(parts)
    initials = "".join(p[0] for p in parts)
    variants = [
        joined,
        dashed,
        dotted,
        underscored,
        joined + "official",
        joined + "_official",
        joined + "1",
        initials + parts[-1] if parts else joined,
        parts[-1] + initials if parts else joined,
    ]
    # Deduplicate and cap
    seen = set()
    out: List[str] = []
    for v in variants:
        v = v.replace("..", ".").replace("__", "_").strip("._")
        if v and v not in seen:
            seen.add(v)
            out.append(v)
        if len(out) >= max_candidates:
            break
    return out

def guess_username_from_name(full_name: str) -> Optional[str]:
    for cand in _handle_candidates_from_name(full_name, max_candidates=10):
        gh = fetch_github_user(cand)
        if gh:
            return cand
    return None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/footprint", response_model=GraphResponse)
def footprint(
    username: Optional[str] = Query(None, min_length=1),
    full_name: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=25),
    per_platform: int = Query(5, ge=1, le=10),
):
    nodes: List[Node] = []
    edges: List[Edge] = []

    center_label = (username or full_name or "user").strip()
    nodes.append(Node(id=f"user:{center_label}", label=center_label, group="user"))

    profiles_map: Dict[str, Profile] = {}

    def add_profile(p: Profile):
        pid = f"{p.platform}:{p.username}"
        if pid in {n.id for n in nodes}:
            return
        nodes.append(
            Node(
                id=pid,
                label=f"{p.platform}:{p.username}",
                group=p.platform,
                meta={
                    "display_name": p.display_name,
                    "bio": p.bio,
                    "followers": p.followers,
                    "url": p.profile_url,
                    "avatar": p.avatar_url,
                },
            )
        )
        edges.append(Edge(source=f"user:{center_label}", target=pid))

    if username:
        profiles_map = collect_profiles(username.strip())
        for p in profiles_map.values():
            add_profile(p)
    elif full_name:
        # Expand candidates and gather across platforms until limit is reached
        for cand in _handle_candidates_from_name(full_name, max_candidates=50):
            if len([n for n in nodes if n.group and n.group != "user"]) >= limit:
                break
            for fetcher in (fetch_instagram_user, fetch_twitter_user, fetch_github_user, fetch_reddit_user):
                p = fetcher(cand)
                if p:
                    add_profile(p)
                    if len([n for n in nodes if n.group and n.group != "user"]) >= limit:
                        break
    else:
        raise HTTPException(status_code=400, detail="username or full_name is required")

    # Enforce per-platform cap
    platform_counts: Dict[str, int] = {}
    filtered_nodes: List[Node] = []
    keep_ids = set()
    for n in nodes:
        if n.group is None or n.group == "user":
            filtered_nodes.append(n)
            keep_ids.add(n.id)
            continue
        c = platform_counts.get(n.group, 0)
        if c < per_platform:
            filtered_nodes.append(n)
            keep_ids.add(n.id)
            platform_counts[n.group] = c + 1
    filtered_edges = [e for e in edges if e.source in keep_ids and e.target in keep_ids]

    return GraphResponse(nodes=filtered_nodes, edges=filtered_edges)


@app.get("/compare", response_model=GraphResponse)
def compare(user_a: str = Query(..., min_length=1), user_b: str = Query(..., min_length=1)):
    ua = user_a.strip()
    ub = user_b.strip()
    if not ua or not ub:
        raise HTTPException(status_code=400, detail="user_a and user_b are required")

    profiles_a = collect_profiles(ua)
    profiles_b = collect_profiles(ub)

    nodes: List[Node] = [
        Node(id="user:A", label=ua, group="user"),
        Node(id="user:B", label=ub, group="user"),
    ]
    edges: List[Edge] = []

    # per-platform nodes
    platforms = set(list(profiles_a.keys()) + list(profiles_b.keys()))
    for platform in platforms:
        pa = profiles_a.get(platform)
        pb = profiles_b.get(platform)
        if pa:
            nid = f"A:{platform}"
            nodes.append(
                Node(
                    id=nid,
                    label=f"A:{platform}:{pa.username}",
                    group=platform,
                    meta={"bio": pa.bio, "url": pa.profile_url, "avatar": pa.avatar_url},
                )
            )
            edges.append(Edge(source="user:A", target=nid))
        if pb:
            nid = f"B:{platform}"
            nodes.append(
                Node(
                    id=nid,
                    label=f"B:{platform}:{pb.username}",
                    group=platform,
                    meta={"bio": pb.bio, "url": pb.profile_url, "avatar": pb.avatar_url},
                )
            )
            edges.append(Edge(source="user:B", target=nid))

        # similarity edge if both exist
        if pa and pb:
            u_sim = compare_usernames(pa.username, pb.username)
            b_sim = bio_similarity(pa.bio, pb.bio)
            score = 0.5 * u_sim + 0.5 * b_sim
            edges.append(
                Edge(
                    source=f"A:{platform}",
                    target=f"B:{platform}",
                    weight=score,
                    label=f"{int(score*100)}%",
                )
            )

    return GraphResponse(nodes=nodes, edges=edges)


