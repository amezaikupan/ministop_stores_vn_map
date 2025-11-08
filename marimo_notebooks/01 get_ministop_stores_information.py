import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import pandas as pd
    import time
    import re
    import requests
    from bs4 import BeautifulSoup
    from diskcache import Cache

    pages = range(15)
    cache = Cache("stores_cache")
    stores_info = []
    stores_name = []
    stores_err_info = []
    phone_pattern = re.compile(r'(\(0\d{2,3}\)|0\d{2,3})')  # match (028), (029), 090, 091, etc.

    for page in pages:
        base_url = f'https://www.ministop.vn/vi/ms?page={page}'
        print(f"Fetching page {page}...")
        try:
            _res = requests.get(base_url, timeout=10)
            _res.raise_for_status()
        except requests.RequestException as e:
            print(f"⚠️ Failed to fetch page {page}: {e}")
            continue

        _soup = BeautifulSoup(_res.text, "html.parser")
        last_location = None

        stores_name = stores_name + [el.get_text(separator=" ", strip=True) for el in _soup.select("#block-fluffiness-content .views-field-title a")]

        for store in _soup.select("#block-fluffiness-content p"):
            # Convert store element to string for cache key
            store_key = str(store)
            if store_key in cache:
                continue

            spans = [s.get_text(strip=True) for s in store.select("span")]
            raw_text = store.get_text(separator=" ", strip=True)
            location, phone = None, None

            try:
                # ✅ Case 1: multi-span with long location + phone + avail
                if len(spans) >= 3:
                    possible_phone = spans[-2]
                    if phone_pattern.search(possible_phone):
                        phone = possible_phone
                        location = " ".join(spans[:-2])
                    else:
                        phone = spans[-1] if phone_pattern.search(spans[-1]) else ""
                        location = " ".join(spans[:-1])
                    last_location = location

                # ✅ Case 2: text + <span>phone</span><span>avail</span>
                elif len(spans) == 2:
                    if phone_pattern.search(spans[0]) or phone_pattern.search(spans[1]):
                        # extract phone
                        phone = spans[0] if phone_pattern.search(spans[0]) else spans[1]
                        # location is text before phone
                        match = phone_pattern.search(raw_text)
                        location = raw_text[:match.start()].strip() if match else ""
                    else:
                        location = raw_text
                    last_location = location

                # ✅ Case 3: <p><span>location</span></p><p><span>phone</span></p>
                elif len(spans) == 1:
                    text = spans[0]
                    if phone_pattern.search(text):
                        # this is the phone line
                        phone = text
                        location = last_location
                    else:
                        # this is a location line
                        location = text
                        last_location = location

                # ✅ Fallback — handle text mixed with <br> or unwrapped spans
                else:
                    match = phone_pattern.search(raw_text)
                    if match:
                        phone = match.group()
                        location = raw_text[:match.start()].strip()
                    else:
                        location = raw_text
                        last_location = location

                # ✅ store only if phone and location found
                if location and phone:
                    store_info = {
                        "Location": location,
                        "Phone": phone
                    }
                    stores_info.append(store_info)
                    cache[store_key] = store_info

            except Exception as e:
                print(f"⚠️ Error parsing store: {e}")
                stores_err_info.append((raw_text, str(e)))

        time.sleep(1)  # polite delay

    df = pd.DataFrame(stores_info)
    print(df.head(10))
    print(f"✅ Total stores parsed: {len(df)}")
    print(f"⚠️ Errors: {len(stores_err_info)}")
    return df, stores_name


@app.cell
def _(df, stores_name):
    df['Name'] = stores_name
    df[~df['Name'].duplicated()][['Name', 'Location', 'Phone']].to_csv("data/0 raw/ministop_stores_information.csv", index=False)
    return


if __name__ == "__main__":
    app.run()
