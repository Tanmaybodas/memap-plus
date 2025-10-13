from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Profile:
    platform: str
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    followers: Optional[int] = None
    location: Optional[str] = None
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
