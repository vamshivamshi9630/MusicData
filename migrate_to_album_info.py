import ast
import json
from pathlib import Path
from generator.config import BASE_PATH, LEGACY_METADATA_FILE
from generator.utils import normalize

def get_legacy_metadata():
    if not LEGACY_METADATA_FILE.exists():
        return {}
    try:
        content = LEGACY_METADATA_FILE.read_text(encoding='utf-8')
        tree = ast.parse(content)
        metadata = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if getattr(target, 'id', '') == 'ALBUM_METADATA':
                        metadata = ast.literal_eval(node.value)
                        break
        
        normalized_meta = {}
        for k, v in metadata.items():
            dir_name = v.get("musicDirector", "Unknown").strip()
            year_val = v.get("year", "Unknown")
            try:
                year_num = int(year_val)
            except (ValueError, TypeError):
                year_num = 2026

            normalized_meta[normalize(k)] = {
                "musicDirector": dir_name,
                "year": year_num
            }
        return normalized_meta
    except Exception as e:
        print(f"Warning: Could not parse legacy file {LEGACY_METADATA_FILE}: {e}")
        return {}

def migrate_all_albums():
    legacy_meta = get_legacy_metadata()
    created_count = 0
    existing_count = 0

    album_dirs = sorted(
        [d for d in BASE_PATH.iterdir() if d.is_dir() and not d.name.startswith('.') and d.name not in ['generator', 'metadata', '.git']],
        key=lambda d: d.name.lower()
    )

    for album_dir in album_dirs:
        info_file = album_dir / "album_info.json"
        if info_file.exists():
            existing_count += 1
            continue

        album_name = album_dir.name
        norm_key = normalize(album_name)

        meta = legacy_meta.get(norm_key, {"musicDirector": "Unknown", "year": 2026})
        
        album_info_data = {
            "album": album_name,
            "year": meta["year"],
            "musicDirector": meta["musicDirector"],
            "genre": "Tollywood Soundtrack",
            "language": "Telugu",
            "country": "India",
            "releaseDate": f"{meta['year']}-01-01",
            "director": "Unknown",
            "producer": "Unknown",
            "banner": "Unknown"
        }

        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(album_info_data, f, indent=4, ensure_ascii=False)
        
        created_count += 1

    print(f"Migration finished: {created_count} album_info.json files created, {existing_count} already existed.")

if __name__ == "__main__":
    migrate_all_albums()
