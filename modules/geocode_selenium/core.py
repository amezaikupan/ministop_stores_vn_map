import pandas as pd
import time
import random
import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .driver import init_driver
from .utils import (
    clean_google_maps_url,
    parse_latlon_from_maps_url,
    detect_gmaps_type,
    extract_address_from_page,
    click_first_search_result
)

# ---------------- Logging Setup ---------------- #
def setup_logging(log_file="data/logs/02_geocoding_log.txt"):
    logger = logging.getLogger("geocoder")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    import os
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

# ---------------- Main Function ---------------- #
def geocode_with_selenium(input_csv, output_csv, search_col, log_file, headless=True, stabilization_wait=3):
    """
    Geocode a list of location names using Selenium + Google Maps.
    
    Parameters
    ----------
    input_csv : str
        Path to a CSV file containing at least a `search_col` column.
        Example:
            Name
            Ministop Nguyen Trai
            Ministop Le Lai

    output_csv : str
        Path to write results with latitude, longitude, cleaned URL, etc.
    
    search_col: str 
        Columns with location data used for search.

    log_file: str 
        Path to write logs.

    headless : bool, optional
        Run Chrome in headless mode (default: True)

    stabilization_wait : int, optional
        Number of seconds to wait for URL stabilization after navigation.

    Returns
    -------
    pandas.DataFrame
        Geocoded results with columns:
        ['address', 'extracted_address', 'latitude', 'longitude', 'url', 'cleaned_url', 'url_type']
    """
    logger = setup_logging(log_file=log_file)
     
    df = pd.read_csv(input_csv)
    driver = init_driver(headless=headless)
    wait = WebDriverWait(driver, 15)
    results = []

    try:
        for idx, addr in enumerate(df[search_col].astype(str), 1):
            logger.info(f"\n[{idx}/{len(df)}] Geocoding: {addr}")
            driver.get("https://www.google.com/maps")

            search_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
            search_box.clear()
            search_box.send_keys(addr)
            driver.find_element(By.ID, "searchbox-searchbutton").click()
            logger.info("  → Waiting for search results to load...")
            time.sleep(3)

            first_url = driver.current_url
            logger.info(f"  → Initial URL (full):\n     {first_url}")
            url_type = detect_gmaps_type(first_url)
            logger.info(f"  → URL type: {url_type}")

            if url_type == "search":
                logger.info("  → Search results page detected, clicking first result...")
                if click_first_search_result(driver, wait):
                    # Wait for page transition after click
                    logger.info("  → Waiting for place page to load after click...")
                    time.sleep(2)
                    intermediate_url = driver.current_url
                    logger.info(f"  → URL after click (full):\n     {intermediate_url}")
                else:
                    intermediate_url = first_url
            else:
                # Direct place or other
                intermediate_url = first_url

            logger.info("  → Cleaning Google Maps URL...")
            try:
                cleaned_url = clean_google_maps_url(intermediate_url)
                logger.info("  → Navigating to cleaned URL...")
                driver.get(cleaned_url)
                logger.info("  → Start waiting to stablize URL")
                time.sleep(stabilization_wait)
                logger.info("  → Stop waiting to stablize URL")

                final_url = driver.current_url
            except Exception as e:
                logger.warning(f"Error cleaning/navigating URL: {e}")
                final_url = intermediate_url
                cleaned_url = None

            lat, lon = parse_latlon_from_maps_url(final_url)
            logger.info(f' -> Lat: {lat}, Lon: {lon}')
            extracted_address = extract_address_from_page(driver, wait)
            results.append({
                "address": addr,
                "extracted_address": extracted_address,
                "latitude": lat,
                "longitude": lon,
                "url": final_url,
                "cleaned_url": cleaned_url,
                "url_type": detect_gmaps_type(final_url),
            })

            time.sleep(1 + random.random() * 2)
    finally:
        driver.quit()

    out_df = pd.DataFrame(results)
    out_df.to_csv(output_csv, index=False)
    logger.info(f"✅ Saved geocoded results to {output_csv}")

    return out_df

