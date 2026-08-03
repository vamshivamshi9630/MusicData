import json
from pathlib import Path
from typing import List, Dict, Tuple
from generator.config import ALBUMS_DIR
from generator.models import Album
from generator.utils import get_album_partition, compute_sha256_text

def write_album_json(album: Album) -> Tuple[str, str]:
    """Write an album to metadata/albums/{Partition}/{AlbumName}.json. Returns (relative_path, sha256_hash)."""
    partition = get_album_partition(album.name)
    partition_dir = ALBUMS_DIR / partition
    partition_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{album.name}.json"
    file_path = partition_dir / filename

    album_dict = {
        "album": {
            "id": album.id,
            "name": album.name,
            "year": album.year,
            "musicDirector": album.musicDirector,
            "genre": album.genre,
            "language": album.language,
            "image": album.image,
            "songCount": len(album.songs)
        },
        "songs": [
            {
                "id": song.id,
                "title": song.title,
                "normalizedTitle": song.normalizedTitle,
                "trackNumber": song.trackNumber,
                "duration": song.duration,
                "durationSeconds": song.durationSeconds,
                "audio": song.audio,
                "composer": song.composer,
                "singers": song.singers,
                "bitrate": song.bitrate,
                "sampleRate": song.sampleRate,
                "channels": song.channels,
                "fileSize": song.fileSize
            }
            for song in album.songs
        ]
    }

    json_text = json.dumps(album_dict, indent=2, ensure_ascii=False)
    file_path.write_text(json_text, encoding="utf-8")

    rel_path = f"albums/{partition}/{filename}"
    file_hash = compute_sha256_text(json_text)

    return rel_path, file_hash

def write_all_albums(albums: List[Album]) -> Dict[str, Dict[str, str]]:
    """Write all albums to disk and return map of {AlbumId: {"name": ..., "partition": ..., "hash": ...}}."""
    album_hashes = {}
    for album in albums:
        rel_path, file_hash = write_album_json(album)
        partition = get_album_partition(album.name)
        album_hashes[album.id] = {
            "name": album.name,
            "partition": partition,
            "path": rel_path,
            "hash": file_hash
        }
    return album_hashes
