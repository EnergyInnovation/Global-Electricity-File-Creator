"""Clock of the Electrification Futures Study (EFS) hourly profiles: vehicle charging (LDVs, HDVs), rail and the
EFS industry column.

The EFS file gives each state's load by `LocalHourID`, the hour of the year on that state's local clock, and the
reader adds the states up hour by hour. Every other SHELF source is on Eastern Standard Time (Cambium and the
ResStock / ComStock files as stamped; SIELS after its per-state shift), so the national EFS series puts western
load up to three hours early against them.

The raw file is not needed to correct this approximately. If every state's profile has the same shape in local
time, the national series on Eastern time is the local-time series moved later by k hours with weight w_k, the
share of the load in states k hours behind Eastern, summed over k = 0..3. States differ somewhat in shape, so this
is an approximation; it is exact for the part of each profile that the states share.

Weights: share of 2024 population of the 48 contiguous states (Census Vintage 2025 state estimates, via
state-data-forecast `sources/processed/census/state_population_annual_2024_2050.csv`; DC, about 0.2% and Eastern,
is not in that file and is left out) by the time zone each state is given in STATE_TZ_OFFSET_TO_ET in
build_shelf_workbook.py. Population stands in for charging load; today's electric vehicles lean west (California),
so in early years the true shift is somewhat larger. Mean offset 0.918 h.

The saved EFS series shows no step at the 2012 daylight-saving changes (11 March, 4 November), so no daylight-saving
correction is made: as with the building data, NREL's modelled timing is kept as published.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CLOCKS = ('local', 'eastern')
# share of contiguous-US population 0, 1, 2 and 3 hours behind Eastern (Eastern, Central, Mountain, Pacific)
WEIGHTS = (0.4755, 0.2940, 0.0679, 0.1626)


def to_eastern(efs: pd.DataFrame) -> pd.DataFrame:
    """Move a national local-hour EFS series onto Eastern Standard Time: a weighted sum of the series moved later by
    0, 1, 2 and 3 hours (the year wraps). Annual energy is unchanged."""
    w = np.asarray(WEIGHTS) / sum(WEIGHTS)
    out = efs.copy()
    for c in efs.columns:
        v = efs[c].to_numpy(dtype=float)
        out[c] = sum(wk * np.roll(v, k) for k, wk in enumerate(w))
    return out
