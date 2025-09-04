import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse

# Constants
ALBUM_FILE = "albumUrls.txt"
SEARCH_WAIT_TIMEOUT = 15
BASE_DIR = os.getcwd()

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_album_folders():
    folders = [f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))]
    return folders

def load_existing_urls():
    existing = {}
    if os.path.exists(ALBUM_FILE):
        with open(ALBUM_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if " : " in line:
                    name, url = line.strip().split(" : ", 1)
                    existing[name.strip()] = url.strip()
    return existing

def search_album(driver, album_name, is_first_search=False):
    query = f"{album_name} movie mp3 songs download telugu site:naasongs.com.co"
    print(f"\n🎧 Album: {album_name}")
    print(f"🔍 Searching: {query}")

    driver.get("https://www.google.com")
    time.sleep(2)

    try:
        box = driver.find_element(By.NAME, "q")
        box.clear()
        box.send_keys(query)
        box.submit()
    except NoSuchElementException:
        print("❌ Search box not found. Skipping.")
        return "NOT FOUND"

    if is_first_search:
        print("🛑 Please complete any verification (CAPTCHA) in 15 seconds if shown...")
        time.sleep(15)

    print("⏳ Waiting for results...")

    for _ in range(SEARCH_WAIT_TIMEOUT):
        try:
            links = driver.find_elements(By.CSS_SELECTOR, 'a')
            for link in links:
                href = link.get_attribute("href")
                if href and "naasongs.com.co" in href:
                    parsed = urlparse(href)
                    if parsed.netloc.startswith("naasongs.com.co") and ".html" in href:
                        print(f"  ✅ Found: {href}")
                        return href
        except Exception:
            pass
        time.sleep(1)

    print("  ❌ No results found or structure changed.")
    return "NOT FOUND"

def main():
    print("📂 Reading album folders...")
    folders = get_album_folders()
    print(f"📁 Found {len(folders)} folders.")

    existing_urls = load_existing_urls()
    driver = setup_driver()

    try:
        with open(ALBUM_FILE, "a", encoding="utf-8") as file:
            for idx, album in enumerate(folders):
                if album in existing_urls:
                    print(f"⏩ Skipping already processed: {album}")
                    continue

                url = search_album(driver, album, is_first_search=(idx == 0))
                file.write(f"{album} : {url}\n")
                file.flush()
    finally:
        driver.quit()

    print("\n✅ Done. All URLs saved to:", ALBUM_FILE)

if __name__ == "__main__":
    main()
