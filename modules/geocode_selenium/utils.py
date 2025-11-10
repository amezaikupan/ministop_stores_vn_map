import re
from urllib.parse import urlparse, quote, unquote
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def clean_google_maps_url(url: str) -> str:
    url = unquote(url)
    name_match = re.search(r'/maps/place/([^/@]+)', url)
    name = name_match.group(1) if name_match else "Unknown"
    coords_match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
    lat, lon = coords_match.groups() if coords_match else ("0", "0")
    cid_match = re.search(r'!1s(0x[0-9a-f]+:[0-9a-fx]+)', url)
    cid = cid_match.group(1) if cid_match else ""
    gid_match = re.search(r'!16s(/g/[A-Za-z0-9_-]+)', url)
    gid = gid_match.group(1) if gid_match else ""
    return (f"https://www.google.com/maps/place/{quote(name)}"
            f"/@{lat},{lon},17z/data=!3m1!4b1!4m6!3m5!1s{cid}!8m2!3d{lat}!4d{lon}!16s{quote(gid)}")

def parse_latlon_from_maps_url(url):
    for pattern in [r'@(-?\d+\.\d+),(-?\d+\.\d+)', r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)']:
        m = re.search(pattern, url)
        if m:
            return float(m.group(1)), float(m.group(2))
    return None, None

def detect_gmaps_type(url: str) -> str:
    path = urlparse(url).path
    if "/maps/dir/" in path:
        return "directions"
    if "/maps/search/" in path:
        return "search"
    if "/maps/place/" in path:
        return "place"
    return "unknown"

def extract_address_from_page(driver, wait):
    try:
        elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".fdkmkc")))
        return elem.text.strip()
    except Exception:
        return None

def click_first_search_result(driver, wait):
    for selector in ["a[href*='/maps/place/']", "div[role='article']", "div.Nv2PK"]:
        try:
            elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            elem.click()
            return True
        except Exception:
            continue
    return False
