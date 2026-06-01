"""Read BCEU per-bucket csv files; return annual MWh by SHELF residential/commercial category.

Each per-bucket CSV (e.g. BCEU-urban-residential-heating.csv) has rows:
  Year, 2020, 2021, ..., 2050
  electricity (BTU), <values>
  natural gas (BTU), ...
  ...

We pull the 'electricity (BTU)' row at the requested start year, sum urban+rural for
residential, convert BTU -> MWh.

Returns dict[str, float] keyed by SHELF category name.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict
import csv

from ..paths import resolve_input

BTU_PER_MWH = 3.412e6  # 1 kWh = 3412 BTU; 1 MWh = 3.412e6 BTU


def _read_electricity_btu(csv_path: Path, year: int) -> float:
    """Return the electricity (BTU) value for the given year, or 0.0 if missing."""
    if not csv_path.exists():
        return 0.0
    with open(csv_path, newline='') as f:
        reader = list(csv.reader(f))
    header = reader[0]
    # Year columns may be like "2020.0" -> map to int year
    year_to_col: dict[int, int] = {}
    for j, h in enumerate(header):
        try:
            y = int(float(h))
            year_to_col[y] = j
        except (ValueError, TypeError):
            continue
    if year not in year_to_col:
        return 0.0
    col = year_to_col[year]
    for row in reader[1:]:
        if not row:
            continue
        label = row[0].strip().lower()
        if label.startswith('electricity'):
            try:
                return float(row[col])
            except (ValueError, IndexError):
                return 0.0
    return 0.0


def read_bceu_annual(bcue_dir: str, year: int) -> Dict[str, float]:
    """Read all 12 BCEU bucket csvs and return annual MWh per SHELF category.

    Returns keys:
      residential-heating, residential-cooling, residential-lighting,
      residential-appliances, residential-other,
      commercial-heating, commercial-cooling, commercial-lighting,
      commercial-appliances, commercial-other.
    """
    base = resolve_input(bcue_dir)
    # BCEU subcategory names map to SHELF appliance category 'appl' -> 'appliances'
    sub_to_cat = {
        'heating': 'heating',
        'cooling': 'cooling',
        'lighting': 'lighting',
        'appl': 'appliances',
        'other': 'other',
    }
    out: Dict[str, float] = {}
    for sub, cat_suffix in sub_to_cat.items():
        # residential = urban + rural
        u = _read_electricity_btu(base / f'BCEU-urban-residential-{sub}.csv', year)
        r = _read_electricity_btu(base / f'BCEU-rural-residential-{sub}.csv', year)
        out[f'residential-{cat_suffix}'] = (u + r) / BTU_PER_MWH
        # commercial single file
        c = _read_electricity_btu(base / f'BCEU-commercial-{sub}.csv', year)
        out[f'commercial-{cat_suffix}'] = c / BTU_PER_MWH
    return out
