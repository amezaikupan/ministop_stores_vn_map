import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # Notebook 2: Getting latitude/longitude of Ministop stores with `Google maps`

    The data from *Notebook 1* will be used to search on `Google maps` to identify their geographical location on the map. The code is a bit long so I break it down to a module call `geocode_selenium`

    The following is a simple documentation written by Chat GPT.

    ----

    This guide explains how to organize, document, and use a Python module that can be imported and run from anywhere.

    ## Project Structure
    ```
    my_module/
    │
    ├── core.py          # Core logic of your module
    ├── utils.py         # Helper functions or shared utilities
    ├── driver.py        # Entry point functions or scripts
    ├── __init__.py      # Makes this directory a package
    ├── __main__.py      # Allows `python -m my_module` execution
    └── setup.py         # Installation configuration
    ```

    ### `core.py`

    Defines the main functionality of the module.
    You can import and use its functions anywhere.

    ```
    # core.py
    def run_core():
        print("Running core logic...")

    ```

    ### `utils.py`

    Contains helper functions or small tools used across the package.

    ### `driver.py`

    Sets up and configures the Chrome WebDriver.

    ### `__init__.py`

    Makes the directory a Python package.


    ### `__main__.py`

    Enables running your module directly with:

    ```
    python -m my_module
    ```

    ```
    # __main__.py
    from .driver import main

    if __name__ == "__main__":
        main()
    ```

    ### `setup.py`

    Allows you to install the package locally or share it. After setup, you can install it locally:

    ```
    pip install -e .
    ```

    And run it anywhere with:
    ```
    geocode_selenium
    ```
    """)
    return


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
    import logging
    from datetime import datetime
    from urllib.parse import urlparse, quote, unquote
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options

    INPUT_CSV = "data/0 raw/ministop_stores_information.csv"
    OUTPUT_CSV = "data/1 interim/01_ministop_stores_geocoded.csv"
    LOG_FILE = "data/logs/geocoding_log.txt"

    # ---------------------- Logging Setup ---------------------- #
    def setup_logging():
        """Setup logging to both file and console"""
        # Create logger
        logger = logging.getLogger('geocoder')
        logger.setLevel(logging.INFO)
    
        # Clear any existing handlers
        logger.handlers.clear()
    
        # Create formatters
        file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', 
                                           datefmt='%Y-%m-%d %H:%M:%S')
        console_formatter = logging.Formatter('%(message)s')
    
        # File handler
        import os
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)
    
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
    
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
        return logger

    logger = setup_logging()

    # ---------------------- Driver setup ---------------------- #
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

    # ---------------------- Utility functions ---------------------- #
    def clean_google_maps_url(url: str) -> str:
        """Clean and normalize Google Maps URL"""
        # Decode the URL for easier parsing
        url = unquote(url)
    
        # 1. Extract visible name
        name_match = re.search(r'/maps/place/([^/@]+)', url)
        name = name_match.group(1) if name_match else "Unknown"
    
        # 2. Extract place coordinates (!3d... !4d...)
        coords_match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
        lat, lon = coords_match.groups() if coords_match else ("0", "0")
    
        # 3. Extract CID (0x...:0x...)
        cid_match = re.search(r'!1s(0x[0-9a-f]+:[0-9a-fx]+)', url)
        cid = cid_match.group(1) if cid_match else ""
    
        # 4. Extract place global ID (!16s/g/...)
        gid_match = re.search(r'!16s(/g/[A-Za-z0-9_-]+)', url)
        gid = gid_match.group(1) if gid_match else ""
    
        # 5. Rebuild clean URL
        clean_url = (
            f"https://www.google.com/maps/place/{quote(name)}"
            f"/@{lat},{lon},17z/"
            f"data=!3m1!4b1!4m6!3m5!1s{cid}!8m2!3d{lat}!4d{lon}!16s{quote(gid)}"
        )
        return clean_url


    def parse_latlon_from_maps_url(url):
        # Google Maps URLs often contain an @lat,lon,zoom segment
        m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if m:
            return float(m.group(1)), float(m.group(2))
        # Alternative !3dLAT!4dLON format
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


    def wait_for_stable_url(driver, timeout=10, stable_duration=2):
        """Wait until URL stops changing for stable_duration seconds.
        Returns the final stable URL and list of URL changes detected."""
        print("  → Waiting for URL to stabilize...")
        start_time = time.time()
        last_url = driver.current_url
        stable_since = time.time()
        url_changes = 0
    
        while time.time() - start_time < timeout:
            time.sleep(0.5)
            current_url = driver.current_url
        
            if current_url != last_url:
                url_changes += 1
                print(f"  → URL changed ({url_changes} times)")
                last_url = current_url
                stable_since = time.time()
            elif time.time() - stable_since >= stable_duration:
                print(f"  ✓ URL stable for {stable_duration}s")
                return current_url
    
        print(f"  ⚠ Timeout reached after {timeout}s")
        return driver.current_url


    def extract_address_from_page(driver, wait):
        """Extract address text from the .fdkmkc class"""
        try:
            # Wait for the address element to be present
            address_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".fdkmkc"))
            )
            address_text = address_element.text.strip()
            logger.info(f"  → Address found: {address_text}")
            return address_text
        except Exception as e:
            logger.warning(f"  → Could not extract address: {e}")
            return None


    def click_first_search_result(driver, wait):
        """Attempt to click the first search result from search results list"""
        try:
            # Try multiple selectors to find the first result
            selectors = [
                "a[href*='/maps/place/']",
                "div[role='article']",
                "div.Nv2PK",
            ]
            for selector in selectors:
                try:
                    first_result = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    first_result.click()
                    logger.info("  → Clicked first search result")
                    return True
                except Exception:
                    continue
            logger.warning("  → Could not find clickable first result")
            return False
        except Exception as e:
            logger.error(f"  → Error clicking first result: {e}")
            return False

    # ---------------------- Main function ---------------------- #
    def geocode_with_selenium(input_csv=INPUT_CSV, output_csv=OUTPUT_CSV, headless=True, stabilization_wait=3):
        df = pd.read_csv(input_csv)
        driver = init_driver(headless=headless)
        wait = WebDriverWait(driver, 15)
        results = []

        try:
            for idx, addr in enumerate(df['Name'].astype(str), 1):
                print(f"\n[{idx}/{len(df)}] Geocoding: {addr}")
                driver.get("https://www.google.com/maps")

                # Wait for the search box and perform search
                try:
                    search_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
                except Exception:
                    search_box = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input[aria-label='Search Google Maps']")
                    ))

                search_box.clear()
                search_box.send_keys(addr)
                driver.find_element(By.ID, "searchbox-searchbutton").click()

                # Wait for page to load after search (brief wait for DOM)
                print("  → Waiting for search results to load...")
                time.sleep(3)
            
                first_url = driver.current_url
                print(f"  → Initial URL (full):\n     {first_url}")
                url_type = detect_gmaps_type(first_url)
                print(f"  → URL type: {url_type}")

                lat, lon, extracted_address = None, None, None
                cleaned_url = None

                # Handle search results page - click first result
                if url_type == "search":
                    print("  → Search results page detected, clicking first result...")
                    if click_first_search_result(driver, wait):
                        # Wait for page transition after click
                        print("  → Waiting for place page to load after click...")
                        time.sleep(2)
                        intermediate_url = driver.current_url
                        print(f"  → URL after click (full):\n     {intermediate_url}")
                    else:
                        intermediate_url = first_url
                else:
                    # Direct place or other
                    intermediate_url = first_url

                # Now clean the URL and navigate to it
                print("  → Cleaning Google Maps URL...")
                try:
                    cleaned_url = clean_google_maps_url(intermediate_url)
                    print(f"  → Cleaned URL (full):\n     {cleaned_url}")
                
                    # Navigate to the cleaned URL
                    print("  → Navigating to cleaned URL...")
                    driver.get(cleaned_url)
                
                    # Wait for page to fully load and URL to stabilize
                    print(f"  → Waiting for page to stabilize ({stabilization_wait} seconds)...")
                    for i in range(stabilization_wait, 0, -1):
                        print(f"     {i}...", end=" ", flush=True)
                        time.sleep(1)
                    print("Done!")
                
                    # Collect final URL
                    final_url = driver.current_url
                    print(f"  → Final URL (full):\n     {final_url}")
                
                except Exception as e:
                    print(f"  ⚠ Error cleaning/navigating URL: {e}")
                    final_url = intermediate_url

                # Parse coordinates from final URL
                lat, lon = parse_latlon_from_maps_url(final_url)
                final_url_type = detect_gmaps_type(final_url)
                print(f"  → Final URL type: {final_url_type}")

                if lat and lon:
                    print(f"  ✓ Coordinates found: ({lat}, {lon})")
                    # Extract address after URL is stable
                    extracted_address = extract_address_from_page(driver, wait)
                else:
                    print("  ✗ Failed to extract coordinates")

                results.append({
                    "address": addr,
                    "extracted_address": extracted_address,
                    "latitude": lat,
                    "longitude": lon,
                    "url": final_url,
                    "cleaned_url": cleaned_url,
                    "url_type": final_url_type
                })

                # Random delay between requests
                time.sleep(1 + random.random() * 2)

        finally:
            driver.quit()

        out_df = pd.DataFrame(results)
        out_df.to_csv(output_csv, index=False)
        print(f"\n{'='*60}")
        print(f"Saved Selenium geocoded results to {output_csv}")

        success = out_df['latitude'].notna().sum()
        total = len(out_df)
        print(f"Coordinates success rate: {success}/{total} ({success/total*100:.1f}%)")
        print(f"{'='*60}")

    if __name__ == "__main__":
        # Default: 3 seconds wait
        geocode_with_selenium(headless=True, stabilization_wait=3)
    
        # Examples for different wait times:
        # geocode_with_selenium(headless=True, stabilization_wait=5)   # 5 seconds
        # geocode_with_selenium(headless=True, stabilization_wait=10)  # 10 seconds
        # geocode_with_selenium(headless=False, stabilization_wait=7)  # 7 seconds, visible browser
    return INPUT_CSV, OUTPUT_CSV, pd


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
