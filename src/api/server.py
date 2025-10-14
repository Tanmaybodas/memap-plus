from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from src.models.types import Profile
from src.data.github_client import fetch_github_user
from src.data.reddit_client import fetch_reddit_user
from src.data.instagram_client import fetch_instagram_user
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
    return profiles


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/footprint", response_model=GraphResponse)
def footprint(username: str = Query(..., min_length=1)):
    username = username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="username is required")

    profiles = collect_profiles(username)

    nodes: List[Node] = [Node(id=f"user:{username}", label=username, group="user")]
    edges: List[Edge] = []

    for platform, p in profiles.items():
        pid = f"{platform}:{p.username}"
        nodes.append(
            Node(
                id=pid,
                label=f"{platform}:{p.username}",
                group=platform,
                meta={
                    "display_name": p.display_name,
                    "bio": p.bio,
                    "followers": p.followers,
                    "url": p.profile_url,
                    "avatar": p.avatar_url,
                },
            )
        )
        edges.append(Edge(source=f"user:{username}", target=pid))

    return GraphResponse(nodes=nodes, edges=edges)


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


