"""Ambil data terbuka OpenStreetMap (Overpass API): fasilitas kesehatan & sekolah.
Data (c) OpenStreetMap contributors, lisensi ODbL.
BBOX = (south, west, north, east) - PERIKSA ulang di peta, sesuaikan area studi.
"""
import argparse
import time
from pathlib import Path

import geopandas as gpd
import requests
from shapely.geometry import Point

DEFAULT_BBOX = (-3.92, 102.19, -3.70, 102.36)  # sekitar Kota Bengkulu (perkiraan)
HEADERS = {"User-Agent": "gis-akses-faskes/1.0 (student project; github.com/Rahmahf074/gis-akses-faskes)"}
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]


def _post(q):
    """Coba semua server, ulangi 3 putaran dengan jeda bertambah."""
    last = None
    for attempt in range(3):
        for url in ENDPOINTS:
            try:
                r = requests.post(url, data={"data": q}, headers=HEADERS, timeout=120)
                if r.status_code == 200:
                    print(f"OK: {url}")
                    return r
                last = f"{url} -> HTTP {r.status_code}"
            except requests.RequestException as e:
                last = f"{url} -> {e}"
            print("retry:", last)
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"Semua server Overpass gagal. Terakhir: {last}")


def query(bbox, tag_regex):
    s, w, n, e = bbox
    q = f'[out:json][timeout:90];nwr["amenity"~"^({tag_regex})$"]({s},{w},{n},{e});out center;'
    r = _post(q)
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