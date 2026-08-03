import json
from pathlib import Path
from typing import List, Tuple
from generator.config import INDEXES_DIR
from generator.models import Album
from generator.utils import get_album_partition, compute_sha256_text

def write_albums_index(albums: List[Album]) -> Tuple[str, str]:
    """Write metadata/indexes/albums.json summary list. Returns (relative_path, file_hash)."""
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)
    file_path = INDEXES_DIR / "albums.json"

    album_items = [
        {
            "id": album.id,
            "name": album.name,
            "artist": album.musicDirector,
            "year": album.year,
            "genre": album.genre,
            "language": album.language,
            "image": album.image,
            "songCount": len(album.songs),
            "partition": get_album_partition(album.name)
        }
        for album in albums
    ]

    json_text = json.dumps(album_items, indent=2, ensure_ascii=False)
    file_path.write_text(json_text, encoding="utf-8")

    file_hash = compute_sha256_text(json_text)
    return "indexes/albums.json", file_hash