def geocode_from_urls(input_csv, output_csv, url_col, log_file, headless=True, stabilization_wait=3):
    """
    Extract geocoding data from Google Maps URLs using Selenium.
    
    Parameters
    ----------
    input_csv : str
        Path to a CSV file containing at least a `url_col` column with Google Maps URLs.
        Example:
            Name,URL
            Ministop Nguyen Trai,https://www.google.com/maps/place/...
            Ministop Le Lai,https://maps.google.com/?q=...

    output_csv : str
        Path to write results with latitude, longitude, cleaned URL, etc.
    
    url_col: str 
        Column name containing Google Maps URLs.

    log_file: str 
        Path to write logs.

    headless : bool, optional
        Run Chrome in headless mode (default: True)

    stabilization_wait : int, optional
        Number of seconds to wait for URL stabilization after navigation.

    Returns
    -------
    pandas.DataFrame
        Geocoded results with columns:
        ['input_url', 'extracted_address', 'latitude', 'longitude', 'final_url', 'cleaned_url', 'url_type']
    """
    logger = setup_logging(log_file=log_file)
     
    df = pd.read_csv(input_csv)
    driver = init_driver(headless=headless)
    wait = WebDriverWait(driver, 15)
    results = []

    try:
        for idx, url in enumerate(df[url_col].astype(str), 1):
            logger.info(f"\n[{idx}/{len(df)}] Processing URL: {url}")
            
            # Navigate directly to the URL
            try:
                driver.get(url)
                logger.info("  → Waiting for page to load...")
                time.sleep(2)
            except Exception as e:
                logger.error(f"  → Error loading URL: {e}")
                results.append({
                    "input_url": url,
                    "extracted_address": None,
                    "latitude": None,
                    "longitude": None,
                    "final_url": None,
                    "cleaned_url": None,
                    "url_type": None,
                    "error": str(e)
                })
                continue

            initial_url = driver.current_url
            logger.info(f"  → Current URL after load:\n     {initial_url}")
            url_type = detect_gmaps_type(initial_url)
            logger.info(f"  → URL type: {url_type}")

            # Handle search results pages
            if url_type == "search":
                logger.info("  → Search results page detected, clicking first result...")
                if click_first_search_result(driver, wait):
                    logger.info("  → Waiting for place page to load after click...")
                    time.sleep(2)
                    intermediate_url = driver.current_url
                    logger.info(f"  → URL after click:\n     {intermediate_url}")
                else:
                    logger.warning("  → Could not click first result, using current URL")
                    intermediate_url = initial_url
            else:
                intermediate_url = initial_url

            # Clean and navigate to cleaned URL
            logger.info("  → Cleaning Google Maps URL...")
            try:
                cleaned_url = clean_google_maps_url(intermediate_url)
                logger.info("  → Navigating to cleaned URL...")
                driver.get(cleaned_url)
                logger.info(f"  → Waiting {stabilization_wait}s for URL to stabilize...")
                time.sleep(stabilization_wait)

                final_url = driver.current_url
            except Exception as e:
                logger.warning(f"  → Error cleaning/navigating URL: {e}")
                final_url = intermediate_url
                cleaned_url = None

            # Extract coordinates and address
            lat, lon = parse_latlon_from_maps_url(final_url)
            logger.info(f'  → Lat: {lat}, Lon: {lon}')
            extracted_address = extract_address_from_page(driver, wait)
            
            results.append({
                "input_url": url,
                "extracted_address": extracted_address,
                "latitude": lat,
                "longitude": lon,
                "final_url": final_url,
                "cleaned_url": cleaned_url,
                "url_type": detect_gmaps_type(final_url),
            })

            # Random delay between requests
            time.sleep(1 + random.random() * 2)
            
    finally:
        driver.quit()

    out_df = pd.DataFrame(results)
    out_df.to_csv(output_csv, index=False)
    logger.info(f"✅ Saved geocoded results to {output_csv}")

    return out_df