"""YouTube channel RSS feed monitor for detecting new uploads."""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import httpx

YOUTUBE_RSS_BASE = "https://www.youtube.com/feeds/videos.xml"

def get_latest_youtube_uploads(channel_id: str) -> List[Dict[str, Any]]:
    """Parse YouTube channel RSS feed to extract newly uploaded videos."""
    url = f"{YOUTUBE_RSS_BASE}?channel_id={channel_id.strip()}"
    with httpx.Client(timeout=10.0) as client:
        res = client.get(url)
        if res.status_code != 200:
            return []

    root = ET.fromstring(res.text)
    # Atom XML namespace
    ns = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}

    videos: List[Dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns):
        vid_id_elem = entry.find("yt:videoId", ns)
        title_elem = entry.find("atom:title", ns)
        published_elem = entry.find("atom:published", ns)

        if vid_id_elem is not None and vid_id_elem.text:
            vid_id = vid_id_elem.text
            videos.append({
                "video_id": vid_id,
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "title": title_elem.text if title_elem is not None else "",
                "published_at": published_elem.text if published_elem is not None else "",
            })

    return videos
