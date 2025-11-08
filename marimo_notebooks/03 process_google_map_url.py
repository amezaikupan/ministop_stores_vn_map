import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _(clean_google_maps_url):
    import pandas as pd 

    data = pd.read_csv('data/1 interim/02_ministop_stores_geocoded_with_extra_addr.csv', index_col=False)
    data['url'] = data['url'].apply(lambda x: clean_google_maps_url(x))
    data.to_csv('data/1 interim/03_ministop_stores_geocoded_fixed_url.csv', index=False)
    return


@app.cell
def _():
    import re
    from urllib.parse import quote, unquote

    def clean_google_maps_url(url: str) -> str:
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
    return (clean_google_maps_url,)


if __name__ == "__main__":
    app.run()
