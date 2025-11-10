import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # Notebook 2: Getting latitude/longitude of Ministop stores with `Google maps`

    The data from *Notebook 1* will be used to search on `Google maps` to identify their geographical location on the map. The code is a bit long so I break it down to a module call `geocode_selenium`

    The following is a simple documentation written by Chat GPT.

    ----

    This guide explains how to organize, document, and use a Python module that can be imported and run from anywhere.

    ## Project Structure
    ```
    my_module/
    │
    ├── core.py          # Core logic of your module
    ├── utils.py         # Helper functions or shared utilities
    ├── driver.py        # Entry point functions or scripts
    ├── __init__.py      # Makes this directory a package
    ├── __main__.py      # Allows `python -m my_module` execution
    └── setup.py         # Installation configuration
    ```

    ### `core.py`

    Defines the main functionality of the module.
    You can import and use its functions anywhere.

    ```
    # core.py
    def run_core():
        print("Running core logic...")

    ```

    ### `utils.py`

    Contains helper functions or small tools used across the package.

    ### `driver.py`

    Sets up and configures the Chrome WebDriver.

    ### `__init__.py`

    Makes the directory a Python package.


    ### `__main__.py`

    Enables running your module directly with:

    ```
    python -m my_module
    ```

    ```
    # __main__.py
    from .driver import main

    if __name__ == "__main__":
        main()
    ```

    ### `setup.py`

    Allows you to install the package locally or share it. After setup, you can install it locally:

    ```
    pip install -e .
    ```

    And run it anywhere with:
    ```
    geocode_selenium
    ```
    """)
    return


@app.cell
def _(INPUT_CSV, OUTPUT_CSV):
    import pandas as pd 
    ADD_ADDR_OUTPUT_CSV = "data/1 interim/02_ministop_stores_geocoded_with_extra_addr.csv"

    output_data = pd.read_csv(OUTPUT_CSV).rename(columns={'address': 'name'})
    input_data = pd.read_csv(INPUT_CSV).rename(columns={"Location": "address"})

    output_data['address'] = input_data['address']
    output_data.to_csv(ADD_ADDR_OUTPUT_CSV)
    return


@app.cell
def _():
    import sys 
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parents[1] / "modules/"))

    from geocode_selenium.core import geocode_with_selenium

    INPUT_CSV = "data/0 raw/ministop_stores_information.csv"
    OUTPUT_CSV = "data/1 interim/01_ministop_stores_geocoded.csv"
    LOG_FILE = "data/logs/geocoding_log.txt"

    geocode_with_selenium(
        input_csv=INPUT_CSV,
        output_csv=OUTPUT_CSV,
        search_col='Name',
        log_file=LOG_FILE
    )

    return INPUT_CSV, OUTPUT_CSV


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
