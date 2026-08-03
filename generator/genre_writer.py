import json
from pathlib import Path
from typing import List, Tuple, Dict
from generator.config import INDEXES_DIR
from generator.models import Album
from generator.utils import get_stable_id, compute_sha256_text

def write_genres_index(albums: List[Album]) -> Tuple[str, str]:
    """Write metadata/indexes/genres.json summary list. Returns (relative_path, file_hash)."""
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)
    file_path = INDEXES_DIR / "genres.json"

    genres_map: Dict[str, Dict] = {}

    for album in albums:
        genre_name = album.genre.strip() or "Soundtrack"
        genre_id = get_stable_id(genre_name)

        if genre_id not in genres_map:
            genres_map[genre_id] = {
                "id": genre_id,
                "name": genre_name,
                "songCount": 0,
                "albumCount": 0
            }

        genres_map[genre_id]["albumCount"] += 1
        genres_map[genre_id]["songCount"] += len(album.songs)

    genre_items = sorted(list(genres_map.values()), key=lambda x: x["name"].lower())

    json_text = json.dumps(genre_items, indent=2, ensure_ascii=False)
    file_path.write_text(json_text, encoding="utf-8")

    file_hash = compute_sha256_text(json_text)
    return "indexes/genres.json", file_hash
