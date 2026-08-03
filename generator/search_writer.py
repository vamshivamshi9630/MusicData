import json
from pathlib import Path
from typing import List, Tuple
from generator.config import INDEXES_DIR
from generator.models import Album
from generator.utils import get_stable_id, normalize, compute_sha256_text

def write_search_index(albums: List[Album]) -> Tuple[str, str]:
    """Write metadata/indexes/search_index.json. Returns (relative_path, file_hash)."""
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)
    file_path = INDEXES_DIR / "search_index.json"

    search_items = []
    for album in albums:
        artist_id = get_stable_id(album.musicDirector)
        language_id = get_stable_id(album.language)

        for song in album.songs:
            search_items.append({
                "id": song.id,
                "title": song.title,
                "normalizedTitle": song.normalizedTitle,
                "albumId": album.id,
                "artistId": artist_id,
                "languageId": language_id
            })

    json_text = json.dumps(search_items, separators=(',', ':'), ensure_ascii=False)
    file_path.write_text(json_text, encoding="utf-8")

    file_hash = compute_sha256_text(json_text)
    return "indexes/search_index.json", file_hash
