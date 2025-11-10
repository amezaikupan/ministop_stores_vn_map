import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # Notebook 01: Getting Ministop stores data list from `ministop.vn`

    **Work flow**: Use `SelectorGadget` extension (Chrome App Store) to identify the `html` elements that we're trying to get.
    1. Name of store: `#block-fluffiness-content .views-field-title a`
    2. Address and phone of store: `"#block-fluffiness-content p"`


    Because of inconsistencies in the `html` structure, 4 parsing strategy is used to process store information details. Summarized of approaches is presented in cell below (written by `Claude`).

    ---
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Store Information Parsing Logic

    ## Overview
    This scraper extracts **location** and **phone number** data from Ministop store listings. Due to inconsistent HTML formatting across entries, the parser implements a multi-case strategy to handle different structural patterns.

    ---

    ## Parsing Strategy

    ### Phone Pattern
    ```regex
    (\(0\d{2,3}\)|0\d{2,3})
    ```
    Matches Vietnamese phone formats: `(028)`, `(029)`, `090`, `091`, etc.

    ### Memory Mechanism
    **`last_location`** variable stores the most recent location to handle split entries where location and phone appear in separate `<p>` tags.

    ---

    ## Case Breakdown

    ### **Case 1: Multiple Spans (≥3)**
    **HTML Structure:**
    ```html
    <p><span>123</span> <span>Main St</span> <span>HCMC</span> <span>0281234567</span> <span>Available</span></p>
    ```

    **Processing Logic:**
    1. Check if **2nd-to-last span** contains phone pattern
       - ✅ Phone found → Location = all spans before last 2
       - ❌ Not found → Check **last span** for phone → Location = all spans before last 1
    2. Join location spans with spaces

    **Example Output:**
    - Location: `"123 Main St HCMC"`
    - Phone: `"0281234567"`

    ---

    ### **Case 2: Two Spans**
    **HTML Structure:**
    ```html
    <p>123 Main St, HCMC <span>0281234567</span><span>Available</span></p>
    ```

    **Processing Logic:**
    1. Check if either span contains phone pattern
    2. **If phone found:**
       - Identify which span has the phone
       - Search for phone position in full text
       - Extract everything **before** phone as location
    3. **If no phone:** Treat entire text as location

    **Example Output:**
    - Location: `"123 Main St, HCMC"`
    - Phone: `"0281234567"`

    ---

    ### **Case 3: Single Span**
    **HTML Structure:**
    ```html
    <p><span>123 Main St, HCMC</span></p>
    <p><span>0281234567</span></p>
    ```

    **Processing Logic:**
    1. **If span contains phone pattern:**
       - Phone = span text
       - Location = `last_location` (from previous entry)
       - ✅ **Save store info** (both values present)

    2. **If span does NOT contain phone:**
       - Location = span text
       - Update `last_location` for next iteration
       - ⏭️ Skip saving (no phone yet)

    **Example Output:**
    - Entry 1: Location stored, waiting for phone
    - Entry 2: `("123 Main St, HCMC", "0281234567")` ✅ Saved

    ---

    ### **Case 4: Fallback (No Spans)**
    **HTML Structure:**
    ```html
    <p>123 Main St, HCMC 0281234567</p>
    ```

    **Processing Logic:**
    1. Search for phone pattern in raw text
    2. **If phone found:**
       - Phone = matched text
       - Location = everything before phone position
    3. **If no phone:** Entire text = location

    **Example Output:**
    - Location: `"123 Main St, HCMC"`
    - Phone: `"0281234567"`

    ---

    ## Save Conditions

    ```python
    if location and phone:
        stores_info.append({"Location": location, "Phone": phone})
        cache[store_key] = store_info
    ```

    **Only saves when BOTH location AND phone are present** to ensure data completeness.

    ---

    ## Error Handling

    ### Network Errors
    ```python
    try:
        _res = requests.get(base_url, timeout=10)
        _res.raise_for_status()
    except requests.RequestException as e:
        print(f"⚠️ Failed to fetch page {page}: {e}")
        continue
    ```

    ### Parsing Errors
    ```python
    try:
        # ... parsing logic ...
    except Exception as e:
        print(f"⚠️ Error parsing store: {e}")
        stores_err_info.append((raw_text, str(e)))
    ```

    All errors are logged to `stores_err_info` for later review.

    ---

    ## Optimization Features

    ### Caching
    ```python
    cache = Cache("stores_cache")
    if store_key in cache:
        continue  # Skip already processed stores
    ```
    Prevents re-processing of previously scraped entries across multiple runs.

    ### Polite Scraping
    ```python
    time.sleep(1)  # 1 second delay between pages
    ```
    Respects server resources with rate limiting.

    ---

    ## Output

    ### Success Metrics
    ```python
    print(f"✅ Total stores parsed: {len(df)}")
    print(f"⚠️ Errors: {len(stores_err_info)}")
    ```

    ### Data Structure
    ```python
    df = pd.DataFrame(stores_info)
    # Columns: Location, Phone
    ```

    Ready for analysis, export, or further processing!
    """)
    return


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


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
