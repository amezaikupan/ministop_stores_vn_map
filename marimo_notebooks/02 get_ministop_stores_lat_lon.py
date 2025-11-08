import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _(INPUT_CSV, OUTPUT_CSV, pd):
    output_data = pd.read_csv(OUTPUT_CSV).rename(columns={'address': 'name'})
    input_data = pd.read_csv(INPUT_CSV).rename(columns={"Location": "address"})

    output_data['address'] = input_data['address']
    output_data.to_csv("data/1 interim/02_ministop_stores_geocoded_with_extra_addr.csv")
    return


@app.cell
def _():
    # geocode_selenium_google_maps.py
    import pandas as pd
    import time
    import re
    import random
    from urllib.parse import urlparse
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options

    INPUT_CSV = "data/0 raw/ministop_stores_information.csv"
    OUTPUT_CSV = "data/1 interim/01_ministop_stores_geocoded.csv"

    def init_driver(headless=True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--lang=en-US")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_window_size(1200, 900)
        return driver

    def parse_latlon_from_maps_url(url):
        # Google Maps URLs often contain an @lat,lon,zoom segment
        m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if m:
            return float(m.group(1)), float(m.group(2))
        # Some other url forms: look for /data=!3m1!4b1!4m5!3m4!1s...!8m2!3dLAT!4dLON
        m2 = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
        if m2:
            return float(m2.group(1)), float(m2.group(2))
        return None, None

    def detect_gmaps_type(url: str) -> str:
        path = urlparse(url).path
        if "/maps/dir/" in path:
            return "directions"
        if "/maps/search/" in path:
            return "search"
        if "/maps/place/" in path:
            if "!4m" in url:
                return "search+selected_place"
            if "!3m1!4b1" in url or "!1s" in url:
                return "direct_place"
            return "place_unknown_detail"
        if re.search(r"/maps/@-?\d+\.\d+,-?\d+\.\d+", path):
            return "coordinate_view"
        return "unknown"

    def extract_address_from_page(driver, wait):
        """Extract address text from the .fdkmkc class"""
        try:
            # Wait a moment for the address to load
            time.sleep(1)

            # Try to find the address element
            address_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".fdkmkc"))
            )
            address_text = address_element.text.strip()
            print(f"  → Address found: {address_text}")
            return address_text
        except Exception as e:
            print(f"  → Could not extract address: {e}")
            return None

    def click_first_search_result(driver, wait):
        """Attempt to click the first search result from search results list"""
        try:
            # Wait for search results container
            time.sleep(2)  # Give results time to populate

            # Try multiple selectors for first result
            selectors = [
                "a[href*='/maps/place/']",  # Links to places
                "div[role='article']",  # Article cards in results
                "div.Nv2PK",  # Common class for result items (may change)
            ]

            for selector in selectors:
                try:
                    first_result = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    first_result.click()
                    print("  → Clicked first search result")
                    return True
                except Exception:
                    continue

            print("  → Could not find clickable first result")
            return False
        except Exception as e:
            print(f"  → Error clicking first result: {e}")
            return False

    def geocode_with_selenium(input_csv=INPUT_CSV, output_csv=OUTPUT_CSV, headless=True):
        df = pd.read_csv(input_csv)
        driver = init_driver(headless=headless)
        wait = WebDriverWait(driver, 15)
        results = []

        try:
            for idx, addr in enumerate(df['Name'].astype(str), 1):
                print(f"[{idx}/{len(df)}] Geocoding:", addr)
                driver.get("https://www.google.com/maps")

                # Wait for the search box
                try:
                    search_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
                except Exception:
                    search_box = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input[aria-label='Search Google Maps']")
                    ))

                # Clear and type address
                search_box.clear()
                search_box.send_keys(addr)

                # Click search button
                search_button = driver.find_element(By.ID, "searchbox-searchbutton")
                search_button.click()

                # Wait for URL to update and determine result type
                lat, lon = None, None
                extracted_address = None
                url_type = "unknown"

                for attempt in range(30):  # up to ~15s
                    time.sleep(0.5)
                    current_url = driver.current_url
                    url_type = detect_gmaps_type(current_url)

                    print(f"  → URL type: {url_type}")

                    if url_type in ["direct_place", "search+selected_place", "place_unknown_detail"]:
                        # Direct place match - extract coordinates immediately
                        lat, lon = parse_latlon_from_maps_url(current_url)
                        if lat and lon:
                            print(f"  ✓ Direct place found: ({lat}, {lon})")
                            # Extract address from the page
                            extracted_address = extract_address_from_page(driver, wait)
                            break

                    elif url_type == "search":
                        # Search results page - need to click first result
                        print("  → Search results detected, clicking first result...")
                        if click_first_search_result(driver, wait):
                            # Wait for place page to load
                            time.sleep(2)
                            current_url = driver.current_url
                            lat, lon = parse_latlon_from_maps_url(current_url)
                            if lat and lon:
                                print(f"  ✓ Coordinates from first result: ({lat}, {lon})")
                                # Extract address from the page
                                extracted_address = extract_address_from_page(driver, wait)
                                break
                        else:
                            # Fallback: try to extract from search page URL if available
                            lat, lon = parse_latlon_from_maps_url(current_url)
                            if lat and lon:
                                print(f"  ✓ Coordinates from search URL: ({lat}, {lon})")
                            break

                    elif url_type == "coordinate_view":
                        # Coordinate view - extract directly
                        lat, lon = parse_latlon_from_maps_url(current_url)
                        if lat and lon:
                            print(f"  ✓ Coordinate view: ({lat}, {lon})")
                            break

                    # If we got coordinates from any method, break
                    if lat and lon:
                        break

                if not lat or not lon:
                    print(f"  ✗ Failed to extract coordinates (URL type: {url_type})")

                # Save result
                results.append({
                    "address": addr,
                    "extracted_address": extracted_address,
                    "latitude": lat,
                    "longitude": lon,
                    "url": current_url,
                    "url_type": url_type
                })

                # Polite delay between requests
                time.sleep(1 + random.random() * 2)

        finally:
            driver.quit()

        out_df = pd.DataFrame(results)
        out_df.to_csv(output_csv, index=False)
        print(f"\nSaved Selenium geocoded results to {output_csv}")

        # Print summary
        success = out_df['latitude'].notna().sum()
        address_success = out_df['extracted_address'].notna().sum()
        total = len(out_df)
        print(f"Coordinates success rate: {success}/{total} ({success/total*100:.1f}%)")
        print(f"Address extraction success rate: {address_success}/{total} ({address_success/total*100:.1f}%)")

    if __name__ == "__main__":
        geocode_with_selenium(headless=True)
    return INPUT_CSV, OUTPUT_CSV, pd


if __name__ == "__main__":
    app.run()
