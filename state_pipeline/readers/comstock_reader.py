"""Aggregate ComStock 15-min state-level files to hourly commercial SHELF categories.

5 commercial categories per AEO BCEU mapping.
"""
from __future__ import annotations
from pathlib import Path
import re
import pandas as pd
from ..paths import resolve_input

CS_COLS = [
    'out.electricity.cooling.energy_consumption',
    'out.electricity.heating.energy_consumption',
    'out.electricity.heat_rejection.energy_consumption',
    'out.electricity.heat_recovery.energy_consumption',
    'out.electricity.fans.energy_consumption',
    'out.electricity.pumps.energy_consumption',
    'out.electricity.interior_lighting.energy_consumption',
    'out.electricity.exterior_lighting.energy_consumption',
    'out.electricity.interior_equipment.energy_consumption',
    'out.electricity.refrigeration.energy_consumption',
    'out.electricity.water_systems.energy_consumption',
]

# End-use name inside a column header: `out.electricity.<end use>.energy_consumption`, optionally followed by a
# units suffix (none in ComStock 2021 R1, `.kwh` in 2025 R2). Matching the end use by pattern lets one map serve both.
END_USE = re.compile(r'^out\.electricity\.(.+?)\.energy_consumption(?:\.{1,2}[a-z0-9_]+)?$')
CS_END_USES = [END_USE.match(col).group(1) for col in CS_COLS]
# columns that are totals or on-site generation, not end uses (reported apart from unmapped end uses)
NOT_END_USES = {'net', 'total', 'purchased', 'pv'}


def read_comstock_hourly(comstock_dir: str, report: dict | None = None) -> pd.DataFrame:
    """Hourly load by SHELF category for one state folder.

    report, if given, collects what the category map does not cover: report['unmapped'] (end uses in the files
    that no category takes), report['totals'] (total / net / generation columns, left out on purpose) and
    report['missing'] (mapped end uses absent from a file; this raises an error as well).
    """
    base = resolve_input(comstock_dir)
    files = sorted(base.glob('*.csv'))
    if not files:
        raise FileNotFoundError(f"No ComStock CSVs in {base}")
    combined: pd.DataFrame | None = None
    for f in files:
        header = pd.read_csv(f, nrows=0).columns
        found = {c: END_USE.match(c).group(1) for c in header if END_USE.match(c)}
        if len(set(found.values())) != len(found):
            raise ValueError(f"{f.name}: two columns for the same end use")
        missing = sorted(set(CS_END_USES) - set(found.values()))
        if report is not None:
            report.setdefault('missing', set()).update(missing)
            report.setdefault('unmapped', set()).update(set(found.values()) - set(CS_END_USES) - NOT_END_USES)
            report.setdefault('totals', set()).update(set(found.values()) & NOT_END_USES)
        if missing:
            raise ValueError(f"{f.name}: no column for end use(s) {missing}")
        use = {c: u for c, u in found.items() if u in CS_END_USES}
        df = pd.read_csv(f, usecols=['timestamp'] + list(use)).rename(columns=use).set_index('timestamp')
        if combined is None:
            combined = df
        else:
            combined = combined.add(df, fill_value=0)
    combined.index = pd.to_datetime(combined.index)

    cat = pd.DataFrame(index=combined.index)
    cat['commercial-heating'] = combined['heating']
    cat['commercial-cooling'] = (
        combined['cooling']
        + combined['heat_rejection']
        + combined['fans']
        + combined['pumps']
    )
    cat['commercial-lighting'] = (
        combined['interior_lighting']
        + combined['exterior_lighting']
    )
    cat['commercial-appliances'] = (
        combined['refrigeration']
        + combined['water_systems']
    )
    cat['commercial-other'] = (
        combined['interior_equipment']
        + combined['heat_recovery']
    )

    cat = cat.reset_index().rename(columns={'index': 'ts', 'timestamp': 'ts'})
    cat['hour_start'] = (cat['ts'] - pd.Timedelta(minutes=15)).dt.floor('h')
    hourly = cat.drop(columns=['ts']).groupby('hour_start').sum()
    hourly.index.name = 'ts'
    if len(hourly) > 8760:
        hourly = hourly.iloc[:8760]
    return hourly
