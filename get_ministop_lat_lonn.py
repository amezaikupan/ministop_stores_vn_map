import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _(pd):
    # geocode_selenium_google_maps.py
    import time
    import re
    import random
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options

    INPUT_CSV = "ministop_stores_location_data_w_name.csv"
    OUTPUT_CSV = "ministop_stores_location_data.csv_geocoded.csv"

    def init_driver(headless=True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--lang=en-US")
        # helpful for some sites
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_window_size(1200, 900)
        return driver

    def parse_latlon_from_maps_url(url):
        # Google Maps URLs often contain an @lat,lon,zoom segment:
        # e.g. https://www.google.com/maps/place/.../@10.762622,106.660172,17z/...
        m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if m:
            return float(m.group(1)), float(m.group(2))
        # Some other url forms: look for /data=!3m1!4b1!4m5!3m4!1s...!8m2!3dLAT!4dLON
        m2 = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
        if m2:
            return float(m2.group(1)), float(m2.group(2))
        return None, None

    def geocode_with_selenium(input_csv=INPUT_CSV, output_csv=OUTPUT_CSV, headless=True):
        df = pd.read_csv(input_csv)
        driver = init_driver(headless=headless)
        wait = WebDriverWait(driver, 15)

        results = []
        try:
            for addr in df['Name'].astype(str):
                print("Geocoding:", addr)
                driver.get("https://www.google.com/maps")
                # Wait for the search box
                try:
                    search_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
                except Exception:
                    # fallback: try CSS selector
                    search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Search Google Maps']")))
                # Clear and type address
                search_box.clear()
                search_box.send_keys(addr)
                # Click search button
                search_button = driver.find_element(By.ID, "searchbox-searchbutton")
                search_button.click()

                # Wait for the URL to update or for a place panel to appear
                # We'll wait up to 10-15s for coords to appear in URL
                lat, lon = None, None
                for _ in range(30):  # up to ~30 * 0.5s = 15s
                    current_url = driver.current_url
                    lat, lon = parse_latlon_from_maps_url(current_url)
                    if lat and lon:
                        break
                    time.sleep(0.5)

                # Alternative: if place result appears, try to click first result in sidebar (fragile)
                # Save result
                results.append({"address": addr, "latitude": lat, "longitude": lon, "url": current_url})
                # polite delay between requests
                time.sleep(1 + random.random() * 2)
        finally:
            driver.quit()

        out_df = pd.DataFrame(results)
        out_df.to_csv(output_csv, index=False)
        print(f"Saved Selenium geocoded results to {output_csv}")

    if __name__ == "__main__":
        geocode_with_selenium(headless=True)
    return


@app.cell
def _():
    import pandas as pd 
    data = pd.read_csv("ministop_stores_location_data_w_name.csv", index_col=False)
    data.drop(columns=['Unnamed: 0'])
    return (pd,)


if __name__ == "__main__":
    app.run()
