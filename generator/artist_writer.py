import json
from pathlib import Path
from typing import List, Tuple, Dict
from generator.config import INDEXES_DIR
from generator.models import Album
from generator.utils import get_stable_id, compute_sha256_text

def write_artists_index(albums: List[Album]) -> Tuple[str, str]:
    """Write metadata/indexes/artists.json summary list. Returns (relative_path, file_hash)."""
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)
    file_path = INDEXES_DIR / "artists.json"

    artists_map: Dict[str, Dict] = {}

    for album in albums:
        artist_name = album.musicDirector.strip()
        if not artist_name:
            artist_name = "Unknown"
        artist_id = get_stable_id(artist_name)

        if artist_id not in artists_map:
            artists_map[artist_id] = {
                "id": artist_id,
                "name": artist_name,
                "songCount": 0,
                "albumCount": 0
            }

        artists_map[artist_id]["albumCount"] += 1
        artists_map[artist_id]["songCount"] += len(album.songs)

    artist_items = sorted(list(artists_map.values()), key=lambda x: x["name"].lower())

    json_text = json.dumps(artist_items, indent=2, ensure_ascii=False)
    file_path.write_text(json_text, encoding="utf-8")

    file_hash = compute_sha256_text(json_text)
    return "indexes/artists.json", file_hash
