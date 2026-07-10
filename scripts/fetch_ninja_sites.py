"""Bulk-download Renewables.ninja WIND SIMULATION output for specific sites.

This pulls the hub-height, power-curve-applied wind product (NOT the raw 2 m
weather variable) for a user-specified list of lat/lon points, one CSV per
(site, year), for 2018-2024. Use this for China / South Korea where the bulk
country downloads on the website are not available (EU-only there).

Each request returns, per hour:
  - `electricity`  : output for the configured capacity. With CAPACITY = 1 this
                     is effectively the capacity factor (0-1).
  - `wind_speed`   : the hub-height wind speed used (only if RAW = True) -- this
                     is the sheared, hub-height speed, i.e. the correct-diurnal
                     variable, unlike the 2 m weather download.

Requires a Renewables.ninja account token (free registration raises your API
rate limit). The script NEVER stores the token in code -- it reads it from,
in priority order:
  1. env var RENEWABLES_NINJA_TOKEN
  2. a token file (see TOKEN_FILE below), first line = the token
Get your token from https://www.renewables.ninja/profile after logging in.

Output: data/weather/ninja_sim/<COUNTRY>/<site>_<year>.csv  (cached; re-runs
skip files that already exist, so the job is fully resumable).

Usage:
    python scripts/fetch_ninja_sites.py                 # all sites, 2018-2024
    python scripts/fetch_ninja_sites.py --country CN    # China only
    python scripts/fetch_ninja_sites.py --years 2020 2021
    python scripts/fetch_ninja_sites.py --dry-run       # list calls, fetch nothing
    python scripts/fetch_ninja_sites.py --combine       # also build tidy combined CSVs

Rate limits (Renewables.ninja, logged-in): ~50 requests/hour sustained, burst
~6/sec. This script self-throttles under the hourly cap and backs off on HTTP
429. A full 2018-2024 x (many sites) run may span multiple hours -- just leave
it running; caching makes it safe to stop and restart.

NOTE: the SITES coordinates below are APPROXIMATE regional placeholders for
major wind areas. REPLACE them with the actual coordinates of the sites you
want, and verify each against your own siting source before use. Frame results
as inputs for staff review; validate against primary sources.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "weather" / "ninja_sim"
TOKEN_FILE = PROJECT_ROOT / "data" / ".ninja_token"  # git-ignore this; first line = token

DATASET = "merra2"        # 'merra2' (matches your existing weather files) or 'era5'
CAPACITY = 1              # 1 => `electricity` column is the capacity factor (0-1)
RAW = True               # also return hub-height wind_speed column
DEFAULT_YEARS = list(range(2018, 2025))  # 2018..2024 inclusive

# Turbine / hub-height defaults by site type. China's current fleet is largely
# ~3 MW class at ~100 m hub height; offshore uses large machines at ~140 m.
# These must be turbine model names that Renewables.ninja recognises.
TURBINE_DEFAULTS = {
    "onshore":  {"turbine": "Vestas V112 3000", "height": 100},
    "offshore": {"turbine": "Vestas V164 8000", "height": 140},
}

# Polite throttling
SECONDS_BETWEEN_CALLS = 2.0     # keep well under the ~6/sec burst limit
MAX_CALLS_PER_HOUR = 45         # stay under the ~50/hr sustained cap
MAX_RETRIES = 5

# --------------------------------------------------------------------------
# Sites -- EDIT THESE. Approximate placeholders for major wind areas.
# name must be filesystem-safe. type drives turbine/height (override per site
# with explicit "turbine"/"height"/"capacity" keys if you want).
# --------------------------------------------------------------------------
SITES = [
    # ---- China (mostly onshore "Three North" bases + coastal offshore) ----
    {"country": "CN", "name": "InnerMongolia_Xilingol", "lat": 43.9, "lon": 116.0, "type": "onshore"},
    {"country": "CN", "name": "InnerMongolia_Ulanqab",  "lat": 41.0, "lon": 113.1, "type": "onshore"},
    {"country": "CN", "name": "Gansu_Jiuquan",          "lat": 40.0, "lon":  97.5, "type": "onshore"},
    {"country": "CN", "name": "Xinjiang_Dabancheng",    "lat": 43.4, "lon":  88.3, "type": "onshore"},
    {"country": "CN", "name": "Hebei_Zhangjiakou",      "lat": 40.8, "lon": 114.9, "type": "onshore"},
    {"country": "CN", "name": "Jilin_Baicheng",         "lat": 45.6, "lon": 122.8, "type": "onshore"},
    {"country": "CN", "name": "Ningxia_Yanchi",         "lat": 37.8, "lon": 107.4, "type": "onshore"},
    {"country": "CN", "name": "Jiangsu_Rudong_OSW",     "lat": 32.7, "lon": 121.6, "type": "offshore"},
    {"country": "CN", "name": "Guangdong_Yangjiang_OSW","lat": 21.5, "lon": 111.8, "type": "offshore"},
    {"country": "CN", "name": "Fujian_Putian_OSW",      "lat": 25.2, "lon": 119.4, "type": "offshore"},

    # ---- South Korea (onshore Gangwon ridge + southwest offshore) ----
    {"country": "KR", "name": "Gangwon_Daegwallyeong",  "lat": 37.7, "lon": 128.7, "type": "onshore"},
    {"country": "KR", "name": "Jeonbuk_Buan_OSW",       "lat": 35.6, "lon": 126.3, "type": "offshore"},
    {"country": "KR", "name": "Jeonnam_Sinan_OSW",      "lat": 34.8, "lon": 126.1, "type": "offshore"},
    {"country": "KR", "name": "Ulsan_Offshore",         "lat": 35.4, "lon": 129.6, "type": "offshore"},
    {"country": "KR", "name": "Jeju_Southwest",         "lat": 33.2, "lon": 126.2, "type": "onshore"},
]

API_URL = "https://www.renewables.ninja/api/data/wind"


# --------------------------------------------------------------------------
# Token
# --------------------------------------------------------------------------
def _clean_token(tok: str) -> str:
    """Strip whitespace, surrounding quotes, and an accidental 'Token ' prefix."""
    tok = tok.strip()
    if tok.lower().startswith("token "):
        tok = tok[6:].strip()
    tok = tok.strip("'\"").strip()  # remove wrapping quotes then any inner whitespace
    return tok


def load_token() -> str:
    tok = _clean_token(os.environ.get("RENEWABLES_NINJA_TOKEN", ""))
    if tok:
        return tok
    if TOKEN_FILE.exists():
        first_line = TOKEN_FILE.read_text(encoding="utf-8").strip().splitlines()
        tok = _clean_token(first_line[0]) if first_line else ""
        if tok:
            return tok
    sys.exit(
        "ERROR: no API token found.\n"
        "  Set env var RENEWABLES_NINJA_TOKEN, or put your token on the first\n"
        f"  line of {TOKEN_FILE}\n"
        "  Get it from https://www.renewables.ninja/profile (log in first)."
    )


# --------------------------------------------------------------------------
# Fetch
# --------------------------------------------------------------------------
def site_params(site: dict, year: int) -> dict:
    defaults = TURBINE_DEFAULTS[site["type"]]
    return {
        "lat": site["lat"],
        "lon": site["lon"],
        "date_from": f"{year}-01-01",
        "date_to": f"{year}-12-31",
        "dataset": DATASET,
        "capacity": site.get("capacity", CAPACITY),
        "height": site.get("height", defaults["height"]),
        "turbine": site.get("turbine", defaults["turbine"]),
        "format": "csv",
        "header": "true",     # keep the metadata header (lat/lon/turbine/etc.)
        "raw": "true" if RAW else "false",
    }


def fetch_one(token: str, site: dict, year: int) -> str:
    """Return CSV text for one (site, year), with retry/backoff on 429/5xx."""
    url = API_URL + "?" + urllib.parse.urlencode(site_params(site, year))
    req = urllib.request.Request(url, headers={
        "Authorization": f"Token {token}",
        "User-Agent": "Energy Innovation EPS calibration (staff review)",
    })
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry_after = e.headers.get("Retry-After")
                wait = int(retry_after) if retry_after and retry_after.isdigit() else 60 * attempt
                print(f"      429 rate-limited; sleeping {wait}s (attempt {attempt}/{MAX_RETRIES})", flush=True)
                time.sleep(wait)
                continue
            if 500 <= e.code < 600:
                wait = 10 * attempt
                print(f"      HTTP {e.code}; retrying in {wait}s (attempt {attempt}/{MAX_RETRIES})", flush=True)
                time.sleep(wait)
                continue
            body = e.read().decode("utf-8", "replace")[:300]
            raise RuntimeError(f"HTTP {e.code} for {site['name']} {year}: {body}") from e
        except urllib.error.URLError as e:
            wait = 10 * attempt
            print(f"      network error {e.reason}; retrying in {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"gave up after {MAX_RETRIES} retries: {site['name']} {year}")


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------
def out_path(site: dict, year: int) -> Path:
    return OUT_DIR / site["country"] / f"{site['name']}_{year}.csv"


def run(countries: set[str], years: list[int], dry_run: bool):
    token = None if dry_run else load_token()
    sites = [s for s in SITES if not countries or s["country"] in countries]
    jobs = [(s, y) for s in sites for y in years]
    print(f"Output dir: {OUT_DIR}")
    print(f"Sites: {len(sites)}  Years: {years}  Total (site,year) jobs: {len(jobs)}")
    print(f"Dataset={DATASET}  capacity={CAPACITY}  raw={RAW}")
    print()

    fetched = skipped = failed = 0
    call_times: list[float] = []  # timestamps of API calls in the last hour

    for site, year in jobs:
        cp = out_path(site, year)
        if cp.exists():
            skipped += 1
            continue
        label = f"{site['country']}/{site['name']} {year} ({site['type']})"
        if dry_run:
            print(f"  WOULD FETCH  {label}  lat={site['lat']} lon={site['lon']}")
            continue

        # Proactive hourly-cap throttle
        now = time.time()
        call_times = [t for t in call_times if now - t < 3600]
        if len(call_times) >= MAX_CALLS_PER_HOUR:
            sleep_for = 3600 - (now - call_times[0]) + 5
            print(f"  Hourly cap reached; sleeping {sleep_for/60:.1f} min...", flush=True)
            time.sleep(max(sleep_for, 0))
            call_times = []

        print(f"  Fetching {label}...", flush=True)
        try:
            text = fetch_one(token, site, year)
            cp.parent.mkdir(parents=True, exist_ok=True)
            cp.write_text(text, encoding="utf-8")
            call_times.append(time.time())
            fetched += 1
            time.sleep(SECONDS_BETWEEN_CALLS)
        except Exception as e:  # noqa: BLE001 - report and continue
            print(f"    ERROR: {e}", flush=True)
            failed += 1

    print(f"\nDone. fetched={fetched} skipped(cached)={skipped} failed={failed}")
    if failed:
        print("Re-run to retry failed jobs (cached files are skipped).")


# --------------------------------------------------------------------------
# Optional: combine per-(site,year) CSVs into one tidy CSV per country
# --------------------------------------------------------------------------
def combine(countries: set[str]):
    import pandas as pd

    for country in sorted({s["country"] for s in SITES if not countries or s["country"] in countries}):
        cdir = OUT_DIR / country
        files = sorted(cdir.glob("*.csv")) if cdir.exists() else []
        if not files:
            print(f"[{country}] no files to combine")
            continue
        frames = []
        for f in files:
            # Renewables.ninja CSVs have a metadata header block; data header
            # row starts with 'time'. Find it dynamically.
            with open(f, encoding="utf-8") as fh:
                skip = next(i for i, line in enumerate(fh) if line.startswith("time"))
            df = pd.read_csv(f, skiprows=skip, parse_dates=["time"])
            name, year = f.stem.rsplit("_", 1)
            df.insert(1, "site", name)
            frames.append(df)
        out = cdir.parent / f"{country}_wind_sim_combined.csv"
        pd.concat(frames, ignore_index=True).to_csv(out, index=False)
        print(f"[{country}] combined {len(files)} files -> {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", action="append", default=[],
                    help="Restrict to a country code (repeatable), e.g. --country CN --country KR")
    ap.add_argument("--years", type=int, nargs="+", default=DEFAULT_YEARS,
                    help=f"Years to fetch (default {DEFAULT_YEARS[0]}-{DEFAULT_YEARS[-1]})")
    ap.add_argument("--dry-run", action="store_true", help="List the calls without fetching")
    ap.add_argument("--combine", action="store_true",
                    help="After fetching, build one tidy combined CSV per country")
    args = ap.parse_args()

    countries = {c.upper() for c in args.country}
    run(countries, args.years, args.dry_run)
    if args.combine and not args.dry_run:
        combine(countries)


if __name__ == "__main__":
    main()
