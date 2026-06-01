"""Aggregate ComStock 15-min state-level files to hourly commercial SHELF categories.

5 commercial categories per AEO BCEU mapping.
"""
from __future__ import annotations
from pathlib import Path
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


def read_comstock_hourly(comstock_dir: str) -> pd.DataFrame:
    base = resolve_input(comstock_dir)
    files = sorted(base.glob('*.csv'))
    if not files:
        raise FileNotFoundError(f"No ComStock CSVs in {base}")
    combined: pd.DataFrame | None = None
    for f in files:
        df = pd.read_csv(f, usecols=['timestamp'] + CS_COLS)
        df = df.set_index('timestamp')
        if combined is None:
            combined = df
        else:
            combined = combined.add(df, fill_value=0)
    combined.index = pd.to_datetime(combined.index)

    cat = pd.DataFrame(index=combined.index)
    cat['commercial-heating'] = combined['out.electricity.heating.energy_consumption']
    cat['commercial-cooling'] = (
        combined['out.electricity.cooling.energy_consumption']
        + combined['out.electricity.heat_rejection.energy_consumption']
        + combined['out.electricity.fans.energy_consumption']
        + combined['out.electricity.pumps.energy_consumption']
    )
    cat['commercial-lighting'] = (
        combined['out.electricity.interior_lighting.energy_consumption']
        + combined['out.electricity.exterior_lighting.energy_consumption']
    )
    cat['commercial-appliances'] = (
        combined['out.electricity.refrigeration.energy_consumption']
        + combined['out.electricity.water_systems.energy_consumption']
    )
    cat['commercial-other'] = (
        combined['out.electricity.interior_equipment.energy_consumption']
        + combined['out.electricity.heat_recovery.energy_consumption']
    )

    cat = cat.reset_index().rename(columns={'index': 'ts', 'timestamp': 'ts'})
    cat['hour_start'] = (cat['ts'] - pd.Timedelta(minutes=15)).dt.floor('h')
    hourly = cat.drop(columns=['ts']).groupby('hour_start').sum()
    hourly.index.name = 'ts'
    if len(hourly) > 8760:
        hourly = hourly.iloc[:8760]
    return hourly
