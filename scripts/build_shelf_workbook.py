"""Build the canonical SHELF Excel workbook as a self-contained derivation.

Two versions of the workbook can be built:

  --version 4.0  (default)  the workbook EPS 4.0.x reads: timeslices Winter / Spring / Summer / Fall /
                 Summer Peak / Winter Peak, one SHELF-<category> tab for each of 22 categories.
  --version 5.0  the workbook EPS 5.0 reads: timeslices Representative Day 1-4 / Net Peak Summer Day /
                 Net Peak Winter Day, data centers split by end use, district heat / hydrogen and
                 geoengineering on the total-load shape, per-process industry tabs, and whole-industry
                 load shapes for 25 industries. The additions live in scripts/shelf_v5/ (see its README).

Workbook tabs written here (in order), for both versions:
  - About
  - Clustering            — days-per-timeslice + DOY -> slice (editable)
  - Annual category totals — per-category 2025 annual TWh (parameter tab)
  - ResStock national source — TZ-corrected aggregation across 49 states
  - ComStock national source — TZ-corrected aggregation across 51 state folders
  - EFS source            — filtered Reference/Moderate Industrial+Transport
  - Cambium hourly source — Cambium 2024 MidCase national 2025 (clustering ref)
  - SHELF-days-per-timeslice (output)
  - SHELF-<category> × 22 (outputs, dark blue) in subscript order
  - SHELF-datacenters (output, dark blue) — flat 24/7

Inputs are found through scripts/shelf_v5/paths.py (command-line option, environment variable,
local_paths.yml, or a default inside or beside the repository); nothing points at a user folder.
Each hourly source is read from its saved national series in data/national_aggregated/ when one
exists, and rebuilt from the raw download only when it does not or when --refresh names it.

Output: <out>/elec/SHELF/Seasonal Hourly Equipment Load Factors by End Use.xlsx (and, for 5.0,
<out>/ctrl-settings/ICwIwLF/). <out> defaults to output/us_shelf_<version>/ in this repository; point
it at an eps-us InputData folder to write in place. The saved workbook holds formulas without
values: recalculate and export the CSVs with scripts/shelf_v5/recalc_export.py.

Options that change the numbers (the defaults reproduce eps-us develop; with --version 5.0 that means
--buildings amy2012 --building-clock eastern, with television counted):
    --buildings {amy2012,typical}  NREL runs with the actual weather of 2012 (5.0 default) or typical-year weather (4.0)
    --building-clock {eastern,pipeline}  eastern (5.0 default): no time-zone shift, the files are already Eastern;
                                 pipeline (4.0): the old shift, which moves western states twice
    --television {omit,other}    (amy2012) television is counted in residential-other by default; omit leaves it out
    --building-delay-hours H     delay every building hourly series by H hours (a calibration; off on develop)
    --align-weekdays             (typical-year buildings) match the buildings' weekends to the clustering calendar's
    --efs-clock {eastern,local}  eastern (5.0 default): EFS charging and rail moved from local hours to Eastern time
    --siels-tennessee central    Tennessee on Central time in the SIELS industry shapes

Run:
    python scripts/build_shelf_workbook.py                    # 4.0.x
    python scripts/build_shelf_workbook.py --version 5.0
"""
from __future__ import annotations
import argparse
import csv
import sys
import zipfile
import io
from pathlib import Path
import datetime as dt
import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from shelf_v5 import buildings as bld, efs_clock, names as slice_names, paths as shelf_paths
from state_pipeline.readers.resstock_reader import read_resstock_hourly
from state_pipeline.readers.comstock_reader import read_comstock_hourly

# Same list as state_pipeline.builders.clustering.SLICE_NAMES. That module needs scikit-learn, so it is
# imported only when the clustering is re-run (see get_clustering).
SLICE_NAMES = slice_names.CANONICAL

CAMBIUM_HOURLY = shelf_paths.lookup('cambium_hourly')
CACHE_DIR = shelf_paths.lookup('cache_dir')
WORKBOOK_NAME = "Seasonal Hourly Equipment Load Factors by End Use.xlsx"

# State LST → ET offsets (matches rebuild_us_national_v2.py)
STATE_TZ_OFFSET_TO_ET = {
    'CT': 0, 'DE': 0, 'DC': 0, 'FL': 0, 'GA': 0, 'IN': 0, 'KY': 0, 'ME': 0,
    'MD': 0, 'MA': 0, 'MI': 0, 'NH': 0, 'NJ': 0, 'NY': 0, 'NC': 0, 'OH': 0,
    'PA': 0, 'RI': 0, 'SC': 0, 'VT': 0, 'VA': 0, 'WV': 0,
    'AL': 1, 'AR': 1, 'IA': 1, 'IL': 1, 'KS': 1, 'LA': 1, 'MN': 1, 'MS': 1,
    'MO': 1, 'NE': 1, 'ND': 1, 'OK': 1, 'SD': 1, 'TN': 1, 'TX': 1, 'WI': 1,
    'AZ': 2, 'CO': 2, 'ID': 2, 'MT': 2, 'NM': 2, 'UT': 2, 'WY': 2,
    'CA': 3, 'NV': 3, 'OR': 3, 'WA': 3,
    'AK': 4, 'HI': 5,
}

# SHELF output category order (from existing EPS-test-folder file, plus datacenters).
SHELF_OUTPUT_ORDER = [
    'days-per-timeslice',
    'residential-heating',
    'residential-cooling',
    'residential-envelope',
    'residential-lighting',
    'residential-appliances',
    'residential-other',
    'commercial-heating',
    'commercial-cooling',
    'commercial-envelope',
    'commercial-lighting',
    'commercial-appliances',
    'commercial-other',
    'LDVs',
    'HDVs',
    'aircraft',
    'rail',
    'ships',
    'motorbikes',
    'industry',
    'district-heat-hydrogen',
    'geoeng',
    'datacenters',
]

# Categories sourced from ResStock (column name in aggregated CSV)
RESSTOCK_CATS = ['residential-heating', 'residential-cooling', 'residential-lighting',
                 'residential-appliances', 'residential-other']
COMSTOCK_CATS = ['commercial-heating', 'commercial-cooling', 'commercial-lighting',
                 'commercial-appliances', 'commercial-other']
# EFS categories — mapped from EFS Industrial + Transportation subsectors
EFS_CATS = ['industry', 'LDVs', 'HDVs', 'rail']
# Always-zero categories (EPS convention)
ZERO_CATS = ['residential-envelope', 'commercial-envelope',
             'aircraft', 'ships', 'motorbikes',
             'district-heat-hydrogen', 'geoeng']
# Flat 24/7 categories
FLAT_CATS = ['datacenters']

# Approximate 2025 annual TWh per category for the AEO/BCEU "Annual category totals"
# tab. These are placeholders the user can edit. They reflect typical US national
# AEO Reference Case values; do NOT propagate into the LF math.
ANNUAL_TWH_DEFAULTS = {
    'residential-heating':    150.0,
    'residential-cooling':    270.0,
    'residential-envelope':     0.0,
    'residential-lighting':   120.0,
    'residential-appliances': 600.0,
    'residential-other':      360.0,
    'commercial-heating':      80.0,
    'commercial-cooling':     190.0,
    'commercial-envelope':      0.0,
    'commercial-lighting':    190.0,
    'commercial-appliances':  400.0,
    'commercial-other':       640.0,
    'industry':              1000.0,
    'LDVs':                    50.0,
    'HDVs':                     5.0,
    'aircraft':                 0.0,
    'rail':                     8.0,
    'ships':                    0.0,
    'motorbikes':               0.0,
    'district-heat-hydrogen':   0.0,
    'geoeng':                   0.0,
    'datacenters':            245.0,
}

