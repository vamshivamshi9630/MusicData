import json
from pathlib import Path
from typing import List, Tuple, Dict
from generator.config import INDEXES_DIR
from generator.models import Album
from generator.utils import get_stable_id, compute_sha256_text

def write_languages_index(albums: List[Album]) -> Tuple[str, str]:
    """Write metadata/indexes/languages.json summary list. Returns (relative_path, file_hash)."""
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)
    file_path = INDEXES_DIR / "languages.json"

    lang_map: Dict[str, Dict] = {}

    for album in albums:
        lang_name = album.language.strip() or "Telugu"
        lang_id = get_stable_id(lang_name)

        if lang_id not in lang_map:
            lang_map[lang_id] = {
                "id": lang_id,
                "name": lang_name,
                "songCount": 0,
                "albumCount": 0
            }

        lang_map[lang_id]["albumCount"] += 1
        lang_map[lang_id]["songCount"] += len(album.songs)

    lang_items = sorted(list(lang_map.values()), key=lambda x: x["name"].lower())

    json_text = json.dumps(lang_items, indent=2, ensure_ascii=False)
    file_path.write_text(json_text, encoding="utf-8")

    file_hash = compute_sha256_text(json_text)
    return "indexes/languages.json", file_hash
