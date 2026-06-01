"""US national K6/H24 rebuild — ResStock + ComStock + EFS (correct sources).

Per-category SHELF sources:
  - residential-*  : ResStock aggregated across all 50 states
  - commercial-*   : ComStock aggregated across all 50 states
  - industry       : EFS national (industrial sector)
  - LDVs, HDVs, rail : EFS national (transportation subsectors)
  - aircraft, ships, motorbikes, envelope, datacenters, district-heat-hydrogen, geoeng : zero (EPS convention)

Clustering uses Cambium 2024 MidCase national hourly for net-load + VRE.
Legacy rep-day methodology (clustering_repday) — no peak day cap.

SYSHECF uses Cambium 2024 per-tech hourly with EIA annual CF calibration.

Run:
  python rebuild_us_national_v2.py
"""
from __future__ import annotations
import argparse
import csv
import sys
from pathlib import Path
import datetime as dt
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from state_pipeline.builders.clustering import SLICE_NAMES
from state_pipeline.builders.clustering_repday import cluster_days_repday as cluster_days
from state_pipeline.builders.shelf_builder import build_shelf_for_category
from state_pipeline.builders.syshecf_builder import _build_variable_table
from state_pipeline.readers.resstock_reader import read_resstock_hourly, RES_AGG
from state_pipeline.readers.comstock_reader import read_comstock_hourly

CAMBIUM_HOURLY = ROOT / "data" / "cambium24_midcase_national" / "Cambium24_MidCase_hourly_usa_2025.csv"
CAMBIUM_ANNUAL = ROOT / "data" / "cambium24_midcase_national" / "Cambium24_MidCase_annual_national.csv"
EFS_ZIP        = ROOT / "data" / "efs" / "EFSLoadProfile_Reference_Moderate.zip"
RESSTOCK_ROOT  = Path(r"C:\Users\RobbieOrvis\Models\ResStock SHELF\ResStock_Upgrade0")
COMSTOCK_ROOT  = Path(r"C:\Users\RobbieOrvis\Models\ResStock SHELF\ComStock_tmy_release1")

EPS_SHELF   = Path(r"C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SHELF")
EPS_SYSHECF = Path(r"C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SYSHECF")

EIA_CF_TARGETS = {
    'solar-pv':      0.232,
    'solar-pv-dist': 0.170,
    'solar-thermal': 0.250,
    'onshore-wind':  0.343,
    'offshore-wind': 0.420,
}

CAMBIUM_TECH_COLS = {
    'solar-pv':         ('upv_MWh',       'upv_MW'),
    'solar-pv-dist':    ('distpv_MWh',    'distpv_MW'),
    'solar-thermal':    ('csp_MWh',       'csp_MW'),
    'onshore-wind':     ('wind-ons_MWh',  'wind-ons_MW'),
    'offshore-wind':    ('wind-ofs_MWh',  'wind-ofs_MW'),
    'hydro':            ('hydro_MWh',     'hydro_MW'),
    'pumped-hydro':     ('phs_MWh',       'phs_MW'),
    'nuclear':          ('nuclear_MWh',   'nuclear_MW'),
    'combined-cycle':   ('gas-cc_MWh',    'gas-cc_MW'),
    'natural-gas-peaker': ('gas-ct_MWh',  'gas-ct_MW'),
    'hard-coal':        ('coal_MWh',      'coal_MW'),
    'biomass':          ('biomass_MWh',   'biomass_MW'),
    'geothermal':       ('geothermal_MWh', 'geothermal_MW'),
    'petroleum':        ('o-g-s_MWh',     'o-g-s_MW'),
}

SHELF_ZERO_CATEGORIES = {
    'residential-envelope', 'commercial-envelope',
    'aircraft', 'ships', 'motorbikes',
    'district-heat-hydrogen', 'geoeng',
}

# Categories where the SHELF is a flat 24/7 profile (continuous-operation load).
# LF = 1/8760 in every (slice, hour) cell. Balance check verifies 1.0.
SHELF_FLAT_CATEGORIES = {
    'datacenters',  # data centers run 24/7; daytime workload variation is small
}

