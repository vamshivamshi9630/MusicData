import ast
import json
from pathlib import Path

from generator.config import BASE_PATH, LEGACY_METADATA_FILE
from generator.utils import normalize


# ============================================================
# READ LEGACY METADATA
# ============================================================

def get_legacy_metadata():
    """
    Read ALBUM_METADATA from MusiDirector_Year.txt
    and return normalized metadata.
    """

    if not LEGACY_METADATA_FILE.exists():
        print(
            f"ERROR: Legacy metadata file not found:\n"
            f"{LEGACY_METADATA_FILE}"
        )
        return None

    try:
        content = LEGACY_METADATA_FILE.read_text(
            encoding="utf-8"
        )

        tree = ast.parse(content)

        metadata = None

        for node in tree.body:

            if not isinstance(node, ast.Assign):
                continue

            for target in node.targets:

                if getattr(target, "id", "") == "ALBUM_METADATA":
                    metadata = ast.literal_eval(node.value)
                    break

            if metadata is not None:
                break

        if metadata is None:
            print(
                "ERROR: ALBUM_METADATA dictionary "
                "was not found in legacy file."
            )
            return None

        normalized_meta = {}

        for key, value in metadata.items():

            if not isinstance(value, dict):
                continue

            music_director = str(
                value.get("musicDirector", "")
            ).strip()

            year_value = value.get("year")

            # Convert year safely
            try:
                year_number = int(year_value)
            except (ValueError, TypeError):
                year_number = None

            normalized_meta[normalize(key)] = {
                "musicDirector": music_director,
                "year": year_number
            }

        print(
            f"Loaded {len(normalized_meta)} "
            f"metadata entries from legacy file."
        )

        return normalized_meta

    except SyntaxError as e:

        print("\n" + "=" * 70)
        print("ERROR: LEGACY FILE HAS INVALID PYTHON SYNTAX")
        print("=" * 70)

        print(f"File : {LEGACY_METADATA_FILE}")
        print(f"Line : {e.lineno}")
        print(f"Error: {e.msg}")

        if e.text:
            print(f"\nProblematic line:")
            print(e.text.strip())

        print(
            "\nNO album_info.json files were modified."
        )

        return None

    except Exception as e:

        print(
            f"ERROR: Could not parse legacy file:\n{e}"
        )

        return None


# ============================================================
# LOAD EXISTING ALBUM INFO
# ============================================================

def load_album_info(info_file):
    """
    Read existing album_info.json safely.
    """

    try:

        with open(
            info_file,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if not isinstance(data, dict):
            return {}

        return data

    except Exception as e:

        print(
            f"WARNING: Could not read {info_file}: {e}"
        )

        return {}


# ============================================================
# SAVE ALBUM INFO
# ============================================================

def save_album_info(info_file, data):

    with open(
        info_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

        f.write("\n")


# ============================================================
# MIGRATE / UPDATE ALL ALBUMS
# ============================================================

def migrate_all_albums():

    print("\n" + "=" * 70)
    print("ALBUM METADATA MIGRATION / UPDATE")
    print("=" * 70)

    # --------------------------------------------------------
    # Load legacy metadata
    # --------------------------------------------------------

    legacy_meta = get_legacy_metadata()

    # VERY IMPORTANT:
    # If legacy metadata cannot be parsed,
    # do not touch existing album_info.json files.
    if legacy_meta is None:
        print("\nMigration aborted safely.")
        return

    # --------------------------------------------------------
    # Find album folders
    # --------------------------------------------------------

    album_dirs = sorted(
        [
            d
            for d in BASE_PATH.iterdir()
            if (
                d.is_dir()
                and not d.name.startswith(".")
                and d.name not in [
                    "generator",
                    "metadata",
                    ".git"
                ]
            )
        ],
        key=lambda d: d.name.lower()
    )

    print(
        f"\nAlbum folders found: {len(album_dirs)}"
    )

    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

    created_count = 0
    updated_count = 0
    unchanged_count = 0
    no_legacy_match_count = 0
    invalid_json_count = 0

    # --------------------------------------------------------
    # Process every album
    # --------------------------------------------------------

    for album_dir in album_dirs:

        album_name = album_dir.name
        norm_key = normalize(album_name)

        info_file = album_dir / "album_info.json"

        # ----------------------------------------------------
        # Get legacy metadata
        # ----------------------------------------------------

        legacy = legacy_meta.get(norm_key)

        if legacy is None:

            no_legacy_match_count += 1

        # ----------------------------------------------------
        # Existing album_info.json
        # ----------------------------------------------------

        if info_file.exists():

            album_info = load_album_info(info_file)

            if not isinstance(album_info, dict):
                print(
                    f"WARNING: Invalid JSON structure: "
                    f"{info_file}"
                )

                invalid_json_count += 1
                continue

            original = dict(album_info)

            # ------------------------------------------------
            # ALWAYS keep actual folder name
            # ------------------------------------------------

            album_info["album"] = album_name

            # ------------------------------------------------
            # UPDATE ONLY WHEN LEGACY DATA EXISTS
            # ------------------------------------------------

            if legacy is not None:

                music_director = legacy.get(
                    "musicDirector"
                )

                year = legacy.get("year")

                # --------------------------------------------
                # Music Director
                # --------------------------------------------

                if (
                    music_director
                    and music_director.strip()
                ):

                    # Don't replace good existing data
                    # with Unknown.
                    if music_director.lower() != "unknown":

                        album_info["musicDirector"] = (
                            music_director.strip()
                        )

                # --------------------------------------------
                # Year
                # --------------------------------------------

                if year is not None:

                    album_info["year"] = year

            # ------------------------------------------------
            # Save only if something changed
            # ------------------------------------------------

            if album_info != original:

                save_album_info(
                    info_file,
                    album_info
                )

                updated_count += 1

                print(
                    f"UPDATED : {album_name}"
                )

            else:

                unchanged_count += 1

        # ----------------------------------------------------
        # CREATE new album_info.json
        # ----------------------------------------------------

        else:

            # Defaults for new albums
            if legacy is not None:

                music_director = (
                    legacy.get("musicDirector")
                    or "Unknown"
                )

                year = legacy.get("year")

                if year is None:
                    year = 2026

            else:

                music_director = "Unknown"
                year = 2026

            album_info = {

                "album": album_name,

                "year": year,

                "musicDirector": music_director,

                "genre": "Tollywood Soundtrack",

                "language": "Telugu",

                "country": "India",

                # IMPORTANT:
                # This is only a fallback date.
                "releaseDate": f"{year}-01-01",

                "director": "Unknown",

                "producer": "Unknown",

                "banner": "Unknown"
            }

            save_album_info(
                info_file,
                album_info
            )

            created_count += 1

            print(
                f"CREATED : {album_name}"
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)

    print(
        f"Created             : {created_count}"
    )

    print(
        f"Updated             : {updated_count}"
    )

    print(
        f"Already up-to-date  : {unchanged_count}"
    )

    print(
        f"No legacy match     : {no_legacy_match_count}"
    )

    print(
        f"Invalid JSON files  : {invalid_json_count}"
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    migrate_all_albums()