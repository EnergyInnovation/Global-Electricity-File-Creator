"""Write SHELF / SYSHECF / days-per-timeslice CSVs in the legacy format."""
from __future__ import annotations
from pathlib import Path
import csv
import pandas as pd

from ..builders.clustering import SLICE_NAMES
from ..builders.syshecf_builder import SYSHECF_DISPLAY_NAME


SHELF_HEADER = (
    "Unit: dimensionless (ratio of electricity demand in this hour to annual demand)"
)
SYSHECF_UNIT = "dimensionless (capacity factor in this hour)"

HOUR_COLS = [f'Hour{h}' for h in range(24)]


def _fmt(v) -> str:
    f = float(v)
    if f == 0.0:
        return '0.0'
    return repr(f)


def write_shelf_csv(out_dir: Path | str, category: str, table: pd.DataFrame) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f'SHELF-{category}.csv'
    with open(p, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([SHELF_HEADER] + HOUR_COLS)
        for sl in SLICE_NAMES:
            row = table.loc[sl].tolist() if sl in table.index else [0.0] * 24
            w.writerow([sl] + [_fmt(v) for v in row])
    return p


def write_days_per_timeslice_csv(out_dir: Path | str, days_per_ts: dict[str, int]) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / 'SHELF-days-per-timeslice.csv'
    with open(p, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Unit: days', 'Days per Timeslice'])
        for sl in SLICE_NAMES:
            w.writerow([sl, int(days_per_ts.get(sl, 0))])
    return p


def write_syshecf_csv(out_dir: Path | str, tech: str, table: pd.DataFrame) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f'SYSHECF-{tech}.csv'
    label = SYSHECF_DISPLAY_NAME.get(tech, tech)
    with open(p, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([label] + HOUR_COLS)
        for sl in SLICE_NAMES:
            row = table.loc[sl].tolist() if sl in table.index else [0.0] * 24
            w.writerow([sl] + [_fmt(v) for v in row])
    return p
