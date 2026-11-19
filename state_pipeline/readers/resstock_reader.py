"""Aggregate ResStock 15-min state-level files to hourly residential SHELF categories.

Output: 8760 x 5 DataFrame indexed by hour-beginning timestamp (2018 LST), columns:
  residential-heating, residential-cooling, residential-lighting,
  residential-appliances, residential-other.
Values: kWh per hour (later normalized to LF by demand assembler).
"""
from __future__ import annotations
from pathlib import Path
import re
import pandas as pd
from ..paths import resolve_input

RES_AGG = {
    'residential-heating': [
        'out.electricity.heating.energy_consumption.kwh',
        'out.electricity.heating_hp_bkup.energy_consumption.kwh',
        'out.electricity.heating_hp_bkup_fa.energy_consumption.kwh',
    ],
    'residential-cooling': [
        'out.electricity.cooling.energy_consumption.kwh',
        'out.electricity.cooling_fans_pumps.energy_consumption.kwh',
        'out.electricity.heating_fans_pumps.energy_consumption.kwh',
    ],
    'residential-lighting': [
        'out.electricity.lighting_interior.energy_consumption.kwh',
        'out.electricity.lighting_exterior.energy_consumption.kwh',
        'out.electricity.lighting_garage.energy_consumption.kwh',
    ],
    'residential-appliances': [
        'out.electricity.clothes_dryer.energy_consumption.kwh',
        'out.electricity.clothes_washer.energy_consumption.kwh',
        'out.electricity.dishwasher.energy_consumption.kwh',
        'out.electricity.range_oven.energy_consumption.kwh',
        'out.electricity.refrigerator.energy_consumption.kwh',
        'out.electricity.freezer.energy_consumption.kwh',
        'out.electricity.hot_water.energy_consumption.kwh',
    ],
    'residential-other': [
        'out.electricity.ceiling_fan.energy_consumption.kwh',
        'out.electricity.plug_loads.energy_consumption.kwh',
        'out.electricity.mech_vent.energy_consumption.kwh',
        'out.electricity.permanent_spa_heat.energy_consumption.kwh',
        'out.electricity.permanent_spa_pump.energy_consumption.kwh',
        'out.electricity.pool_heater.energy_consumption.kwh',
        'out.electricity.pool_pump.energy_consumption.kwh',
        'out.electricity.well_pump.energy_consumption.kwh',
    ],
}


# End-use name inside a column header: `out.electricity.<end use>.energy_consumption` followed by a units suffix
# that differs between releases (`.kwh` in ResStock 2024 R2, `..kwh` in 2025 R1). Matching the end use by pattern
# lets one map serve both.
END_USE = re.compile(r'^out\.electricity\.(.+?)\.energy_consumption(?:\.{1,2}[a-z0-9_]+)?$')
RES_END_USES = {cat: [END_USE.match(col).group(1) for col in cols] for cat, cols in RES_AGG.items()}
# columns that are totals or on-site generation, not end uses (reported apart from unmapped end uses)
NOT_END_USES = {'net', 'total', 'purchased', 'pv'}


def read_resstock_hourly(resstock_dir: str, report: dict | None = None,
                         extra_end_uses: dict[str, list[str]] | None = None) -> pd.DataFrame:
    """Hourly load by SHELF category for one state folder.

    report, if given, collects what the category map does not cover: report['unmapped'] (end uses in the files
    that no category takes), report['totals'] (total / net / generation columns, left out on purpose) and
    report['missing'] (mapped end uses absent from a file; this raises an error as well).

    extra_end_uses adds end uses to a category, e.g. {'residential-other': ['television']} (ResStock 2025 R1 lists
    television on its own; earlier releases counted it in plug_loads).
    """
    base = resolve_input(resstock_dir)
    cats = {c: list(uses) + list((extra_end_uses or {}).get(c, [])) for c, uses in RES_END_USES.items()}
    known = [u for uses in cats.values() for u in uses]

    combined: pd.DataFrame | None = None
    files = sorted(base.glob('*.csv'))
    if not files:
        raise FileNotFoundError(f"No ResStock CSVs in {base}")
    for f in files:
        header = pd.read_csv(f, nrows=0).columns
        found = {c: END_USE.match(c).group(1) for c in header if END_USE.match(c)}
        if len(set(found.values())) != len(found):
            raise ValueError(f"{f.name}: two columns for the same end use")
        missing = sorted(set(known) - set(found.values()))
        if report is not None:
            report.setdefault('missing', set()).update(missing)
            report.setdefault('unmapped', set()).update(set(found.values()) - set(known) - NOT_END_USES)
            report.setdefault('totals', set()).update(set(found.values()) & NOT_END_USES)
        if missing:
            raise ValueError(f"{f.name}: no column for end use(s) {missing}")
        use = {c: u for c, u in found.items() if u in known}
        df = pd.read_csv(f, usecols=['timestamp'] + list(use)).rename(columns=use).set_index('timestamp')
        if combined is None:
            combined = df
        else:
            combined = combined.add(df, fill_value=0)
    combined.index = pd.to_datetime(combined.index)

    # Build category-aggregated frame
    cat = pd.DataFrame(index=combined.index)
    for c, members in cats.items():
        cat[c] = combined[members].sum(axis=1)

    # 15-min end-of-period -> hour-beginning hourly
    cat = cat.reset_index().rename(columns={'index': 'ts', 'timestamp': 'ts'})
    cat['hour_start'] = (cat['ts'] - pd.Timedelta(minutes=15)).dt.floor('h')
    hourly = cat.drop(columns=['ts']).groupby('hour_start').sum()
    hourly.index.name = 'ts'

    # Trim to 8760 if leading/trailing year boundaries off-by-one
    if len(hourly) > 8760:
        hourly = hourly.iloc[:8760]
    return hourly
