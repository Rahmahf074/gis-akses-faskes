# Open-Source Spatial Analysis: Health-Facility Access & Candidate Site Selection

Case study for the *Informatics Practitioner Lecture Series* session
"Career and Competition in Industrial Era with GIS" (Universitas Bengkulu).

## Idea from the lecture
Informatics graduates add value to GIS through **programming, data handling and automation**, using **open data** and **open-source tools** instead of manual, siloed workflows.
This project automates a typical GIS-analyst task end to end with Python: open data -> spatial analysis -> decision-support map.

## Question
Which schools (a proxy for community locations) are farther than R metres from the nearest hospital/clinic, and where would **k new facilities** reach the most uncovered schools?

## Pipeline
| Step | Module | Output |
|---|---|---|
| Fetch open data (OpenStreetMap via Overpass API) | `src/fetch_data.py` | `data/raw/*.geojson` |
| Project to metric CRS, nearest-facility distance | `src/analyze.py` | `results/school_access.csv` |
| Maximum-coverage site selection (greedy) | `src/analyze.py` | `results/summary.json` |
| Interactive map | `src/analyze.py` | `results/map.html` |

## Run
```bash
pip install -r requirements.txt
python -m src.fetch_data                 # or: --bbox S W N E
python -m src.analyze --radius 3000 --k 3
# open results/map.html in a browser
```
`python -m src.demo_data` writes **random synthetic points** to test the pipeline offline. Never use it for reporting.

## Results
> TODO: paste `results/summary.json`, a screenshot of `map.html`, and discuss which areas look underserved and why the suggested sites make sense (or not).

## Limitations (important)
- Distances are **straight-line**, not road-network travel time.
- Schools are only a **proxy for population**; no census data is used. Results indicate a method, not a verified planning recommendation.
- OpenStreetMap completeness varies; missing facilities make coverage look worse than reality.
- The greedy algorithm is not guaranteed optimal.
- The bounding box and the 3 km radius are assumptions; check the box on a map. UTM 48S (EPSG:32748) is used for metres, verify it suits your study area.

## Possible extension (from the lecture)
Store layers in PostgreSQL/PostGIS and publish the map as a web app. Not implemented here.

Data: (c) OpenStreetMap contributors, ODbL.
