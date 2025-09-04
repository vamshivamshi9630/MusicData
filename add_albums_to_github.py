import os
import shutil
import subprocess

# --- CONFIGURATION ---
SOURCE_PATH = "D:/Songs"         # The path with the folders/albums to copy
REPO_PATH = "C:/Users/KudikalaVamshi/AndroidStudioProjects/MusicData"     # The path to your already-cloned GitHub repo

def folder_exists_in_repo(album, repo_path):
    """Check if a folder exists at the root of the repo."""
    return os.path.isdir(os.path.join(repo_path, album))

def copy_folder(album, source_path, repo_path):
    """Copy the folder into the repo root."""
    src = os.path.join(source_path, album)
    dst = os.path.join(repo_path, album)
    # If it exists (shouldn't, due to check), remove to avoid errors
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

def git_commit_and_push(repo_path, album):
    """Add, commit, and push the given album folder to the remote repo."""
    subprocess.run(['git', 'add', album], cwd=repo_path, check=True)
    subprocess.run(['git', 'commit', '-m', album], cwd=repo_path, check=True)
    subprocess.run(['git', 'push'], cwd=repo_path, check=True)

def main():
    albums = [f for f in os.listdir(SOURCE_PATH) if os.path.isdir(os.path.join(SOURCE_PATH, f))]
    for album in albums:
        print(f"\n--- Processing album: {album} ---")
        if folder_exists_in_repo(album, REPO_PATH):
            print(f"Album {album} already in repo. Skipping.")
            continue
        try:
            copy_folder(album, SOURCE_PATH, REPO_PATH)
            git_commit_and_push(REPO_PATH, album)
            print(f"Album {album} added, committed & pushed!")
        except Exception as e:
            print(f"Failed to process {album}: {e}")
            # Clean up if copy failed
            dst = os.path.join(REPO_PATH, album)
            if os.path.exists(dst):
                shutil.rmtree(dst)

if __name__ == '__main__':
    main()
