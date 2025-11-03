import pandas as pd 
from draw_point_map import draw_point_map

data = pd.read_csv("ministop_stores_full_points.csv", index_col=False)
print(data.head())


fig = draw_point_map(data, lat_col="lat", lon_col="lon")
fig.show()