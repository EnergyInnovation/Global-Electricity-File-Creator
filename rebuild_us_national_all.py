"""Full US national K6/H24 rebuild — SHELF + SYSHECF + days_per_timeslice.

End-to-end:
  1. Load EFS national hourly per-category demand (Reference/Moderate)
  2. Load Cambium 2024 MidCase national hourly load + VRE generation + capacity
  3. Cluster days using state_pipeline.cluster_days (no peak-day cap)
  4. Build per-category SHELF (matches eps-us category structure) from EFS hourly
  5. Build per-tech SYSHECF from Cambium 2024 per-tech CFs
  6. Apply EIA annual CF calibration to VRE SYSHECF
  7. Write everything to eps-us folders (SHELF + SYSHECF)

EFS data semantics:
  EFS has Sector/Subsector breakdowns:
    Residential: space heating and cooling, water heating, clothes and dish washing, other
    Commercial:  space heating and cooling, water heating, other
    Industrial:  machine drives, process heat, other
    Transportation: light-duty vehicles, medium-duty trucks, heavy-duty trucks, other
  Space conditioning is split into heating/cooling via RECS monthly split.

eps-us SHELF categories the pipeline maps to:
  residential-{heating, cooling, lighting, appliances, other, envelope}
  commercial-{heating, cooling, lighting, appliances, other, envelope}
  industry, LDVs, HDVs, aircraft, rail, ships, motorbikes
  datacenters, district-heat-hydrogen, geoeng
  (envelope, datacenters, district-heat-hydrogen, geoeng = always zero per EPS convention)

Args:
  --peak-top-n   initial pinned days per peak slice (k-means start). default 5
  --max-peak-days  iterative reassignment cap. default 365 (no cap)
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

CAMBIUM_HOURLY = ROOT / "data" / "cambium24_midcase_national" / "Cambium24_MidCase_hourly_usa_2025.csv"
CAMBIUM_ANNUAL = ROOT / "data" / "cambium24_midcase_national" / "Cambium24_MidCase_annual_national.csv"
EFS_ZIP        = ROOT / "data" / "efs" / "EFSLoadProfile_Reference_Moderate.zip"

EPS_SHELF   = Path(r"C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SHELF")
EPS_SYSHECF = Path(r"C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SYSHECF")

# EIA annual CF targets (Table 4.8.B, capacity-weighted national averages)
EIA_CF_TARGETS = {
    'solar-pv':      0.232,
    'solar-pv-dist': 0.170,
    'solar-thermal': 0.250,
    'onshore-wind':  0.343,
    'offshore-wind': 0.420,
}

# Cambium per-tech column mapping (matches SYSHECF_CATEGORIES)
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

# SHELF categories that should always be zero
SHELF_ZERO_CATEGORIES = {
    'residential-envelope', 'commercial-envelope',
    'aircraft', 'ships', 'motorbikes',
    'datacenters', 'district-heat-hydrogen', 'geoeng',
}

SLICES = SLICE_NAMES  # ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']
HOUR_COLS = [f'Hour{h}' for h in range(24)]


# ---------------------------------------------------------------------------
# Cambium 2024 hourly load
# ---------------------------------------------------------------------------

def load_cambium_hourly(path: Path) -> pd.DataFrame:
    """Parse Cambium 2024 hourly CSV. Returns DataFrame indexed by timestamp with all columns numeric."""
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
    """Return dict of column -> value for the t=2025 row."""
    df = pd.read_csv(path)
    row = df[df['t'] == 2025]
    if row.empty:
        raise RuntimeError("No 2025 row in Cambium annual file")
    return row.iloc[0].to_dict()


# ---------------------------------------------------------------------------
# EFS national hourly (per-category demand)
# ---------------------------------------------------------------------------

def load_efs_national(zip_path: Path, year: int = 2025) -> pd.DataFrame:
    """Load EFS Reference/Moderate national hourly per-subsector demand.

    Returns DataFrame with hourly index (8760), columns are eps-us SHELF
    categories. Energy is in MWh per hour.
    """
    import zipfile
    import io
    try:
        import zipfile_deflate64  # noqa: F401
    except ImportError:
        raise ImportError("zipfile_deflate64 required for EFS archive")

    # Pick nearest EFS year (EFS published in 5-year intervals)
    efs_years = [2018, 2020, 2024, 2030, 2040, 2050]
    efs_year = min(efs_years, key=lambda y: abs(y - year))

    needed = ['Electrification', 'TechnologyAdvancement', 'Year',
              'LocalHourID', 'Sector', 'Subsector', 'LoadMW']
    frames = []
    with zipfile.ZipFile(zip_path) as zf:
        # find the main CSV
        candidates = [n for n in zf.namelist() if n.endswith('.csv')]
        if not candidates:
            raise FileNotFoundError(f"No CSV inside {zip_path}")
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
    if not frames:
        raise ValueError(f"No EFS data found for year {efs_year}")
    agg = pd.concat(frames).groupby(['LocalHourID', 'Sector', 'Subsector'], as_index=False)['LoadMW'].sum()
    print(f"  [efs] year used = {efs_year}; rows = {len(agg)}")

    pivoted = agg.pivot_table(index='LocalHourID', columns=['Sector', 'Subsector'],
                              values='LoadMW', aggfunc='sum', fill_value=0.0).sort_index()
    if len(pivoted.index) != 8760:
        raise ValueError(f"EFS national hourly should have 8760 rows; got {len(pivoted.index)}")

    # Use Cambium 2025 calendar for timestamps (matches the clustering input)
    ts = pd.date_range(start='2025-01-01 00:00:00', periods=8760, freq='h')
    pivoted.index = ts

    def col(sec, sub):
        return pivoted[(sec, sub)].astype(float) if (sec, sub) in pivoted.columns else pd.Series(0.0, index=ts)

    # Raw EFS subsectors
    res_spaceconditioning = col('Residential', 'space heating and cooling')
    res_waterheating      = col('Residential', 'water heating')
    res_clothes           = col('Residential', 'clothes and dish washing/drying')
    res_other             = col('Residential', 'other')

    com_spaceconditioning = col('Commercial', 'space heating and cooling')
    com_waterheating      = col('Commercial', 'water heating')
    com_other             = col('Commercial', 'other')

    ind_machine    = col('Industrial', 'machine drives')
    ind_process    = col('Industrial', 'process heat')
    ind_other      = col('Industrial', 'other')

    tr_ldv = col('Transportation', 'light-duty vehicles')
    tr_mdv = col('Transportation', 'medium-duty trucks')
    tr_hdv = col('Transportation', 'heavy-duty trucks')
    tr_other = col('Transportation', 'other')

    # Split residential space conditioning into heating/cooling via monthly proxy:
    # use cooling share = max(0, min(1, (avg_temp - 15)/15)) crude proxy.
    # Better: use RECS monthly split. For now, use a simple heating-vs-cooling
    # rule based on the residential cooling shape itself if available; otherwise
    # use a default seasonal split.
    # SIMPLE APPROACH: assign all summer (Apr-Sep) hours to cooling, all winter to heating.
    # This is approximate; refine with RECS monthly split if needed.
    summer_months = {4, 5, 6, 7, 8, 9}
    is_summer = pd.Series([ts_.month in summer_months for ts_ in ts], index=ts)

    # Better: split by season-weighted shares (RECS-ish):
    # Heating dominates Nov-Mar (90% heat), Apr-Oct mostly cooling (90% cool)
    monthly_heating_share = {
        1: 0.95, 2: 0.92, 3: 0.75, 4: 0.40, 5: 0.15, 6: 0.05,
        7: 0.03, 8: 0.03, 9: 0.08, 10: 0.30, 11: 0.70, 12: 0.90,
    }
    heat_share = pd.Series([monthly_heating_share[ts_.month] for ts_ in ts], index=ts)
    cool_share = 1.0 - heat_share

    res_heating = res_spaceconditioning * heat_share
    res_cooling = res_spaceconditioning * cool_share
    com_heating = com_spaceconditioning * heat_share
    com_cooling = com_spaceconditioning * cool_share

    # Map to eps-us SHELF categories
    out = pd.DataFrame(index=ts)
    # Residential — heating, cooling already split
    out['residential-heating']    = res_heating
    out['residential-cooling']    = res_cooling
    # Lighting/appliances/other — EFS doesn't separately give lighting.
    # Split residential 'other' into lighting (~28% per RECS), and remaining other.
    # Appliances = waterheating + clothes washing
    out['residential-lighting']   = res_other * 0.28
    out['residential-appliances'] = res_waterheating + res_clothes
    out['residential-other']      = res_other * 0.72
    # Commercial
    out['commercial-heating']     = com_heating
    out['commercial-cooling']     = com_cooling
    # Commercial lighting (CBECS): ~21% of commercial 'other'
    out['commercial-lighting']    = com_other * 0.21
    out['commercial-appliances']  = com_waterheating + (com_other * 0.10)
    out['commercial-other']       = com_other * 0.69
    # Industry — all industrial subsectors aggregated
    out['industry']               = ind_machine + ind_process + ind_other
    # Transport
    out['LDVs']                   = tr_ldv
    out['HDVs']                   = tr_mdv + tr_hdv
    # Other transport modes — split tr_other equally for now (EFS doesn't differentiate)
    out['rail']                   = tr_other * 0.40
    # aircraft, ships, motorbikes get zero (per eps-us convention)

    # Zero-out always-zero categories
    for cat in SHELF_ZERO_CATEGORIES:
        if cat in out.columns:
            out[cat] = 0.0

    return out


# ---------------------------------------------------------------------------
# Write SHELF / SYSHECF
# ---------------------------------------------------------------------------

SHELF_HEADER_LABEL = 'Unit: dimensionless (ratio of electricity demand in this hour to annual demand)'
SYSHECF_HEADER_LABEL = 'Unit: dimensionless (ratio of expected hourly capacity factor)'


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
    # Use legacy header style: first cell is the human-readable tech name (lowercase with spaces)
    display = tech.replace('-', ' ').replace('CCS', 'ccs').replace('SMR', 'SMR').replace('MSW', 'MSW')
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


# ---------------------------------------------------------------------------
# EIA calibration of VRE SYSHECF (preserves shape, scales to target annual CF)
# ---------------------------------------------------------------------------

def calibrate_to_eia(syshecf_table: pd.DataFrame, days_per_slice: dict, target_cf: float) -> pd.DataFrame:
    """Scale all values so annual CF (slice-weighted) = target_cf."""
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
    # Clip to [0, 1]
    out = out.clip(lower=0.0, upper=1.0)
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(peak_top_n: int = 5, max_peak_days: int = 365):
    print("="*72)
    print("US National K6/H24 rebuild (Cambium 2024 MidCase 2025 + EFS national)")
    print("="*72)

    print(f"[load] Cambium hourly: {CAMBIUM_HOURLY}")
    camb = load_cambium_hourly(CAMBIUM_HOURLY)
    print(f"  {len(camb)} rows; annual busbar = {camb['busbar_load'].sum()/1e6:.1f} TWh; "
          f"peak busbar = {camb['busbar_load'].max()/1e3:.1f} GW")

    print(f"[load] Cambium annual: {CAMBIUM_ANNUAL}")
    camb_ann = load_cambium_annual_2025(CAMBIUM_ANNUAL)

    # ---- Cluster on Cambium net load ----
    print(f"[cluster] cluster_days (peak_top_n={peak_top_n}, max_peak_days={max_peak_days})")
    total_demand = camb['busbar_load']
    solar_gen = camb['upv_MWh'] + camb['distpv_MWh']
    wind_gen = camb['wind-ons_MWh'] + camb['wind-ofs_MWh']
    cr = cluster_days(
        total_demand, solar_gen, wind_gen,
        peak_top_n=peak_top_n,
        max_peak_days=max_peak_days,
        feature_weight_mode='netload_focus',
        summer_months=(6, 7, 8),
        winter_months=(11, 12, 1, 2),
    )
    print(f"  NRMSE = {cr.nrmse:.4f}; days_per_timeslice = {cr.days_per_timeslice}")
    print(f"  Summer Peak ({len(cr.sp_top_days)} days): {cr.sp_top_days}")
    print(f"  Winter Peak ({len(cr.wp_top_days)} days): {cr.wp_top_days}")

    # ---- Load EFS national hourly per-category demand ----
    print(f"[load] EFS national hourly")
    efs = load_efs_national(EFS_ZIP, year=2025)
    print(f"  EFS shape: {efs.shape}; non-zero categories: {(efs.sum(axis=0) > 0).sum()}")
    annual_by_cat = efs.sum(axis=0)
    annual_total = annual_by_cat.sum()
    print(f"  EFS total annual = {annual_total/1e6:.1f} TWh")
    for cat in efs.columns:
        if annual_by_cat[cat] > 0:
            print(f"    {cat}: {annual_by_cat[cat]/1e6:.1f} TWh ({100*annual_by_cat[cat]/annual_total:.1f}%)")

    # ---- Build SHELF per category ----
    print(f"[shelf] building SHELF per category")
    shelf_dir = EPS_SHELF
    shelf_dir.mkdir(exist_ok=True, parents=True)

    # All eps-us SHELF categories (including zero-only)
    ALL_SHELF = [
        'residential-heating', 'residential-cooling', 'residential-lighting',
        'residential-appliances', 'residential-other', 'residential-envelope',
        'commercial-heating', 'commercial-cooling', 'commercial-lighting',
        'commercial-appliances', 'commercial-other', 'commercial-envelope',
        'industry', 'LDVs', 'HDVs', 'aircraft', 'rail', 'ships', 'motorbikes',
        'datacenters', 'district-heat-hydrogen', 'geoeng',
    ]
    for cat in ALL_SHELF:
        if cat in SHELF_ZERO_CATEGORIES:
            write_shelf(shelf_dir, cat, None, all_zero=True)
            continue
        if cat not in efs.columns or efs[cat].sum() <= 0:
            print(f"  WARN: {cat} not in EFS or zero; writing zeros")
            write_shelf(shelf_dir, cat, None, all_zero=True)
            continue
        tbl = build_shelf_for_category(efs[cat], cr)
        write_shelf(shelf_dir, cat, tbl, all_zero=False)
    print(f"  wrote {len(ALL_SHELF)} SHELF files")

    # ---- Build SYSHECF per tech ----
    print(f"[syshecf] building SYSHECF per tech")
    syshecf_dir = EPS_SYSHECF
    syshecf_dir.mkdir(exist_ok=True, parents=True)

    # Compute per-tech hourly CFs
    cf_series_by_tech: dict[str, pd.Series] = {}
    for tech, (mwh_col, mw_col) in CAMBIUM_TECH_COLS.items():
        if mwh_col not in camb.columns:
            print(f"  SKIP {tech}: column {mwh_col} not in Cambium hourly")
            continue
        cap_mw = float(camb_ann.get(mw_col, 0.0))
        if cap_mw <= 0:
            print(f"  SKIP {tech}: capacity = {cap_mw} MW")
            continue
        cf = camb[mwh_col].clip(lower=0.0) / cap_mw
        cf = cf.clip(upper=1.0)
        cf_series_by_tech[tech] = cf

    days_per_slice = cr.days_per_timeslice
    syshecf_count = 0
    for tech, cf in cf_series_by_tech.items():
        tbl = _build_variable_table(cf, cr)
        # EIA calibration for VRE techs
        if tech in EIA_CF_TARGETS:
            before_annual_cf = sum(float(tbl.loc[sl, HOUR_COLS].sum()) * days_per_slice[sl]
                                   for sl in SLICES) / 8760.0
            tbl = calibrate_to_eia(tbl, days_per_slice, EIA_CF_TARGETS[tech])
            after_annual_cf = sum(float(tbl.loc[sl, HOUR_COLS].sum()) * days_per_slice[sl]
                                  for sl in SLICES) / 8760.0
            print(f"  {tech}: pre-calib CF = {before_annual_cf:.4f}, "
                  f"target = {EIA_CF_TARGETS[tech]}, post-calib CF = {after_annual_cf:.4f}")
        write_syshecf(syshecf_dir, tech, tbl)
        syshecf_count += 1
    print(f"  wrote {syshecf_count} SYSHECF files (variable techs)")

    # Non-variable techs: keep existing files in eps-us (template-only). We do NOT
    # overwrite these because they're not in Cambium or have constant CFs.
    print(f"  (non-variable techs left as existing eps-us templates: lignite, lignite-CCS,")
    print(f"   heavy-or-residual-oil, crude-oil, hydrogen-CC, hydrogen-CT, SMR, MSW, steam-turbine,")
    print(f"   combined-cycle-CCS, hard-coal-CCS)")

    # ---- Write days_per_timeslice ----
    out_days_path = shelf_dir / 'SHELF-days-per-timeslice.csv'
    write_days_per_timeslice(out_days_path, days_per_slice)
    print(f"[days] wrote {out_days_path}")
    print(f"  Winter={days_per_slice['Winter']}  Spring={days_per_slice['Spring']}  "
          f"Summer={days_per_slice['Summer']}  Fall={days_per_slice['Fall']}  "
          f"SP={days_per_slice['Summer Peak']}  WP={days_per_slice['Winter Peak']}")

    # ---- Final summary: aggregate Summer Peak gross/net peaks from the rebuild ----
    print(f"\n[verify] Aggregate Summer Peak slice from this rebuild:")
    # Build aggregate SHELF by summing across categories weighted by annual energy
    aggregate_demand = sum(efs[cat] for cat in efs.columns if efs[cat].sum() > 0)
    # Peak hour values for Summer Peak slice
    sp_days = set(cr.sp_top_days)
    wp_days = set(cr.wp_top_days)
    is_sp = pd.Series([d.dayofyear in sp_days for d in aggregate_demand.index], index=aggregate_demand.index)
    sp_subset = aggregate_demand[is_sp]
    sp_by_hour = sp_subset.groupby(sp_subset.index.hour).mean()
    print(f"  Summer Peak slice gross peak: {sp_by_hour.max()/1e3:.1f} GW @ hr {int(sp_by_hour.idxmax())}")
    print(f"  Summer Peak slice 24-hr mean: {sp_by_hour.mean()/1e3:.1f} GW")
    print(f"  (Cambium 2024 busbar Summer Peak gross peak should be ~745 GW)")

    print(f"\n[done] All outputs written.")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--peak-top-n', type=int, default=5)
    ap.add_argument('--max-peak-days', type=int, default=365)
    args = ap.parse_args()
    main(peak_top_n=args.peak_top_n, max_peak_days=args.max_peak_days)
