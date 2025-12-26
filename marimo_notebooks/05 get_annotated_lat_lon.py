import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys 
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parents[1] / "modules/"))

    from geocode_selenium.core import geocode_from_urls

    INPUT_CSV = "data/1 interim/04_ministop_stores_review_annotated.csv"
    OUTPUT_CSV = "data/1 interim/05_ministop_stores_review_annotated_lat_lon.csv"
    LOG_FILE = "data/logs/geocoding_log_review.txt"

    geocode_from_urls(
        input_csv=INPUT_CSV,
        output_csv=OUTPUT_CSV,
        url_col='annotated_url',
        log_file=LOG_FILE
    )
    return


if __name__ == "__main__":
    app.run()
