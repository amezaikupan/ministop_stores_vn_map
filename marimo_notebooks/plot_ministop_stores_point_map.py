import marimo

__generated_with = "0.17.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import re
    def parse_latlon_from_maps_url(url):
        # Google Maps URLs often contain an @lat,lon,zoom segment:
        # e.g. https://www.google.com/maps/place/.../@10.762622,106.660172,17z/...
        m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if m:
            return float(m.group(1)), float(m.group(2))
        # Some other url forms: look for /data=!3m1!4b1!4m5!3m4!1s...!8m2!3dLAT!4dLON
        m2 = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
        if m2:
            return float(m2.group(1)), float(m2.group(2))
        return None, None
    return (parse_latlon_from_maps_url,)


@app.cell
def _(parse_latlon_from_maps_url):
    import pandas as pd 
    annot_url = pd.read_csv("annotated_map_url.csv", index_col=False).drop(columns=['Unnamed: 0'])

    data = pd.read_csv("ministop_stores_location_data_geocode_w_name.csv")
    data['url'] = annot_url

    data[['lat', 'lon']] = data['url'].apply(lambda x: pd.Series(parse_latlon_from_maps_url(x)))
    data = data.drop(columns=['latitude', 'longitude']).rename(columns={'address': 'Name'})

    location_data = pd.read_csv("ministop_stores_location_data_w_name.csv", index_col=False).drop(columns=['Unnamed: 0'])

    plot_data = pd.merge(left=data, right=location_data, on="Name")
    plot_data[plot_data['url'].str.contains("https://www.google.com/maps/search")]

    plot_data.to_csv("ministop_stores_full_points.csv")
    return (plot_data,)


@app.cell
def _(plot_data):
    from draw_point_map import draw_point_map, export_to_svg

    fig = draw_point_map(plot_data, lat_col='lat', lon_col='lon', point_color='#fff22e', point_size=5, outline_color='#3461a4', outline_width=6)
    fig.show()

    export_to_svg(fig=fig)
    return


if __name__ == "__main__":
    app.run()
