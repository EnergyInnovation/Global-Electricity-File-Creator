"""Verify SYSHECF workbook formulas evaluate to the same values as the CSV files.

Recomputes what each formula SHOULD produce (using the same Cambium hourly +
clustering + EIA inputs as the workbook references) and compares cell-by-cell
to the corresponding CSV file written by `rebuild_us_national_v2.py`.
"""
from __future__ import annotations
import sys
import csv
from pathlib import Path
import datetime as dt
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from state_pipeline.builders.clustering_repday import cluster_days_repday

CAMBIUM_HOURLY = ROOT / "data" / "cambium24_midcase_national" / "Cambium24_MidCase_hourly_usa_2025.csv"
CAMBIUM_ANNUAL = ROOT / "data" / "cambium24_midcase_national" / "Cambium24_MidCase_annual_national.csv"
SYSHECF_DIR    = Path(r"C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SYSHECF")

EIA_CF_TARGETS = {
    'solar-pv':      0.232,
    'solar-pv-dist': 0.170,
    'solar-thermal': 0.250,
    'onshore-wind':  0.343,
    'offshore-wind': 0.420,
}

TECHS = [
    ('solar-pv',          'upv_MWh',       'upv_MW'),
    ('solar-pv-dist',     'distpv_MWh',    'distpv_MW'),
    ('onshore-wind',      'wind-ons_MWh',  'wind-ons_MW'),
    ('offshore-wind',     'wind-ofs_MWh',  'wind-ofs_MW'),
    ('hydro',             'hydro_MWh',     'hydro_MW'),
    ('nuclear',           'nuclear_MWh',   'nuclear_MW'),
    ('combined-cycle',    'gas-cc_MWh',    'gas-cc_MW'),
    ('natural-gas-peaker', 'gas-ct_MWh',   'gas-ct_MW'),
    ('hard-coal',         'coal_MWh',      'coal_MW'),
    ('biomass',           'biomass_MWh',   'biomass_MW'),
]

SLICES = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']


def load_cambium_hourly(path: Path) -> pd.DataFrame:
    with open(path) as f:
        lines = f.readlines()
    headers = lines[5].strip().split(',')
    rows = []
    for line in lines[6:]:
        parts = line.strip().split(',')
        if len(parts) < 5:
            continue
        try:
            ts = dt.datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
        row = {'_ts': ts}
        for i, h in enumerate(headers):
            if h == 'timestamp':
                continue
            try:
                row[h] = float(parts[i])
            except (ValueError, IndexError):
                row[h] = np.nan
        rows.append(row)
    df = pd.DataFrame(rows).set_index('_ts')
    df.index.name = None
    return df


def main():
    cambium = load_cambium_hourly(CAMBIUM_HOURLY)
    annual = pd.read_csv(CAMBIUM_ANNUAL)
    annual = annual[annual['t'] == 2025].iloc[0].to_dict()

    cr = cluster_days_repday(
        cambium['busbar_load'],
        cambium['upv_MWh'] + cambium['distpv_MWh'],
        cambium['wind-ons_MWh'] + cambium['wind-ofs_MWh'],
        peak_top_n=1, max_peak_days=365,
    )
    slice_map = cr.slice_assignment.to_dict()  # DOY -> slice name

    # Build slice + hour arrays for the 8760 rows
    n = len(cambium)
    doys = np.array([ts.timetuple().tm_yday for ts in cambium.index[:n]])
    hours = np.array([ts.hour for ts in cambium.index[:n]])
    slices = np.array([slice_map.get(int(d), 'Winter') for d in doys])

    print(f"{'Tech':<22}{'max abs diff':>14}{'mean abs diff':>16}{'verdict':>14}")
    print('-' * 66)

    overall_max = 0.0
    for tech, mwh_col, mw_col in TECHS:
        cap = float(annual.get(mw_col, 0.0))
        if cap <= 0:
            continue
        cf_hourly = np.clip(cambium[mwh_col].iloc[:n].values / cap, 0.0, 1.0)
        annual_mean = float(cf_hourly.mean())

        # Compute SYSHECF as AVERAGEIFS-equivalent, then scale by EIA/annual if VRE
        target = EIA_CF_TARGETS.get(tech)
        scale = (target / annual_mean) if (target and annual_mean > 0) else 1.0

        computed = {}
        for sl in SLICES:
            for h in range(24):
                mask = (slices == sl) & (hours == h)
                if mask.sum() == 0:
                    computed[(sl, h)] = 0.0
                else:
                    val = cf_hourly[mask].mean() * scale
                    val = max(0.0, min(1.0, val))
                    computed[(sl, h)] = val

        # Read CSV
        csv_path = SYSHECF_DIR / f"SYSHECF-{tech}.csv"
        if not csv_path.exists():
            print(f"{tech:<22}  CSV missing")
            continue
        with open(csv_path) as f:
            rows = list(csv.reader(f))
        csv_vals = {}
        for r in rows[1:]:
            if not r or r[0] not in SLICES:
                continue
            sl = r[0]
            for h in range(24):
                try:
                    csv_vals[(sl, h)] = float(r[1 + h])
                except (ValueError, IndexError):
                    csv_vals[(sl, h)] = 0.0

        diffs = []
        for k in computed:
            diffs.append(abs(computed[k] - csv_vals.get(k, 0.0)))
        max_d = max(diffs)
        mean_d = sum(diffs) / len(diffs)
        overall_max = max(overall_max, max_d)
        verdict = 'OK' if max_d < 1e-6 else ('CLOSE' if max_d < 1e-3 else 'MISMATCH')
        print(f"{tech:<22}{max_d:>14.2e}{mean_d:>16.2e}{verdict:>14}")

    print(f"\nOverall max abs diff across all techs: {overall_max:.2e}")
    print("Verdict:", "OK (workbook formulas match CSV values)" if overall_max < 1e-6
          else "INSPECT — divergence detected")


if __name__ == '__main__':
    main()
