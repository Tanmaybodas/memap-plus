import os
from typing import Optional
import requests
from src.models.types import Profile

TWITTER_API = "https://api.twitter.com/2"


def fetch_twitter_user(query: str) -> Optional[Profile]:
    """Fetch a Twitter user by username or full name (best-effort).

    Requires TWITTER_BEARER_TOKEN in env. Uses recent Users lookup endpoints.
    If `query` starts with @, treat as username; otherwise tries by username first,
    then falls back to a name search.
    """
    token = os.getenv("TWITTER_BEARER_TOKEN")
    if not token:
        return None

    headers = {"Authorization": f"Bearer {token}"}

    def get_by_username(username: str) -> Optional[Profile]:
        url = f"{TWITTER_API}/users/by/username/{username}"
        params = {"user.fields": "name,username,description,public_metrics,profile_image_url"}
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json().get("data")
        if not data:
            return None
        metrics = (data.get("public_metrics") or {})
        return Profile(
            platform="twitter",
            username=data.get("username"),
            display_name=data.get("name"),
            bio=data.get("description"),
            followers=metrics.get("followers_count"),
            profile_url=f"https://twitter.com/{data.get('username')}",
            avatar_url=data.get("profile_image_url"),
        )

    q = query.strip().lstrip("@")
    # Try as username first
    prof = get_by_username(q)
    if prof:
        return prof

    # Fallback: search users by query (name). Note: Elevated access may be required.
    search_url = f"{TWITTER_API}/users/by"
    params = {"usernames": q.replace(" ", ""), "user.fields": "name,username,description,public_metrics,profile_image_url"}
    try:
        r = requests.get(search_url, headers=headers, params=params, timeout=15)
        if r.status_code == 200:
            for u in (r.json().get("data") or []):
                metrics = (u.get("public_metrics") or {})
                return Profile(
                    platform="twitter",
                    username=u.get("username"),
                    display_name=u.get("name"),
                    bio=u.get("description"),
                    followers=metrics.get("followers_count"),
                    profile_url=f"https://twitter.com/{u.get('username')}",
                    avatar_url=u.get("profile_image_url"),
                )
    except Exception:
        pass

    return None


