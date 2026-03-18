# script_2_fetch_album_urls.py

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

ALBUM_FILE = "albumUrls.txt"
BASE_DIR = os.getcwd()
SEARCH_SITE = "naasongs.com.co"

def setup_browser():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def search_album_url(driver, album_name):
    query = f"{album_name} movie mp3 songs download site:{SEARCH_SITE}"
    print(f"\n🎧 Album: {album_name}\n🔍 Searching: {query}")
    
    driver.get("https://www.google.com")
    time.sleep(2)

    search_box = driver.find_element(By.NAME, "q")
    search_box.clear()
    search_box.send_keys(query)
    search_box.submit()

    print("⏳ Waiting for results...")

    for _ in range(15):  # up to 15 seconds to allow for captcha manually
        try:
            links = driver.find_elements(By.CSS_SELECTOR, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and SEARCH_SITE in href and href.endswith(".html"):
                    print(f"  ✅ Found: {href}")
                    return href
        except:
            pass
        time.sleep(1)

    print("  ❌ No valid link found.")
    return "NOT FOUND"

def main():
    folders = [f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))]
    print(f"📁 Found {len(folders)} album folders.")

    existing = {}
    if os.path.exists(ALBUM_FILE):
        with open(ALBUM_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if " : " in line:
                    name, url = line.strip().split(" : ", 1)
                    existing[name.strip()] = url.strip()

    driver = setup_browser()
    try:
        with open(ALBUM_FILE, "a", encoding="utf-8") as f:
            for folder in folders:
                if folder in existing:
                    print(f"⏩ Skipping: {folder}")
                    continue

                url = search_album_url(driver, folder)
                f.write(f"{folder} : {url}\n")
                f.flush()
    finally:
        driver.quit()

    print("\n✅ All URLs saved to albumUrls.txt")

if __name__ == "__main__":
    main()
