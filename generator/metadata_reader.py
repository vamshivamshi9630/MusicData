from pathlib import Path
from typing import Dict, Tuple, List
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

def read_audio_info(file_path: Path) -> Dict:
    """Extract audio technical specifications using mutagen.mp3.MP3."""
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
