from typing import List, Dict, Tuple
from generator.models import Album, Song

def validate_albums(albums: List[Album]) -> Tuple[bool, List[str]]:
    """Validate all generated album structures. Returns (is_valid, list_of_errors)."""
    errors = []
    seen_album_ids = set()
    seen_song_ids = set()

    if not albums:
        errors.append("Validation Error: No albums were scanned or found!")
        return False, errors

    for album in albums:
        # Check album ID collision
        if album.id in seen_album_ids:
            errors.append(f"Duplicate Album ID: {album.id} for album '{album.name}'")
        seen_album_ids.add(album.id)

        if not album.name.strip():
            errors.append("Album Name is empty.")

        if not album.songs:
            errors.append(f"Album '{album.name}' has no MP3 songs!")

        for song in album.songs:
            # Check song ID collision
            if song.id in seen_song_ids:
                errors.append(f"Duplicate Song ID: {song.id} for song '{song.title}' in album '{album.name}'")
            seen_song_ids.add(song.id)

            if not song.title.strip():
                errors.append(f"Song in album '{album.name}' has an empty title.")

            if not song.audio.strip():
                errors.append(f"Song '{song.title}' in album '{album.name}' is missing audio filename.")

    is_valid = len(errors) == 0
    return is_valid, errors
