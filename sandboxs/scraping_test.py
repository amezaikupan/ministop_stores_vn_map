import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _():
    # from modules.geocode_selenium.core import geocode_with_selenium
    # LOG_FILE = "data/logs/geocoding_log.txt"

    # geocode_with_selenium(
    #     input_csv="data/0 raw/ministop_stores_information.csv",
    #     output_csv="data/geocoded.csv",
    #     search_col='Name',
    #     log_file=LOG_FILE
    # )
    return


@app.cell
def _():
    import pandas as pd
    INPUT_CSV = "data/0 raw/ministop_stores_information.csv"
    OUTPUT_CSV = "data/1 interim/01_ministop_stores_geocoded.csv"
    ADD_ADDR_OUTPUT_CSV = "data/1 interim/02_temp_ministop_stores_geocoded_with_extra_addr.csv"

    output_data = pd.read_csv(OUTPUT_CSV).rename(columns={'address': 'name'})
    input_data = pd.read_csv(INPUT_CSV).rename(columns={"Location": "address"})

    output_data['address'] = input_data['address']
    output_data.to_csv(ADD_ADDR_OUTPUT_CSV)
    return


if __name__ == "__main__":
    app.run()
