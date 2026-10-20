"""Ambil data terbuka OpenStreetMap (Overpass API): fasilitas kesehatan & sekolah.
Data (c) OpenStreetMap contributors, lisensi ODbL.
BBOX = (south, west, north, east) - PERIKSA ulang di peta, sesuaikan area studi.
"""
import argparse
from pathlib import Path

import geopandas as gpd
import requests
from shapely.geometry import Point

URL = "https://overpass-api.de/api/interpreter"
DEFAULT_BBOX = (-3.92, 102.19, -3.70, 102.36)  # sekitar Kota Bengkulu (perkiraan)


def query(bbox, tag_regex):
    s, w, n, e = bbox
    q = f'[out:json][timeout:90];nwr["amenity"~"^({tag_regex})$"]({s},{w},{n},{e});out center;'
    r = requests.post(URL, data={"data": q}, timeout=120)
    r.raise_for_status()
    rows = []
    for el in r.json()["elements"]:
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None:
            continue
        rows.append({"name": el.get("tags", {}).get("name", ""), "geometry": Point(lon, lat)})
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bbox", type=float, nargs=4, default=DEFAULT_BBOX,
                    metavar=("S", "W", "N", "E"))
    a = ap.parse_args()
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    health = query(a.bbox, "hospital|clinic")
    schools = query(a.bbox, "school")
    health.to_file("data/raw/health.geojson", driver="GeoJSON")
    schools.to_file("data/raw/schools.geojson", driver="GeoJSON")
    print(f"health facilities: {len(health)} | schools: {len(schools)}")
