import os
from typing import Optional
from src.models.types import Profile

def fetch_instagram_user(username: str) -> Optional[Profile]:
    if not username:
        return None
    try:
        import instaloader  # lazy import
    except Exception:
        return None

    try:
        L = instaloader.Instaloader(download_pictures=False, download_videos=False, download_video_thumbnails=False,
                                     download_geotags=False, download_comments=False, save_metadata=False, compress_json=False)
        ig_user = os.getenv("IG_USERNAME")
        ig_pass = os.getenv("IG_PASSWORD")
        if ig_user and ig_pass:
            try:
                L.login(ig_user, ig_pass)
            except Exception:
                pass  # proceed without login
        ctx = L.context
        profile = instaloader.Profile.from_username(ctx, username)
        return Profile(
            platform="instagram",
            username=profile.username,
            display_name=profile.full_name or profile.username,
            bio=profile.biography or None,
            followers=profile.followers,
            profile_url=f"https://instagram.com/{profile.username}",
            avatar_url=str(profile.profile_pic_url) if getattr(profile, "profile_pic_url", None) else None,
        )
    except Exception:
        return None
