import os
import requests
from bs4 import BeautifulSoup
import re

BASE_DIR = os.path.abspath(os.getcwd())
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}
URL_FILE = "albumUrls.txt"  # Format: AlbumName : URL

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def load_album_urls():
    album_urls = {}
    if os.path.exists(URL_FILE):
        with open(URL_FILE, "r", encoding="utf-8") as file:
            for line in file:
                if " : " in line:
                    name, url = line.strip().split(" : ", 1)
                    album_urls[name.strip()] = url.strip()
    return album_urls

def download_song(song_url, save_path):
    try:
        response = requests.get(song_url, headers=HEADERS, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"  ✅ Downloaded: {os.path.basename(save_path)}")
        else:
            print(f"  ❌ Failed to download: {song_url}")
    except Exception as e:
        print(f"  ❌ Error downloading: {e}")

def process_album(album_name, album_url):
    print(f"\n🎧 Album: {album_name}")
    
    if not album_url or album_url == "NOT FOUND":
        print("  ⚠️ Skipped (URL not found).")
        return

    album_path = os.path.join(BASE_DIR, album_name)
    os.makedirs(album_path, exist_ok=True)

    try:
        html = requests.get(album_url, headers=HEADERS).text
        soup = BeautifulSoup(html, 'html.parser')

        song_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.endswith('.mp3'):
                name = None
                prev = a.find_previous(['b', 'strong', 'p'])
                if prev:
                    full_text = prev.get_text(strip=True)
                    name_only = re.sub(r"^\d{1,2}[.)\s-]*", "", full_text)
                    name_only = re.split(r"–| - ", name_only)[0].strip()
                    name = sanitize_filename(name_only)
                if not name:
                    name = f"Song_{len(song_links)+1}"
                song_links.append((name, href))

        if not song_links:
            print("  ❌ No songs found.")
            return

        for name, link in song_links:
            save_path = os.path.join(album_path, name + ".mp3")
            if os.path.exists(save_path):
                print(f"  ⏩ Skipped (already exists): {name}.mp3")
            else:
                download_song(link, save_path)

        print(f"  ✅ Finished album '{album_name}' with {len(song_links)} songs.")

    except Exception as e:
        print(f"  ❌ Error processing album '{album_name}': {e}")

def main():
    print("\n📂 Scanning album folders...")
    folders = [f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))]
    print(f"📁 Found {len(folders)} folders.")

    album_urls = load_album_urls()

    for album in folders:
        url = album_urls.get(album)
        process_album(album, url)

    print("\n🎉 Done!")

if __name__ == "__main__":
    main()
