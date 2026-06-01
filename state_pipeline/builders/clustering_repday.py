"""K6/H24 clustering — legacy methodology (representative-day, net-load, NRMSE-std).

Faithfully reproduces energy_timeslice_pipeline.cluster_timeslices' scoring:

  * Net load (busbar - solar - wind), NOT gross demand
  * Per-slice REPRESENTATIVE DAY (single day), NOT slice mean
      - Non-peak slices: rep day = day closest to feature-space centroid
      - Peak slices: rep day = initially pinned day (most extreme by net peak)
      - Rep days are FIXED — adding more days to a peak slice does NOT change
        which day is "representative"
  * Score = RMSE / std of observed net load (NRMSE-std)

Why this matters: with slice-mean reconstruction, adding days to a peak slice
flattens the mean, so the optimizer absorbs "hot half / cold half" into Peak
slices to minimize mean fit error. With rep-day reconstruction, the rep day
profile doesn't change when growing the slice — peak slices only grow with
days whose actual shape matches the extreme rep day's shape. The result is
semantically meaningful, capacity-driven peak slices.

Numpy-vectorized for speed.
"""
from __future__ import annotations
from typing import Iterable
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .clustering import (
    ClusteringResult, SLICE_NAMES, FEATURE_WEIGHTS,
    _build_daily_features, _name_clusters_by_doy,
)


SLICE_INDEX = {sl: i for i, sl in enumerate(SLICE_NAMES)}


def _fast_score_repday(
    net_8760: np.ndarray,            # (8760,) net load
    hour_arr_8760: np.ndarray,       # (8760,) hour-of-day 0..23
    day_arr_8760: np.ndarray,        # (8760,) day-of-year 1..365
    day_slice_arr: np.ndarray,       # (367,) slice index per DOY
    rep_profile: np.ndarray,         # (6, 24) FIXED rep profile per slice
    std_net: float,                  # std of full-year net load (for normalization)
) -> float:
    """NRMSE-std using FIXED rep profiles. Returns rmse/std."""
    slice_per_hr = day_slice_arr[day_arr_8760]
    recon = rep_profile[slice_per_hr, hour_arr_8760]
    rmse = float(np.sqrt(np.mean((net_8760 - recon) ** 2)))
    if std_net <= 0:
        return float('inf')
    return rmse / std_net


def _greedy_grow_peaks(
    net_8760: np.ndarray,
    hour_arr_8760: np.ndarray,
    day_arr_8760: np.ndarray,
    day_slice_init: np.ndarray,
    rep_profile: np.ndarray,          # FIXED, set once before iteration
    std_net: float,
    day_peak_by_day: np.ndarray,
    summer_pool: list[int],
    winter_pool: list[int],
    max_peak_days: int = 365,
) -> tuple[np.ndarray, float]:
    """Iteratively reassign candidate days into peak slice if NRMSE improves.
    Rep profile is FIXED — only slice membership changes."""
    day_slice = day_slice_init.copy()
    current = _fast_score_repday(
        net_8760, hour_arr_8760, day_arr_8760, day_slice, rep_profile, std_net
    )

    for season_pool, peak_idx in [(summer_pool, SLICE_INDEX['Summer Peak']),
                                    (winter_pool, SLICE_INDEX['Winter Peak'])]:
        cands = [d for d in season_pool if day_slice[d] != peak_idx]
        cands.sort(key=lambda d: -day_peak_by_day[d])
        improved = True
        while improved:
            improved = False
            cur_count = int(np.sum(day_slice == peak_idx))
            if cur_count >= max_peak_days:
                break
            best_score = current
            best_day = -1
            for d in cands:
                if day_slice[d] == peak_idx:
                    continue
                prev = day_slice[d]
                day_slice[d] = peak_idx
                s = _fast_score_repday(
                    net_8760, hour_arr_8760, day_arr_8760, day_slice, rep_profile, std_net
                )
                day_slice[d] = prev
                if s + 1e-12 < best_score:
                    best_score = s
                    best_day = d
            if best_day >= 0:
                day_slice[best_day] = peak_idx
                current = best_score
                improved = True
    return day_slice, current


