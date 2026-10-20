"""Analisis spasial: akses ke fasilitas kesehatan + usulan lokasi baru (maximum coverage, greedy).

Jarak = garis lurus (Euclidean) di CRS metrik, BUKAN jarak jalan.
Titik demand = sekolah (proxy sebaran komunitas), bukan data populasi.
"""
import argparse
import json
from pathlib import Path

import folium
import geopandas as gpd
import numpy as np

CRS_M = "EPSG:32748"  # UTM 48S (meter) - verifikasi cocok dengan area studimu


def load(path):
    return gpd.read_file(path).to_crs(CRS_M)


def nearest_distance(demand, fac):
    nn = gpd.sjoin_nearest(demand[["geometry"]], fac[["geometry"]], distance_col="dist_m", how="left")
    nn = nn[~nn.index.duplicated()]
    out = demand.copy()
    out["dist_m"] = nn["dist_m"]
    return out


def greedy_sites(uncovered, candidates, k, radius):
    if len(uncovered) == 0:
        return []
    c = np.c_[candidates.geometry.x, candidates.geometry.y]
    u = np.c_[uncovered.geometry.x, uncovered.geometry.y]
    cover = np.sqrt(((c[:, None, :] - u[None, :, :]) ** 2).sum(-1)) <= radius
    remaining = np.ones(len(u), bool)
    chosen = []
    for _ in range(k):
        gains = (cover & remaining).sum(1)
        i = int(gains.argmax())
        if gains[i] == 0:
            break
        chosen.append((i, int(gains[i])))
        remaining &= ~cover[i]
    return chosen


def main(radius, k):
    health, schools = load("data/raw/health.geojson"), load("data/raw/schools.geojson")
    d = nearest_distance(schools, health)
    d["covered"] = d["dist_m"] <= radius
    unc = d[~d["covered"]]
    picks = greedy_sites(unc, schools, k, radius)
    sites = schools.iloc[[i for i, _ in picks]].copy() if picks else schools.iloc[0:0].copy()
    sites["newly_covered"] = [g for _, g in picks]

    summary = {
        "radius_m": radius, "n_health": len(health), "n_schools": len(schools),
        "coverage_pct_before": round(100 * d["covered"].mean(), 1),
        "mean_dist_m": round(float(d["dist_m"].mean()), 0),
        "n_uncovered": int(len(unc)),
        "recommended_sites": int(len(sites)),
        "coverage_pct_after": round(100 * (d["covered"].sum() + sites["newly_covered"].sum()) / len(d), 1),
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/summary.json").write_text(json.dumps(summary, indent=2))
    d.to_crs(4326).drop(columns="geometry").assign(
        lon=d.to_crs(4326).geometry.x, lat=d.to_crs(4326).geometry.y).to_csv("results/school_access.csv", index=False)

    wgs = lambda g: g.to_crs(4326)
    m = folium.Map(location=[wgs(schools).geometry.y.mean(), wgs(schools).geometry.x.mean()],
                   zoom_start=12, tiles="OpenStreetMap")
    for _, r in wgs(health).iterrows():
        folium.CircleMarker([r.geometry.y, r.geometry.x], radius=6, color="blue", fill=True,
                            tooltip=f"Faskes: {r['name']}").add_to(m)
    for _, r in wgs(d).iterrows():
        folium.CircleMarker([r.geometry.y, r.geometry.x], radius=3,
                            color="green" if r["covered"] else "red", fill=True,
                            tooltip=f"{r['name']} - {r['dist_m']:.0f} m").add_to(m)
    for _, r in wgs(sites).iterrows():
        folium.Marker([r.geometry.y, r.geometry.x], icon=folium.Icon(color="orange", icon="star"),
                      tooltip=f"Usulan lokasi (+{r['newly_covered']} sekolah)").add_to(m)
    m.save("results/map.html")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=float, default=3000, help="radius akses (meter), asumsi")
    ap.add_argument("--k", type=int, default=3, help="jumlah lokasi baru")
    a = ap.parse_args()
    main(a.radius, a.k)
