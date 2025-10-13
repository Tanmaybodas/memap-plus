import os
from typing import Optional
import requests
from src.models.types import Profile

GITHUB_API = "https://api.github.com"

def fetch_github_user(username: str) -> Optional[Profile]:
    if not username:
        return None
    url = f"{GITHUB_API}/users/{username}"
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        data = r.json()
        return Profile(
            platform="github",
            username=data.get("login") or username,
            display_name=data.get("name"),
            bio=data.get("bio"),
            followers=data.get("followers"),
            location=data.get("location"),
            profile_url=data.get("html_url"),
            avatar_url=data.get("avatar_url"),
            extra={"public_repos": data.get("public_repos")},
        )
    except Exception:
        return None
