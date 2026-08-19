import json
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional
from generator.utils import get_stable_id, get_album_partition

class CacheStatus(Enum):
    HIT = "HIT"
    MISS = "MISS"
    INVALID = "INVALID"

class CacheError(Exception):
    pass

class CacheMissError(CacheError):
    pass

class CacheInvalidError(CacheError):
    pass

class StrictCloudSafetyViolation(CacheError):
    pass

@dataclass
class GeneratorTelemetry:
    historical_songs_processed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_invalid_records: int = 0
    newly_uploaded_songs: int = 0
    actual_mp3_files_opened: int = 0
    mutagen_reads_performed: int = 0

    def summary(self) -> Dict[str, int]:
        return {
            "historical_songs_processed": self.historical_songs_processed,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_invalid_records": self.cache_invalid_records,
            "newly_uploaded_songs": self.newly_uploaded_songs,
            "actual_mp3_files_opened": self.actual_mp3_files_opened,
            "mutagen_reads_performed": self.mutagen_reads_performed
        }

@dataclass
class CacheResult:
    status: CacheStatus
    audio_info: Optional[Dict] = None
    id3_tags: Optional[Tuple[List[str], str]] = None
    reason: str = ""

def load_album_cache(metadata_dir: Path, album_name: str) -> Optional[Dict]:
    """Load cached album JSON from metadata/albums/{partition}/{albumName}.json."""
    partition = get_album_partition(album_name)
    cache_file = metadata_dir / "albums" / partition / f"{album_name}.json"
    if not cache_file.exists():
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def read_song_from_cache(album_cache: Optional[Dict], album_name: str, mp3_file: Path) -> CacheResult:
    """Validate and extract audio & ID3 specs from cached album JSON for a historical song."""
    if not album_cache:
        return CacheResult(status=CacheStatus.MISS, reason=f"No album cache found for album '{album_name}'.")

    album_data = album_cache.get("album", {})
    if album_data.get("name") != album_name:
        return CacheResult(status=CacheStatus.INVALID, reason=f"Album cache name '{album_data.get('name')}' mismatch for '{album_name}'.")

    songs_data = album_cache.get("songs", [])
    expected_song_id = get_stable_id(f"{album_name}{mp3_file.name}")

    matched_song = None
    for song in songs_data:
        if song.get("audio") == mp3_file.name or song.get("id") == expected_song_id:
            matched_song = song
            break

    if not matched_song:
        return CacheResult(status=CacheStatus.MISS, reason=f"Song '{mp3_file.name}' not found in album cache.")

    # Validation Checks
    # 1. ID Mismatch Check
    if matched_song.get("id") != expected_song_id:
        return CacheResult(
            status=CacheStatus.INVALID,
            reason=f"Song ID mismatch for '{mp3_file.name}'. Expected '{expected_song_id}', found '{matched_song.get('id')}'."
        )

    # 2. Audio Filename Check
    if matched_song.get("audio") != mp3_file.name:
        return CacheResult(status=CacheStatus.INVALID, reason=f"Audio filename mismatch for '{mp3_file.name}'.")

    # 3. Audio Metadata Completeness Check
    required_audio_fields = ["duration", "durationSeconds", "bitrate", "sampleRate", "channels", "fileSize"]
    for field_name in required_audio_fields:
        if field_name not in matched_song or matched_song[field_name] is None:
            return CacheResult(status=CacheStatus.INVALID, reason=f"Missing required audio field '{field_name}' in cache for '{mp3_file.name}'.")

    # 4. ID3 Tag Field Check
    if "singers" not in matched_song or not isinstance(matched_song["singers"], list):
        return CacheResult(status=CacheStatus.INVALID, reason=f"Missing or invalid 'singers' list in cache for '{mp3_file.name}'.")
    if "composer" not in matched_song or matched_song["composer"] is None:
        return CacheResult(status=CacheStatus.INVALID, reason=f"Missing 'composer' field in cache for '{mp3_file.name}'.")

    audio_info = {
        "duration": matched_song["duration"],
        "durationSeconds": int(matched_song["durationSeconds"]),
        "bitrate": int(matched_song["bitrate"]),
        "sampleRate": int(matched_song["sampleRate"]),
        "channels": int(matched_song["channels"]),
        "fileSize": int(matched_song["fileSize"])
    }

    id3_tags = (
        matched_song["singers"],
        str(matched_song["composer"])
    )

    return CacheResult(
        status=CacheStatus.HIT,
        audio_info=audio_info,
        id3_tags=id3_tags,
        reason="Valid cache hit."
    )
