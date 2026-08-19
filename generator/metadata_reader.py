from pathlib import Path
from typing import Dict, Tuple, List, Optional
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

from generator.cache_reader import (
    CacheStatus,
    CacheResult,
    CacheMissError,
    CacheInvalidError,
    StrictCloudSafetyViolation,
    GeneratorTelemetry,
    read_song_from_cache
)

def read_audio_info(file_path: Path, telemetry: Optional[GeneratorTelemetry] = None) -> Dict:
    """Extract audio technical specifications using mutagen.mp3.MP3."""
    if telemetry:
        telemetry.actual_mp3_files_opened += 1
        telemetry.mutagen_reads_performed += 1

    try:
        audio = MP3(file_path)
        duration_sec = int(audio.info.length)
        minutes = duration_sec // 60
        seconds = duration_sec % 60
        duration_str = f"{minutes}:{seconds:02d}"

        return {
            "duration": duration_str,
            "durationSeconds": duration_sec,
            "bitrate": int(getattr(audio.info, "bitrate", 0)),
            "sampleRate": int(getattr(audio.info, "sample_rate", 0)),
            "channels": int(getattr(audio.info, "channels", 2)),
            "fileSize": file_path.stat().st_size
        }
    except Exception:
        return {
            "duration": "0:00",
            "durationSeconds": 0,
            "bitrate": 0,
            "sampleRate": 0,
            "channels": 2,
            "fileSize": file_path.stat().st_size if file_path.exists() else 0
        }

def read_id3_tags(mp3_file: Path, default_composer: str) -> Tuple[List[str], str]:
    """Extract singers and composer from MP3 ID3 tags."""
    singers = []
    composer = default_composer
    try:
        tags = ID3(mp3_file)
        tpe1 = tags.get("TPE1")
        if tpe1:
            raw_singers = str(tpe1[0])
            for delim in ["/", ";", ",", "\\", " ft. ", " feat. ", " Ft. ", " Feat. "]:
                raw_singers = raw_singers.replace(delim, "|")
            parts = [p.strip() for p in raw_singers.split("|") if p.strip()]
            if parts:
                singers = parts

        tcom = tags.get("TCOM")
        if tcom:
            comp_str = str(tcom[0]).strip()
            if comp_str:
                composer = comp_str
    except Exception:
        pass

    if not singers:
        singers = [default_composer]

    return singers, composer

def read_song_metadata(
    album_name: str,
    mp3_file: Path,
    music_director: str,
    album_cache: Optional[Dict] = None,
    is_new_or_modified: bool = False,
    strict_cloud_safety: bool = False,
    telemetry: Optional[GeneratorTelemetry] = None
) -> Tuple[Dict, List[str], str]:
    """Cache-aware song metadata extraction."""
    
    # Newly uploaded or explicitly modified song -> Must perform actual mutagen read
    if is_new_or_modified:
        if telemetry:
            telemetry.newly_uploaded_songs += 1
        audio_info = read_audio_info(mp3_file, telemetry=telemetry)
        singers, composer = read_id3_tags(mp3_file, music_director)
        return audio_info, singers, composer

    # Historical song -> Attempt cache-first read
    if telemetry:
        telemetry.historical_songs_processed += 1

    cache_res = read_song_from_cache(album_cache, album_name, mp3_file)

    if cache_res.status == CacheStatus.HIT:
        if telemetry:
            telemetry.cache_hits += 1
        # NO MP3 FILE OPENED!
        return cache_res.audio_info, cache_res.id3_tags[0], cache_res.id3_tags[1]

    if cache_res.status == CacheStatus.MISS:
        if telemetry:
            telemetry.cache_misses += 1
        if strict_cloud_safety:
            raise CacheMissError(f"Strict Cloud Safety Violation: Cache miss for historical song '{album_name}/{mp3_file.name}'. {cache_res.reason}")
        # Local Mode fallback
        audio_info = read_audio_info(mp3_file, telemetry=telemetry)
        singers, composer = read_id3_tags(mp3_file, music_director)
        return audio_info, singers, composer

    if cache_res.status == CacheStatus.INVALID:
        if telemetry:
            telemetry.cache_invalid_records += 1
        if strict_cloud_safety:
            raise CacheInvalidError(f"Strict Cloud Safety Violation: Invalid cache record for historical song '{album_name}/{mp3_file.name}'. {cache_res.reason}")
        # Local Mode fallback
        audio_info = read_audio_info(mp3_file, telemetry=telemetry)
        singers, composer = read_id3_tags(mp3_file, music_director)
        return audio_info, singers, composer

    # Default fallback
    audio_info = read_audio_info(mp3_file, telemetry=telemetry)
    singers, composer = read_id3_tags(mp3_file, music_director)
    return audio_info, singers, composer