ANNUAL_TWH_SOURCES = {
    'residential-heating':    'bldgs/BCEU/BAU Components Energy Use.xlsx — urban+rural residential heating, electricity',
    'residential-cooling':    'bldgs/BCEU/BAU Components Energy Use.xlsx — urban+rural residential cooling, electricity',
    'residential-envelope':   'EPS convention: 0 in start year',
    'residential-lighting':   'bldgs/BCEU/BAU Components Energy Use.xlsx — urban+rural residential lighting, electricity',
    'residential-appliances': 'bldgs/BCEU/BAU Components Energy Use.xlsx — urban+rural residential appl + water heat, electricity',
    'residential-other':      'bldgs/BCEU/BAU Components Energy Use.xlsx — urban+rural residential other, electricity',
    'commercial-heating':     'bldgs/BCEU/BAU Components Energy Use.xlsx — commercial heating, electricity',
    'commercial-cooling':     'bldgs/BCEU/BAU Components Energy Use.xlsx — commercial cooling, electricity',
    'commercial-envelope':    'EPS convention: 0 in start year',
    'commercial-lighting':    'bldgs/BCEU/BAU Components Energy Use.xlsx — commercial lighting, electricity',
    'commercial-appliances':  'bldgs/BCEU/BAU Components Energy Use.xlsx — commercial appliances, electricity',
    'commercial-other':       'bldgs/BCEU/BAU Components Energy Use.xlsx — commercial other, electricity',
    'industry':               'indst/BIFUbC/BIFUbC-electricity.csv (AEO industrial subsectors aggregated)',
    'LDVs':                   'trans calculator (AEO transport, light-duty vehicles)',
    'HDVs':                   'trans calculator (AEO transport, medium + heavy-duty trucks)',
    'aircraft':               'EPS convention: 0 in start year',
    'rail':                   'trans calculator (~40% of EFS "other transport")',
    'ships':                  'EPS convention: 0 in start year',
    'motorbikes':             'EPS convention: 0 in start year',
    'district-heat-hydrogen': 'EPS convention: 0 in start year (ramps post-2030)',
    'geoeng':                 'EPS convention: 0 in start year (ramps post-2030)',
    'datacenters':            'BCEU/AEO data-center electricity (~245 TWh in 2025 per EIA)',
}

SLICES = list(SLICE_NAMES)
HOUR_COLS = [f'Hour{h}' for h in range(24)]

HEADER_FILL = PatternFill(start_color='305496', end_color='305496', fill_type='solid')
HEADER_FONT = Font(bold=True, color='FFFFFF')
SECTION_FILL = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
SECTION_FONT = Font(bold=True)
PURPOSE_FILL = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
OUTPUT_TAB_COLOR = '1F3864'
LEFT_TOP_WRAP = Alignment(horizontal='left', vertical='top', wrap_text=True)


# ---------------------------------------------------------------------------
# Aggregation (with caching)
# ---------------------------------------------------------------------------

def _tz_correct(df: pd.DataFrame, state: str) -> pd.DataFrame:
    offset = STATE_TZ_OFFSET_TO_ET.get(state, 0)
    if offset == 0:
        return df
    out = df.copy()
    for col in out.columns:
        out[col] = np.roll(out[col].values, offset)
    return out


def _aggregate_states(kind: str, state_dirs: list, state_of, reader, shift: bool = True,
                      hours: int | None = None) -> pd.DataFrame:
    """Add the states' hourly series. shift=True moves each state later by its distance from Eastern time
    (clock 'pipeline'); shift=False adds them as they are (clock 'eastern': the files are already stamped in
    Eastern Standard Time). hours, if given, is the number of hours every state must have (no silent trimming)."""
    how = 'TZ-corrected to ET' if shift else 'no time-zone shift: files already on Eastern Standard Time'
    print(f"  [{kind}] aggregating {len(state_dirs)} states ({how})...")
    combined: pd.DataFrame | None = None
    report: dict = {}
    skipped = []
    for sd in state_dirs:
        state = state_of(sd)
        try:
            sh = reader(str(sd), report)
        except Exception as e:
            print(f"    SKIP {state}: {e}")
            skipped.append(state)
            continue
        if hours is not None and len(sh) != hours:
            raise ValueError(f"[{kind}] {state}: {len(sh)} hours, expected {hours}")
        if shift:
            sh = _tz_correct(sh, state)
        combined = sh.copy() if combined is None else combined.add(sh, fill_value=0)
        print(f"    + {state}", flush=True)
    print(f"  [{kind}] states skipped: {skipped or 'none'}")
    print(f"  [{kind}] end uses the category map expects but a file lacks: {sorted(report.get('missing', [])) or 'none'}")
    print(f"  [{kind}] end uses in the files that no category takes: {sorted(report.get('unmapped', [])) or 'none'}")
    print(f"  [{kind}] total / net / generation columns left out on purpose: {sorted(report.get('totals', [])) or 'none'}")
    return combined


def _cached(kind: str, cache_name: str, raw: Path, refresh: bool, build) -> tuple[pd.DataFrame, str]:
    """Saved national series if present (and not refreshing), else build it from the raw download and save it.
    Returns (hourly frame, 'saved series' or 'raw files')."""
    cache = CACHE_DIR / cache_name
    if cache.exists() and not refresh:
        print(f"  [{kind}] using cache {cache}")
        return pd.read_csv(cache, index_col=0, parse_dates=True), 'saved series'
    if not Path(raw).exists():
        raise FileNotFoundError(
            f"[{kind}] no saved series at {cache} and no raw download at {raw}. "
            f"Set its location (see local_paths.example.yml) or restore the saved series.")
    CACHE_DIR.mkdir(exist_ok=True, parents=True)
    combined = build(Path(raw))
    combined.to_csv(cache)
    print(f"  [{kind}] cached -> {cache}")
    return combined, 'raw files'


def aggregate_resstock_cached(root: Path, refresh: bool = False, source: str = 'typical',
                              clock: str = 'pipeline', television: str = 'omit') -> tuple[pd.DataFrame, str]:
    # the actual-2012-weather files hold exactly 8,760 hours; the typical-year files are trimmed to 8,760 by the reader
    extra = bld.television_end_uses(television)
    return _cached('resstock', bld.cache_name('resstock', source, clock, television), root, refresh,
                   lambda r: _aggregate_states(
        'resstock', sorted([p for p in r.glob('state=*') if p.is_dir()]),
        lambda sd: sd.name.split('=')[1], lambda d, rep: read_resstock_hourly(d, rep, extra),
        shift=(clock == 'pipeline'), hours=8760 if source == 'amy2012' else None))


def aggregate_comstock_cached(root: Path, refresh: bool = False, source: str = 'typical',
                              clock: str = 'pipeline') -> tuple[pd.DataFrame, str]:
    return _cached('comstock', bld.cache_name('comstock', source, clock), root, refresh, lambda r: _aggregate_states(
        'comstock', sorted([p for p in r.iterdir() if p.is_dir() and len(p.name) == 2]),
        lambda sd: sd.name, read_comstock_hourly, shift=(clock == 'pipeline'),
        hours=8760 if source == 'amy2012' else None))


def load_efs_cached(efs_zip: Path, refresh: bool = False, year: int = 2024) -> tuple[pd.DataFrame, str]:
    return _cached('efs', "efs_national_hourly.csv", efs_zip, refresh, lambda z: load_efs_filtered(z, year=year))


