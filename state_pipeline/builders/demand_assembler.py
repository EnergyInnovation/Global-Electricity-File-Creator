"""Combine annual demand totals with hourly shapes -> 8760 x 22 DataFrame of MWh per hour."""
from __future__ import annotations
import numpy as np
import pandas as pd

from ..categories import SHELF_CATEGORIES


def assemble_hourly_demand(
    annual_mwh: dict[str, float],
    resstock_hourly: pd.DataFrame,    # kWh per hour by residential category
    comstock_hourly: pd.DataFrame,    # kWh per hour by commercial category
    efs_hourly: pd.DataFrame,         # MW per hour shapes by industry/transport
) -> pd.DataFrame:
    """Return 8760 x 22 DataFrame, columns are SHELF category names, values are MWh.

    annual_mwh keys may include any subset of SHELF category names; missing -> 0.
    """
    idx = resstock_hourly.index  # 2018 LST hourly
    out = pd.DataFrame(index=idx, columns=[c.name for c in SHELF_CATEGORIES],
                       dtype=float).fillna(0.0)

    def _scale(shape: np.ndarray, annual: float) -> np.ndarray:
        s = shape.sum()
        if s <= 0 or annual <= 0:
            return np.zeros_like(shape)
        return shape * (annual / s)

    # Residential 5
    for cat in ['residential-heating', 'residential-cooling', 'residential-lighting',
                'residential-appliances', 'residential-other']:
        if cat in resstock_hourly.columns:
            shape = resstock_hourly[cat].values.astype(float)
            out[cat] = _scale(shape, annual_mwh.get(cat, 0.0))

    # Commercial 5
    for cat in ['commercial-heating', 'commercial-cooling', 'commercial-lighting',
                'commercial-appliances', 'commercial-other']:
        if cat in comstock_hourly.columns:
            shape = comstock_hourly[cat].values.astype(float)
            out[cat] = _scale(shape, annual_mwh.get(cat, 0.0))

    # Envelopes always zero
    out['residential-envelope'] = 0.0
    out['commercial-envelope'] = 0.0

    # Transportation 6 - use EFS shapes
    tr_shape_keys = {
        'LDVs': 'LDVs',
        'HDVs': 'HDVs',
        'aircraft': 'aircraft',
        'rail': 'rail',
        'ships': 'ships',
        'motorbikes': 'motorbikes',
    }
    for cat, key in tr_shape_keys.items():
        if key in efs_hourly.columns:
            shape = efs_hourly[key].values.astype(float)
            out[cat] = _scale(shape, annual_mwh.get(cat, 0.0))

    # Industry
    if 'industry' in efs_hourly.columns:
        out['industry'] = _scale(efs_hourly['industry'].values.astype(float),
                                 annual_mwh.get('industry', 0.0))

    # district-heat-hydrogen, geoeng -> industry-shape proxy; default annual=0
    proxy = efs_hourly.get('other_industry_proxy', efs_hourly.get('industry'))
    if proxy is not None:
        out['district-heat-hydrogen'] = _scale(proxy.values.astype(float),
                                               annual_mwh.get('district-heat-hydrogen', 0.0))
        out['geoeng'] = _scale(proxy.values.astype(float),
                               annual_mwh.get('geoeng', 0.0))

    # datacenters: flat 1/8760 shape
    dc_annual = annual_mwh.get('datacenters', 0.0)
    if dc_annual > 0:
        out['datacenters'] = dc_annual / 8760.0
    else:
        out['datacenters'] = 0.0

    out.index.name = 'ts'
    return out