# State -> hours-ahead offset to align Local Standard Time to Eastern Time.
# ResStock and ComStock files use LST per state; Cambium 2024 busbar is in ET.
# To convert state-LST series to ET, np.roll(series, +offset) — data moves
# forward in time so it aligns with the ET clock.
STATE_TZ_OFFSET_TO_ET = {
    # ET (offset = 0, no shift)
    'CT': 0, 'DE': 0, 'DC': 0, 'FL': 0, 'GA': 0, 'IN': 0, 'KY': 0, 'ME': 0,
    'MD': 0, 'MA': 0, 'MI': 0, 'NH': 0, 'NJ': 0, 'NY': 0, 'NC': 0, 'OH': 0,
    'PA': 0, 'RI': 0, 'SC': 0, 'VT': 0, 'VA': 0, 'WV': 0,
    # CT (one hour earlier than ET → shift +1)
    'AL': 1, 'AR': 1, 'IA': 1, 'IL': 1, 'KS': 1, 'LA': 1, 'MN': 1, 'MS': 1,
    'MO': 1, 'NE': 1, 'ND': 1, 'OK': 1, 'SD': 1, 'TN': 1, 'TX': 1, 'WI': 1,
    # MT (two hours earlier → shift +2)
    'AZ': 2, 'CO': 2, 'ID': 2, 'MT': 2, 'NM': 2, 'UT': 2, 'WY': 2,
    # PT (three hours earlier → shift +3)
    'CA': 3, 'NV': 3, 'OR': 3, 'WA': 3,
    # AKT/HST (only in ComStock; not in ResStock)
    'AK': 4, 'HI': 5,
}

SLICES = SLICE_NAMES
HOUR_COLS = [f'Hour{h}' for h in range(24)]
SHELF_HEADER_LABEL = 'Unit: dimensionless (ratio of electricity demand in this hour to annual demand)'


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


def load_cambium_annual_2025(path: Path) -> dict:
    df = pd.read_csv(path)
    row = df[df['t'] == 2025]
    if row.empty:
        raise RuntimeError("No 2025 row in Cambium annual file")
    return row.iloc[0].to_dict()


def _tz_correct_to_ET(df: pd.DataFrame, state: str) -> pd.DataFrame:
    """Shift each state's hourly series forward by its LST→ET offset (np.roll with wraparound)."""
    offset = STATE_TZ_OFFSET_TO_ET.get(state, 0)
    if offset == 0:
        return df
    shifted = df.copy()
    for col in shifted.columns:
        shifted[col] = np.roll(shifted[col].values, offset)
    return shifted


def aggregate_resstock_national() -> pd.DataFrame:
    """Sum ResStock hourly across all state folders, TZ-corrected to ET."""
    state_dirs = sorted([p for p in RESSTOCK_ROOT.glob('state=*') if p.is_dir()])
    print(f"  [resstock] aggregating {len(state_dirs)} state folders (TZ-corrected to ET)...")
    combined: pd.DataFrame | None = None
    for sd in state_dirs:
        state = sd.name.split('=')[1]
        try:
            state_hr = read_resstock_hourly(str(sd))
        except Exception as e:
            print(f"    SKIP {state}: {e}")
            continue
        # TZ-correct: shift LST→ET
        tz_offset = STATE_TZ_OFFSET_TO_ET.get(state, 0)
        state_hr = _tz_correct_to_ET(state_hr, state)
        if combined is None:
            combined = state_hr.copy()
        else:
            combined = combined.add(state_hr, fill_value=0)
        print(f"    + {state} (TZ+{tz_offset}h): {state_hr.sum().sum()/1e6:.1f} TWh")
    return combined


def aggregate_comstock_national() -> pd.DataFrame:
    """Sum ComStock hourly across all state folders, TZ-corrected to ET."""
    state_dirs = sorted([p for p in COMSTOCK_ROOT.iterdir() if p.is_dir() and len(p.name) == 2])
    print(f"  [comstock] aggregating {len(state_dirs)} state folders (TZ-corrected to ET)...")
    combined: pd.DataFrame | None = None
    for sd in state_dirs:
        state = sd.name
        try:
            state_hr = read_comstock_hourly(str(sd))
        except Exception as e:
            print(f"    SKIP {state}: {e}")
            continue
        # TZ-correct: shift LST→ET
        tz_offset = STATE_TZ_OFFSET_TO_ET.get(state, 0)
        state_hr = _tz_correct_to_ET(state_hr, state)
        if combined is None:
            combined = state_hr.copy()
        else:
            combined = combined.add(state_hr, fill_value=0)
        print(f"    + {state} (TZ+{tz_offset}h): {state_hr.sum().sum()/1e6:.1f} TWh")
    return combined


