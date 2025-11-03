import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _(plot_data):
    import marimo as mo
    import polars as pl 

    plot_data_pl = pl.from_pandas(plot_data)
    annot_stream = (_ for _ in plot_data_pl.to_dicts())
    get_example, set_example = mo.state(next(annot_stream))
    get_annot, set_annot = mo.state([])
    get_perc, set_perc = mo.state(0)

    def update(outcome):
        ex = get_example()
        ex["corrected_url"] = outcome 
        set_annot(get_annot() + [outcome])
        set_example(next(annot_stream))
        set_perc(get_perc() + 1/178)


    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    import time, io, base64

    # --- 1️⃣  Set up headless Chrome ---
    def make_driver():
        opts = Options()
        opts.add_argument("--headless=new")   # new headless mode
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1280,800")
        return webdriver.Chrome(options=opts)

    driver = make_driver()

    # --- 2️⃣  Grab a screenshot from a URL ---
    def capture_map(url):
        driver.get(url)
        time.sleep(2)             # wait for map to render
        png = driver.get_screenshot_as_png()
        return png                # raw bytes

    # --- 3️⃣  Display in Marimo ---
    def display_map(url):
        png = capture_map(url)
        encoded = base64.b64encode(png).decode("utf-8")
        return mo.Html(f'<img src="data:image/png;base64,{encoded}" width="600">')

    return display_map, get_example, get_perc, mo, update


@app.cell
def _(get_example, mo, update):
    text_box = mo.ui.text(label="Enter corrected url", value="")
    wrong_btn = mo.ui.button(label="Wrong URL!", keyboard_shortcut="Ctrl-j", on_change=lambda d: update(text_box.value))
    right_btn = mo.ui.button(label="Right URL!", keyboard_shortcut="Ctrl-k", on_change=lambda d: update(get_example()["url"]))
    return right_btn, text_box, wrong_btn


@app.cell
def _(display_map, get_example, get_perc, mo, right_btn, text_box, wrong_btn):
    mo.vstack([
            mo.md(f"## Is this the right add? - {get_perc():.2f}%"),
            mo.vstack([
                get_example()["Location"],
                mo.md(f"[Address for {get_example()["Name"]}]({get_example()["url"]})"), 
                display_map(get_example()["url"])   # 👈 embedded screenshot here

            ]),
            text_box,
            mo.hstack([
                wrong_btn,
                right_btn
            ], align='start')
        ])
    return


@app.cell
def _():
    import pandas as pd 
    from draw_point_map import draw_point_map


    data = pd.read_csv("ministop_stores_location_data_geocode_w_name.csv", index_col=False).rename(columns={'address': "Name"})
    location_data = pd.read_csv("ministop_stores_location_data_w_name.csv", index_col=False).drop(columns=['Unnamed: 0'])

    plot_data = pd.merge(left=data, right=location_data, on="Name")
    plot_data[plot_data['url'].str.contains("https://www.google.com/maps/search")]
    return (plot_data,)


if __name__ == "__main__":
    app.run()
