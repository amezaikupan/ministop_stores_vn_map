import plotly.express as px 
import geopandas as gpd
import os 

BASE_DIR = os.path.dirname(__file__)
GEO_PATH = os.path.join(BASE_DIR, "vn_map.geojson")
vn_geo_json = gpd.read_file(GEO_PATH)

def draw_point_map(data, lat_col='latitude', lon_col='longitude'):
    """
    Draw Vietnam map with scatter points using plotly with OpenStreetMap base layer.
    Parameters: 
        data (pd.DataFrame): Data with latitude and longitude columns
        lat_col (str): Name of latitude column in data (default: 'latitude')
        lon_col (str): Name of longitude column in data (default: 'longitude')
    Returns: 
        Plotly scatter map object
    """
    
    # Add padding to bounds
    padding = 0.1  # degrees of padding
    
    # Use scatter_mapbox instead of scatter_geo for OSM support
    fig = px.scatter_mapbox(
        data,
        lat=lat_col,
        lon=lon_col,
        hover_name='Name', 
        hover_data={'Name': True, 'Location': True, 'Phone': True, 'url': False, lat_col: False, lon_col: False}
    )
    
    # Set OpenStreetMap as the base map with padding
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            bounds=dict(
                west=data[lon_col].min() - padding,
                east=data[lon_col].max() + padding,
                south=data[lat_col].min() - padding,
                north=data[lat_col].max() + padding
            )
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,
        autosize=True  # Makes it responsive to container size
    )
    
    return fig