def load_efs_for_industry_transport(zip_path: Path, year: int = 2025) -> pd.DataFrame:
    """Load EFS national hourly — keep ONLY industry + transport subsectors."""
    import zipfile, io
    try:
        import zipfile_deflate64  # noqa: F401
    except ImportError:
        raise ImportError("zipfile_deflate64 required for EFS archive")
    efs_years = [2018, 2020, 2024, 2030, 2040, 2050]
    efs_year = min(efs_years, key=lambda y: abs(y - year))

    needed = ['Electrification', 'TechnologyAdvancement', 'Year',
              'LocalHourID', 'Sector', 'Subsector', 'LoadMW']
    frames = []
    with zipfile.ZipFile(zip_path) as zf:
        candidates = [n for n in zf.namelist() if n.endswith('.csv')]
        member = candidates[0]
        with zf.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding='utf-8-sig', newline='')
            reader = pd.read_csv(text, usecols=needed, chunksize=500_000)
            for chunk in reader:
                m = ((chunk['Electrification'].astype(str).str.strip().str.lower() == 'reference')
                     & (chunk['TechnologyAdvancement'].astype(str).str.strip().str.lower() == 'moderate')
                     & (pd.to_numeric(chunk['Year'], errors='coerce') == efs_year))
                f = chunk.loc[m, ['LocalHourID', 'Sector', 'Subsector', 'LoadMW']]
                if f.empty:
                    continue
                f['LocalHourID'] = pd.to_numeric(f['LocalHourID'], errors='coerce').astype('Int64')
                f['LoadMW'] = pd.to_numeric(f['LoadMW'], errors='coerce')
                frames.append(f.dropna(subset=['LocalHourID', 'LoadMW'])
                                .groupby(['LocalHourID', 'Sector', 'Subsector'], as_index=False)['LoadMW'].sum())
    agg = pd.concat(frames).groupby(['LocalHourID', 'Sector', 'Subsector'], as_index=False)['LoadMW'].sum()
    pivoted = agg.pivot_table(index='LocalHourID', columns=['Sector', 'Subsector'],
                              values='LoadMW', aggfunc='sum', fill_value=0.0).sort_index()
    if len(pivoted.index) != 8760:
        raise ValueError(f"EFS national hourly should have 8760 rows; got {len(pivoted.index)}")
    ts = pd.date_range(start='2018-01-01', periods=8760, freq='h')
    pivoted.index = ts

    def col(sec, sub):
        return pivoted[(sec, sub)].astype(float) if (sec, sub) in pivoted.columns else pd.Series(0.0, index=ts)

    ind_machine = col('Industrial', 'machine drives')
    ind_process = col('Industrial', 'process heat')
    ind_other   = col('Industrial', 'other')
    tr_ldv = col('Transportation', 'light-duty vehicles')
    tr_mdv = col('Transportation', 'medium-duty trucks')
    tr_hdv = col('Transportation', 'heavy-duty trucks')
    tr_other = col('Transportation', 'other')

    out = pd.DataFrame(index=ts)
    out['industry'] = ind_machine + ind_process + ind_other
    out['LDVs'] = tr_ldv
    out['HDVs'] = tr_mdv + tr_hdv
    out['rail'] = tr_other * 0.40
    print(f"  [efs] industry+transport loaded; ind={out['industry'].sum()/1e6:.1f} TWh, "
          f"LDV={out['LDVs'].sum()/1e6:.2f} TWh, HDV={out['HDVs'].sum()/1e6:.3f} TWh, "
          f"rail={out['rail'].sum()/1e6:.2f} TWh")
    return out


# ---------------------------------------------------------------------------
# Calendar alignment
# ---------------------------------------------------------------------------

def align_to_common_year(df: pd.DataFrame, target_year: int = 2018) -> pd.DataFrame:
    """Reindex to a 2018-style 8760-hour calendar (drop leap day if present)."""
    out = df.copy()
    # Cambium 2024 file uses 2025 calendar starting on Sunday; ResStock uses 2018 TMY.
    # We just need 8760 hours in order; the calendar year doesn't matter for clustering.
    target_idx = pd.date_range(start=f'{target_year}-01-01', periods=8760, freq='h')
    if len(out) >= 8760:
        out = out.iloc[:8760].copy()
        out.index = target_idx
    return out


