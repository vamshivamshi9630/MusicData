import json
from datetime import datetime
from typing import Dict
from generator.config import METADATA_DIR, SCHEMA_VERSION, GENERATOR_VERSION
from generator.hash_manager import load_existing_manifest

MANIFEST_FILE = METADATA_DIR / "manifest.json"

def write_manifest(
    index_hashes: Dict[str, str],
    album_hashes: Dict[str, Dict[str, str]]
) -> str:
    """Generate and save metadata/manifest.json."""
    old_manifest = load_existing_manifest()
    old_manifest_version = old_manifest.get("manifestVersion", 0)

    old_indexes = old_manifest.get("indexes", {})
    old_albums = old_manifest.get("albums", {})

    indexes_manifest = {}
    indexes_changed = False

    for idx_name, current_hash in index_hashes.items():
        old_info = old_indexes.get(idx_name, {})
        old_hash = old_info.get("hash", "")
        old_ver = old_info.get("version", 1)

        if old_hash != current_hash:
            ver = old_ver + 1 if old_hash else 1
            indexes_changed = True
        else:
            ver = old_ver

        indexes_manifest[idx_name] = {
            "version": ver,
            "hash": current_hash
        }

    albums_manifest = {}
    albums_changed = False

    for album_id, album_data in album_hashes.items():
        current_hash = album_data["hash"]
        old_info = old_albums.get(album_id, {})
        old_hash = old_info.get("hash", "")
        old_ver = old_info.get("version", 1)

        if old_hash != current_hash:
            ver = old_ver + 1 if old_hash else 1
            albums_changed = True
        else:
            ver = old_ver

        albums_manifest[album_id] = {
            "name": album_data["name"],
            "partition": album_data["partition"],
            "version": ver,
            "hash": current_hash
        }

    manifest_version = old_manifest_version + 1 if (indexes_changed or albums_changed or old_manifest_version == 0) else old_manifest_version

    manifest_data = {
        "manifestVersion": manifest_version,
        "schemaVersion": SCHEMA_VERSION,
        "generatorVersion": GENERATOR_VERSION,
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "compression": "none",
        "indexes": indexes_manifest,
        "albums": albums_manifest
    }

    json_text = json.dumps(manifest_data, indent=2, ensure_ascii=False)
    MANIFEST_FILE.write_text(json_text, encoding="utf-8")

    return json_text
