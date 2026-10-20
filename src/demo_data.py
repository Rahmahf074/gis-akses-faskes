"""DATA SINTETIS (acak) hanya untuk menguji pipeline tanpa internet. JANGAN dipakai untuk laporan."""
import geopandas as gpd
import numpy as np
from shapely.geometry import Point

rng = np.random.default_rng(1)
def pts(n):
    return gpd.GeoDataFrame({"name": [f"p{i}" for i in range(n)]},
        geometry=[Point(x, y) for x, y in zip(rng.uniform(102.20, 102.33, n), rng.uniform(-3.88, -3.72, n))],
        crs="EPSG:4326")
pts(12).to_file("data/raw/health.geojson", driver="GeoJSON")
pts(150).to_file("data/raw/schools.geojson", driver="GeoJSON")
print("demo data written")