def write_shelf(out_dir: Path, cat: str, table: pd.DataFrame, all_zero: bool = False):
    p = out_dir / f'SHELF-{cat}.csv'
    with open(p, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([SHELF_HEADER_LABEL] + HOUR_COLS)
        for sl in SLICES:
            if all_zero:
                vals = [0.0] * 24
            else:
                vals = [float(table.loc[sl, h]) for h in HOUR_COLS]
            w.writerow([sl] + [f"{v:.10g}" for v in vals])


def write_syshecf(out_dir: Path, tech: str, table: pd.DataFrame):
    p = out_dir / f'SYSHECF-{tech}.csv'
    display = tech.replace('-', ' ')
    with open(p, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([display] + HOUR_COLS)
        for sl in SLICES:
            vals = [float(table.loc[sl, h]) for h in HOUR_COLS]
            w.writerow([sl] + [f"{v:.10g}" for v in vals])


def write_days_per_timeslice(path: Path, days: dict):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Unit: days', 'Days per Timeslice'])
        for sl in SLICES:
            w.writerow([sl, int(days[sl])])


def calibrate_to_eia(syshecf_table: pd.DataFrame, days_per_slice: dict, target_cf: float) -> pd.DataFrame:
    annual_cf = 0.0
    for sl in SLICES:
        if sl in syshecf_table.index:
            annual_cf += float(syshecf_table.loc[sl, HOUR_COLS].sum()) * days_per_slice[sl]
    annual_cf /= 8760.0
    if annual_cf <= 0:
        return syshecf_table
    scale = target_cf / annual_cf
    out = syshecf_table.copy()
    for sl in SLICES:
        if sl in out.index:
            out.loc[sl] = out.loc[sl] * scale
    out = out.clip(lower=0.0, upper=1.0)
    return out


def main():
    print("="*72)
    print("US National K6/H24 rebuild v2 — ResStock + ComStock + EFS + Cambium 2024")
    print("="*72)

    # ---- Load Cambium hourly + annual ----
    print(f"[load] Cambium hourly")
    camb = load_cambium_hourly(CAMBIUM_HOURLY)
    print(f"  {len(camb)} rows; annual busbar = {camb['busbar_load'].sum()/1e6:.1f} TWh; "
          f"peak busbar = {camb['busbar_load'].max()/1e3:.1f} GW")
    camb_ann = load_cambium_annual_2025(CAMBIUM_ANNUAL)

    # Align Cambium to common 2018 calendar for clustering
    camb_aligned = align_to_common_year(camb, target_year=2018)
    total_demand = camb_aligned['busbar_load']
    solar_gen = camb_aligned['upv_MWh'] + camb_aligned['distpv_MWh']
    wind_gen = camb_aligned['wind-ons_MWh'] + camb_aligned['wind-ofs_MWh']

    # ---- Cluster ----
    print(f"[cluster] cluster_days_repday (peak_top_n=1, no cap)")
    cr = cluster_days(
        total_demand, solar_gen, wind_gen,
        peak_top_n=1, max_peak_days=365,
        feature_weight_mode='netload_focus',
        summer_months=(6, 7, 8), winter_months=(11, 12, 1, 2),
    )
    print(f"  NRMSE = {cr.nrmse:.4f}; days_per_timeslice = {cr.days_per_timeslice}")
    print(f"  Summer Peak ({len(cr.sp_top_days)}): {cr.sp_top_days}")
    print(f"  Winter Peak ({len(cr.wp_top_days)}): {cr.wp_top_days}")

    # ---- Load ResStock + ComStock + EFS ----
    print(f"[load] ResStock national (aggregating all 50 states)")
    rs_hr = aggregate_resstock_national()
    rs_hr = align_to_common_year(rs_hr, target_year=2018)
    print(f"  ResStock total annual: {rs_hr.sum().sum()/1e6:.1f} TWh")
    for c in rs_hr.columns:
        print(f"    {c}: {rs_hr[c].sum()/1e6:.1f} TWh")

    print(f"[load] ComStock national (aggregating all 50 states)")
    cs_hr = aggregate_comstock_national()
    cs_hr = align_to_common_year(cs_hr, target_year=2018)
    print(f"  ComStock total annual: {cs_hr.sum().sum()/1e6:.1f} TWh")
    for c in cs_hr.columns:
        print(f"    {c}: {cs_hr[c].sum()/1e6:.1f} TWh")

    print(f"[load] EFS national (industry + transport only)")
    efs_hr = load_efs_for_industry_transport(EFS_ZIP, year=2025)
    efs_hr = align_to_common_year(efs_hr, target_year=2018)

    # ---- Build SHELF per category ----
    print(f"[shelf] building SHELF per category")
    EPS_SHELF.mkdir(exist_ok=True, parents=True)

    ALL_SHELF = [
        'residential-heating', 'residential-cooling', 'residential-lighting',
        'residential-appliances', 'residential-other', 'residential-envelope',
        'commercial-heating', 'commercial-cooling', 'commercial-lighting',
        'commercial-appliances', 'commercial-other', 'commercial-envelope',
        'industry', 'LDVs', 'HDVs', 'aircraft', 'rail', 'ships', 'motorbikes',
        'datacenters', 'district-heat-hydrogen', 'geoeng',
    ]
    # Build category map
    series_for_cat = {}
    for c in rs_hr.columns:
        series_for_cat[c] = rs_hr[c]
    for c in cs_hr.columns:
        series_for_cat[c] = cs_hr[c]
    for c in efs_hr.columns:
        series_for_cat[c] = efs_hr[c]

    written, zero_count, flat_count = 0, 0, 0
    for cat in ALL_SHELF:
        if cat in SHELF_ZERO_CATEGORIES:
            write_shelf(EPS_SHELF, cat, None, all_zero=True)
            zero_count += 1
            continue
        if cat in SHELF_FLAT_CATEGORIES:
            # Build a flat 24/7 LF table: 1/8760 in every cell
            flat = pd.DataFrame(1.0 / 8760.0, index=SLICES, columns=HOUR_COLS)
            write_shelf(EPS_SHELF, cat, flat, all_zero=False)
            flat_count += 1
            continue
        if cat not in series_for_cat or series_for_cat[cat].sum() <= 0:
            print(f"  WARN: {cat} not available; writing zeros")
            write_shelf(EPS_SHELF, cat, None, all_zero=True)
            zero_count += 1
            continue
        tbl = build_shelf_for_category(series_for_cat[cat], cr)
        write_shelf(EPS_SHELF, cat, tbl, all_zero=False)
        written += 1
    print(f"  wrote {written} non-zero SHELF files; {flat_count} flat files; {zero_count} zero files")

    # ---- Days per timeslice ----
    write_days_per_timeslice(EPS_SHELF / 'SHELF-days-per-timeslice.csv', cr.days_per_timeslice)
    print(f"  Winter={cr.days_per_timeslice['Winter']}  Spring={cr.days_per_timeslice['Spring']}  "
          f"Summer={cr.days_per_timeslice['Summer']}  Fall={cr.days_per_timeslice['Fall']}  "
          f"SP={cr.days_per_timeslice['Summer Peak']}  WP={cr.days_per_timeslice['Winter Peak']}")

    # ---- Build SYSHECF per tech ----
    print(f"[syshecf] building SYSHECF per tech")
    EPS_SYSHECF.mkdir(exist_ok=True, parents=True)
    cf_series_by_tech: dict[str, pd.Series] = {}
    for tech, (mwh_col, mw_col) in CAMBIUM_TECH_COLS.items():
        if mwh_col not in camb_aligned.columns:
            continue
        cap_mw = float(camb_ann.get(mw_col, 0.0))
        if cap_mw <= 0:
            print(f"  SKIP {tech}: cap=0")
            continue
        cf = camb_aligned[mwh_col].clip(lower=0.0) / cap_mw
        cf = cf.clip(upper=1.0)
        cf_series_by_tech[tech] = cf

    syshecf_count = 0
    for tech, cf in cf_series_by_tech.items():
        tbl = _build_variable_table(cf, cr)
        if tech in EIA_CF_TARGETS:
            tbl = calibrate_to_eia(tbl, cr.days_per_timeslice, EIA_CF_TARGETS[tech])
        write_syshecf(EPS_SYSHECF, tech, tbl)
        syshecf_count += 1
    print(f"  wrote {syshecf_count} SYSHECF files")

    # ---- Aggregate SP peak verification ----
    print(f"\n[verify] Aggregate Summer Peak slice from ResStock+ComStock+EFS:")
    aggregate = sum(series_for_cat[cat] for cat in series_for_cat if series_for_cat[cat].sum() > 0)
    sp_set = set(cr.sp_top_days)
    is_sp = pd.Series([d.dayofyear in sp_set for d in aggregate.index], index=aggregate.index)
    sp_subset = aggregate[is_sp]
    sp_by_hour = sp_subset.groupby(sp_subset.index.hour).mean()
    print(f"  Aggregate annual: {aggregate.sum()/1e6:.1f} TWh")
    print(f"  Summer Peak slice gross peak: {sp_by_hour.max()/1e3:.1f} GW @ hr {int(sp_by_hour.idxmax())}")
    print(f"  Summer Peak slice 24-hr mean: {sp_by_hour.mean()/1e3:.1f} GW")
    print(f"  (Cambium 2024 SP slice gross peak: 745 GW @ hr 15)")

    print(f"\n[done] All outputs written.")


if __name__ == '__main__':
    main()
