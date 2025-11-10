import plotly.express as px 
import geopandas as gpd
import os 

BASE_DIR = os.path.dirname(__file__)
GEO_PATH = os.path.join(BASE_DIR, "vn_map.geojson")
vn_geo_json = gpd.read_file(GEO_PATH)

def draw_point_map(data, lat_col='latitude', lon_col='longitude', point_color='red', point_size=8, outline_color='white', outline_width=2):
    """
    Draw Vietnam map with scatter points using plotly with OpenStreetMap base layer.
    
    Parameters: 
        data (pd.DataFrame): Data with latitude and longitude columns
        lat_col (str): Name of latitude column in data (default: 'latitude')
        lon_col (str): Name of longitude column in data (default: 'longitude')
        point_color (str): Color of the scatter points (default: 'red')
                          Can be color name, hex code, or column name for color mapping
        point_size (int): Size of the scatter points (default: 8)
        outline_color (str): Color of the point outline/border (default: 'white')
        outline_width (int): Width of the point outline in pixels (default: 2)
    
    Returns: 
        Plotly scatter map object
    """
    
    # Add padding to bounds
    padding = 0.1  # degrees of padding
    
    # Check if point_color is a column name in data
    color_param = point_color if point_color in data.columns else None
    
    # Use scatter_mapbox instead of scatter_geo for OSM support
    fig = px.scatter_mapbox(
        data,
        lat=lat_col,
        lon=lon_col,
        hover_name='name', 
        hover_data={'name': True, 'address': True},
      
        color=color_param,  # Use column for color mapping if available
        size_max=point_size
    )
    
    # If point_color is not a column, set it as a fixed color
    if color_param is None:
        fig.update_traces(marker=dict(color=point_color, size=point_size))
    
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

def export_to_svg(fig, output_path='map_output.svg', width=1200, height=600):
    """
    Export the plotly figure to SVG format.
    
    Parameters:
        fig: Plotly figure object
        output_path (str): Path where SVG file will be saved (default: 'map_output.svg')
        width (int): Width of the exported SVG in pixels (default: 1200)
        height (int): Height of the exported SVG in pixels (default: 600)
    
    Returns:
        str: Path to the saved SVG file
    """
    fig.write_image(output_path, format='svg', width=width, height=height)
    print(f"Map exported to: {output_path}")
    return output_path