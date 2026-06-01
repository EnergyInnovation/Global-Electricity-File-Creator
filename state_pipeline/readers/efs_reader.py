"""Read EFS Reference/Moderate state-level hourly load profiles.

Returns a DataFrame indexed by 8760 hour-beginning timestamps (2018 LST) with
columns for industry, transportation by veh-type, and 'other' shapes used by
non-building SHELF categories.

EFS subsectors actually present:
  Commercial: other, space heating and cooling, water heating
  Industrial: other, machine drives, process heat
  Residential: other, space heating and cooling, water heating, clothes and dish washing/drying
  Transportation: light-duty vehicles, heavy-duty trucks, medium-duty trucks

Industry shape modes (v1.1)
---------------------------
EFS industrial uses 2012 actual weather + regression-based modeling, which
overstates diurnal/seasonal variation for the bulk of industrial load that
runs continuously. We support three modes:

- `efs` : original EFS-derived shape (legacy behavior).
- `flat`: constant per hour (annual / 8760). Simplest & most defensible
  default for bulk manufacturing/mining (~24/7 operation).
- `cambium_residual`: derive industry shape as
  `cambium_busbar_load - resstock_total - comstock_total - efs_transport`,
  giving a residual that captures real industrial dispatch. Falls back to
  `flat` if the residual produces negatives or non-physical values.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import zipfile_deflate64 as zipfile

from ..paths import resolve_input


def _hourly_index_2018() -> pd.DatetimeIndex:
    return pd.date_range('2018-01-01', periods=8760, freq='h')


def read_efs_state(efs_zip: str, state_iso2: str, year: int) -> pd.DataFrame:
    """Return DataFrame with 8760 rows indexed 2018-Jan-1 hourly LST.

    Columns include shape series (relative; raw MW, not normalized) for:
      industry           : Industrial sum (EFS-based, weather-driven)
      LDVs               : Transportation light-duty vehicles
      HDVs               : Transportation heavy-duty + medium-duty trucks
      aircraft, rail, ships, motorbikes : (proxy = LDVs since EFS lacks these)
      other_industry_proxy: same as industry, for district-heat-hydrogen + geoeng
      transport_total    : sum of LDVs + HDVs (used by cambium_residual)
    """
    p = resolve_input(efs_zip)
    z = zipfile.ZipFile(p)
    name = z.namelist()[0]
    with z.open(name) as f:
        chunks = []
        for ch in pd.read_csv(f, chunksize=2_000_000):
            ch = ch[(ch['State'] == state_iso2) & (ch['Year'] == year)]
            if not ch.empty:
                chunks.append(ch)
    if not chunks:
        z = zipfile.ZipFile(p)
        with z.open(name) as f:
            chunks = []
            for ch in pd.read_csv(f, chunksize=2_000_000):
                ch = ch[ch['State'] == state_iso2]
                if not ch.empty:
                    chunks.append(ch)
        if chunks:
            allf = pd.concat(chunks, ignore_index=True)
            yrs = sorted(allf['Year'].unique())
            nearest = min(yrs, key=lambda y: abs(int(y) - year))
            allf = allf[allf['Year'] == nearest]
            chunks = [allf]
    if not chunks:
        raise RuntimeError(f"EFS: no rows for state {state_iso2}")
    df = pd.concat(chunks, ignore_index=True)

    df = df.sort_values(['Sector', 'Subsector', 'LocalHourID'])

    idx = _hourly_index_2018()
    out = pd.DataFrame(index=idx)

    ind = df[df['Sector'] == 'Industrial'].groupby('LocalHourID')['LoadMW'].sum()
    out['industry'] = ind.reindex(range(1, 8761)).fillna(0).values

    tr = df[df['Sector'] == 'Transportation']
    ldv = tr[tr['Subsector'] == 'light-duty vehicles'].groupby('LocalHourID')['LoadMW'].sum()
    hdv = tr[tr['Subsector'] == 'heavy-duty trucks'].groupby('LocalHourID')['LoadMW'].sum()
    mdv = tr[tr['Subsector'] == 'medium-duty trucks'].groupby('LocalHourID')['LoadMW'].sum()

    out['LDVs'] = ldv.reindex(range(1, 8761)).fillna(0).values
    out['HDVs'] = (hdv.reindex(range(1, 8761)).fillna(0)
                   + mdv.reindex(range(1, 8761)).fillna(0)).values

    out['aircraft'] = out['LDVs'].values
    out['rail'] = out['LDVs'].values
    out['ships'] = out['LDVs'].values
    out['motorbikes'] = out['LDVs'].values

    out['other_industry_proxy'] = out['industry'].values
    out['transport_total'] = (out['LDVs'].values + out['HDVs'].values)

    for col in out.columns:
        if out[col].sum() == 0:
            out[col] = out['industry'].values

    out.index.name = 'ts'
    return out


def apply_industry_shape_mode(
    efs_hr: pd.DataFrame,
    mode: str = 'flat',
    *,
    cambium_busbar_load: pd.Series | None = None,
    resstock_total: pd.Series | None = None,
    comstock_total: pd.Series | None = None,
) -> pd.DataFrame:
    """Override `industry` column in efs_hr per the chosen mode.

    mode in {'efs', 'flat', 'cambium_residual'}.
    - 'efs': leave EFS industrial shape unchanged.
    - 'flat': replace industry with constant 1.0 (shape sum scaled later).
    - 'cambium_residual': industry = busbar_load - resstock_total - comstock_total - transport.
      Requires cambium_busbar_load (8760), resstock_total, comstock_total.
      Falls back to flat if residual has > 5% negative hours.

    Returns a copy with industry + other_industry_proxy updated.
    """
    out = efs_hr.copy()
    n = len(out)
    if mode == 'efs':
        return out
    if mode == 'flat':
        out['industry'] = 1.0
        out['other_industry_proxy'] = 1.0
        return out
    if mode == 'cambium_residual':
        if cambium_busbar_load is None or resstock_total is None or comstock_total is None:
            # missing inputs - fallback to flat
            out['industry'] = 1.0
            out['other_industry_proxy'] = 1.0
            return out
        # Cambium busbar is in MWh; ResStock/ComStock totals are in kWh per hour.
        bl = pd.Series(cambium_busbar_load).reindex(out.index).fillna(0).values.astype(float)
        rs = pd.Series(resstock_total).reindex(out.index).fillna(0).values.astype(float) / 1000.0
        cs = pd.Series(comstock_total).reindex(out.index).fillna(0).values.astype(float) / 1000.0
        # Approach: residual = bl - rs - cs (transport is small share for shape; ignore).
        residual = bl - rs - cs
        neg_share = float((residual < 0).sum()) / n
        if neg_share > 0.05 or residual.sum() <= 0:
            out['industry'] = 1.0
            out['other_industry_proxy'] = 1.0
        else:
            residual = np.clip(residual, 0.0, None)
            out['industry'] = residual
            out['other_industry_proxy'] = residual
        return out
    # unknown mode -> flat
    out['industry'] = 1.0
    out['other_industry_proxy'] = 1.0
    return out
