"""Aggregate ResStock 15-min state-level files to hourly residential SHELF categories.

Output: 8760 x 5 DataFrame indexed by hour-beginning timestamp (2018 LST), columns:
  residential-heating, residential-cooling, residential-lighting,
  residential-appliances, residential-other.
Values: kWh per hour (later normalized to LF by demand assembler).
"""
from __future__ import annotations
from pathlib import Path
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


def read_resstock_hourly(resstock_dir: str) -> pd.DataFrame:
    base = resolve_input(resstock_dir)
    cols = sorted({c for v in RES_AGG.values() for c in v})

    combined: pd.DataFrame | None = None
    files = sorted(base.glob('*.csv'))
    if not files:
        raise FileNotFoundError(f"No ResStock CSVs in {base}")
    for f in files:
        df = pd.read_csv(f, usecols=['timestamp'] + cols)
        df = df.set_index('timestamp')
        if combined is None:
            combined = df
        else:
            combined = combined.add(df, fill_value=0)
    combined.index = pd.to_datetime(combined.index)

    # Build category-aggregated frame
    cat = pd.DataFrame(index=combined.index)
    for c, members in RES_AGG.items():
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
