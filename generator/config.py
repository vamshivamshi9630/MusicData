import os
from pathlib import Path

# Paths
BASE_PATH = Path(__file__).parent.parent.resolve()
METADATA_DIR = BASE_PATH / "metadata"
INDEXES_DIR = METADATA_DIR / "indexes"
ALBUMS_DIR = METADATA_DIR / "albums"

# Master Legacy Metadata File (for migration reference)
LEGACY_METADATA_FILE = BASE_PATH / "MusiDirector_Year.txt"

# GitHub Base URL
BASE_URL = "https://raw.githubusercontent.com/vamshivamshi9630/MusicData/main/"

# Versions & Schemas
SCHEMA_VERSION = "1.0"
GENERATOR_VERSION = "2.0.0"

# Supported File Extensions
AUDIO_EXTENSIONS = [".mp3"]
IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"]
