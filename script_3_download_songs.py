import os
import re
import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.abspath(os.getcwd())
HEADERS = {"User-Agent": "Mozilla/5.0"}
URL_FILE = "albumUrls.txt"  # Format: AlbumName : URL

def sanitize_filename(name):
    # Remove characters invalid in filenames
    return re.sub(r'[\/*?:"<>|]', "", name).strip()

def load_album_urls():
    album_urls = {}
    if os.path.exists(URL_FILE):
        with open(URL_FILE, "r", encoding="utf-8") as file:
            for line in file:
                if " : " in line:
                    name, url = line.strip().split(" : ", 1)
                    album_urls[name.strip()] = url.strip()
    else:
        print(f"⚠️ File '{URL_FILE}' not found.")
    return album_urls

def download_song(song_url, save_path):
    try:
        response = requests.get(song_url, headers=HEADERS, stream=True, timeout=(5, 30))
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"  ✅ Downloaded: {os.path.basename(save_path)}")
    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout downloading: {song_url}")
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error downloading: {e}")

def extract_song_name(p_tag, a_tag):
    p_text = p_tag.get_text(separator=" ", strip=True)
    # Remove anchor text like "Download"
    p_text = p_text.replace(a_tag.get_text(strip=True), '').strip()
    # Remove leading numbering like "01. "
    p_text = re.sub(r'^\d{1,2}\.\s*', '', p_text)
    # Remove trailing keywords like "Song"
    p_text = re.sub(r'\s*Song\s*$', '', p_text, flags=re.IGNORECASE).strip()
    # Remove artist name, bit rates, anything after the song title
    # Extract till first dash or digits start or multiple spaces as rough delimiter
    match = re.match(r'^([^\d–-]+)', p_text)
    if match:
        song_name = match.group(1).strip()
    else:
        song_name = p_text
    return sanitize_filename(song_name)

def process_album(album_name, album_url):
    print(f"\n🎧 Album: {album_name}")

    if not album_url or album_url == "NOT FOUND":
        print("  ⚠️ Skipped (URL not found).")
        return

    album_path = os.path.join(BASE_DIR, album_name)
    os.makedirs(album_path, exist_ok=True)

    try:
        response = requests.get(album_url, headers=HEADERS, timeout=(5, 30))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        song_links = []

        for p_tag in soup.find_all('p'):
            a_tag = p_tag.find('a', href=True)
            if a_tag and a_tag['href'].endswith('.mp3'):
                href = a_tag['href']
                song_name = extract_song_name(p_tag, a_tag)
                if not song_name:
                    song_name = f"Song_{len(song_links)+1}"
                print(f"  🎵 Found song: {song_name}")
                song_links.append((song_name, href))

        if not song_links:
            print("  ❌ No songs found.")
            return

        for song_name, song_url in song_links:
            save_path = os.path.join(album_path, song_name + ".mp3")
            if os.path.exists(save_path):
                print(f"  ⏩ Skipped (already exists): {song_name}.mp3")
            else:
                download_song(song_url, save_path)

        print(f"  ✅ Finished album '{album_name}' with {len(song_links)} songs.")

    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout fetching album page: {album_url}")
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error fetching album page: {e}")
    except Exception as e:
        print(f"  ❌ Unexpected error processing album '{album_name}': {e}")

def main():
    print("\n📂 Scanning album folders...")
    folders = [f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))]
    print(f"📁 Found {len(folders)} folders.")
    album_urls = load_album_urls()

    for album in folders:
        url = album_urls.get(album)
        if url:
            process_album(album, url)
        else:
            print(f"⚠️ No URL found for album: {album}")

    print("\n🎉 Done!")

if __name__ == "__main__":
    main()
