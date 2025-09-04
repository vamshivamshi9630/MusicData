import os
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://naasongs.com.co/page/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def sanitize_folder_name(name):
    return "".join(c for c in name if c not in r'<>:"/\|?*').strip()

def fetch_albums_from_page(page_num):
    url = f"{BASE_URL}{page_num}"
    print(f"🔍 Fetching albums from: {url}")
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            print(f"❌ Failed to fetch page {page_num}")
            return []
        soup = BeautifulSoup(res.text, 'html.parser')
        # Naasongs lists albums within 'h2' tags having class 'entry-title'
        album_names = []
        for h2 in soup.select('h2.entry-title a'):
            album_name = h2.text.strip()
            if album_name:
                album_names.append(album_name)
        return album_names
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def create_album_folders(albums, base_dir):
    for album in albums:
        folder_name = sanitize_folder_name(album)
        folder_path = os.path.join(base_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        print(f"📁 Created: {folder_name}")

def main():
    start_page = int(input("Enter start page number (e.g. 1): "))
    end_page = int(input("Enter end page number (e.g. 5): "))
    # Main directory for this batch
    folder_batch_name = f"albums_{start_page}_{end_page}"
    batch_folder = os.path.join(os.getcwd(), folder_batch_name)
    os.makedirs(batch_folder, exist_ok=True)
    print(f"\nStarting scrape from page {start_page} to {end_page}...")
    all_albums = []
    for page_num in range(start_page, end_page+1):
        albums = fetch_albums_from_page(page_num)
        all_albums.extend(albums)
    print(f"\nTotal albums found: {len(all_albums)}")
    create_album_folders(all_albums, batch_folder)
    print("\n✅ All folders created.")

if __name__ == "__main__":
    main()
