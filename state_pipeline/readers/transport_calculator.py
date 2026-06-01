"""Compute per-veh-type annual electricity MWh and aggregate to 6 SHELF transportation cats.

Inputs (per-state CSVs):
  trans/SYVbT/SYVbT-{passenger,freight}.csv   - vehicle stock (rows: veh type; cols: tech)
  trans/AVLo/AVLo-{passengers,freight}.csv    - loading (rows: veh type; cols: years)
  trans/BAADTbVT/BAADTbVT-{passengers,freight}.csv - distance miles/vehicle
  trans/SYFAFE/SYFAFE-{psgr,frgt}.csv         - fuel economy (passenger*miles/BTU or freight units)
  trans/BPoEFUbVT/BPoEFUbVT-{vt}-{psgr|frgt}-{tech}.csv - per fuel share by year

For each vehicle-type x technology x [psgr|frgt]:
  vehicles = stock[vt, tech]
  loading  = AVLo[vt, year]
  distance = BAADTbVT[vt, year]
  fe       = SYFAFE[vt, tech]                 # passenger*miles/BTU
  fuel_BTU = vehicles * distance * loading / fe   when fe > 0
  electricity_share = BPoEFUbVT[vt-mode-tech].electricity row at year
  electric_BTU += fuel_BTU * electricity_share

Aggregate vehicle types: LDVs, HDVs (incl. mtrbks? no - own bucket), aircraft, rail, ships, motorbikes.
MDVs are not in this dataset (only LDVs/HDVs/aircraft/rail/ships/mtrbks).

Returns dict[str, float] keyed by SHELF transport category name -> annual MWh.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict
import csv

from ..paths import resolve_input

BTU_PER_MWH = 3.412e6

VEH_TYPES = ['LDVs', 'HDVs', 'aircraft', 'rail', 'ships', 'motorbikes']
SHELF_BUCKETS = {
    'LDVs': 'LDVs',
    'HDVs': 'HDVs',
    'aircraft': 'aircraft',
    'rail': 'rail',
    'ships': 'ships',
    'motorbikes': 'motorbikes',
    # SYVbT uses 'mtrbks' in some files, but stock uses 'motorbikes' -- keep direct map
}

TECHS_STOCK = ['battery electric vehicle', 'natural gas vehicle', 'gasoline vehicle',
               'diesel vehicle', 'plugin hybrid vehicle', 'LPG vehicle', 'hydrogen vehicle']

# Map stock tech -> BPoEFUbVT tech slug
STOCK_TO_SLUG = {
    'battery electric vehicle': 'batelc',
    'natural gas vehicle': 'natgas',
    'gasoline vehicle': 'gasveh',
    'diesel vehicle': 'dslveh',
    'plugin hybrid vehicle': 'plghyb',
    'LPG vehicle': 'LPG',
    'hydrogen vehicle': 'hydgn',
}

# Map vehicle type -> BPoEFUbVT vehicle-type slug
VT_TO_SLUG = {
    'LDVs': 'LDVs',
    'HDVs': 'HDVs',
    'aircraft': 'aircraft',
    'rail': 'rail',
    'ships': 'ships',
    'motorbikes': 'mtrbks',
}


def _load_csv_rows_by_first_col(p: Path) -> tuple[list[str], dict[str, list[str]]]:
    """Read csv -> (header, dict[firstcol_value -> remaining_columns_as_list])."""
    with open(p, newline='') as f:
        rows = list(csv.reader(f))
    header = rows[0]
    out: dict[str, list[str]] = {}
    for r in rows[1:]:
        if not r:
            continue
        out[r[0].strip()] = r[1:]
    return header, out


def _year_col_index(header: list[str], year: int, base_offset: int = 0) -> int | None:
    """Find column index in header (0=label) where year matches; returns abs index or None."""
    for j, h in enumerate(header):
        try:
            if int(float(h)) == year:
                return j
        except (ValueError, TypeError):
            continue
    return None


def _val(d: dict[str, list[str]], key: str, idx: int) -> float:
    """Pull a value, treating empty/missing as 0."""
    if key not in d:
        return 0.0
    row = d[key]
    if idx <= 0 or idx - 1 >= len(row):
        return 0.0
    try:
        return float(row[idx - 1])
    except (ValueError, IndexError):
        return 0.0


def _read_bpoefuvt_electricity_share(path: Path, year: int) -> float:
    """BPoEFUbVT per-(vt,mode,tech) csv: rows are fuels; pull 'electricity' row at year."""
    if not path.exists():
        return 0.0
    with open(path, newline='') as f:
        rows = list(csv.reader(f))
    if not rows:
        return 0.0
    header = rows[0]
    year_col = None
    for j, h in enumerate(header):
        try:
            if int(float(h)) == year:
                year_col = j
                break
        except (ValueError, TypeError):
            continue
    if year_col is None:
        return 0.0
    for r in rows[1:]:
        if not r:
            continue
        if r[0].strip().lower() == 'electricity':
            try:
                return float(r[year_col])
            except (ValueError, IndexError):
                return 0.0
    return 0.0


def compute_transport_electricity(transport_dir: str, year: int) -> Dict[str, float]:
    base = resolve_input(transport_dir)

    out: Dict[str, float] = {b: 0.0 for b in SHELF_BUCKETS.values()}

    for mode_label, stock_file, avlo_file, dist_file, fe_file, mode_slug in [
        ('passengers',
         'SYVbT/SYVbT-passenger.csv',
         'AVLo/AVLo-passengers.csv',
         'BAADTbVT/BAADTbVT-passengers.csv',
         'SYFAFE/SYFAFE-psgr.csv',
         'psgr'),
        ('freight',
         'SYVbT/SYVbT-freight.csv',
         'AVLo/AVLo-freight.csv',
         'BAADTbVT/BAADTbVT-freight.csv',
         'SYFAFE/SYFAFE-frgt.csv',
         'frgt'),
    ]:
        sf = base / stock_file
        af = base / avlo_file
        df = base / dist_file
        ff = base / fe_file
        if not (sf.exists() and af.exists() and df.exists() and ff.exists()):
            continue

        stock_hdr, stock_rows = _load_csv_rows_by_first_col(sf)
        avlo_hdr, avlo_rows = _load_csv_rows_by_first_col(af)
        dist_hdr, dist_rows = _load_csv_rows_by_first_col(df)
        fe_hdr, fe_rows = _load_csv_rows_by_first_col(ff)

        # AVLo and BAADTbVT have year columns, col 0 is label. Find year col.
        avlo_yc = _year_col_index(avlo_hdr, year)
        dist_yc = _year_col_index(dist_hdr, year)
        if avlo_yc is None or dist_yc is None:
            continue

        # stock and fe headers are tech names (col 0 = "..."; cols 1+ are techs)
        stock_techs = stock_hdr[1:]
        fe_techs = fe_hdr[1:]

        for vt in VEH_TYPES:
            # Get loading and distance values for this vehicle type
            loading = _val(avlo_rows, vt, avlo_yc)
            distance = _val(dist_rows, vt, dist_yc)
            if loading <= 0 or distance <= 0:
                continue
            for tech in stock_techs:
                vehicles = _val(stock_rows, vt, stock_techs.index(tech) + 1)
                if vehicles <= 0:
                    continue
                # fuel economy lookup: same tech name in fe_techs
                if tech not in fe_techs:
                    continue
                fe = _val(fe_rows, vt, fe_techs.index(tech) + 1)
                if fe <= 0:
                    continue
                # passenger-miles or freight-miles served
                pm = vehicles * distance * loading
                fuel_btu = pm / fe
                # electricity share
                tech_slug = STOCK_TO_SLUG.get(tech)
                vt_slug = VT_TO_SLUG.get(vt, vt)
                if tech_slug is None:
                    continue
                bpof_path = (base / 'BPoEFUbVT' /
                             f'BPoEFUbVT-{vt_slug}-{mode_slug}-{tech_slug}.csv')
                share = _read_bpoefuvt_electricity_share(bpof_path, year)
                if share <= 0:
                    continue
                electric_btu = fuel_btu * share
                out[SHELF_BUCKETS[vt]] += electric_btu / BTU_PER_MWH
    return out
