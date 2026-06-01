"""Build per-category 6x24 SHELF LF tables.

LF semantics (preserved from legacy + VA prototype):
  LF[slice, hour] = mean over days in slice of (category[d, h] / annual_category)
For peak slices: mean across the top-N peak days (DOY list).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from .clustering import ClusteringResult, SLICE_NAMES


def build_shelf_for_category(
    series: pd.Series,
    cr: ClusteringResult,
) -> pd.DataFrame:
    """Return 6 x 24 DataFrame of LFs for one SHELF category, indexed by SLICE_NAMES."""
    out = pd.DataFrame(0.0, index=SLICE_NAMES, columns=[f'Hour{h}' for h in range(24)])
    annual = float(series.sum())
    if annual <= 0:
        return out
    df = pd.DataFrame({'v': series.values}, index=series.index)
    df['day'] = df.index.dayofyear
    df['hour'] = df.index.hour
    df['lf'] = df['v'] / annual
    df['slice'] = df['day'].map(cr.slice_assignment.to_dict())

    for sl in ['Winter', 'Spring', 'Summer', 'Fall']:
        mask = df['slice'] == sl
        if mask.sum() == 0:
            continue
        prof = df[mask].groupby('hour')['lf'].mean().reindex(range(24)).fillna(0).values
        out.loc[sl] = prof

    sp = df[df['day'].isin(cr.sp_top_days)].groupby('hour')['lf'].mean().reindex(range(24)).fillna(0).values
    wp = df[df['day'].isin(cr.wp_top_days)].groupby('hour')['lf'].mean().reindex(range(24)).fillna(0).values
    out.loc['Summer Peak'] = sp
    out.loc['Winter Peak'] = wp
    return out


def build_all_shelf(
    hourly_demand: pd.DataFrame,
    cr: ClusteringResult,
) -> dict[str, pd.DataFrame]:
    """Return {category_name: 6x24 DataFrame}."""
    return {col: build_shelf_for_category(hourly_demand[col], cr)
            for col in hourly_demand.columns}
