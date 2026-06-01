"""Fast K6/H24 clustering — numpy-vectorized version of clustering.cluster_days.

Drop-in replacement that runs ~50-100x faster on the iterative peak-day
reassignment, allowing higher (or unbounded) max_peak_days values without
prohibitive runtime.

Algorithm is identical to clustering.cluster_days:
  1. Build daily net-load features (mean, min, p95, ramp_max)
  2. Pin top-N peak days per season (k-means seed)
  3. K-means cluster remaining days into 4 clusters
  4. Iteratively reassign high-peak days into peak slices if NRMSE improves
  5. Multi-seed search; pick lowest NRMSE
  6. Map non-peak cluster IDs to {Winter, Spring, Summer, Fall} by mean DOY

Optimization: _score_reconstruction does the heavy work via numpy add.at
instead of pandas groupby.
"""
from __future__ import annotations
from typing import Iterable
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .clustering import (
    ClusteringResult, SLICE_NAMES, FEATURE_WEIGHTS,
    _build_daily_features, _max_abs_ramp, _name_clusters_by_doy,
)


SLICE_INDEX = {sl: i for i, sl in enumerate(SLICE_NAMES)}


def _fast_score(
    demand_8760: np.ndarray,        # (8760,)
    hour_arr_8760: np.ndarray,      # (8760,) hour-of-day 0..23
    day_arr_8760: np.ndarray,       # (8760,) day-of-year 1..365
    day_slice_arr: np.ndarray,      # (365,) slice index 0..5 per day-of-year (1-based: index 0 unused)
    n_days: int = 365,
) -> float:
    """Vectorized NRMSE. day_slice_arr[d] gives slice index for day-of-year d.
    Returns NRMSE of reconstruction.
    """
    # slice index per hour
    slice_per_hr = day_slice_arr[day_arr_8760]  # (8760,)

    # Build (slice, hour) accumulators: 6 slices x 24 hours
    sum_table = np.zeros((6, 24), dtype=np.float64)
    cnt_table = np.zeros((6, 24), dtype=np.int64)
    np.add.at(sum_table, (slice_per_hr, hour_arr_8760), demand_8760)
    np.add.at(cnt_table, (slice_per_hr, hour_arr_8760), 1)

    mean_table = np.where(cnt_table > 0, sum_table / np.maximum(cnt_table, 1), 0.0)
    recon = mean_table[slice_per_hr, hour_arr_8760]

    rng = demand_8760.max() - demand_8760.min()
    if rng <= 0:
        rng = 1.0
    nrmse = float(np.sqrt(np.mean((demand_8760 - recon) ** 2)) / rng)
    return nrmse


def _fast_improve_pinned(
    demand_8760: np.ndarray,
    hour_arr_8760: np.ndarray,
    day_arr_8760: np.ndarray,
    day_slice_init: np.ndarray,  # initial day -> slice index (length 366; index 0 unused)
    day_peak_by_day: np.ndarray, # (366,) peak demand per day (0 unused)
    summer_pool: list[int],
    winter_pool: list[int],
    max_peak_days: int = 365,
) -> tuple[np.ndarray, float]:
    """Greedy hill-climb. Try moving each candidate day to peak slice; accept if NRMSE improves."""
    day_slice = day_slice_init.copy()
    current = _fast_score(demand_8760, hour_arr_8760, day_arr_8760, day_slice)

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
                s = _fast_score(demand_8760, hour_arr_8760, day_arr_8760, day_slice)
                day_slice[d] = prev
                if s + 1e-12 < best_score:
                    best_score = s
                    best_day = d
            if best_day >= 0:
                day_slice[best_day] = peak_idx
                current = best_score
                improved = True
    return day_slice, current


