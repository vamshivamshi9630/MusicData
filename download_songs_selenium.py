# -*- coding: utf-8 -*-
import os
import sys
import time
import shutil
import re
import glob
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Set download and project paths
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
BASE_DIR = os.getcwd()

# Get the album URL from command line
if len(sys.argv) < 2:
    print("Usage: python download_songs_selenium.py <naasongs-url>")
    sys.exit(1)

NAASONGS_URL = sys.argv[1]
print(f"\nFetching song list from: {NAASONGS_URL}\n")

# Configure Chrome WebDriver
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-infobars")

driver = webdriver.Chrome(options=chrome_options)

# Scrape the webpage
resp = requests.get(NAASONGS_URL)
soup = BeautifulSoup(resp.text, 'html.parser')

# Extract song blocks
entries = soup.find_all("p")

for entry in entries:
    text = entry.get_text(separator="\n")
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    if not lines or 'Download' not in text:
        continue

    # Extract song name
    raw_song_name = lines[0].split("–")[0].strip()
    song_name = re.sub(r"\s*Song$", "", raw_song_name, flags=re.IGNORECASE).strip()

    # Extract movie name
    movie = "Unknown"
    for line in lines:
        if line.lower().startswith("movie"):
            movie = line.split(":", 1)[1].strip()
            movie = re.sub(r"\(.*?\)", "", movie)  # Remove (2023)
            movie = movie.replace("-", "").strip()

    # Extract download URL
    link_tag = entry.find("a", string=re.compile("Download", re.I))
    if not link_tag or not link_tag.get("href"):
        continue

    download_url = link_tag["href"]

    print(f"{song_name}")
    print(f"️  Movie: {movie}")
    print(f" Opening: {download_url}")

    # Start the download by visiting the URL
    driver.get(download_url)
    time.sleep(5)  # Give it time to begin download

    # Wait for .mp3 file to appear in Downloads
    start_time = time.time()
    downloaded_file = None
    while time.time() - start_time < 60:
        files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.mp3"))
        files = sorted(files, key=os.path.getmtime, reverse=True)
        if files:
            last_file = files[0]
            if time.time() - os.path.getmtime(last_file) < 60:
                downloaded_file = last_file
                break
        time.sleep(2)

    if downloaded_file:
        print(f" Downloaded: {os.path.basename(downloaded_file)}")

        # Prepare folder
        target_folder = os.path.join(BASE_DIR, movie)
        os.makedirs(target_folder, exist_ok=True)

        # Clean song name and rename with .mp3 extension
        clean_name = re.sub(r'[\\/*?:"<>|]', "", song_name)  # Remove illegal file characters
        new_file_name = f"{clean_name}.mp3"
        dest_path = os.path.join(target_folder, new_file_name)

        # Move and rename file
        shutil.move(downloaded_file, dest_path)
        print(f" Moved to: {dest_path}\n")
    else:
        print("  Failed to detect downloaded file.\n")

# Cleanup
driver.quit()
print("\n Done downloading all songs.")