def load_efs_filtered(efs_zip: Path, year: int = 2024) -> pd.DataFrame:
    """Return 8760×N DataFrame of EFS national hourly demand by subsector,
    filtered to Reference/Moderate/year. Columns: timestamp index, plus
    industry / LDVs / HDVs / rail derived from EFS subsectors.
    """
    print(f"  [efs] loading + filtering...")
    try:
        import zipfile_deflate64  # noqa: F401  (registers Deflate64 codec on import)
    except ImportError:
        raise ImportError("EFS zip uses Deflate64; install with `pip install zipfile_deflate64`")
    needed = ['Electrification', 'TechnologyAdvancement', 'Year',
              'LocalHourID', 'Sector', 'Subsector', 'LoadMW']
    frames = []
    with zipfile.ZipFile(efs_zip) as zf:
        member = [n for n in zf.namelist() if n.endswith('.csv')][0]
        with zf.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding='utf-8-sig', newline='')
            reader = pd.read_csv(text, usecols=needed, chunksize=500_000)
            for chunk in reader:
                m = ((chunk['Electrification'].str.lower() == 'reference')
                     & (chunk['TechnologyAdvancement'].str.lower() == 'moderate')
                     & (pd.to_numeric(chunk['Year'], errors='coerce') == year))
                f = chunk.loc[m]
                if f.empty:
                    continue
                frames.append(f.groupby(['LocalHourID', 'Sector', 'Subsector'],
                                        as_index=False)['LoadMW'].sum())
    agg = pd.concat(frames).groupby(['LocalHourID', 'Sector', 'Subsector'],
                                     as_index=False)['LoadMW'].sum()
    piv = agg.pivot_table(index='LocalHourID', columns=['Sector', 'Subsector'],
                          values='LoadMW', aggfunc='sum', fill_value=0.0).sort_index()
    ts = pd.date_range('2018-01-01', periods=8760, freq='h')
    piv.index = ts

    def col(sec, sub):
        return piv[(sec, sub)].astype(float) if (sec, sub) in piv.columns else pd.Series(0.0, index=ts)

    out = pd.DataFrame(index=ts)
    out['industry'] = (col('Industrial', 'machine drives')
                       + col('Industrial', 'process heat')
                       + col('Industrial', 'other'))
    out['LDVs'] = col('Transportation', 'light-duty vehicles')
    out['HDVs'] = (col('Transportation', 'medium-duty trucks')
                   + col('Transportation', 'heavy-duty trucks'))
    out['rail'] = col('Transportation', 'other') * 0.40
    return out


def load_cambium_raw_rows() -> list[list[str]]:
    with open(CAMBIUM_HOURLY, newline='') as f:
        return list(csv.reader(f))


def load_cambium_for_clustering() -> pd.DataFrame:
    rows = load_cambium_raw_rows()
    headers = rows[5]
    idx = {h: i for i, h in enumerate(headers)}
    timestamps, vals = [], {'busbar_load': [], 'upv_MWh': [], 'distpv_MWh': [],
                            'wind-ons_MWh': [], 'wind-ofs_MWh': []}
    for r in rows[6:]:
        try:
            ts = dt.datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S')
        except (ValueError, IndexError):
            continue
        timestamps.append(ts)
        for c in vals:
            try:
                vals[c].append(float(r[idx[c]]))
            except (ValueError, IndexError):
                vals[c].append(0.0)
    return pd.DataFrame(vals, index=pd.DatetimeIndex(timestamps))


def _read_saved_clustering() -> tuple[dict, dict]:
    saved = shelf_paths.lookup('clustering_list')
    with open(saved, newline='') as f:
        rows = list(csv.reader(f))[1:]
    assignment = {int(d): sl for d, sl in rows}
    if sorted(assignment) != list(range(1, 366)) or set(assignment.values()) - set(SLICE_NAMES):
        raise ValueError(f'{saved} is not a day-to-timeslice list for days 1-365')
    return {sl: sum(1 for v in assignment.values() if v == sl) for sl in SLICE_NAMES}, assignment


def get_clustering(mode: str = 'auto') -> tuple[dict, dict, str]:
    """Days per timeslice and the day -> timeslice list, in the clustering code's own timeslice names.

    mode 'rerun': run cluster_days_repday on the Cambium file (needs scikit-learn).
    mode 'saved': read data/cambium24_midcase_national/k6_slice_assignment_repday.csv.
    mode 'auto' : re-run when scikit-learn is installed, otherwise use the saved list and say so.
    Returns (days_per_timeslice, slice_assignment, where it came from).
    """
    cluster = None
    if mode in ('auto', 'rerun'):
        try:
            from state_pipeline.builders.clustering_repday import cluster_days_repday as cluster
        except ImportError as e:
            if mode == 'rerun':
                raise
            print(f"  [clustering] cannot re-run ({e}); using the saved day-to-timeslice list")
    if cluster is None:
        days, assignment = _read_saved_clustering()
        return days, assignment, 'saved list'
    cambium_df = load_cambium_for_clustering()
    cr = cluster(
        cambium_df['busbar_load'],
        cambium_df['upv_MWh'] + cambium_df['distpv_MWh'],
        cambium_df['wind-ons_MWh'] + cambium_df['wind-ofs_MWh'],
        peak_top_n=1, max_peak_days=365,
    )
    assignment = {int(k): v for k, v in cr.slice_assignment.to_dict().items()}
    try:
        _, saved = _read_saved_clustering()
        moved = sum(1 for d in saved if assignment.get(d) != saved[d])
        print(f"  [clustering] re-run differs from the saved list on {moved} of 365 days"
              + ("" if not moved else "  <-- WARNING: outputs will not match files built from the saved list"))
    except FileNotFoundError:
        pass
    return dict(cr.days_per_timeslice), assignment, 're-run on the Cambium file'


# ---------------------------------------------------------------------------
# About tab + parameter/source tabs
# ---------------------------------------------------------------------------

def _building_sources(buildings: str, clock: str, television: str, delay: float = 0.0) -> list[dict]:
    """The two About-tab source entries for the home and business load shapes."""
    if buildings == 'amy2012':
        shift = ('each state is then moved later by its distance from Eastern time (Central 1 hour, Mountain 2, '
                 'Pacific 3, Alaska 4, Hawaii 5), as in earlier versions of this file (see "Buildings clock" '
                 'below)' if clock == 'pipeline' else
                 'the states are added as they are, with no time-zone shift, because the files are already on '
                 'Eastern Standard Time (see "Buildings clock" below)')
        tv = (' Television is counted in residential-other.' if television == 'other' else
              ' Television, a separate line in this release, is not counted in any category (see "Buildings '
              'source and calendar" below).')
        dl = (f' Each hourly series is then delayed by {delay:g} hours (see "Buildings delay" below).' if delay else '')
        return [
            {
                'purpose': 'Residential Hourly End-Use Load Profiles by State',
                'source':  'NREL',
                'publication': 'NREL End-Use Load Profiles for the U.S. Building Stock (ResStock 2025 Release 1, '
                               'actual 2012 weather)',
                'year':    2025,
                'url':     'https://www.nrel.gov/buildings/end-use-load-profiles.html',
                'info':    'Baseline housing stock (upgrade 0), simulated with the actual weather of 2012 rather '
                          'than a typical year: state files for 49 states and DC (Hawaii is not in the release). Each '
                          'file is 15-minute interval data stamped at the end of the interval in Eastern Standard '
                          'Time (no daylight saving), from 1 January to 30 December 2012, 8,760 hours with 29 '
                          f'February kept. National aggregation: {shift}; sum residential end-use columns (heating + '
                          'hp_bkup, cooling + fans, etc.) into five SHELF categories, downsample to hourly.' + tv + dl +
                          ' Cached to data/national_aggregated/'
                          + bld.cache_name('resstock', buildings, clock, television) + '.',
            },
            {
                'purpose': 'Commercial Hourly End-Use Load Profiles by State',
                'source':  'NREL',
                'publication': 'NREL End-Use Load Profiles for the U.S. Building Stock (ComStock 2025 Release 2, '
                               'actual 2012 weather)',
                'year':    2025,
                'url':     'https://www.nrel.gov/buildings/end-use-load-profiles.html',
                'info':    'Baseline commercial building stock (upgrade 0), simulated with the actual weather of '
                          '2012: 51 state folders (50 states and DC). Same calendar and clock as ResStock; '
                          f'{shift}. Commercial end-uses aggregated into five SHELF categories per the AEO BCEU '
                          'mapping. NREL reports that all weather files for Hawaii in this release are incorrect and '
                          'does not recommend the release for Hawaii; Hawaii is kept here (about 0.5% of national '
                          'commercial load; see "Buildings source and calendar" below).' + dl + ' Cached to '
                          'data/national_aggregated/' + bld.cache_name('comstock', buildings, clock) + '.',
            },
        ]
    out = [
        {
            'purpose': 'Residential Hourly End-Use Load Profiles by State',
            'source':  'NREL',
            'publication': 'NREL End-Use Load Profiles for the U.S. Building Stock (ResStock)',
            'year':    2024,
            'url':     'https://www.nrel.gov/buildings/end-use-load-profiles.html',
            'info':    '49 state files at ResStock SHELF/ResStock_Upgrade0/state=XX/. Each state '
                      'file is 15-min interval data in Local Standard Time (no DST). National '
                      'aggregation: TZ-correct each state forward to ET (np.roll by hours-LST-to-ET), '
                      'sum residential end-use columns (heating + hp_bkup, cooling + fans, etc.) into '
                      'five SHELF categories, downsample to hourly. Cached to '
                      'data/national_aggregated/resstock_national_hourly.csv.',
        },
        {
            'purpose': 'Commercial Hourly End-Use Load Profiles by State',
            'source':  'NREL',
            'publication': 'NREL End-Use Load Profiles for the U.S. Building Stock (ComStock TMY)',
            'year':    2024,
            'url':     'https://www.nrel.gov/buildings/end-use-load-profiles.html',
            'info':    '51 state folders at ResStock SHELF/ComStock_tmy_release1/XX/. Same TZ '
                      'correction as ResStock; commercial end-uses aggregated into five SHELF '
                      'categories per the AEO BCEU mapping. Cached to '
                      'data/national_aggregated/comstock_national_hourly.csv.',
        },
    ]
    if clock == 'eastern':
        # typical-year files, states added without the time-zone shift (the files are already on Eastern Standard Time)
        res, com = out
        for d, kind in ((res, 'resstock'), (com, 'comstock')):
            d['info'] = d['info'].replace('data/national_aggregated/' + bld.cache_name(kind, 'typical', 'pipeline'),
                                          'data/national_aggregated/' + bld.cache_name(kind, 'typical', clock))
        for old, new in (
                ('Each state file is 15-min interval data in Local Standard Time (no DST). ',
                 'Each state file is 15-min interval data stamped in Eastern Standard Time (no DST). '),
                ('National aggregation: TZ-correct each state forward to ET (np.roll by hours-LST-to-ET), ',
                 'National aggregation: no time-zone shift, because the files are already on Eastern Standard Time '
                 '(see "Buildings clock" below); ')):
            assert old in res['info'], old
            res['info'] = res['info'].replace(old, new)
        assert 'Same TZ correction as ResStock; ' in com['info']
        com['info'] = com['info'].replace('Same TZ correction as ResStock; ', 'Same clock as ResStock (no time-zone shift); ')
    return out


