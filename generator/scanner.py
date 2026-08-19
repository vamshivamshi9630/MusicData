import json
import io
from pathlib import Path
from typing import List, Dict, Optional
from generator.config import BASE_PATH, AUDIO_EXTENSIONS, IMAGE_EXTENSIONS

class DummyMp3Path(Path):
    _flavour = Path()._flavour
    def __new__(cls, filename: str, album_dir_ref: Path):
        path_obj = super().__new__(cls, album_dir_ref / filename)
        path_obj._custom_filename = filename
        return path_obj

    @property
    def name(self) -> str:
        return getattr(self, "_custom_filename", super().name)

    def stat(self, *, follow_symlinks=True):
        class DummyStat:
            st_size = 1000
        return DummyStat()

    def exists(self, *, follow_symlinks=True):
        return True

    def read_bytes(self):
        return b""

    def open(self, *args, **kwargs):
        return io.BytesIO(b"")

def find_album_image(album_path: Path, album_name: str) -> str:
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

    for ext in IMAGE_EXTENSIONS:
        for f in album_path.glob(f"*{ext}"):
            if f.stat().st_size > 0:
                return f.name

    return ""

def scan_album_directory(album_dir: Path) -> Optional[Dict]:
    info_file = album_dir / "album_info.json"
    if not info_file.exists():
        return None

    mp3_files = sorted(
        [f for f in album_dir.glob("*.mp3") if f.stat().st_size > 0],
        key=lambda f: f.name.lower()
    )

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
    ignored = {".git", "generator", "metadata", "tmp", "__pycache__", ".idea", "MusicDirectorImages", "New_Icons"}
    disk_dirs = sorted(
        [d for d in BASE_PATH.iterdir() if d.is_dir() and not d.name.startswith(".") and d.name not in ignored],
        key=lambda d: d.name.lower()
    )

    scanned_albums = []
    scanned_names = set()

    for d in disk_dirs:
        data = scan_album_directory(d)
        if data:
            scanned_albums.append(data)
            scanned_names.add(d.name.lower())

    metadata_albums_dir = BASE_PATH / "metadata" / "albums"
    if metadata_albums_dir.exists():
        for partition_dir in metadata_albums_dir.iterdir():
            if partition_dir.is_dir():
                for json_file in partition_dir.glob("*.json"):
                    album_stem = json_file.stem
                    if album_stem.lower() not in scanned_names:
                        try:
                            with open(json_file, "r", encoding="utf-8") as f:
                                cached_data = json.load(f)
                            alb = cached_data.get("album", {})
                            songs_list = cached_data.get("songs", [])
                            alb_name = alb.get("name", album_stem)
                            dummy_dir = BASE_PATH / alb_name
                            dummy_mp3s = [
                                DummyMp3Path(s.get("audio") or f"{s.get('title')}.mp3", dummy_dir)
                                for s in songs_list
                            ]
                            scanned_albums.append({
                                "dir_path": dummy_dir,
                                "album_name": alb_name,
                                "album_info": {
                                    "musicDirector": alb.get("musicDirector", "Unknown"),
                                    "year": alb.get("year", 2026),
                                    "genre": alb.get("genre", "Tollywood Soundtrack"),
                                    "language": alb.get("language", "Telugu")
                                },
                                "image_name": alb.get("image", f"{alb_name}.png"),
                                "mp3_files": dummy_mp3s
                            })
                            scanned_names.add(alb_name.lower())
                        except Exception:
                            pass

    return scanned_albums
