import os
import sys
import time
from typing import List, Optional, Set, Tuple
from generator.config import BASE_PATH, METADATA_DIR
from generator.logger import log_step, log_info, log_success, log_error
from generator.scanner import scan_all_albums
from generator.metadata_reader import read_song_metadata
from generator.cache_reader import (
    load_album_cache,
    GeneratorTelemetry,
    StrictCloudSafetyViolation,
    CacheMissError,
    CacheInvalidError
)
from generator.models import Album, Song
from generator.utils import get_stable_id, normalize
from generator.validator import validate_albums
from generator.album_writer import write_all_albums
from generator.album_index_writer import write_albums_index
from generator.artist_writer import write_artists_index
from generator.genre_writer import write_genres_index
from generator.language_writer import write_languages_index
from generator.search_writer import write_search_index
from generator.statistics_writer import write_statistics
from generator.manifest_writer import write_manifest

def build_album_objects(
    scanned_data: List[dict],
    use_cache: bool = True,
    strict_cloud_safety: bool = False,
    modified_songs: Optional[Set[Tuple[str, str]]] = None,
    telemetry: Optional[GeneratorTelemetry] = None
) -> Tuple[List[Album], GeneratorTelemetry]:
    if telemetry is None:
        telemetry = GeneratorTelemetry()

    modified_songs_set = modified_songs or set()
    albums = []

    for data in scanned_data:
        album_name = data["album_name"]
        album_info = data["album_info"]
        image_name = data["image_name"]
        mp3_files = data["mp3_files"]

        album_id = get_stable_id(album_name)
        music_director = album_info.get("musicDirector", "Unknown").strip() or "Unknown"
        year = int(album_info.get("year", 2026))
        genre = album_info.get("genre", "Soundtrack").strip() or "Soundtrack"
        language = album_info.get("language", "Telugu").strip() or "Telugu"

        album_cache = load_album_cache(METADATA_DIR, album_name) if use_cache else None

        songs = []
        for track_num, mp3_file in enumerate(mp3_files, start=1):
            song_title = mp3_file.stem
            song_id = get_stable_id(f"{album_name}{mp3_file.name}")

            is_modified = album_cache is None or (album_name, mp3_file.name) in modified_songs_set or not use_cache

            audio_info, singers, composer = read_song_metadata(
                album_name=album_name,
                mp3_file=mp3_file,
                music_director=music_director,
                album_cache=album_cache,
                is_new_or_modified=is_modified,
                strict_cloud_safety=strict_cloud_safety,
                telemetry=telemetry
            )

            songs.append(
                Song(
                    id=song_id,
                    title=song_title,
                    normalizedTitle=normalize(song_title),
                    trackNumber=track_num,
                    duration=audio_info["duration"],
                    durationSeconds=audio_info["durationSeconds"],
                    audio=mp3_file.name,
                    composer=composer,
                    singers=singers,
                    bitrate=audio_info["bitrate"],
                    sampleRate=audio_info["sampleRate"],
                    channels=audio_info["channels"],
                    fileSize=audio_info["fileSize"]
                )
            )

        albums.append(
            Album(
                id=album_id,
                name=album_name,
                year=year,
                musicDirector=music_director,
                genre=genre,
                language=language,
                image=image_name,
                songCount=len(songs),
                songs=songs
            )
        )

    albums.sort(key=lambda a: a.name.lower())
    return albums, telemetry

def main():
    start_time = time.time()
    total_steps = 8

    # Read environment configuration flags
    use_cache = os.environ.get("GENERATOR_CACHE_MODE", "1") != "0"
    strict_cloud_safety = os.environ.get("STRICT_CLOUD_SAFETY", "0") == "1" or os.environ.get("CLOUD_MODE", "0") == "1"

    print("=====================================================")
    print(f" Tunezy Metadata Generator v2.1.0 (Cache-Aware Mode)")
    print(f" Cache Reading: {'ENABLED' if use_cache else 'DISABLED'}")
    print(f" Strict Cloud Safety: {'ACTIVE' if strict_cloud_safety else 'INACTIVE'}")
    print("=====================================================")

    # Step 1: Scan
    log_step(1, total_steps, "Scanning Album Directories")
    scanned_data = scan_all_albums()
    log_info(f"Discovered {len(scanned_data)} valid album folders with album_info.json")

    # Step 2: Read Metadata & Construct Objects
    log_step(2, total_steps, "Extracting Audio Specs & Metadata")
    telemetry = GeneratorTelemetry()
    try:
        albums, telemetry = build_album_objects(
            scanned_data,
            use_cache=use_cache,
            strict_cloud_safety=strict_cloud_safety,
            telemetry=telemetry
        )
    except (StrictCloudSafetyViolation, CacheMissError, CacheInvalidError) as e:
        log_error(f"Generator Execution Halted: {e}")
        sys.exit(1)

    total_songs = sum(len(a.songs) for a in albums)
    log_info(f"Successfully processed {len(albums)} albums and {total_songs} songs")
    log_info(
        f"Telemetry -> Historical Songs: {telemetry.historical_songs_processed}, Cache Hits: {telemetry.cache_hits}, "
        f"Cache Misses: {telemetry.cache_misses}, Invalid: {telemetry.cache_invalid_records}, "
        f"New Songs: {telemetry.newly_uploaded_songs}, MP3 Files Opened: {telemetry.actual_mp3_files_opened}"
    )

    # Step 3: Validate
    log_step(3, total_steps, "Running Data Integrity Validation")
    is_valid, errors = validate_albums(albums)
    if not is_valid:
        log_error("Validation failed with errors:")
        for err in errors:
            log_error(f" - {err}")
        sys.exit(1)
    log_info("All validation checks passed cleanly!")

    # Step 4: Write Per-Album JSONs
    log_step(4, total_steps, "Writing Per-Album Metadata JSONs")
    album_hashes = write_all_albums(albums)
    log_info(f"Generated {len(album_hashes)} album JSON files in metadata/albums/")

    # Step 5: Write Index Files
    log_step(5, total_steps, "Writing Index Files (Albums, Artists, Genres, Languages, Search)")
    index_hashes = {}
    
    albums_path, albums_hash = write_albums_index(albums)
    index_hashes["albums"] = albums_hash

    artists_path, artists_hash = write_artists_index(albums)
    index_hashes["artists"] = artists_hash

    genres_path, genres_hash = write_genres_index(albums)
    index_hashes["genres"] = genres_hash

    langs_path, langs_hash = write_languages_index(albums)
    index_hashes["languages"] = langs_hash

    search_path, search_hash = write_search_index(albums)
    index_hashes["search"] = search_hash

    log_info("Generated 5 index files in metadata/indexes/")

    # Step 6: Write Statistics
    log_step(6, total_steps, "Writing Statistics Summary")
    stats_path, stats_hash = write_statistics(albums)
    log_info("Generated metadata/statistics.json")

    # Step 7: Write Manifest
    log_step(7, total_steps, "Generating Manifest & Computing SHA-256 Hashes")
    manifest_json = write_manifest(index_hashes, album_hashes)
    log_info("Generated metadata/manifest.json")

    # Step 8: Done
    elapsed = time.time() - start_time
    log_step(8, total_steps, "Finalizing Execution")
    log_success(f"Tunezy Metadata v2 Generation Complete in {elapsed:.2f} seconds!")
    print("=====================================================\n")

if __name__ == "__main__":
    main()
