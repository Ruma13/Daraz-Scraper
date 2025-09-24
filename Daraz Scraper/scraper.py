import os
import time
import random
import pandas as pd
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# --------------------
# Chrome driver setup
# --------------------
def create_driver(headless=True):
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    if headless:
        options.add_argument("--headless=new")
    driver_path = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# --------------------
# Helper functions
# --------------------
def build_search_url(query_or_url: str) -> str:
    if query_or_url.startswith("http://") or query_or_url.startswith("https://"):
        return query_or_url
    return f"https://www.daraz.com.bd/catalog/?q={quote_plus(query_or_url)}"

def extract_price(text: str):
    import re
    if not text:
        return None
    m = re.search(r'[৳₹$]?[\s\d,]+\.?\d*', text)
    return m.group(0).strip() if m else None

# --------------------
# Main scraping function
# --------------------
def scrape_listing(query_or_url, headless=True, max_items=100, max_scrolls=6):
    driver = create_driver(headless=headless)
    url = build_search_url(query_or_url)
    driver.get(url)

    # Wait for product listings to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href,'/product')]"))
    )

    items, seen = [], set()
    for _ in range(max_scrolls):
        anchors = driver.find_elements(By.XPATH, "//a[contains(@href,'/product')]")
        for a in anchors:
            href = a.get_attribute("href")
            if not href or href in seen:
                continue
            seen.add(href)

            title = a.get_attribute("title") or a.text.strip()
            price, img = None, None

            try:
                parent = a.find_element(By.XPATH, ".//ancestor::div[1]")

                # Price extraction
                try:
                    price_span = parent.find_element(By.XPATH, ".//span[contains(@class,'price')]")
                    price = price_span.text.strip()
                except:
                    price = None

                # Image extraction
                try:
                    img = a.find_element(By.TAG_NAME, "img").get_attribute("src")
                except:
                    img = None

            except NoSuchElementException:
                pass

            items.append({"title": title, "price": price, "url": href, "image": img})
            if len(items) >= max_items:
                break
        if len(items) >= max_items:
            break

        # Scroll down to load more items
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1 + random.random() * 1.5)

    driver.quit()
    return items

# --------------------
# Save to CSV
# --------------------
def save_to_csv(items, filename="static/exports/daraz_products.csv"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    df = pd.DataFrame(items)
    df.to_csv(filename, index=False)
    return filename

# --------------------
# CLI usage
# --------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", "-q", required=True, help="Search query or URL")
    parser.add_argument("--max-items", type=int, default=50)
    parser.add_argument("--out", default="static/exports/daraz_products.csv")
    args = parser.parse_args()

    rows = scrape_listing(args.query, max_items=args.max_items)
    save_to_csv(rows, args.out)
    print(f"Saved {len(rows)} rows to {args.out}")
