import json
from pathlib import Path
from typing import Dict, List
from generator.config import METADATA_DIR

MANIFEST_FILE = METADATA_DIR / "manifest.json"

def load_existing_manifest() -> Dict:
    """Load existing manifest.json if present to manage version incrementing."""
    if not MANIFEST_FILE.exists():
        return {}
    try:
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def get_next_version(existing_manifest: Dict, key_path: List[str], current_hash: str) -> int:
    """Helper to retrieve version, incrementing if hash has changed."""
    target = existing_manifest
    for k in key_path:
        if not isinstance(target, dict) or k not in target:
            return 1
        target = target[k]

    if isinstance(target, dict):
        old_hash = target.get("hash", "")
        old_ver = target.get("version", 1)
        if old_hash == current_hash:
            return old_ver
        return old_ver + 1

    return 1