def cluster_days_repday(
    total_demand: pd.Series,
    solar_gen: pd.Series,
    wind_gen: pd.Series,
    *,
    peak_top_n: int = 1,
    max_peak_days: int = 365,
    feature_weight_mode: str = 'netload_focus',
    search_seeds: Iterable[int] | None = None,
    n_init: int = 10,
    summer_months: Iterable[int] = (6, 7, 8),
    winter_months: Iterable[int] = (11, 12, 1, 2),
) -> ClusteringResult:
    """Cluster using the legacy rep-day / net-load methodology."""
    idx = total_demand.index
    if not isinstance(idx, pd.DatetimeIndex):
        raise TypeError("total_demand must have DatetimeIndex")

    net = (total_demand - solar_gen.reindex(idx, fill_value=0)
           - wind_gen.reindex(idx, fill_value=0))

    df = pd.DataFrame({'demand': total_demand.values, 'net': net.values}, index=idx)
    df['day'] = df.index.dayofyear
    df['hour'] = df.index.hour
    df['month'] = df.index.month

    daily_net_max = df.groupby('day')['net'].max()
    daily_demand_max = df.groupby('day')['demand'].max()
    day_month = df.groupby('day')['month'].first()

    summer_set = set(int(m) for m in summer_months)
    winter_set = set(int(m) for m in winter_months)
    summer_pool = [int(d) for d in day_month.index if int(day_month.loc[d]) in summer_set]
    winter_pool = [int(d) for d in day_month.index if int(day_month.loc[d]) in winter_set]
    sp_pinned_init = sorted(daily_net_max.loc[summer_pool].sort_values(ascending=False)
                            .head(peak_top_n).index.astype(int).tolist())
    wp_pinned_init = sorted(daily_net_max.loc[winter_pool].sort_values(ascending=False)
                            .head(peak_top_n).index.astype(int).tolist())
    pinned_init = set(sp_pinned_init) | set(wp_pinned_init)

    # Net load 367x24 matrix (DOY 0 unused)
    net_by_day_hr = np.zeros((367, 24), dtype=np.float64)
    for d in range(1, 366):
        rows = df[df['day'] == d]
        if len(rows) >= 24:
            net_by_day_hr[d] = rows.set_index('hour')['net'].reindex(range(24)).values

    # Daily features for k-means
    net_by_day_hour_pd = df.set_index([df['day'], df['hour']])['net'].unstack('hour')
    if net_by_day_hour_pd.isna().any().any():
        raise ValueError("Net load must contain 24 hourly values per day.")
    features = _build_daily_features(net_by_day_hour_pd)

    if feature_weight_mode not in FEATURE_WEIGHTS:
        raise ValueError(f"Unknown feature_weight_mode '{feature_weight_mode}'.")
    weighted = features.mul(pd.Series(FEATURE_WEIGHTS[feature_weight_mode]), axis=1)
    scaled = pd.DataFrame(
        StandardScaler().fit_transform(weighted),
        index=weighted.index, columns=weighted.columns,
    )

    nonpeak_days = [int(d) for d in features.index if int(d) not in pinned_init]

    if search_seeds is None:
        candidate_seeds = [0, 1, 2, 3, 4, 5, 10, 20, 99]
    else:
        candidate_seeds = list(search_seeds)
    seen = []
    for s in candidate_seeds:
        if int(s) not in seen:
            seen.append(int(s))

    net_arr = df['net'].values.astype(np.float64)
    hour_arr = df['hour'].values.astype(np.int64)
    day_arr = df['day'].values.astype(np.int64)
    std_net = float(np.std(net_arr))
    day_net_peak = np.zeros(367, dtype=np.float64)
    for d in daily_net_max.index:
        day_net_peak[int(d)] = float(daily_net_max.loc[d])

    best_score = float('inf')
    best_day_slice: np.ndarray | None = None
    best_rep_profile: np.ndarray | None = None
    score_by_seed: dict[int, float] = {}

    for seed in seen:
        km = KMeans(n_clusters=4, random_state=seed, n_init=n_init)
        raw = km.fit_predict(scaled.loc[nonpeak_days])
        cid_series = pd.Series(raw, index=nonpeak_days, name='cid')
        cid_to_season = _name_clusters_by_doy(cid_series)

        # Initial day -> slice
        day_slice = np.full(367, SLICE_INDEX['Winter'], dtype=np.int64)
        for d, cid in cid_series.items():
            day_slice[int(d)] = SLICE_INDEX[cid_to_season[int(cid)]]
        for d in sp_pinned_init:
            day_slice[int(d)] = SLICE_INDEX['Summer Peak']
        for d in wp_pinned_init:
            day_slice[int(d)] = SLICE_INDEX['Winter Peak']

        # FIXED rep profiles per slice (legacy methodology):
        # - Non-peak slices: closest to feature-space centroid in that cluster
        # - Peak slices: the initially pinned most-extreme day
        rep_profile = np.zeros((6, 24), dtype=np.float64)
        # Non-peak: closest to centroid
        for season_name in ['Winter', 'Spring', 'Summer', 'Fall']:
            sl_idx = SLICE_INDEX[season_name]
            cluster_members = [d for d, cid in cid_series.items()
                                if cid_to_season[int(cid)] == season_name]
            if not cluster_members:
                continue
            feats = scaled.loc[cluster_members]
            centroid = feats.mean(axis=0)
            dists = ((feats - centroid) ** 2).sum(axis=1)
            rep_doy = int(dists.idxmin())
            rep_profile[sl_idx] = net_by_day_hr[rep_doy]
        # Peak slices: the initially pinned day (a single day)
        if sp_pinned_init:
            rep_profile[SLICE_INDEX['Summer Peak']] = net_by_day_hr[sp_pinned_init[0]]
        if wp_pinned_init:
            rep_profile[SLICE_INDEX['Winter Peak']] = net_by_day_hr[wp_pinned_init[0]]

        # Iteratively grow peak slices — rep_profile is fixed
        day_slice, score = _greedy_grow_peaks(
            net_arr, hour_arr, day_arr, day_slice, rep_profile, std_net,
            day_net_peak, summer_pool, winter_pool, max_peak_days=max_peak_days,
        )
        score_by_seed[seed] = score
        if score < best_score:
            best_score = score
            best_day_slice = day_slice.copy()
            best_rep_profile = rep_profile.copy()

    if best_day_slice is None:
        raise RuntimeError("Clustering failed")

    label_by_day: dict[int, str] = {}
    for d in features.index:
        label_by_day[int(d)] = SLICE_NAMES[int(best_day_slice[int(d)])]

    sp_top = sorted([d for d, sl in label_by_day.items() if sl == 'Summer Peak'])
    wp_top = sorted([d for d, sl in label_by_day.items() if sl == 'Winter Peak'])
    days_per_ts: dict[str, int] = {s: 0 for s in SLICE_NAMES}
    for d, sl in label_by_day.items():
        days_per_ts[sl] += 1

    slice_series = pd.Series(label_by_day, name='slice').sort_index()
    best_seed = min(score_by_seed, key=score_by_seed.get)

    return ClusteringResult(
        slice_assignment=slice_series,
        days_per_timeslice=days_per_ts,
        sp_top_days=sp_top,
        wp_top_days=wp_top,
        daily_peak=daily_demand_max,
        net_load=net,
        nrmse=float(best_score),
        best_seed=int(best_seed),
        score_by_seed=score_by_seed,
    )
