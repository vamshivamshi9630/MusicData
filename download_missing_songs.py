import os
import time
import subprocess
import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Kill all chrome processes to avoid conflicts
subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)

BASE_DIR = os.path.abspath(os.getcwd())
DOWNLOAD_DIR = os.path.join(BASE_DIR, "Downloads")
SELENIUM_PROFILE_DIR = os.path.join(BASE_DIR, "selenium_profile")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(SELENIUM_PROFILE_DIR, exist_ok=True)


def clean_song_name(raw_name, element_text=None):
    name = element_text if element_text else raw_name

    # Decode URL encoding for spaces and strip
    name = name.replace("%20", " ").strip()

    # Remove numeric prefixes like 1-, 2=, 3/
    name = re.sub(r"^[0-9]+[-=/]*", "", name)

    # Remove unwanted suffixes like '-SenSongsMp3.Co.mp3' or variations, but keep '.mp3' extension
    name = re.sub(r"(-senSongsmp3\.co\.mp3|-sensongsmp3\.co\.mp3|-sensusmp3\.co\.mp3|-sensongs\.co\.mp3|-sensongsmp3\.co\.mp3|-sensong\.co\.mp3|-senastories\.com\.mp3|-song.*?\.mp3)", "", name, flags=re.IGNORECASE)

    # Remove trailing mp3 or Mp3 Song text except extension
    name = re.sub(r"\s*mp3\s*song\s*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\.mp3$", "", name, flags=re.IGNORECASE)

    # Remove trailing bracketed suffixes like [Download] or (2020)
    name = re.sub(r"\s*[\[\(].*?[\]\)]\s*$", "", name)

    # Remove trailing dashes/hyphens
    name = re.sub(r"[-–—]\s*$", "", name)

    # Normalize spaces
    name = re.sub(r"\s+", " ", name).strip()

    # Add .mp3 extension again
    return name + ".mp3"


def setup_browser():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={SELENIUM_PROFILE_DIR}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "safebrowsing.enabled": True,
    })
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def wait_for_user_login(driver):
    driver.get("https://accounts.google.com/signin")
    print("\nPlease log into Google in the opened browser window.")
    print("After logging in, close the browser window to continue.")
    print("Waiting for browser window to close...")
    while True:
        try:
            driver.find_element(By.TAG_NAME, "body")
            time.sleep(30)
        except:
            break
    print("Login detected. Continuing...")

def search_and_open_album(driver, album_name):
    query = f"{album_name} mp3 songs download site:naasongs.com.co"
    search_url = f"https://www.google.com/search?q={query}"
    driver.get(search_url)
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='naasongs.com.co']"))
    )
    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='naasongs.com.co']")
    for link in links:
        try:
            href = link.get_attribute("href")
            if "songs" in href:
                link.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                current_url = driver.current_url
                if "accounts.google.com/v3/signin" in current_url:
                    print("\n⚠️ Login page detected.")
                    print("Please manually hit browser back, then open the album site link in the same browser.")
                    print("Waiting for you to navigate away from login page and open the album.")
                    WebDriverWait(driver, 600).until_not(
                        EC.url_contains("accounts.google.com/v3/signin")
                    )
                    album_url = driver.current_url
                    print(f"Album page detected: {album_url}. Resuming download...")
                    return album_url
                else:
                    return current_url
        except Exception:
            continue
    print(f"  ❌ No valid NaaSongs link found for {album_name}")
    return None

def download_songs(driver, album_folder, page_url):
    driver.get(page_url)
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href$='.mp3']"))
    )
    mp3_links = driver.find_elements(By.CSS_SELECTOR, "a[href$='.mp3']")
    if not mp3_links:
        print("  ❌ No mp3 links found.")
        return
    existing_files = set(os.listdir(album_folder))
    downloaded_count = 0
    for link in mp3_links:
        try:
            song_url = link.get_attribute("href")
            visible_name = link.text.strip()
            if not visible_name or len(visible_name) < 3 or visible_name.lower() == "download":
                visible_name = os.path.basename(song_url)

            # Print log of original name and download URL
            print(f"Song link text: '{visible_name}' - URL: {song_url}")

            cleaned_name = clean_song_name("", element_text=visible_name)

            print(f"Renaming to: {cleaned_name}")

            if cleaned_name in existing_files:
                print(f"  ⚠️ Already exists: {cleaned_name}")
                continue

            print(f"  ⬇️ Downloading: {cleaned_name}")
            r = requests.get(song_url, timeout=20)
            if r.status_code == 200:
                with open(os.path.join(album_folder, cleaned_name), "wb") as f:
                    f.write(r.content)
                downloaded_count += 1
            else:
                print(f"  ❌ Failed to download {cleaned_name} (status {r.status_code})")
        except Exception as e:
            print(f"  ❌ Error downloading {visible_name}: {e}")

    if downloaded_count == 0:
        print("  🔍 No new songs downloaded.")
    else:
        print(f"  ✅ Downloaded {downloaded_count} new songs.")

def main():
    print("\n🔍 Scanning album folders...")
    album_folders = [
        d for d in os.listdir(BASE_DIR)
        if os.path.isdir(os.path.join(BASE_DIR, d)) and not d.lower().startswith("downloads")
    ]
    print(f"\n📂 {len(album_folders)} albums found.\n")

    driver = setup_browser()
    profile_files = os.listdir(SELENIUM_PROFILE_DIR)
    if len(profile_files) < 5:
        wait_for_user_login(driver)
        driver.quit()
        print("\nPlease rerun the script after login.")
        return

    for album in album_folders:
        print(f"\n🎧 Album: {album}")
        album_path = os.path.join(BASE_DIR, album)
        os.makedirs(album_path, exist_ok=True)
        page_url = search_and_open_album(driver, album)
        if not page_url:
            continue
        download_songs(driver, album_path, page_url)
        time.sleep(3)

    driver.quit()
    print("\n✅ All albums processed.")

if __name__ == "__main__":
    main()
