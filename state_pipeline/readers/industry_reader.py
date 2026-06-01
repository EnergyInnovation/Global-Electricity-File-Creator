"""Read BIFUbC-electricity.csv; sum NAICS/ISIC categories for start year, return MWh."""
from __future__ import annotations
from pathlib import Path
import csv
from ..paths import resolve_input

BTU_PER_MWH = 3.412e6


def read_industry_annual(industry_csv: str, year: int) -> dict[str, float]:
    p = resolve_input(industry_csv)
    with open(p, newline='') as f:
        rows = list(csv.reader(f))
    header = rows[0]
    # find year column
    year_col = None
    for j, h in enumerate(header):
        try:
            if int(float(h)) == year:
                year_col = j
                break
        except (ValueError, TypeError):
            continue
    if year_col is None:
        return {'industry': 0.0}
    total_btu = 0.0
    for row in rows[1:]:
        if not row or len(row) <= year_col:
            continue
        try:
            total_btu += float(row[year_col])
        except ValueError:
            continue
    return {'industry': total_btu / BTU_PER_MWH}
