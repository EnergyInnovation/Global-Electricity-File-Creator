"""Fetch multi-year hourly VRE data from renewables.ninja for representative US sites.

Caches each (tech, site, year) CSV in Downloads/ninja_cache/ to avoid re-fetching.
"""
import csv
import os
import time
import urllib.request
import urllib.parse
from pathlib import Path
import datetime as dt

CACHE_DIR = Path(r"C:\Users\RobbieOrvis\Downloads\ninja_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Representative US wind sites (capacity-weighted toward Plains states)
WIND_SITES = [
    ("IA_Iowa",         42.0,  -93.5),   # Iowa, top wind state
    ("TX_Panhandle",    35.5, -101.5),   # Texas Panhandle, largest single capacity
    ("KS_Kansas",       38.5, -100.0),   # Kansas, high CF
    ("OK_Oklahoma",     35.5,  -98.0),   # Oklahoma
    ("ND_NorthDakota",  47.0, -100.0),   # North Dakota, high CF
]

# Representative US solar sites (capacity-weighted)
SOLAR_SITES = [
    ("CA_CentralValley", 36.0, -120.0),  # California, biggest fleet
    ("TX_West",          31.5, -103.0),  # West Texas
    ("AZ_Arizona",       33.0, -111.5),  # Arizona
    ("FL_Florida",       28.0,  -82.0),  # Florida
    ("NC_NorthCarolina", 35.5,  -78.0),  # NC, southeast
]

# Offshore wind sites (limited US fleet, use Atlantic sites)
OFFSHORE_SITES = [
    ("NE_Massachusetts", 41.0,  -70.5),  # Vineyard Wind area
    ("MA_RhodeIsland",   41.3,  -71.0),
    ("NY_NewYorkBight",  40.0,  -73.0),
]

# Years to pull (more years = better tail-event capture)
YEARS = [2019, 2020, 2021, 2022, 2023]   # public API only allows 2019+

HEADERS = {"User-Agent": "Mozilla/5.0 (Energy Innovation EPS calibration)"}


def cache_path(tech: str, site: str, year: int) -> Path:
    return CACHE_DIR / f"{tech}_{site}_{year}.csv"


def _http_get(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read().decode("utf-8")


def fetch_wind(lat: float, lon: float, year: int, offshore: bool = False) -> str:
    """Fetch wind hourly data for one year. Returns CSV text."""
    turbine = "Vestas V164 8000" if offshore else "Vestas V90 2000"
    height = 140 if offshore else 90
    params = {
        "lat": lat, "lon": lon,
        "date_from": f"{year}-01-01",
        "date_to": f"{year}-12-31",
        "capacity": 1000,
        "height": height,
        "turbine": turbine,
        "dataset": "merra2",
        "format": "csv",
    }
    url = "https://www.renewables.ninja/api/data/wind?" + urllib.parse.urlencode(params)
    return _http_get(url)


def fetch_solar(lat: float, lon: float, year: int) -> str:
    """Fetch utility-scale tracking solar PV hourly data."""
    params = {
        "lat": lat, "lon": lon,
        "date_from": f"{year}-01-01",
        "date_to": f"{year}-12-31",
        "capacity": 1000,
        "system_loss": 0.10,
        "tracking": 1,            # single-axis tracking
        "tilt": 0,
        "azim": 180,
        "dataset": "merra2",
        "format": "csv",
    }
    url = "https://www.renewables.ninja/api/data/pv?" + urllib.parse.urlencode(params)
    return _http_get(url)


def fetch_all():
    """Fetch all (tech, site, year) combinations with caching."""
    fetched = 0
    skipped = 0
    for tech_name, sites, fetcher in [
        ("wind", WIND_SITES, lambda lat, lon, year: fetch_wind(lat, lon, year, offshore=False)),
        ("solar", SOLAR_SITES, fetch_solar),
        ("offshore", OFFSHORE_SITES, lambda lat, lon, year: fetch_wind(lat, lon, year, offshore=True)),
    ]:
        for site_name, lat, lon in sites:
            for year in YEARS:
                cp = cache_path(tech_name, site_name, year)
                if cp.exists():
                    skipped += 1
                    continue
                print(f"  Fetching {tech_name} {site_name} {year}...", flush=True)
                try:
                    text = fetcher(lat, lon, year)
                    cp.write_text(text, encoding="utf-8")
                    fetched += 1
                    time.sleep(2.0)  # rate-limit politely
                except Exception as e:
                    print(f"    ERROR: {e}")
                    time.sleep(30)
    print(f"\nFetched: {fetched}, skipped (cached): {skipped}")
    return fetched, skipped


def main():
    print(f"Caching to: {CACHE_DIR}")
    print(f"Sites: {len(WIND_SITES)} wind, {len(SOLAR_SITES)} solar, {len(OFFSHORE_SITES)} offshore")
    print(f"Years: {YEARS}")
    print(f"Total calls expected: {(len(WIND_SITES) + len(SOLAR_SITES) + len(OFFSHORE_SITES)) * len(YEARS)}")
    print()
    fetch_all()


if __name__ == "__main__":
    main()
