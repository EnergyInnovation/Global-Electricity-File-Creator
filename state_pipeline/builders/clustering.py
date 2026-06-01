"""Net-load clustering: 6 timeslices via k-means + pinned peak day optimization.

Optimization layer (ported from original energy_timeslice_pipeline.py):
  1. Compute daily features on net load: mean, min, p95, ramp_max
  2. Pin extreme days as Summer Peak / Winter Peak (1 each by default; can grow
     via iterative reassignment)
  3. K-means cluster the remaining days into 4 clusters, multi-seed search to
     find the lowest reconstruction NRMSE
  4. Iteratively test reassigning each same-season day into the pinned peak
     slice; accept reassignment if NRMSE improves
  5. Pick seed with the best score; map 4 non-peak clusters to season labels
     by their mean day-of-year (low DOY -> Winter ... high DOY -> Fall pattern)

References: Poncelet et al. 2017, NREL ReEDS validation methodology.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


SLICE_NAMES = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']

# Feature-weight presets (carried from original pipeline)
FEATURE_WEIGHTS = {
    'uniform':            {'net_mean': 1.0, 'net_min': 1.0, 'net_p95': 1.0, 'net_ramp_max': 1.0},
    'netload_focus':      {'net_mean': 2.5, 'net_min': 4.0, 'net_p95': 6.0, 'net_ramp_max': 4.0},
    'netload_ramp_focus': {'net_mean': 2.0, 'net_min': 3.0, 'net_p95': 5.0, 'net_ramp_max': 6.0},
}


@dataclass
class ClusteringResult:
    slice_assignment: pd.Series         # index=day_of_year (int), value=slice name in SLICE_NAMES
    days_per_timeslice: dict[str, int]
    sp_top_days: list                    # list of DOY ints assigned to 'Summer Peak'
    wp_top_days: list                    # list of DOY ints assigned to 'Winter Peak'
    daily_peak: pd.Series                # peak demand per day (index=DOY)
    net_load: pd.Series                  # 8760 hourly net load
    nrmse: float                         # reconstruction NRMSE on total demand (slice means)
    best_seed: int                       # seed selected by multi-seed search
    score_by_seed: dict[int, float]      # NRMSE per seed (for debugging)


def _max_abs_ramp(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    if len(arr) < 2:
        return 0.0
    diffs = np.diff(arr)
    return float(np.nanmax(np.abs(diffs))) if len(diffs) else 0.0


def _build_daily_features(net_by_day_hour: pd.DataFrame) -> pd.DataFrame:
    """net_by_day_hour: index=DOY, columns=Hour 0..23. Returns daily feature matrix."""
    feats = pd.DataFrame({
        'net_mean':     net_by_day_hour.mean(axis=1),
        'net_min':      net_by_day_hour.min(axis=1),
        'net_p95':      net_by_day_hour.quantile(0.95, axis=1),
        'net_ramp_max': net_by_day_hour.apply(lambda r: _max_abs_ramp(r.values), axis=1),
    }).sort_index()
    return feats


def _score_reconstruction(
    df_hourly: pd.DataFrame,
    label_by_day: dict[int, str],
) -> tuple[float, np.ndarray]:
    """Compute NRMSE of full-year reconstruction using slice-mean by hour-of-day."""
    work = df_hourly.copy()
    work['slice'] = work['day'].map(label_by_day)
    actual = work['demand'].values
    recon = np.zeros(len(work), dtype=float)
    for sl in SLICE_NAMES:
        mask = work['slice'] == sl
        if mask.sum() == 0:
            continue
        prof = work[mask].groupby('hour')['demand'].mean().reindex(range(24)).values
        idxs = np.where(mask.values)[0]
        recon[idxs] = prof[work['hour'].values[idxs]]
    rng = actual.max() - actual.min() or 1.0
    nrmse = float(np.sqrt(np.mean((actual - recon) ** 2)) / rng)
    return nrmse, recon


def _improve_pinned_assignments(
    label_by_day: dict[int, str],
    daily_peak: pd.Series,
    df_hourly: pd.DataFrame,
    summer_pool: list[int],
    winter_pool: list[int],
    max_peak_days: int = 10,
) -> dict[int, str]:
    """Iteratively reassign same-season days into pinned peak slices if NRMSE improves.

    Constrained greedy hill-climb: at each step, evaluate moving the highest-peak
    unassigned candidate into the peak slice; accept if it lowers NRMSE.

    Constraint: peak slice size cannot exceed `max_peak_days`. This preserves the
    semantic meaning of "Peak" as capacity-driving extreme conditions, not just
    a 6th general cluster. Without this cap, the optimizer aggressively grows
    peak slices toward NRMSE-optimal but capacity-meaningless mean shapes (e.g.
    66 days = "summer's hot half" rather than "extreme peak").
    """
    label = dict(label_by_day)
    current_score, _ = _score_reconstruction(df_hourly, label)

    for season_pool, target_label in [(summer_pool, 'Summer Peak'),
                                      (winter_pool, 'Winter Peak')]:
        # candidates: days in this season pool that are NOT already in the peak slice
        cands = [d for d in season_pool if label.get(d) != target_label]
        # Sort by daily peak descending: try the most extreme first
        cands.sort(key=lambda d: float(daily_peak.loc[d]), reverse=True)
        improved = True
        while improved:
            improved = False
            # Stop if peak slice already at cap
            cur_count = sum(1 for v in label.values() if v == target_label)
            if cur_count >= max_peak_days:
                break
            best_move_score = current_score
            best_day = None
            for d in cands:
                if label.get(d) == target_label:
                    continue
                trial = dict(label)
                trial[d] = target_label
                trial_score, _ = _score_reconstruction(df_hourly, trial)
                if trial_score + 1e-12 < best_move_score:
                    best_move_score = trial_score
                    best_day = d
            if best_day is not None:
                label[best_day] = target_label
                current_score = best_move_score
                improved = True
    return label


def _name_clusters_by_doy(
    cluster_ids: pd.Series,    # index=DOY, value=int cluster_id (0..k-1)
) -> dict[int, str]:
    """Map cluster IDs to season names by mean DOY of cluster members.

    Returns dict mapping cluster_id -> season name.
    Sorted by mean DOY: lowest -> Winter, then Spring, Summer, Fall.
    """
    season_seq = ['Winter', 'Spring', 'Summer', 'Fall']
    cluster_means = cluster_ids.groupby(cluster_ids).apply(lambda g: float(g.index.to_series().mean()))
    # sort cluster IDs by mean DOY ascending
    ranked = cluster_means.sort_values().index.tolist()
    out: dict[int, str] = {}
    for rank, cid in enumerate(ranked):
        if rank < len(season_seq):
            out[int(cid)] = season_seq[rank]
        else:
            # Should never reach here for n_clusters_nonpeak=4
            out[int(cid)] = f'Cluster_{rank}'
    return out


def cluster_days(
    total_demand: pd.Series,
    solar_gen: pd.Series,
    wind_gen: pd.Series,
    *,
    peak_top_n: int = 1,
    max_peak_days: int = 10,
    feature_weight_mode: str = 'netload_focus',
    search_seeds: Iterable[int] | None = None,
    n_init: int = 10,
    summer_months: Iterable[int] = (6, 7, 8),
    winter_months: Iterable[int] = (11, 12, 1, 2),
) -> ClusteringResult:
    """Cluster days into 6 representative timeslices with k-means + pinned peaks.

    Algorithm (matches original energy_timeslice_pipeline.cluster_timeslices):
      1. Build daily features on net load: mean, min, p95, ramp_max
      2. Pin top-N peak days per season as Summer Peak / Winter Peak
      3. K-means cluster remaining days into 4 clusters
      4. Iteratively reassign high-peak days into peak slices if NRMSE improves
      5. Multi-seed search: pick seed with lowest NRMSE
      6. Map non-peak cluster IDs to {Winter, Spring, Summer, Fall} by mean DOY

    peak_top_n: starting number of pinned days per peak slice. Iterative
                reassignment may grow this (e.g., from 1 to 3-5) if the
                expansion improves NRMSE.
    """
    idx = total_demand.index
    if not isinstance(idx, pd.DatetimeIndex):
        raise TypeError("total_demand must be DatetimeIndex")

    # Hourly net load
    net = (total_demand - solar_gen.reindex(idx, fill_value=0)
           - wind_gen.reindex(idx, fill_value=0))

    # Hourly working frame
    df = pd.DataFrame({
        'demand': total_demand.values,
        'net': net.values,
    }, index=idx)
    df['day'] = df.index.dayofyear
    df['hour'] = df.index.hour
    df['month'] = df.index.month

    # Daily peak (used for pinning + reassignment ranking)
    daily_max = df.groupby('day')['demand'].max()

    # Day-month map (for season pooling)
    day_month = df.groupby('day')['month'].first()

    # Pin top-N per season as starting points
    summer_set = set(int(m) for m in summer_months)
    winter_set = set(int(m) for m in winter_months)
    summer_pool = [int(d) for d in day_month.index if int(day_month.loc[d]) in summer_set]
    winter_pool = [int(d) for d in day_month.index if int(day_month.loc[d]) in winter_set]
    sp_pinned_init = sorted(daily_max.loc[summer_pool].sort_values(ascending=False)
                            .head(peak_top_n).index.astype(int).tolist())
    wp_pinned_init = sorted(daily_max.loc[winter_pool].sort_values(ascending=False)
                            .head(peak_top_n).index.astype(int).tolist())
    pinned_init = set(sp_pinned_init) | set(wp_pinned_init)

    # Daily net-load features (for k-means)
    net_by_day_hour = df.set_index([df['day'], df['hour']])['net'].unstack('hour')
    if net_by_day_hour.isna().any().any():
        raise ValueError("Net load profiles must contain 24 hourly values per day.")
    features = _build_daily_features(net_by_day_hour)

    if feature_weight_mode not in FEATURE_WEIGHTS:
        raise ValueError(f"Unknown feature_weight_mode '{feature_weight_mode}'.")
    weighted = features.mul(pd.Series(FEATURE_WEIGHTS[feature_weight_mode]), axis=1)
    scaled = pd.DataFrame(
        StandardScaler().fit_transform(weighted),
        index=weighted.index,
        columns=weighted.columns,
    )

    # K-means runs only on non-pinned days (4 clusters)
    nonpeak_days = [int(d) for d in features.index if int(d) not in pinned_init]
    n_clusters_nonpeak = 4

    # Multi-seed search
    if search_seeds is None:
        candidate_seeds = [0, 1, 2, 3, 4, 5, 10, 20, 99]
    else:
        candidate_seeds = list(search_seeds)
    seen = []
    for s in candidate_seeds:
        if int(s) not in seen:
            seen.append(int(s))

    best_score = float('inf')
    best_label_map: dict[int, str] | None = None
    score_by_seed: dict[int, float] = {}

    for seed in seen:
        km = KMeans(n_clusters=n_clusters_nonpeak, random_state=seed, n_init=n_init)
        raw = km.fit_predict(scaled.loc[nonpeak_days])
        cid_series = pd.Series(raw, index=nonpeak_days, name='cid')
        cid_to_season = _name_clusters_by_doy(cid_series)

        # Build full label_by_day with peak pins + season-named clusters
        label_by_day: dict[int, str] = {}
        for d, cid in cid_series.items():
            label_by_day[int(d)] = cid_to_season[int(cid)]
        for d in sp_pinned_init:
            label_by_day[int(d)] = 'Summer Peak'
        for d in wp_pinned_init:
            label_by_day[int(d)] = 'Winter Peak'

        # Iterative pinned-reassignment improvement (capped to max_peak_days)
        label_by_day = _improve_pinned_assignments(
            label_by_day, daily_max, df, summer_pool, winter_pool,
            max_peak_days=max_peak_days,
        )

        score, _ = _score_reconstruction(df, label_by_day)
        score_by_seed[seed] = score
        if score < best_score:
            best_score = score
            best_label_map = label_by_day

    if best_label_map is None:
        raise RuntimeError("Clustering failed for all seeds")

    # Final outputs
    sp_top = sorted([int(d) for d, sl in best_label_map.items() if sl == 'Summer Peak'])
    wp_top = sorted([int(d) for d, sl in best_label_map.items() if sl == 'Winter Peak'])
    days_per_ts: dict[str, int] = {s: 0 for s in SLICE_NAMES}
    for d, sl in best_label_map.items():
        days_per_ts[sl] += 1

    slice_series = pd.Series(best_label_map, name='slice').sort_index()
    best_seed = min(score_by_seed, key=score_by_seed.get)

    return ClusteringResult(
        slice_assignment=slice_series,
        days_per_timeslice=days_per_ts,
        sp_top_days=sp_top,
        wp_top_days=wp_top,
        daily_peak=daily_max,
        net_load=net,
        nrmse=float(best_score),
        best_seed=int(best_seed),
        score_by_seed=score_by_seed,
    )


# =============================================================================
# Validation metric suite (literature-standard).
# References: Poncelet et al. 2017, Mallapragada et al. 2018, NREL ReEDS.
# =============================================================================

def _nrmse(actual: np.ndarray, recon: np.ndarray) -> float:
    """NRMSE normalized by (max-min) range of actual."""
    a = np.asarray(actual, dtype=float)
    r = np.asarray(recon, dtype=float)
    rng = float(a.max() - a.min())
    if rng <= 0:
        return 0.0
    return float(np.sqrt(np.mean((a - r) ** 2)) / rng)


def _mae(actual: np.ndarray, recon: np.ndarray) -> float:
    a = np.asarray(actual, dtype=float)
    r = np.asarray(recon, dtype=float)
    return float(np.mean(np.abs(a - r)))


def _reconstruct_category_hourly(
    series: pd.Series,
    shelf_table: pd.DataFrame,
    cr: ClusteringResult,
) -> np.ndarray:
    """Reconstruct an 8760-length hourly series for one category from its SHELF
    table (LF[slice, hour]) and the slice assignment.

    Reconstruction at hour h on day d:
      recon[h] = LF[slice(d), hour(d, h)] * annual
    For peak slices (top-N days), use Summer/Winter Peak LF on those specific days.
    Otherwise use the seasonal LF.
    """
    annual = float(series.sum())
    idx = series.index
    n = len(idx)
    out = np.zeros(n, dtype=float)
    if annual <= 0:
        return out
    days = idx.dayofyear.values
    hours = idx.hour.values
    slice_map = cr.slice_assignment.to_dict()
    sp_set = set(cr.sp_top_days)
    wp_set = set(cr.wp_top_days)
    # Pre-extract LF rows
    hour_cols = [f'Hour{h}' for h in range(24)]
    lf_by_slice: dict[str, np.ndarray] = {}
    for sl in SLICE_NAMES:
        if sl in shelf_table.index:
            lf_by_slice[sl] = shelf_table.loc[sl, hour_cols].values.astype(float)
        else:
            lf_by_slice[sl] = np.zeros(24, dtype=float)
    for i in range(n):
        d = int(days[i])
        h = int(hours[i])
        if d in sp_set:
            sl = 'Summer Peak'
        elif d in wp_set:
            sl = 'Winter Peak'
        else:
            sl = slice_map.get(d, 'Winter')
        out[i] = lf_by_slice[sl][h] * annual
    return out


def _ldc_rmse(actual: np.ndarray, recon: np.ndarray, top_frac: float | None = None) -> float:
    """RMSE of load duration curve (sorted descending)."""
    a = np.sort(np.asarray(actual, dtype=float))[::-1]
    r = np.sort(np.asarray(recon, dtype=float))[::-1]
    if top_frac is not None:
        n = max(1, int(round(len(a) * top_frac)))
        a = a[:n]
        r = r[:n]
    return float(np.sqrt(np.mean((a - r) ** 2)))


def compute_validation_metrics(
    *,
    hourly_demand: pd.DataFrame,
    shelf_tables: dict[str, pd.DataFrame],
    cr: ClusteringResult,
    cambium_caps: dict[str, float],
    cambium_cfs: pd.DataFrame,
    annual_mwh: dict[str, float],
    weather_diag: dict[str, Any] | None = None,
    external_refs: dict[str, dict[str, float]] | None = None,
    state_iso2: str = 'VA',
) -> dict[str, Any]:
    """Compute all 10 validation sections.

    Returns a dict where each key is one section, with table/summary content.
    Each table is a list of rows; first row is the header.
    """
    sections: dict[str, Any] = {}
    common_idx = hourly_demand.index

    # Build full system reconstruction (sum of category reconstructions)
    total_actual = hourly_demand.sum(axis=1).values.astype(float)
    total_recon = np.zeros(len(common_idx), dtype=float)
    per_cat_recon: dict[str, np.ndarray] = {}
    for cat in hourly_demand.columns:
        recon = _reconstruct_category_hourly(hourly_demand[cat], shelf_tables.get(cat,
                pd.DataFrame(0.0, index=SLICE_NAMES,
                             columns=[f'Hour{h}' for h in range(24)])), cr)
        per_cat_recon[cat] = recon
        total_recon += recon

    # ----- Section 1: Energy Reconstruction (Annual) -----
    sec1 = [['category', 'annual_input_MWh', 'annual_reconstructed_MWh',
             'abs_diff_MWh', 'rel_diff']]
    for cat in hourly_demand.columns:
        a_in = float(hourly_demand[cat].sum())
        a_rec = float(per_cat_recon[cat].sum())
        diff = a_rec - a_in
        rel = diff / a_in if a_in > 0 else 0.0
        sec1.append([cat, round(a_in, 2), round(a_rec, 2),
                     round(diff, 2), round(rel, 6)])
    sections['section_1_energy_reconstruction'] = sec1

    # ----- Section 2: Hourly NRMSE (Total + per-slice + per-slice MAE) -----
    sec2 = [['scope', 'NRMSE', 'MAE_MWh', 'n_hours']]
    sec2.append(['total_year', round(_nrmse(total_actual, total_recon), 6),
                 round(_mae(total_actual, total_recon), 2), len(total_actual)])
    sa = cr.slice_assignment.to_dict()
    sp_set = set(cr.sp_top_days)
    wp_set = set(cr.wp_top_days)
    days_arr = common_idx.dayofyear.values
    for sl in SLICE_NAMES:
        # mask: days now assigned directly to this slice (peak days are in peak slices)
        mask = np.array([sa.get(int(d)) == sl for d in days_arr])
        if mask.sum() == 0:
            sec2.append([sl, 0.0, 0.0, 0])
        else:
            sec2.append([sl, round(_nrmse(total_actual[mask], total_recon[mask]), 6),
                         round(_mae(total_actual[mask], total_recon[mask]), 2),
                         int(mask.sum())])
    sections['section_2_hourly_nrmse'] = sec2

    # ----- Section 3: Per-end-use NRMSE -----
    sec3 = [['category', 'NRMSE', 'MAE_MWh', 'annual_MWh']]
    for cat in hourly_demand.columns:
        actual = hourly_demand[cat].values.astype(float)
        recon = per_cat_recon[cat]
        if actual.sum() <= 0:
            sec3.append([cat, 0.0, 0.0, 0.0])
        else:
            sec3.append([cat, round(_nrmse(actual, recon), 6),
                         round(_mae(actual, recon), 2),
                         round(float(actual.sum()), 2)])
    sections['section_3_per_enduse_nrmse'] = sec3

    # ----- Section 4: Peak Hour Preservation -----
    sec4 = [['metric', 'representative_MW', 'actual_MW',
             'preservation_ratio', 'note']]
    # System peak: representative = max of total_recon; actual = mean of top-5 days actual peak
    rep_peak = float(total_recon.max())
    daily_actual_peak = pd.Series(total_actual, index=common_idx).groupby(
        common_idx.dayofyear).max()
    actual_top5_avg = float(daily_actual_peak.sort_values(ascending=False).head(5).mean())
    sec4.append(['system_peak_hour',
                 round(rep_peak, 2), round(actual_top5_avg, 2),
                 round(rep_peak / actual_top5_avg, 4) if actual_top5_avg > 0 else 0.0,
                 'representative max vs top-5 days actual peak average'])
    # Summer Peak slice
    if cr.sp_top_days:
        sp_mask = np.array([int(d) in sp_set for d in days_arr])
        sp_recon_peak = float(total_recon[sp_mask].max()) if sp_mask.sum() > 0 else 0.0
        sp_actual_peak = float(daily_actual_peak.loc[
            [d for d in cr.sp_top_days if d in daily_actual_peak.index]].mean())
        sec4.append(['summer_peak_slice',
                     round(sp_recon_peak, 2), round(sp_actual_peak, 2),
                     round(sp_recon_peak / sp_actual_peak, 4) if sp_actual_peak > 0 else 0.0,
                     'Summer Peak slice reconstructed peak vs actual top-5 average'])
    if cr.wp_top_days:
        wp_mask = np.array([int(d) in wp_set for d in days_arr])
        wp_recon_peak = float(total_recon[wp_mask].max()) if wp_mask.sum() > 0 else 0.0
        wp_actual_peak = float(daily_actual_peak.loc[
            [d for d in cr.wp_top_days if d in daily_actual_peak.index]].mean())
        sec4.append(['winter_peak_slice',
                     round(wp_recon_peak, 2), round(wp_actual_peak, 2),
                     round(wp_recon_peak / wp_actual_peak, 4) if wp_actual_peak > 0 else 0.0,
                     'Winter Peak slice reconstructed peak vs actual top-5 average'])
    # Per-category peak preservation for peak-driving categories
    for cat in ['residential-cooling', 'commercial-cooling',
                'residential-heating', 'commercial-heating']:
        if cat not in hourly_demand.columns:
            continue
        cat_actual = hourly_demand[cat].values.astype(float)
        cat_recon = per_cat_recon[cat]
        cat_actual_top5 = float(pd.Series(cat_actual, index=common_idx).groupby(
            common_idx.dayofyear).max().sort_values(ascending=False).head(5).mean())
        cat_rep_peak = float(cat_recon.max())
        sec4.append([f'category_peak_{cat}',
                     round(cat_rep_peak, 2), round(cat_actual_top5, 2),
                     round(cat_rep_peak / cat_actual_top5, 4)
                     if cat_actual_top5 > 0 else 0.0, ''])
    sections['section_4_peak_preservation'] = sec4

    # ----- Section 5: Top-100 Hour Capture -----
    top_n_hours = 100
    actual_sorted_idx = np.argsort(total_actual)[::-1][:top_n_hours]
    captured = 0
    for i in actual_sorted_idx:
        if total_recon[i] >= 0.9 * total_actual[i]:
            captured += 1
    sec5 = [['metric', 'value', 'note']]
    sec5.append(['top_100_hours_capture_pct',
                 round(captured / top_n_hours, 4),
                 'fraction of top-100 actual hours where recon >= 90% of actual'])
    sec5.append(['top_100_actual_min_MW',
                 round(float(total_actual[actual_sorted_idx].min()), 2),
                 'lowest MW threshold of top-100 actual hours'])
    sec5.append(['top_100_recon_avg_MW',
                 round(float(total_recon[actual_sorted_idx].mean()), 2),
                 'avg reconstructed MW at top-100 actual hour positions'])
    sec5.append(['top_100_actual_avg_MW',
                 round(float(total_actual[actual_sorted_idx].mean()), 2),
                 'avg actual MW at top-100 hours'])
    sections['section_5_top100_capture'] = sec5

    # ----- Section 6: Net Load Peak Preservation -----
    # Net load = demand - solar_gen - wind_gen
    solar_gen_arr = np.zeros(len(common_idx), dtype=float)
    for tech in ['solar-pv', 'solar-pv-dist']:
        if tech in cambium_cfs.columns:
            solar_gen_arr += (cambium_cfs[tech].reindex(common_idx).fillna(0).values
                              * float(cambium_caps.get(tech, 0.0)))
    wind_gen_arr = np.zeros(len(common_idx), dtype=float)
    for tech in ['onshore-wind', 'offshore-wind']:
        if tech in cambium_cfs.columns:
            wind_gen_arr += (cambium_cfs[tech].reindex(common_idx).fillna(0).values
                             * float(cambium_caps.get(tech, 0.0)))
    nl_actual = total_actual - solar_gen_arr - wind_gen_arr
    nl_recon = total_recon - solar_gen_arr - wind_gen_arr  # VRE same in both
    sec6 = [['metric', 'representative_MW', 'actual_MW',
             'preservation_ratio', 'note']]
    nl_daily_peak_actual = pd.Series(nl_actual, index=common_idx).groupby(
        common_idx.dayofyear).max()
    nl_actual_top5_avg = float(nl_daily_peak_actual.sort_values(ascending=False).head(5).mean())
    nl_rep_peak = float(nl_recon.max())
    sec6.append(['net_load_peak_hour',
                 round(nl_rep_peak, 2), round(nl_actual_top5_avg, 2),
                 round(nl_rep_peak / nl_actual_top5_avg, 4)
                 if nl_actual_top5_avg > 0 else 0.0,
                 'representative net-load max vs top-5 days actual peak average'])
    if cr.sp_top_days:
        sp_mask = np.array([int(d) in sp_set for d in days_arr])
        if sp_mask.sum() > 0:
            sp_nl_recon = float(nl_recon[sp_mask].max())
            sp_nl_actual = float(nl_daily_peak_actual.loc[
                [d for d in cr.sp_top_days if d in nl_daily_peak_actual.index]].mean())
            sec6.append(['summer_peak_net_load',
                         round(sp_nl_recon, 2), round(sp_nl_actual, 2),
                         round(sp_nl_recon / sp_nl_actual, 4) if sp_nl_actual > 0 else 0.0, ''])
    if cr.wp_top_days:
        wp_mask = np.array([int(d) in wp_set for d in days_arr])
        if wp_mask.sum() > 0:
            wp_nl_recon = float(nl_recon[wp_mask].max())
            wp_nl_actual = float(nl_daily_peak_actual.loc[
                [d for d in cr.wp_top_days if d in nl_daily_peak_actual.index]].mean())
            sec6.append(['winter_peak_net_load',
                         round(wp_nl_recon, 2), round(wp_nl_actual, 2),
                         round(wp_nl_recon / wp_nl_actual, 4) if wp_nl_actual > 0 else 0.0, ''])
    sections['section_6_net_load_peak'] = sec6

    # ----- Section 7: Load Duration Curve Fit -----
    sec7 = [['scope', 'RMSE_MW', 'n_hours', 'note']]
    sec7.append(['top_1pct',
                 round(_ldc_rmse(total_actual, total_recon, top_frac=0.01), 2),
                 int(round(len(total_actual) * 0.01)),
                 'top 1% of LDC = top ~87 hours'])
    sec7.append(['top_5pct',
                 round(_ldc_rmse(total_actual, total_recon, top_frac=0.05), 2),
                 int(round(len(total_actual) * 0.05)),
                 'top 5% of LDC = top ~438 hours'])
    sec7.append(['overall',
                 round(_ldc_rmse(total_actual, total_recon, top_frac=None), 2),
                 len(total_actual),
                 'full 8760 LDC'])
    sections['section_7_ldc_fit'] = sec7

    # ----- Section 8: SHELF Balance Check -----
    # Sum (LF[slice, hour] x days_per_slice) over all 6 slices; should equal 1.0
    # since peak slices now have non-zero days and contribute to energy reconstruction.
    sec8 = [['category', 'shelf_balance_sum', 'deviation_from_1', 'note']]
    days = cr.days_per_timeslice
    for cat, tbl in shelf_tables.items():
        if hourly_demand.get(cat, pd.Series([0])).sum() <= 0:
            sec8.append([cat, 0.0, 0.0, 'category has zero annual energy'])
            continue
        s = 0.0
        for sl in SLICE_NAMES:
            s += float(tbl.loc[sl].sum()) * float(days.get(sl, 0))
        sec8.append([cat, round(s, 6), round(abs(s - 1.0), 6),
                     'expected ~1.0 across all 6 slices'])
    sections['section_8_shelf_balance'] = sec8

    # ----- Section 9: Weather-Year Alignment Diagnostics -----
    sec9 = [['metric', 'value', 'note']]
    if weather_diag:
        corr = weather_diag.get('summer_daily_corr_buildings_vs_solar_cf', float('nan'))
        sec9.append(['summer_daily_corr_buildings_vs_solar_cf',
                     round(float(corr), 4) if not np.isnan(corr) else 'nan',
                     'correlation of daily summer building demand vs daily solar CF'])
        sec9.append(['peak_day_buildings_doy',
                     int(weather_diag.get('peak_day_buildings_doy', 0)),
                     'day-of-year of peak building demand day'])
        for s_days, sd in sorted(weather_diag.get('net_load_under_day_shifts', {}).items()):
            sec9.append([f'net_load_peak_shift_{s_days}d',
                         round(float(sd['peak_MWh']), 2),
                         f"shifted gen by {s_days}d; peak hour {sd.get('peak_hour','')}"])
    else:
        sec9.append(['(weather_diag not provided)', '', ''])
    sections['section_9_weather_alignment'] = sec9

    # ----- Section 10: External Cross-Checks -----
    sec10 = [['name', 'pipeline_value', 'reference_value', 'rel_diff', 'note']]
    # Total annual electricity (TWh)
    pipeline_total_twh = float(total_actual.sum()) / 1e6
    ref_total_twh = (external_refs or {}).get('total_annual_TWh', {}).get('value')
    ref_total_note = (external_refs or {}).get('total_annual_TWh', {}).get('note',
                     'EIA SEDS / EIA-923 cross-check; verify against primary source')
    if ref_total_twh is not None:
        rel = (pipeline_total_twh - ref_total_twh) / ref_total_twh if ref_total_twh else 0.0
        sec10.append([f'{state_iso2}_total_annual_TWh',
                      round(pipeline_total_twh, 2),
                      round(float(ref_total_twh), 2),
                      round(rel, 4), ref_total_note])
    else:
        sec10.append([f'{state_iso2}_total_annual_TWh',
                      round(pipeline_total_twh, 2), '',
                      '', ref_total_note])

    # Solar PV annual generation (TWh) vs Cambium implied
    solar_twh = float(solar_gen_arr.sum()) / 1e6
    sec10.append([f'{state_iso2}_solar_pv_annual_TWh',
                  round(solar_twh, 4),
                  round(solar_twh, 4), 0.0,
                  'Pipeline derived directly from Cambium hourly CFs * capacity; '
                  'reference = same Cambium math (sanity self-check)'])

    # Wind annual generation (TWh)
    wind_twh = float(wind_gen_arr.sum()) / 1e6
    sec10.append([f'{state_iso2}_wind_annual_TWh',
                  round(wind_twh, 4),
                  round(wind_twh, 4), 0.0,
                  'Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; '
                  'reference = same Cambium math'])

    # Cambium capacities (key VRE) for visibility
    for tech in ['solar-pv', 'solar-pv-dist', 'onshore-wind', 'offshore-wind']:
        cap = float(cambium_caps.get(tech, 0.0))
        sec10.append([f'cambium_capacity_{tech}_MW',
                      round(cap, 1),
                      '', '', 'staff-review against Cambium Scenario Viewer'])

    sections['section_10_external_crosschecks'] = sec10

    return sections
