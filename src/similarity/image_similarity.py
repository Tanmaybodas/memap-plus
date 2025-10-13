import os
from typing import Optional
from io import BytesIO

import requests
from PIL import Image

def image_similarity(url1: Optional[str], url2: Optional[str]) -> Optional[float]:
    if not url1 or not url2:
        return None
    try:
        import imagehash  # lazy import
    except Exception:
        return None

    try:
        r1 = requests.get(url1, timeout=20)
        r2 = requests.get(url2, timeout=20)
        r1.raise_for_status(); r2.raise_for_status()
        img1 = Image.open(BytesIO(r1.content)).convert('RGB')
        img2 = Image.open(BytesIO(r2.content)).convert('RGB')
        h1 = imagehash.phash(img1)
        h2 = imagehash.phash(img2)
        dist = h1 - h2  # Hamming distance
        bits = 64.0  # phash default 8x8
        return max(0.0, min(1.0, 1.0 - (dist / bits)))
    except Exception:
        return None