def add_about_tab(wb: openpyxl.Workbook, days_per_slice: dict, file_name_no_ext: str,
                  buildings: str = 'typical', clock: str = 'pipeline', television: str = 'omit', delay: float = 0.0):
    ws = wb.create_sheet('About', 0)
    ws.column_dimensions['A'].width = 14
    ws.column_dimensions['B'].width = 110

    ws.cell(1, 1, f'SHELF {file_name_no_ext}').font = Font(bold=True)
    ws.cell(3, 1, 'Sources:').font = Font(bold=True)

    sources = _building_sources(buildings, clock, television, delay) + [
        {
            'purpose': 'Industrial and Transportation Hourly Load Profiles (National)',
            'source':  'NREL',
            'publication': 'NREL Electrification Futures Study (EFS) Load Profiles',
            'year':    2018,
            'url':     'https://data.nrel.gov/submissions/126',
            'info':    'Reference scenario, Moderate technology advancement, year 2024 EFS vintage. '
                      'Industrial: machine drives + process heat + other. Transportation: LDV / MDV+HDV / '
                      'rail (≈40% of other-transport). File: data/efs/EFSLoadProfile_Reference_Moderate.zip.',
        },
        {
            'purpose': 'Net-Load Clustering Reference (for K6/H24 representative-day slicing)',
            'source':  'NREL',
            'publication': 'NREL Cambium Scenarios 2024',
            'year':    2024,
            'url':     'https://www.nrel.gov/analysis/cambium.html',
            'info':    'MidCase scenario, weather year 2012, USA national, 2025 model year. Used '
                      'only for the clustering (assigning each day-of-year to one of six timeslices). '
                      'SHELF outputs are derived from ResStock/ComStock/EFS, not Cambium. File: '
                      'Cambium24_MidCase_hourly_usa_2025.csv pasted into "Cambium hourly source" tab.',
        },
    ]

    cur = 3
    for src in sources:
        c = ws.cell(cur, 2, src['purpose'])
        c.font = Font(bold=True); c.fill = PURPOSE_FILL; c.alignment = LEFT_TOP_WRAP
        for off, val in enumerate([src['source'], src['publication'], src['year']], start=1):
            ws.cell(cur + off, 2, val).alignment = LEFT_TOP_WRAP
        u = ws.cell(cur + 4, 2, src['url'])
        u.hyperlink = src['url']; u.font = Font(color='0563C1', underline='single')
        u.alignment = LEFT_TOP_WRAP
        ws.cell(cur + 5, 2, src['info']).alignment = LEFT_TOP_WRAP
        cur += 7

    notes_row = cur + 1
    ws.cell(notes_row, 1, 'Notes:').font = Font(bold=True)

    sp = days_per_slice.get('Summer Peak', 0)
    wp = days_per_slice.get('Winter Peak', 0)
    today = dt.date.today().isoformat()

    notes_lines = [
        ('Methodology overview',
         'This workbook produces SHELF (Seasonal Hourly Equipment Load Factor) tables for the '
         'EPS Vensim model. Each output tab gives a 6 (timeslice) × 24 (hour) load-factor table for one '
         'demand category — the ratio of demand in that slice/hour to total annual demand. '
         'Edit the source tabs or the Clustering tab and all SHELF outputs recompute via formulas.'),
        ('Source data layout',
         'Each hourly source tab pastes 8,760 rows of aggregated national hourly demand by category, '
         'with derived day_of_year / hour_of_day / slice columns at the right. Slice is resolved via '
         'VLOOKUP against the Clustering tab. The Cambium hourly source tab is included for '
         'traceability of the clustering (75 source columns × 8,760 rows pasted verbatim).'),
        ('Clustering',
         f'K6/H24 representative-day clustering on Cambium 2024 net load. Optimizer self-terminated '
         f'at SP={sp} days, WP={wp} days. Algorithm: cluster_days_repday in '
         f'state_pipeline/builders/clustering_repday.py. The Clustering tab has the editable per-day '
         f'slice assignment used by all source tabs.'),
        ('SHELF derivation',
         'For each non-zero category: LF[slice, hour] = AVERAGEIFS(demand, slice_col, "<slice>", '
         'hour_col, <hour>) / SUM(demand). Sum across all (slice, hour) × days_per_slice = 1.0 per '
         'category by construction.'),
        ('Zero categories',
         'residential-envelope, commercial-envelope, aircraft, ships, motorbikes, district-heat-hydrogen, '
         'geoeng — all zero in start year per EPS convention. May ramp up in later years for some '
         'scenarios; edit the tab directly to override.'),
        ('Datacenters',
         'Flat 24/7 LF = 1/8760 in every cell. Data centers run continuously; this lets BCEU/AEO '
         'datacenter annual energy contribute to every hour including peak.'),
        ('Annual category totals',
         'The "Annual category totals" tab documents the expected annual TWh per category and the '
         'BCEU/AEO source variable. These values do NOT propagate into the LF math (LFs are '
         'self-normalized within each category). They are reference inputs that help calibrate against '
         'expected model peak load.'),
        ('Tab order',
         'SHELF output tabs follow the EPS subscript order from the EPS-test-folder reference file: '
         'days-per-timeslice, residential-{heating,cooling,envelope,lighting,appliances,other}, '
         'commercial-{...}, LDVs, HDVs, aircraft, rail, ships, motorbikes, industry, '
         'district-heat-hydrogen, geoeng, datacenters.'),
        ('Run metadata',
         f'country: UnitedStates; clustering input: Cambium 2024 MidCase 2025 (weather year 2012); '
         f'EFS vintage: 2024; '
         + ('ResStock 2025 Release 1 / ComStock 2025 Release 2 (actual 2012 weather)' if buildings == 'amy2012'
            else 'ResStock/ComStock: 2024 release')
         + f'; built: {today}; build script: scripts/build_shelf_workbook.py.'),
        ('Caveats',
         'All values are inputs for staff review. Verify against NREL ResStock, ComStock, EFS, '
         'Cambium 2024, and the project methodology (CLAUDE.md at project root) before being used '
         'in any work product.'),
    ]
    for i, (label, text) in enumerate(notes_lines):
        r = notes_row + 1 + i
        ws.cell(r, 1, label).font = Font(bold=True)
        ws.cell(r, 2, text).alignment = LEFT_TOP_WRAP
        ws.row_dimensions[r].height = max(30, 18 * (1 + len(text) // 110))


def add_clustering_tab(wb, days_per_slice, slice_assignment):
    ws = wb.create_sheet('Clustering')
    ws.column_dimensions['A'].width = 14
    ws.column_dimensions['B'].width = 8
    ws.column_dimensions['D'].width = 8
    ws.column_dimensions['E'].width = 14
    ws.cell(1, 1, 'Days per timeslice (snapshot)').font = SECTION_FONT
    ws.cell(1, 1).fill = SECTION_FILL
    ws.cell(2, 1, 'Slice').font = HEADER_FONT
    ws.cell(2, 1).fill = HEADER_FILL
    ws.cell(2, 2, 'Days').font = HEADER_FONT
    ws.cell(2, 2).fill = HEADER_FILL
    for i, sl in enumerate(SLICES):
        ws.cell(3 + i, 1, sl)
        ws.cell(3 + i, 2, int(days_per_slice.get(sl, 0)))
    ws.cell(1, 4, 'DOY → slice (edit to reassign days)').font = SECTION_FONT
    ws.cell(1, 4).fill = SECTION_FILL
    ws.cell(2, 4, 'DOY').font = HEADER_FONT
    ws.cell(2, 4).fill = HEADER_FILL
    ws.cell(2, 5, 'Slice').font = HEADER_FONT
    ws.cell(2, 5).fill = HEADER_FILL
    for doy in range(1, 366):
        ws.cell(2 + doy, 4, doy)
        ws.cell(2 + doy, 5, slice_assignment.get(doy, SLICES[0]))


def add_annual_totals_tab(wb):
    ws = wb.create_sheet('Annual category totals')
    ws.column_dimensions['A'].width = 26
    ws.column_dimensions['B'].width = 14
    ws.column_dimensions['C'].width = 90
    ws.cell(1, 1, 'Annual TWh per SHELF category (start year, reference)') \
      .font = SECTION_FONT
    ws.cell(1, 1).fill = SECTION_FILL
    ws.cell(2, 1, 'Category').font = HEADER_FONT
    ws.cell(2, 1).fill = HEADER_FILL
    ws.cell(2, 2, 'Annual TWh').font = HEADER_FONT
    ws.cell(2, 2).fill = HEADER_FILL
    ws.cell(2, 3, 'Source file / variable').font = HEADER_FONT
    ws.cell(2, 3).fill = HEADER_FILL
    for i, cat in enumerate([c for c in SHELF_OUTPUT_ORDER if c != 'days-per-timeslice']):
        ws.cell(3 + i, 1, cat)
        ws.cell(3 + i, 2, ANNUAL_TWH_DEFAULTS.get(cat, 0.0))
        ws.cell(3 + i, 3, ANNUAL_TWH_SOURCES.get(cat, '')).alignment = LEFT_TOP_WRAP


def _add_hourly_source_tab(
    wb, name: str, df: pd.DataFrame,
    timestamps: list, slice_assignment: dict, align_weekdays: bool = False,
) -> tuple[int, dict[str, str], str, str]:
    """Write a tab with timestamp + per-category cols + derived DOY/hour/slice.
    Returns (data_start_row, {category: col_letter}, slice_col_letter, hour_col_letter).

    align_weekdays: for a source on a calendar that starts on a Monday (ResStock, ComStock: 2018), add a
    clustering_day column = day_of_year + 1 and look the timeslice up by that day, so that the source's
    Saturdays and Sundays land on the Saturdays and Sundays of the clustering calendar (weather year 2012,
    which starts on a Sunday). Off by default: the published files match day number to day number.
    """
    ws = wb.create_sheet(name)
    cols = list(df.columns)
    # Row 1: headers
    ws.cell(1, 1, 'timestamp').font = Font(bold=True)
    for i, c in enumerate(cols):
        ws.cell(1, 2 + i, c).font = Font(bold=True)
    n_main = 1 + len(cols)  # timestamp + categories
    doy_col = n_main + 1
    hour_col = n_main + 2
    slice_col = n_main + (4 if align_weekdays else 3)
    ws.cell(1, doy_col, 'day_of_year').font = Font(bold=True, italic=True)
    ws.cell(1, hour_col, 'hour_of_day').font = Font(bold=True, italic=True)
    if align_weekdays:
        ws.cell(1, n_main + 3, 'clustering_day').font = Font(bold=True, italic=True)
    ws.cell(1, slice_col, 'slice').font = Font(bold=True, italic=True)

    # Data rows
    for i in range(len(df)):
        row = 2 + i
        ts = timestamps[i]
        ws.cell(row, 1, ts.strftime('%Y-%m-%d %H:%M'))
        for j, c in enumerate(cols):
            ws.cell(row, 2 + j, float(df.iloc[i, j]))
        doy = (i // 24) + 1
        ws.cell(row, doy_col, doy)
        ws.cell(row, hour_col, i % 24)
        doy_letter = get_column_letter(doy_col)
        if align_weekdays:
            # this source's day 1 is a Monday; the clustering calendar's first Monday is day 2
            ws.cell(row, n_main + 3, value=f"=MOD({doy_letter}{row},365)+1")
            doy_letter = get_column_letter(n_main + 3)
        ws.cell(row, slice_col,
                value=f"=VLOOKUP({doy_letter}{row},Clustering!$D$3:$E$367,2,FALSE)")

    # Column widths
    ws.column_dimensions['A'].width = 18
    for c in range(2, slice_col + 1):
        ws.column_dimensions[get_column_letter(c)].width = 16
    ws.freeze_panes = 'B2'

    # Build map: category → column letter
    cat_col = {c: get_column_letter(2 + i) for i, c in enumerate(cols)}
    return 2, cat_col, get_column_letter(slice_col), get_column_letter(hour_col)


def add_cambium_source_tab(wb, slice_assignment):
    """Paste full Cambium source verbatim with derived DOY/hour/slice columns."""
    rows = load_cambium_raw_rows()
    ws = wb.create_sheet('Cambium hourly source')
    n_src_cols = len(rows[5])
    print(f"  [cambium] writing {len(rows)} rows × {n_src_cols} src cols...")
    for r_idx, row in enumerate(rows, start=1):
        for c_idx, val in enumerate(row, start=1):
            cell_val = _try_float(val) if r_idx >= 7 and c_idx >= 2 else val
            ws.cell(r_idx, c_idx, cell_val)
    # Add derived columns at the right; data starts row 7
    data_start = 7
    data_end = len(rows)
    doy_col = n_src_cols + 1
    hour_col = n_src_cols + 2
    slice_col = n_src_cols + 3
    ws.cell(6, doy_col, 'day_of_year').font = Font(bold=True, italic=True)
    ws.cell(6, hour_col, 'hour_of_day').font = Font(bold=True, italic=True)
    ws.cell(6, slice_col, 'slice').font = Font(bold=True, italic=True)
    doy_letter = get_column_letter(doy_col)
    for i in range(data_end - data_start + 1):
        r = data_start + i
        ws.cell(r, doy_col, (i // 24) + 1)
        ws.cell(r, hour_col, i % 24)
        ws.cell(r, slice_col,
                value=f"=VLOOKUP({doy_letter}{r},Clustering!$D$3:$E$367,2,FALSE)")
    for c in range(1, min(slice_col, 50) + 1):
        ws.column_dimensions[get_column_letter(c)].width = 14
    ws.freeze_panes = 'B7'


def _try_float(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return s


# ---------------------------------------------------------------------------
# Output tabs
# ---------------------------------------------------------------------------

def add_days_per_timeslice_tab(wb, days_per_slice):
    """SHELF-days-per-timeslice tab. Same format as the CSV file."""
    ws = wb.create_sheet('SHELF-days-per-timeslice')
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 22
    ws.column_dimensions['B'].width = 22
    ws.cell(1, 1, 'Unit: days')
    ws.cell(1, 2, 'Days per Timeslice')
    for i, sl in enumerate(SLICES):
        ws.cell(2 + i, 1, sl)
        ws.cell(2 + i, 2, int(days_per_slice.get(sl, 0)))


def add_shelf_output_tab(
    wb, category: str, source_tab: str, cat_col_letter: str,
    slice_col_letter: str, hour_col_letter: str,
    data_start: int, data_end: int,
):
    """Build a SHELF-<category> tab using AVERAGEIFS / SUM."""
    ws = wb.create_sheet(f'SHELF-{category}')
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 16
    for c in range(2, 26):
        ws.column_dimensions[get_column_letter(c)].width = 12

    # Header row
    ws.cell(1, 1, 'Unit: dimensionless (ratio of electricity demand in this hour to annual demand)')
    for h, name in enumerate(HOUR_COLS):
        ws.cell(1, 2 + h, name)

    cf_range = f"'{source_tab}'!${cat_col_letter}${data_start}:${cat_col_letter}${data_end}"
    slice_range = f"'{source_tab}'!${slice_col_letter}${data_start}:${slice_col_letter}${data_end}"
    hour_range = f"'{source_tab}'!${hour_col_letter}${data_start}:${hour_col_letter}${data_end}"

    for r_off, sl in enumerate(SLICES):
        ws.cell(2 + r_off, 1, sl)
        for h in range(24):
            avg = f"AVERAGEIFS({cf_range},{slice_range},$A{2+r_off},{hour_range},{h})"
            tot = f"SUM({cf_range})"
            formula = f"=IFERROR({avg}/{tot},0)"
            ws.cell(2 + r_off, 2 + h, formula)


def add_zero_tab(wb, category: str):
    """SHELF tab with all zeros (envelope, aircraft, etc.)."""
    ws = wb.create_sheet(f'SHELF-{category}')
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 16
    for c in range(2, 26):
        ws.column_dimensions[get_column_letter(c)].width = 12
    ws.cell(1, 1, 'Unit: dimensionless (ratio of electricity demand in this hour to annual demand)')
    for h, name in enumerate(HOUR_COLS):
        ws.cell(1, 2 + h, name)
    for r_off, sl in enumerate(SLICES):
        ws.cell(2 + r_off, 1, sl)
        for h in range(24):
            ws.cell(2 + r_off, 2 + h, 0.0)


def add_flat_tab(wb, category: str):
    """SHELF tab with flat 1/8760 in every cell (datacenters)."""
    ws = wb.create_sheet(f'SHELF-{category}')
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 16
    for c in range(2, 26):
        ws.column_dimensions[get_column_letter(c)].width = 12
    ws.cell(1, 1, 'Unit: dimensionless (ratio of electricity demand in this hour to annual demand)')
    for h, name in enumerate(HOUR_COLS):
        ws.cell(1, 2 + h, name)
    flat_val = 1.0 / 8760.0
    for r_off, sl in enumerate(SLICES):
        ws.cell(2 + r_off, 1, sl)
        for h in range(24):
            ws.cell(2 + r_off, 2 + h, flat_val)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

WEEKDAY_NOTE = (
    'Weekday alignment',
    'Built with --align-weekdays. The ResStock and ComStock series follow a calendar that starts on a Monday '
    '(2018), while the clustering follows weather year 2012, which starts on a Sunday. On the two buildings '
    'source tabs the clustering_day column is day_of_year + 1, and each hour takes the timeslice of that day, '
    "so the buildings' Saturdays and Sundays fall on the clustering's Saturdays and Sundays. The last day of "
    'the buildings year wraps round to clustering day 1. Without the option, day number is matched to day '
    'number and the buildings weekends sit one day early.')


def building_notes(buildings: str, clock: str, television: str, delay: float = 0.0) -> list[tuple[str, str]]:
    """About-tab notes for the home and business load shapes. None for the default source and clock, so that
    the default workbook's About tab is unchanged."""
    notes = []
    if buildings == 'amy2012':
        tv = ("it is left out of every category here, which is about 5.6% of home electricity and would add about 29% "
              "to residential-other (the option --television other counts it there)" if television == 'omit' else
              "it is counted in residential-other here, as plug loads were in earlier releases (about 5.6% of home "
              "electricity; it adds about 29% to residential-other and moves that shape's evening peak later)")
        notes.append((
            'Buildings source and calendar',
            'The residential and commercial load shapes come from NREL building simulations run with the actual '
            'weather of 2012 (ResStock 2025 Release 1 and ComStock 2025 Release 2). 2012 is also the weather year of '
            'the Cambium file that picks the representative and peak days, so the days chosen as the hottest, '
            'coldest or highest in net load are days on which these buildings were simulated under that same '
            'weather. Earlier versions of this file used NREL typical-year weather (ResStock 2024 Release 2 and '
            'ComStock 2021 Release 1), in which the weather on a given day number has no connection to the weather '
            'on that day in the Cambium file. The NREL files run from 1 January to 30 December 2012: 8,760 hours, '
            'with 29 February kept and 31 December left out. Day number n of the buildings series is therefore day '
            'number n of the Cambium file and of the Clustering tab. 2012 starts on a Sunday, as the clustering '
            'calendar does, so weekends line up with no adjustment (the --align-weekdays option does not apply to '
            'this source), and the timestamps on the two buildings source tabs are 2012 dates. Not counted in any '
            'category: electric vehicle charging (vehicle charging is covered by the transport tabs), '
            'solar-thermal water heating, and the total, net and rooftop-solar columns. Television is a separate '
            'line in the 2025 residential release (earlier releases counted it in plug loads): ' + tv + '. '
            'ResStock has no Hawaii file in this release. NREL reports that all Hawaii weather files in the '
            'ComStock release are incorrect and does not recommend it for Hawaii; Hawaii is included here and makes '
            'up about 0.5% of national commercial load (3% of commercial heating).'))
    if clock == 'eastern':
        if delay:
            limit = ('The simulated day still runs early compared with measured demand; a delay is applied for that '
                     '(see "Buildings delay" below).')
        else:
            limit = ('Limit: compared with measured national hourly demand, the simulated building load still runs '
                     'early, by about half an hour when television is counted and about an hour when it is not. The '
                     "clock is not the cause: NREL's modelled day itself runs slightly early. No correction is "
                     'applied here.')
        notes.append((
            'Buildings clock',
            'NREL stamps every ResStock and ComStock state file in Eastern Standard Time (the end of each 15-minute '
            "interval, no daylight saving), whatever the state's own time zone. The states are therefore added "
            'together as they are, with no time-zone shift. ' + limit))
    elif buildings == 'amy2012':
        notes.append((
            'Buildings clock',
            "Each state's series was moved later by its distance from Eastern time (Central 1 hour, Mountain 2, "
            'Pacific 3, Alaska 4, Hawaii 5) before the states were added, the same step earlier versions of this '
            'file applied. NREL stamps every ResStock and ComStock state file in Eastern Standard Time already (the '
            'end of each 15-minute interval, no daylight saving), so this moves each state outside the Eastern zone '
            'a second time: by about 0.8 hours for home load and 1.0 hours for business load, on a load-weighted '
            'average. It is not a correction for a known timing error and it is wrong for any single state outside '
            "the Eastern zone. Nationally it happens to resemble the half hour to one hour by which NREL's modelled "
            'day runs early compared with measured demand. The options --building-clock eastern and '
            '--building-delay-hours do the same job explicitly.'))
    if delay:
        notes.append((
            'Buildings delay',
            f'Every residential and commercial hourly series is delayed by {delay:g} hours after the states are '
            'added. This is a calibration to measured demand, not a clock correction. NREL\'s simulated day runs '
            'slightly early: compared with measured hourly demand from four grid operators (Florida Power & Light, '
            'Duke Energy Carolinas, Nevada Power and ISO New England; U.S. Energy Information Administration Form '
            'EIA-930, 2018 and 2019), and with television counted, simulated building load rises and falls about '
            'half an hour before measured demand. The earlier NREL releases show the same, and NREL\'s own '
            'validation report (End-Use Load Profiles for the U.S. Building Stock, NREL/TP-5500-80889, 2022) shows '
            'its modelled daily peaks earlier than utility meters in most regions. Method: each hourly series is '
            'replaced by a blend of itself moved later by the whole hours of the delay and by one hour more; for '
            f'{delay:g} hours that is {1 - (delay - int(delay)):g} of each hour\'s load shifted by '
            f'{int(delay)} hours plus {delay - int(delay):g} shifted by {int(delay) + 1}. The year wraps round, so '
            "annual energy is unchanged and every shape still adds to 1; a single day's energy changes slightly, "
            'because load near midnight moves into the next day. The ResStock and ComStock source tabs hold the delayed '
            'series. Limits: a national comparison cannot tell a delay '
            'of 0.5 hours from 0.75 hours, or homes from businesses; the same delay is used for every end use and '
            'every region; NREL has published no correction for this.'))
    return notes


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--version', choices=['4.0', '5.0'], default='4.0', help='which EPS version to build for')
    ap.add_argument('--out', help='output folder (default: output/us_shelf_<version>/ in this repository)')
    ap.add_argument('--resstock-root', help='folder holding ResStock state=XX folders')
    ap.add_argument('--comstock-root', help='folder holding ComStock two-letter state folders')
    ap.add_argument('--efs-zip', help='EFSLoadProfile_Reference_Moderate.zip')
    ap.add_argument('--siels-zip', help='industrial_load_shapes_2018.zip from Mendeley Data (5.0 only)')
    ap.add_argument('--handbuilt-seed', help='workbook holding the hand-built industry tabs (5.0 only)')
    ap.add_argument('--refresh', action='append', default=[], choices=['resstock', 'comstock', 'efs', 'siels'],
                    help='rebuild this saved national series from its raw download (repeatable)')
    ap.add_argument('--clustering', choices=['auto', 'saved', 'rerun'], default='auto',
                    help='re-run the clustering (needs scikit-learn) or use the saved day-to-timeslice list; '
                         'auto re-runs when it can')
    ap.add_argument('--align-weekdays', action='store_true',
                    help='shift the ResStock and ComStock days by one so their weekends line up with the '
                         "clustering calendar's (off by default: reproduces the published files)")
    ap.add_argument('--buildings', choices=list(bld.SOURCES), default=None,
                    help='source of the home and business load shapes. Default: amy2012 with --version 5.0 (what '
                         'eps-us develop reads since 2026-11-18), typical with --version 4.0. amy2012: NREL runs with '
                         'the actual weather of 2012 (ResStock 2025 R1, ComStock 2025 R2), the weather year of the '
                         'clustering; 8,760 hours that match the clustering day for day, so --align-weekdays does not '
                         'apply. typical: NREL typical-year weather on a 2018 calendar (ResStock 2024 R2, ComStock '
                         '2021 R1), which reproduces the 4.0.x files. Folders are set with --resstock-root / '
                         '--comstock-root, SHELF_RESSTOCK_AMY2012_ROOT / SHELF_COMSTOCK_AMY2012_ROOT or local_paths.yml')
    ap.add_argument('--building-clock', choices=list(bld.CLOCKS), default=None,
                    help='time-zone handling for ResStock and ComStock only. Default: eastern with --version 5.0, '
                         "pipeline with --version 4.0. eastern: no shift, because NREL's state files are already "
                         'stamped in Eastern Standard Time. pipeline: move each state later by its distance from '
                         'Eastern time, as the pipeline did before 2026-11-18; that shifts western states twice and is '
                         'kept only to reproduce the 4.0.x files. SIELS industry shapes are '
                         'not affected (see --siels-tennessee)')
    ap.add_argument('--television', choices=list(bld.TELEVISION), default=None,
                    help='--buildings amy2012 only. ResStock 2025 R1 lists television as its own end use (earlier '
                         'releases counted it in plug loads). other (the default for amy2012): add it to '
                         'residential-other, where plug loads are counted; omit: leave it out, as the first '
                         'reference sets did')
    ap.add_argument('--building-delay-hours', type=float, default=0.0, metavar='H',
                    help='delay every ResStock and ComStock hourly series by H hours (fractions allowed, 0 <= H < 24) '
                         'after the states are added. A calibration to measured demand, not a clock correction: '
                         "NREL's modelled day runs about half an hour early (SHELF clock analysis, 2026-11-17). "
                         'Annual energy is unchanged. Default 0 (off)')
    ap.add_argument('--efs-clock', choices=list(efs_clock.CLOCKS), default=None,
                    help='clock of the EFS vehicle-charging, rail and EFS-industry series. Default: eastern with '
                         '--version 5.0, local with --version 4.0. local: the states added by their own local hour, '
                         'as the EFS file gives them (what the pipeline did before 2026-11-18). eastern: that series '
                         'moved onto Eastern Standard Time with population weights by time zone (shelf_v5/efs_clock.py)')
    ap.add_argument('--siels-tennessee', choices=['eastern', 'central'], default='eastern',
                    help='time zone used for Tennessee when the SIELS zip is aggregated. central is what '
                         'STATE_TZ_OFFSET_TO_ET says; eastern (default) reproduces the series behind the files '
                         'on eps-us develop, which were built with Tennessee on Eastern time')
    args = ap.parse_args(argv)
    v5 = args.version == '5.0'
    if args.buildings is None:
        args.buildings = 'amy2012' if v5 else 'typical'
    if args.building_clock is None:
        args.building_clock = 'eastern' if v5 else 'pipeline'
    if args.efs_clock is None:
        args.efs_clock = 'eastern' if v5 else 'local'
    if args.buildings == 'amy2012' and args.align_weekdays:
        ap.error('--align-weekdays does not apply to --buildings amy2012: those files are on the 2012 calendar and '
                 'match the clustering day for day')
    try:
        args.television = bld.resolve_television(args.buildings, args.television)
    except ValueError as e:
        ap.error(str(e))
    if not 0 <= args.building_delay_hours < 24:
        ap.error('--building-delay-hours must be at least 0 and less than 24')
    return args


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):      # Windows consoles cannot print every character used below
        try:
            stream.reconfigure(errors='replace')
        except Exception:
            pass
    args = parse_args(argv)
    v5 = args.version == '5.0'
    global SLICES
    SLICES = slice_names.labels(args.version)
    to_label = dict(zip(SLICE_NAMES, SLICES))
    out_root = Path(args.out) if args.out else ROOT / 'output' / f'us_shelf_{args.version}'
    out = out_root / 'elec' / 'SHELF' / WORKBOOK_NAME
    used: dict[str, str] = {}

    print(f"[1/5] Aggregating ResStock + ComStock (cached)")
    res, used['ResStock'] = aggregate_resstock_cached(
        shelf_paths.lookup(bld.root_key('resstock', args.buildings), args.resstock_root), 'resstock' in args.refresh,
        args.buildings, args.building_clock, args.television)
    com, used['ComStock'] = aggregate_comstock_cached(
        shelf_paths.lookup(bld.root_key('comstock', args.buildings), args.comstock_root), 'comstock' in args.refresh,
        args.buildings, args.building_clock)
    if args.building_delay_hours:
        res = bld.delay_hourly(res, args.building_delay_hours)
        com = bld.delay_hourly(com, args.building_delay_hours)
        print(f"  [buildings] delayed by {args.building_delay_hours:g} h (annual energy unchanged)")
    if (args.buildings, args.building_clock, args.building_delay_hours) != ('typical', 'pipeline', 0.0):
        used['Buildings'] = (f'{args.buildings} source, {args.building_clock} clock'
                             + (f', {args.building_delay_hours:g} h delay' if args.building_delay_hours else ''))
    if args.buildings == 'amy2012':
        assert len(res) == len(com) == 8760 and res.index[0] == com.index[0] == pd.Timestamp('2012-01-01 00:00'), \
            'actual-2012-weather buildings series should be 8,760 hours from 2012-01-01 00:00'
    print(f"  [resstock] shape {res.shape}; [comstock] shape {com.shape}")

    print(f"[2/5] Loading EFS national (filtered)")
    efs, used['EFS'] = load_efs_cached(shelf_paths.lookup('efs_zip', args.efs_zip), 'efs' in args.refresh)
    if args.efs_clock == 'eastern':
        efs = efs_clock.to_eastern(efs)
        used['EFS'] += ', moved to Eastern time (population weights by time zone)'
        print('  [efs] moved from local hours to Eastern time (population weights by time zone)')
    print(f"  [efs] shape {efs.shape}")

    print(f"[3/5] Clustering on Cambium 2024 net load")
    days_canonical, assignment_canonical, used['clustering'] = get_clustering(args.clustering)
    print(f"  days_per_timeslice = {days_canonical}")
    days_per_slice = {to_label[k]: v for k, v in days_canonical.items()}
    slice_assignment = {d: to_label[sl] for d, sl in assignment_canonical.items()}

    print(f"[4/5] Building workbook")
    if v5:
        # the 5.0 workbook starts from the hand-built industry tabs (see scripts/shelf_v5/README.md)
        seed = shelf_paths.lookup('handbuilt_seed', args.handbuilt_seed)
        print(f"  [5.0] hand-built tabs from {seed}")
        wb = openpyxl.load_workbook(seed)
        used['hand-built industry tabs'] = 'seed workbook'
    else:
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
    add_about_tab(wb, days_canonical, file_name_no_ext=out.stem, buildings=args.buildings, clock=args.building_clock,
                  television=args.television, delay=args.building_delay_hours)
    add_clustering_tab(wb, days_per_slice, slice_assignment)
    add_annual_totals_tab(wb)

    # All hourly sources are labelled with a 2018 calendar and matched to the clustering by day number.
    # (ResStock and ComStock really are on a 2018 calendar; EFS and Cambium follow weather year 2012.)
    ts2018 = pd.date_range('2018-01-01', periods=8760, freq='h').to_list()

    # The actual-2012-weather buildings series are on the 2012 calendar (1 Jan - 30 Dec, 29 Feb kept): label them so.
    bld_ts = ts2018 if args.buildings == 'typical' else list(res.index[:8760])
    # ResStock source
    res_aligned = res.reset_index(drop=True).iloc[:8760].copy()
    _, res_cat_col, res_slice_col, res_hour_col = _add_hourly_source_tab(
        wb, 'ResStock national source', res_aligned, bld_ts, slice_assignment, args.align_weekdays,
    )
    # ComStock source
    com_aligned = com.reset_index(drop=True).iloc[:8760].copy()
    _, com_cat_col, com_slice_col, com_hour_col = _add_hourly_source_tab(
        wb, 'ComStock national source', com_aligned, bld_ts, slice_assignment, args.align_weekdays,
    )
    # EFS source
    efs_aligned = efs.reset_index(drop=True).iloc[:8760].copy()
    _, efs_cat_col, efs_slice_col, efs_hour_col = _add_hourly_source_tab(
        wb, 'EFS source', efs_aligned, ts2018, slice_assignment,
    )

    # Cambium source (full raw paste, clustering reference)
    add_cambium_source_tab(wb, slice_assignment)

    # ---- Output tabs ----
    print(f"  building {len(SHELF_OUTPUT_ORDER)} output tabs")
    for cat in SHELF_OUTPUT_ORDER:
        if cat == 'days-per-timeslice':
            add_days_per_timeslice_tab(wb, days_per_slice)
            wb['SHELF-days-per-timeslice'].sheet_properties.tabColor = OUTPUT_TAB_COLOR
            continue
        if cat in ZERO_CATS:
            add_zero_tab(wb, cat)
            continue
        if cat in FLAT_CATS:
            add_flat_tab(wb, cat)
            continue
        if cat in RESSTOCK_CATS:
            add_shelf_output_tab(wb, cat, 'ResStock national source',
                                  res_cat_col[cat], res_slice_col, res_hour_col,
                                  data_start=2, data_end=8761)
        elif cat in COMSTOCK_CATS:
            add_shelf_output_tab(wb, cat, 'ComStock national source',
                                  com_cat_col[cat], com_slice_col, com_hour_col,
                                  data_start=2, data_end=8761)
        elif cat in EFS_CATS:
            add_shelf_output_tab(wb, cat, 'EFS source',
                                  efs_cat_col[cat], efs_slice_col, efs_hour_col,
                                  data_start=2, data_end=8761)
        else:
            print(f"  WARN: category '{cat}' not mapped; writing zeros")
            add_zero_tab(wb, cat)

    extra_notes = building_notes(args.buildings, args.building_clock, args.television, args.building_delay_hours)
    if args.align_weekdays:
        extra_notes.append(WEEKDAY_NOTE)
    if v5:
        from shelf_v5 import build5, icwiwlf, siels
        offsets = dict(STATE_TZ_OFFSET_TO_ET)
        siels_cache = siels.CACHE_NAME
        if args.siels_tennessee == 'eastern':
            offsets['TN'] = 0
        else:
            siels_cache = siels_cache.replace('.csv', '_tennessee_central.csv')   # keep the default series intact
        stamps, cols, used['SIELS'] = siels.load_national(
            CACHE_DIR, shelf_paths.lookup('siels_zip', args.siels_zip), offsets, 'siels' in args.refresh, siels_cache)
        used['SIELS'] += f' (Tennessee on {args.siels_tennessee} time)'
        print(f"  [5.0] adding the industry tabs, data-center split and system-load shapes")
        build5.finish(wb, stamps, cols, OUTPUT_TAB_COLOR, inputs_used=used, extra_notes=extra_notes)
        ic_xlsx, ic_csv = icwiwlf.write(out_root / 'ctrl-settings' / 'ICwIwLF')
        print(f"  [5.0] wrote {ic_xlsx.name} and {ic_csv.name} in {ic_xlsx.parent}")
    elif extra_notes:
        ws = wb['About']
        for label, text in extra_notes:
            r = ws.max_row + 1
            ws.cell(r, 1, label).font = Font(bold=True)
            ws.cell(r, 2, text).alignment = LEFT_TOP_WRAP

    print(f"[5/5] Saving workbook")
    out.parent.mkdir(exist_ok=True, parents=True)
    try:
        wb.save(out)
    except PermissionError:
        print(f"  ERROR: cannot write {out} — close it in Excel first.")
        return
    print(f"[done] wrote {out}")
    print(f"       sheets: {len(wb.sheetnames)} total")
    print(f"       inputs: " + "; ".join(f"{k} from {v}" for k, v in used.items()))
    print(f'       next:   python scripts/shelf_v5/recalc_export.py "{out_root}" --version {args.version}')


if __name__ == '__main__':
    main()
