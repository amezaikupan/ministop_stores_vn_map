import argparse
from .core import geocode_with_selenium

def main():
    parser = argparse.ArgumentParser(description="Geocode addresses with Selenium + Google Maps")
    parser.add_argument("--input", required=True, help="Path to input CSV with a `search_col` column")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    parser.add_argument("--search_col", required=True, help="Columns of location used for search")
    parser.add_argument("--visible", action="store_true", help="Run Chrome visibly")
    parser.add_argument("--wait", type=int, default=3, help="Seconds to wait for URL stabilization")
    args = parser.parse_args()

    geocode_with_selenium(
        input_csv=args.input,
        output_csv=args.output,
        search_col=args.search_col,
        headless=not args.visible,
        stabilization_wait=args.wait
    )

if __name__ == "__main__":
    main()
