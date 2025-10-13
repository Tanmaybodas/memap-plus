import os
from typing import List, Dict

def web_mentions(query: str, num_results: int = 5) -> List[Dict]:
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    if not api_key or not cse_id:
        return []
    try:
        from googleapiclient.discovery import build  # lazy import
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cse_id, num=num_results).execute()
        items = res.get("items", [])
        results: List[Dict] = []
        for it in items:
            results.append({
                "title": it.get("title"),
                "link": it.get("link"),
                "snippet": it.get("snippet"),
            })
        return results
    except Exception:
        return []
