from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class AlbumMetadata:
    album: str
    year: int
    musicDirector: str
    genre: str = "Soundtrack"
    language: str = "Telugu"
    country: str = "India"
    releaseDate: str = "2026-01-01"
    director: str = "Unknown"
    producer: str = "Unknown"
    banner: str = "Unknown"

@dataclass
class Song:
    id: str
    title: str
    normalizedTitle: str
    trackNumber: int
    duration: str
    durationSeconds: int
    audio: str
    composer: str
    singers: List[str]
    bitrate: int
    sampleRate: int
    channels: int
    fileSize: int

@dataclass
class Album:
    id: str
    name: str
    year: int
    musicDirector: str
    genre: str
    language: str
    image: str
    songCount: int
    songs: List[Song] = field(default_factory=list)

@dataclass
class AlbumIndexItem:
    id: str
    name: str
    artist: str
    year: int
    genre: str
    language: str
    image: str
    songCount: int
    partition: str

@dataclass
class SearchIndexItem:
    id: str
    title: str
    normalizedTitle: str
    albumId: str
    artistId: str
    languageId: str

@dataclass
class CategoryIndexItem:
    id: str
    name: str
    songCount: int
    albumCount: int = 0

@dataclass
class IndexVersionHash:
    version: int
    hash: str

@dataclass
class AlbumVersionHash:
    name: str
    partition: str
    version: int
    hash: str

@dataclass
class Statistics:
    totalSongs: int
    totalAlbums: int
    totalArtists: int
    totalGenres: int
    totalLanguages: int
    totalDurationFormatted: str
    totalDurationSeconds: int
