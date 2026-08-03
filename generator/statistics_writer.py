import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from generator.config import METADATA_DIR
from generator.models import Album
from generator.utils import compute_sha256_text

def write_statistics(albums: List[Album]) -> Tuple[str, str]:
    """Write metadata/statistics.json. Returns (relative_path, file_hash)."""
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    file_path = METADATA_DIR / "statistics.json"

    total_albums = len(albums)
    total_songs = sum(len(a.songs) for a in albums)
    artists_set = {a.musicDirector.strip() for a in albums if a.musicDirector.strip()}
    genres_set = {a.genre.strip() for a in albums if a.genre.strip()}
    languages_set = {a.language.strip() for a in albums if a.language.strip()}

    total_duration_sec = sum(
        song.durationSeconds for album in albums for song in album.songs
    )

    hours = total_duration_sec // 3600
    minutes = (total_duration_sec % 3600) // 60
    duration_fmt = f"{hours} Hours {minutes} Mins" if hours > 0 else f"{minutes} Mins"

    stats_dict = {
        "totalSongs": total_songs,
        "totalAlbums": total_albums,
        "totalArtists": len(artists_set),
        "totalGenres": len(genres_set),
        "totalLanguages": len(languages_set),
        "totalDurationFormatted": duration_fmt,
        "totalDurationSeconds": total_duration_sec,
        "generatedAt": datetime.utcnow().isoformat() + "Z"
    }

    json_text = json.dumps(stats_dict, indent=2, ensure_ascii=False)
    file_path.write_text(json_text, encoding="utf-8")

    file_hash = compute_sha256_text(json_text)
    return "statistics.json", file_hash
