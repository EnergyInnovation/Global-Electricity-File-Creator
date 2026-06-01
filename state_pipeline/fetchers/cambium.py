"""Read Cambium 2022 Mid-case state hourly + annual capacity for one state.

- Hourly file: row 6 (1-indexed) is the column-name row; data rows follow.
  We skip the first 5 header rows (skiprows=5) and use header=0 from there.
- Annual file: same structure; row 6 is column names; data starts row 7.

CFs computed: cf[h, tech] = generation_<tech>_MWh[h] / capacity_<tech>_MW
Negative CFs (e.g. phs_charging) and CFs > 1.0 are clipped to [0, 1].

Cambium calendar starts on Sunday 2012; 2018 starts Monday. We shift hours
forward by 1 day so weekday/weekend pattern matches our 2018 LST calendar.

Curtailment add-back (v1.1):
---------------------------
The Cambium 2022 state files (both hourly and annual) do NOT include any
explicit curtailment columns. After auditing both `Cambium22_MidCase_annual_state.csv`
and `Cambium22_MidCase_hourly_VA_2024.csv`, no `curt_*`, `curtailment*`,
`spill*`, or related fields exist. The Cambium documentation
(https://www.nrel.gov/docs/fy23osti/84916.pdf) confirms that per-tech
generation in the state files is reported AFTER curtailment.

For SYSHECF, EPS expects pre-curtailment resource availability so it can
do its own dispatch. Since per-tech curtailment is not directly available,
v1.1 supports an optional per-state, per-tech CF scaling factor configured
in the preset YAML under `curtailment_addback`. The factor `f_t` for tech
`t` represents the assumed annual curtailment fraction (e.g. 0.05 = 5%
curtailed). Effective CF becomes `cf_observed / (1 - f_t)`, then clipped to
[0, 1].

For VA in 2024, VRE penetration is low (solar+wind ~21% of generation) and
curtailment is essentially zero in Cambium dispatch — so the default
curtailment_addback values are 0.0. For high-VRE states (CA, TX, etc.) the
operator should set non-zero values guided by a Cambium nationwide
curtailment estimate or external sources (e.g., CAISO/ERCOT reports).

Documented limitation: this is a uniform annual scale, not an hourly
add-back. A true hourly add-back would require resource-availability data
(NSRDB irradiance, WIND Toolkit) which is deferred to v2.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

from ..paths import resolve_input
from ..categories import SYSHECF_CATEGORIES


def _read_with_skiprows(path: Path, skiprows: int) -> pd.DataFrame:
    return pd.read_csv(path, skiprows=skiprows, low_memory=False)


def fetch_cambium(
    hourly_csv: str,
    annual_csv: str,
    state_iso2: str,
    year: int,
    curtailment_addback: dict[str, float] | None = None,
):
    """Return (hourly_cfs: DataFrame[8760 x N_techs], annual_capacity: dict[tech_slug -> MW]).

    Parameters
    ----------
    curtailment_addback : optional dict mapping SYSHECF tech name to assumed
        annual curtailment fraction in [0, 0.5]. Effective CF is
        `cf_observed / (1 - f)`, clipped to [0, 1]. Default: empty (no scaling).
    """
    hp = resolve_input(hourly_csv)
    ap = resolve_input(annual_csv)
    addback = dict(curtailment_addback or {})

    h = _read_with_skiprows(hp, 5)
    a = _read_with_skiprows(ap, 5)

    a = a[(a['state'] == state_iso2) & (a['t'] == year)]
    if a.empty:
        raise RuntimeError(f"Cambium annual: no row for state={state_iso2}, t={year}")

    tech_caps: dict[str, float] = {}
    cf_data: dict[str, np.ndarray] = {}

    h = h.iloc[:8760].reset_index(drop=True)

    # Apply 1-day shift (Cambium starts Sunday 2012, our calendar is 2018-Monday).
    shift_hours = 24

    for cat in SYSHECF_CATEGORIES:
        if not cat.is_variable:
            continue
        gcol = cat.cambium_column
        ccol = cat.cambium_capacity_column
        if gcol is None or ccol is None:
            continue
        if gcol not in h.columns or ccol not in a.columns:
            cf_data[cat.name] = np.zeros(8760)
            tech_caps[cat.name] = 0.0
            continue
        cap = float(a.iloc[0][ccol]) if pd.notna(a.iloc[0][ccol]) else 0.0
        tech_caps[cat.name] = cap
        gen = h[gcol].fillna(0).values.astype(float)
        gen = np.roll(gen, shift_hours)
        if cap > 0:
            cf = gen / cap
        else:
            cf = np.zeros(8760)
        # Curtailment add-back: scale by 1/(1-f), clip to [0,1]
        f = float(addback.get(cat.name, 0.0))
        if f > 0.0 and f < 0.5:
            cf = cf / (1.0 - f)
        cf = np.clip(cf, 0.0, 1.0)
        cf_data[cat.name] = cf

    idx = pd.date_range('2018-01-01', periods=8760, freq='h')
    cfs = pd.DataFrame(cf_data, index=idx)
    cfs.index.name = 'ts'
    return cfs, tech_caps
