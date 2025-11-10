import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _():
    from modules.geocode_selenium.core import geocode_with_selenium

    geocode_with_selenium(
        input_csv="data/0 raw/ministop_stores_information.csv",
        output_csv="data/geocoded.csv",
        search_col='Name'
    )
    return


if __name__ == "__main__":
    app.run()
