import hashlib
import re

def normalize(name: str) -> str:
    """Normalize string by lowercasing, converting dashes/underscores to spaces, and removing non-alphanumeric characters."""
    if not name:
        return ""
    text = name.lower().replace("–", "-").replace("_", " ")
    # Keep only alphanumeric characters and single spaces
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return " ".join(text.split())

def get_stable_id(val: str) -> str:
    """Generate a stable 12-character SHA-256 hash ID."""
    clean_val = val.strip().lower()
    return hashlib.sha256(clean_val.encode('utf-8')).hexdigest()[:12]

def get_album_partition(album_name: str) -> str:
    """Return the partition directory name ('A'-'Z' or '0-9')."""
    if not album_name:
        return "0-9"
    first_char = album_name.strip()[0].upper()
    if first_char.isalpha():
        return first_char
    return "0-9"

def compute_sha256_text(content: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

def compute_sha256_bytes(content: bytes) -> str:
    """Compute SHA-256 hash of raw bytes."""
    return hashlib.sha256(content).hexdigest()[:16]
