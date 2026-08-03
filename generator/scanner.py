import json
from pathlib import Path
from typing import List, Dict, Optional
from generator.config import BASE_PATH, AUDIO_EXTENSIONS, IMAGE_EXTENSIONS

def find_album_image(album_path: Path, album_name: str) -> str:
    """Locate cover image in album directory or fallback to empty string."""
    possible_names = [
        f"{album_name}.png",
        f"{album_name}.jpg",
        f"{album_name}.jpeg",
        "folder.png",
        "folder.jpg",
        "cover.png",
        "cover.jpg",
        "cover.jpeg"
    ]
    for name in possible_names:
        p = album_path / name
        if p.exists() and p.stat().st_size > 0:
            return name

    # Check any image with supported extension
    for ext in IMAGE_EXTENSIONS:
        for f in album_path.glob(f"*{ext}"):
            if f.stat().st_size > 0:
                return f.name

    return ""

def scan_album_directory(album_dir: Path) -> Optional[Dict]:
    """Scan a single album directory and return raw album structure."""
    info_file = album_dir / "album_info.json"
    if not info_file.exists():
        return None

    mp3_files = sorted(
        [f for f in album_dir.glob("*.mp3") if f.stat().st_size > 0],
        key=lambda f: f.name.lower()
    )

    # Skip folders without MP3 files (e.g. image-only asset folders)
    if not mp3_files:
        return None

    try:
        with open(info_file, "r", encoding="utf-8") as f:
            album_info = json.load(f)
    except Exception as e:
        print(f"Error reading {info_file}: {e}")
        return None

    album_name = album_dir.name
    image_name = find_album_image(album_dir, album_name)

    return {
        "dir_path": album_dir,
        "album_name": album_name,
        "album_info": album_info,
        "image_name": image_name,
        "mp3_files": mp3_files
    }

def scan_all_albums() -> List[Dict]:
    """Scan root MusicData directory for all valid album folders."""
    ignored = {".git", "generator", "metadata", "tmp", "__pycache__", ".idea", "MusicDirectorImages", "New_Icons"}
    album_dirs = sorted(
        [d for d in BASE_PATH.iterdir() if d.is_dir() and not d.name.startswith(".") and d.name not in ignored],
        key=lambda d: d.name.lower()
    )

    scanned_albums = []
    for d in album_dirs:
        data = scan_album_directory(d)
        if data:
            scanned_albums.append(data)

    return scanned_albums
