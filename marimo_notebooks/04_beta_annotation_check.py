import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _(annot_done, pd, plot_data):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    import time, io, base64, pathlib
    import marimo as mo
    import polars as pl 

    # SET UP SELENIUM DRIVER 
    _cache_dir = pathlib.Path("cache")
    _cache_dir.mkdir(exist_ok=True)

    def make_driver():
        opts = Options()
        opts.add_argument("--headless=new")   # new headless mode
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1280,800")
        return webdriver.Chrome(options=opts)

    driver = make_driver()

    def capture_map(url):
        driver.get(url)
        time.sleep(1)             # wait for map to render
        png = driver.get_screenshot_as_png()
        return png                # raw bytes

    def cached_capture(url):
        fname = _cache_dir / f"{get_example['Location']}_{abs(hash(url))}.png"
        if fname.exists():
            return fname.read_bytes()
        png = capture_map(url)
        fname.write_bytes(png)
        return png

    def display_map(url):
        png = capture_map(url)
        encoded = base64.b64encode(png).decode("utf-8")
        return mo.Html(f'<img src="data:image/png;base64,{encoded}" width="600">')

    # SET UP UPDATE FUNCTION
    plot_data_pl = pl.from_pandas(plot_data)
    annot_stream = (_ for _ in plot_data_pl.to_dicts())
    stream_len = len(plot_data_pl)

    get_state, set_state = mo.state(False)
    get_example, set_example = mo.state(next(annot_stream))
    get_annot, set_annot = mo.state([])
    get_perc, set_perc = mo.state(0)
    get_title, set_title = mo.state(f"## Is this the right add? - {get_perc():.2f}%")

    def update(outcome):
        global annot_done
        global driver 
        if get_state():
            print("Annotation is complete. No more update")
            return 

        set_perc(get_perc() + 1/stream_len)
        set_title(f"## Is this the right add? - {get_perc():.2f}%")
        ex = get_example()
        ex["status"] = outcome 
        set_annot(get_annot() + [outcome])

        try:
            set_example(next(annot_stream))
        except StopIteration:
            set_example({
                "name": "", 
                "address": "", 
                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Cat_August_2010-4.jpg/1280px-Cat_August_2010-4.jpg"
            })
            set_title("## Annotation complete!")
            set_state(True)

            plot_data['annotated_url'] = list(get_annot())
            plot_data.to_csv("data/1 interim/04_ministop_stores_review_annotated.csv")

    def export_results():
        pd.DataFrame(list(get_annot())).to_csv("data/1 interim/address_anotation_check.csv", index=False)
    return (
        display_map,
        export_results,
        get_example,
        get_state,
        get_title,
        mo,
        update,
    )


@app.cell
def _(export_results, get_state, mo, update):
    text_box = mo.ui.text(label="Enter corrected url", value="")
    wrong_btn = mo.ui.button(label="Wrong URL!", keyboard_shortcut="Alt-j", on_change=lambda d: update(False), disabled=get_state())
    right_btn = mo.ui.button(label="Right URL!", keyboard_shortcut="Alt-k", on_change=lambda d: update(True), disabled=get_state())
    submit_btn = mo.ui.button(label="Export results!", on_change=export_results())

    def on_submit(value):
        # Do something with the submitted value
        print(f"Submitted value: {value}")

    form = mo.ui.text_area().form(
        clear_on_submit=True,
        on_change=update
    )
    return form, submit_btn


@app.cell
def _(display_map, form, get_example, get_state, get_title, mo, submit_btn):
    def anno_box():
        if get_state() == False:
            return form
        else:
            return mo.vstack([
                mo.md("### Sit down, relax and prepare to go get the real data :')"), 
                submit_btn            
            ])

    mo.vstack([
            mo.md(get_title()),
            mo.vstack([
                get_example()["name"],
                mo.md(f"[{get_example()["address"]}]({get_example()["url"]})"), 
                display_map(get_example()["url"])   # 👈 embedded screenshot here

            ]),
            # text_box,
            anno_box()
        ])
    return


@app.cell
def _():
    import pandas as pd 
    plot_data = pd.read_csv("data/1 interim/03_ministop_stores_review.csv", index_col=False)

    plot_data
    return pd, plot_data


if __name__ == "__main__":
    app.run()