def cluster_days_fast(
    total_demand: pd.Series,
    solar_gen: pd.Series,
    wind_gen: pd.Series,
    *,
    peak_top_n: int = 5,
    max_peak_days: int = 365,
    feature_weight_mode: str = 'netload_focus',
    search_seeds: Iterable[int] | None = None,
    n_init: int = 10,
    summer_months: Iterable[int] = (6, 7, 8),
    winter_months: Iterable[int] = (11, 12, 1, 2),
) -> ClusteringResult:
    """Fast version of cluster_days. See clustering.cluster_days for parameter docs."""
    idx = total_demand.index
    if not isinstance(idx, pd.DatetimeIndex):
        raise TypeError("total_demand must have DatetimeIndex")

    net = (total_demand - solar_gen.reindex(idx, fill_value=0)
           - wind_gen.reindex(idx, fill_value=0))

    df = pd.DataFrame({'demand': total_demand.values, 'net': net.values}, index=idx)
    df['day'] = df.index.dayofyear
    df['hour'] = df.index.hour
    df['month'] = df.index.month

    daily_max = df.groupby('day')['demand'].max()
    day_month = df.groupby('day')['month'].first()

    summer_set = set(int(m) for m in summer_months)
    winter_set = set(int(m) for m in winter_months)
    summer_pool = [int(d) for d in day_month.index if int(day_month.loc[d]) in summer_set]
    winter_pool = [int(d) for d in day_month.index if int(day_month.loc[d]) in winter_set]
    sp_pinned_init = sorted(daily_max.loc[summer_pool].sort_values(ascending=False)
                            .head(peak_top_n).index.astype(int).tolist())
    wp_pinned_init = sorted(daily_max.loc[winter_pool].sort_values(ascending=False)
                            .head(peak_top_n).index.astype(int).tolist())
    pinned_init = set(sp_pinned_init) | set(wp_pinned_init)

    net_by_day_hour = df.set_index([df['day'], df['hour']])['net'].unstack('hour')
    if net_by_day_hour.isna().any().any():
        raise ValueError("Net load must contain 24 hourly values per day.")
    features = _build_daily_features(net_by_day_hour)

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

    # Numpy arrays for fast scoring
    demand_arr = df['demand'].values.astype(np.float64)
    hour_arr = df['hour'].values.astype(np.int64)
    day_arr = df['day'].values.astype(np.int64)
    day_peak = np.zeros(367, dtype=np.float64)
    for d in daily_max.index:
        day_peak[int(d)] = float(daily_max.loc[d])

    best_score = float('inf')
    best_day_slice: np.ndarray | None = None
    score_by_seed: dict[int, float] = {}

    for seed in seen:
        km = KMeans(n_clusters=4, random_state=seed, n_init=n_init)
        raw = km.fit_predict(scaled.loc[nonpeak_days])
        cid_series = pd.Series(raw, index=nonpeak_days, name='cid')
        cid_to_season = _name_clusters_by_doy(cid_series)

        # Build initial day -> slice index array
        day_slice = np.full(367, SLICE_INDEX['Winter'], dtype=np.int64)
        for d, cid in cid_series.items():
            day_slice[int(d)] = SLICE_INDEX[cid_to_season[int(cid)]]
        for d in sp_pinned_init:
            day_slice[int(d)] = SLICE_INDEX['Summer Peak']
        for d in wp_pinned_init:
            day_slice[int(d)] = SLICE_INDEX['Winter Peak']

        day_slice, score = _fast_improve_pinned(
            demand_arr, hour_arr, day_arr, day_slice, day_peak,
            summer_pool, winter_pool, max_peak_days=max_peak_days,
        )
        score_by_seed[seed] = score
        if score < best_score:
            best_score = score
            best_day_slice = day_slice.copy()

    if best_day_slice is None:
        raise RuntimeError("Clustering failed")

    # Convert back to ClusteringResult
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
        daily_peak=daily_max,
        net_load=pd.Series((total_demand.values - solar_gen.reindex(idx, fill_value=0).values
                            - wind_gen.reindex(idx, fill_value=0).values),
                           index=idx),
        nrmse=float(best_score),
        best_seed=int(best_seed),
        score_by_seed=score_by_seed,
    )
