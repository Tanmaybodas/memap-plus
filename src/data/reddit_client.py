import os
from typing import Optional

from src.models.types import Profile

def _build_reddit():
    try:
        import praw  # lazy import
    except Exception:
        return None

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT") or "MeMapPlus/0.1 (by u/unknown)"
    if not client_id or not client_secret:
        return None
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        return reddit
    except Exception:
        return None

def fetch_reddit_user(username: str) -> Optional[Profile]:
    reddit = _build_reddit()
    if not reddit or not username:
        return None
    try:
        redditor = reddit.redditor(username)
        # Accessing attributes may raise if suspended or not found
        _ = redditor.id  # forces a fetch
        display_name = f"u/{username}"
        bio = None
        try:
            bio = getattr(redditor, "subreddit", None).public_description if getattr(redditor, "subreddit", None) else None
        except Exception:
            bio = None
        profile_url = f"https://www.reddit.com/user/{username}"
        avatar_url = None
        try:
            avatar_url = getattr(redditor, "icon_img", None)
        except Exception:
            avatar_url = None
        followers = None
        try:
            followers = getattr(redditor, "subreddit", None).subscribers if getattr(redditor, "subreddit", None) else None
        except Exception:
            followers = None
        return Profile(
            platform="reddit",
            username=username,
            display_name=display_name,
            bio=bio,
            followers=followers,
            profile_url=profile_url,
            avatar_url=avatar_url,
        )
    except Exception:
        return None
