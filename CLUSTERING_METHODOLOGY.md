# Representative-Day Clustering for SHELF + SYSHECF — Methodology Reference

**Purpose:** This document is a self-contained handoff to another session (e.g., one applying the same approach to international / global pipelines). Read it end-to-end before extending the methodology to a new geography.

**Status as of 2026-05-22:**
- Implemented in `state_pipeline/builders/clustering_repday.py` (Python, numpy + sklearn)
- Used by both the US national rebuild (`rebuild_us_national_v2.py`, `build_shelf_workbook.py`, `build_syshecf_workbook.py`) and the per-state pipeline (`state_pipeline/run.py`)
- Replaces an earlier slice-mean clustering that was broken for capacity-planning peak slices when uncapped

---

## TL;DR

We cluster the 365 days of an hourly time series into **6 representative timeslices** (Winter, Spring, Summer, Fall, Summer Peak, Winter Peak). For each timeslice we assemble a 24-hour profile that the EPS Vensim model multiplies by annual demand (SHELF) or installed capacity (SYSHECF) to produce hourly values.

The key methodological choice: **representative-day reconstruction on NET LOAD** with **FIXED rep profiles** and **no peak-day cap**. This produces semantically meaningful peak slices (typically 10–15 days each, capacity-driving extremes) that the optimizer self-terminates at — without the optimizer absorbing "the hot half of the year" into Summer Peak (which is what an uncapped slice-mean approach does).

---

## The problem we fixed

### Old: slice-mean clustering (`clustering.cluster_days`)

```
SHELF[slice, hour] = mean over (days in slice) of demand[day, hour]
```

When you let the optimizer minimize total reconstruction NRMSE *without a peak-day cap*, it grows the peak slices indefinitely — for US national Cambium 2024 it converged to **Summer Peak = 53 days, Winter Peak = 76 days**. Those slices are basically "the entire hot half" and "the entire cold half" of the year, not capacity-driving extreme conditions.

This is mathematically optimal (slice means fit better as you absorb similar-shape days into peak slices), but semantically wrong. The model's Summer Peak slice should represent the 10–15 days that drive capacity adequacy decisions, not the 53 hottest days.

The previous workaround was `max_peak_days=10` — a hard cap that limited peak slices to 10 days each. This produced sensible-looking outputs but was a band-aid on a wrong objective.

### New: representative-day clustering on net load (`clustering_repday.cluster_days_repday`)

```
For each slice, designate ONE representative day:
  - Non-peak slices: the day closest to the cluster's feature-space centroid
  - Peak slices: the initially-pinned day with the highest net peak in that season pool
SHELF[slice, hour] = rep_day[slice]'s hourly profile at hour
```

The rep day is **fixed** during the optimization. When the iterative reassignment moves a candidate day into a peak slice:
- The rep day's profile doesn't change (still the original extreme day)
- The candidate day is now reconstructed using the rep day's profile
- This only improves NRMSE if the candidate's actual shape matches the extreme rep day

So the optimizer **only adds days whose shape resembles the extreme**. It naturally terminates at 10–15 days per peak slice without any cap. For US national Cambium 2024: **Summer Peak = 11 days, Winter Peak = 10 days** uncapped.

### Why score on net load, not gross demand

Net load = gross demand − VRE generation (solar + wind). For the capacity adequacy question, what matters is the residual demand that must be met by dispatchable resources. The peaks of net load are what stress the system. Clustering on gross demand misidentifies "high gross load with lots of solar" days as peaks even when the net load is moderate.

---

## Algorithm — step by step

Given an 8,760-hour time series of:
- `total_demand` (gross hourly load, MWh)
- `solar_gen` (hourly solar generation, MWh)
- `wind_gen` (hourly wind generation, MWh)

1. **Compute net load:**
   `net = total_demand − solar_gen − wind_gen`

2. **Build daily features** (one row per DOY 1..365):
   - `net_mean`: average net load
   - `net_min`: minimum net load
   - `net_p95`: 95th percentile net load
   - `net_ramp_max`: max absolute hourly ramp in net load

3. **Pin top-N peak days by season:**
   - Identify summer pool (months in `summer_months`, default `(6,7,8)`)
   - Identify winter pool (months in `winter_months`, default `(11,12,1,2)`)
   - From summer pool, take the `peak_top_n` days with highest daily net peak — pinned as Summer Peak
   - Same for Winter Peak from winter pool
   - Default `peak_top_n=1` — start with just the single most extreme day per season

4. **K-means cluster the remaining (unpinned) days into 4 clusters:**
   - Features: the daily feature matrix from step 2, weighted by `feature_weight_mode` (default `netload_focus`: weights net_p95 × 6.0, net_min × 4.0, net_ramp_max × 4.0, net_mean × 2.5)
   - Standard-scaled before clustering
   - `n_init=10` random restarts; multi-seed search over `[0,1,2,3,4,5,10,20,99]`

5. **Map the 4 non-peak clusters to season labels** (Winter / Spring / Summer / Fall) by mean DOY of cluster members — lowest mean DOY gets "Winter", highest gets "Fall".

6. **Determine the fixed representative day per slice:**
   - **Non-peak slices** (Winter / Spring / Summer / Fall): rep day = day in that cluster closest to the cluster's feature-space centroid (in standard-scaled feature space). This day's full 24-hour net-load profile becomes the slice's "rep profile."
   - **Peak slices** (Summer Peak / Winter Peak): rep day = the initially-pinned extreme day (the highest-net-peak day in the season pool). Its 24-hour profile is the rep profile.
   - **These rep profiles do NOT change** during the iterative reassignment in step 7.

7. **Iteratively grow peak slices** (greedy hill-climb):
   - For each peak slice, sort the season pool's non-peak-assigned days by daily net peak descending
   - For each candidate day:
     - Tentatively move it from its current cluster to the peak slice
     - Recompute NRMSE: for each hour of the year, predicted_net = rep_profile[slice(day), hour]; NRMSE = sqrt(mean((actual_net − predicted_net)²)) / std(actual_net)
     - If NRMSE improves, accept the move (commit to peak slice); otherwise revert
   - Keep iterating until no candidate improves NRMSE (or `max_peak_days` cap is hit — we default to 365 = effectively uncapped)
   - The optimizer self-terminates because adding days that don't fit the extreme rep profile increases NRMSE

8. **Multi-seed search:** repeat steps 4–7 for each k-means random seed (9 seeds default); return the result with lowest final NRMSE.

9. **Return** a `ClusteringResult`:
   - `slice_assignment`: pd.Series mapping DOY (1..365) → slice name
   - `days_per_timeslice`: dict {slice_name → number_of_days}
   - `sp_top_days`, `wp_top_days`: lists of DOYs in each peak slice
   - `nrmse`: final reconstruction NRMSE-std
   - `best_seed`, `score_by_seed`: diagnostic info

---

## What the NRMSE actually measures (important caveat)

The `nrmse` in the returned `ClusteringResult` is the **clustering optimization objective** — RMSE/std of the rep-day-based reconstruction of the 8,760-hour NET LOAD series. It is NOT a measure of how well the SHELF or SYSHECF outputs reproduce the original data.

- Typical values: 0.30–0.60 for US national; 0.45–0.90 for individual states
- **Lower is not always better.** A perfect rep-day reconstruction would require many slices; we constrain to 6.
- For validation, separately measure:
  - Annual energy reconstruction per category (target: 1.000 exactly via SHELF balance)
  - Peak hour preservation (target: ratio 0.95–1.05 of reconstructed peak / actual top-N-day average)
  - Load duration curve fit at top 1% / top 5% / overall
- See `compute_validation_metrics` in `state_pipeline/builders/clustering.py` for the legacy validation suite

The clustering's NRMSE objective is a means to an end (sensible peak slice selection), not the success metric.

---

## Function signature

```python
from state_pipeline.builders.clustering_repday import cluster_days_repday

cr = cluster_days_repday(
    total_demand: pd.Series,         # 8760 hourly values, DatetimeIndex
    solar_gen:    pd.Series,         # 8760 hourly values, same index
    wind_gen:     pd.Series,         # 8760 hourly values, same index
    *,
    peak_top_n:           int = 1,       # initial pinned days per peak slice
    max_peak_days:        int = 365,     # effective no-cap
    feature_weight_mode:  str = 'netload_focus',  # or 'uniform', 'netload_ramp_focus'
    search_seeds:         Iterable[int] | None = None,  # default [0,1,2,3,4,5,10,20,99]
    n_init:               int = 10,
    summer_months:        Iterable[int] = (6, 7, 8),
    winter_months:        Iterable[int] = (11, 12, 1, 2),
) -> ClusteringResult
```

The `ClusteringResult` dataclass is defined in `state_pipeline/builders/clustering.py` (shared between the two clustering implementations):

```python
@dataclass
class ClusteringResult:
    slice_assignment: pd.Series           # index=DOY (int), value=slice name
    days_per_timeslice: dict[str, int]    # {'Winter': 61, 'Spring': 121, ...}
    sp_top_days: list                     # DOY ints in 'Summer Peak'
    wp_top_days: list                     # DOY ints in 'Winter Peak'
    daily_peak: pd.Series                 # peak demand per DOY
    net_load: pd.Series                   # 8760 hourly net load
    nrmse: float                          # final RMSE/std of rep-day reconstruction
    best_seed: int                        # k-means seed that won
    score_by_seed: dict[int, float]       # diagnostic
```

---

## Inputs the clustering expects

- **Hourly time series at 8,760-hour resolution** (no leap day; if your source has 8,784 you must trim).
- **DatetimeIndex** on the pd.Series (used to derive day-of-year, month, hour-of-day).
- **All three series on the same index.** If your VRE data is on a different calendar than your demand, you must reindex to a common reference first.
- **Units don't matter** for clustering — the algorithm is scale-invariant within each series (features are standard-scaled). But total_demand, solar_gen, and wind_gen must be in the **same units** so net = demand − solar − wind makes physical sense (typically all in MWh).

For the US national case we use:
- `total_demand` = Cambium 2024 MidCase `busbar_load` column (gross MWh/hour at the busbar — includes T&D losses + own use)
- `solar_gen` = `upv_MWh` + `distpv_MWh`
- `wind_gen` = `wind-ons_MWh` + `wind-ofs_MWh`

For a different country we'd need equivalent national hourly load + VRE generation:
- **Demand:** national TSO/ISO published hourly demand, or ENTSO-E for EU, or local equivalents
- **VRE:** if no published per-tech hourly generation, can use renewables.ninja (`https://renewables.ninja/`) to generate synthetic hourly CFs from MERRA-2 weather × installed-capacity weighting, then multiply by national capacity totals from IRENA or local statistics

---

## How outputs flow into SHELF + SYSHECF

The `ClusteringResult.slice_assignment` (DOY → slice) is the bridge to all downstream usage. For each hour of the year:
- Look up its DOY
- Look up its slice from `slice_assignment[DOY]`
- Aggregate per (slice, hour_of_day):

```
SHELF[category, slice, hour] = AVERAGE over (days in slice, this hour) of demand[category]
                             / SUM over all 8,760 hours of demand[category]

SYSHECF[tech, slice, hour] = AVERAGE over (days in slice, this hour) of CF[tech]
                           [optionally × EIA target / Cambium annual mean for VRE]
```

Note: SHELF and SYSHECF aggregate via **slice-mean over the assigned days**, NOT the rep-day profile. The rep-day approach is used only inside the clustering optimization to drive sensible peak-slice membership. Once we have the day assignments, the downstream aggregation is slice-mean, which provides smoother / more energy-faithful 24-hour profiles within each slice.

This is the key insight: **rep-day for clustering decisions, slice-mean for output values.**

---

## What changed (chronological)

1. **Pre-2026-05-15 — Legacy slice-mean clustering with `max_peak_days=10` cap.**
   The `clustering.cluster_days` function used slice-mean reconstruction on gross demand. To prevent peak slices from absorbing the entire hot/cold half of the year, a hard cap of 10 days per peak slice was applied. This produced acceptable outputs but was a band-aid on the wrong objective.

2. **2026-05-15 — User asked to lift the cap.** When we ran uncapped (`max_peak_days=365`), Summer Peak grew to 53 days, Winter Peak to 76 days. The user correctly identified this as broken.

3. **2026-05-15 — Diagnosed the issue:** with slice-mean reconstruction, adding similar-shape days to a peak slice improves the mean fit because it's a different objective than capacity-meaningful peak selection. The optimizer is doing what we asked, but we asked the wrong question.

4. **2026-05-15 — Switched to representative-day reconstruction on net load.** Implemented in `state_pipeline/builders/clustering_repday.py`:
   - Rep profile is FIXED per slice (extreme day for peak, centroid-closest day for non-peak)
   - Score on NET LOAD (not gross demand) — net peak is what matters for capacity
   - Use VLOOKUP-friendly slice assignment (compatibility with downstream Excel workbooks)
   - No `max_peak_days` cap needed; optimizer self-terminates

5. **2026-05-15 — Migrated state pipeline** (`state_pipeline/run.py`) to use `cluster_days_repday` (was using `cluster_days`). State presets updated: `peak_top_n_days: 1`, `max_peak_days: 365`.

6. **2026-05-22 — Built self-contained derivation workbooks** (SHELF and SYSHECF) for the US national case. The clustering result is now exposed in the workbook's "Clustering" tab as an editable DOY→slice mapping that downstream tabs reference via VLOOKUP. Users can hand-edit slice assignments in Excel and the output tabs recompute.

---

## Empirical results for US national (2025, Cambium 2024 MidCase)

After running `cluster_days_repday(peak_top_n=1, max_peak_days=365)`:

| Slice | Days | NRMSE contribution |
|---|---|---|
| Winter | 61 | — |
| Spring | 121 | — |
| Summer | 112 | — |
| Fall | 50 | — |
| **Summer Peak** | **11** | Includes Jul 7, 10, 19, 20, 27 / Aug 1, 2, 3, 8, 9, 10 |
| **Winter Peak** | **10** | Includes Jan 4, 13 / Feb 8 / Dec 12, 25, 27, 28, 29, 30, 31 |
| Total | 365 | NRMSE-std = 0.425 |

For comparison, applying the **slice-mean** clustering with `max_peak_days=365` (broken) produces: Winter 51 / Spring 115 / Summer 41 / Fall 29 / **Summer Peak 53** / **Winter Peak 76**.

For per-state results (rep-day, uncapped), see `scripts/data_outputs/all_states_run_log.csv` — Summer Peak day counts range from 3 (Vermont) to 46 (Arkansas) depending on climate consistency.

---

## Validation pattern (always do this)

After running the clustering, sanity-check by computing:

1. **Days per slice add up to 365.** If not, bug.
2. **Peak slices have at least one day.** If `len(sp_top_days) == 0`, the clustering broke; investigate.
3. **Peak slices contain the actual annual peak hour day.** If not, suspect a feature-weighting bug.
4. **Summer Peak days are mostly in summer months.** A Summer Peak with January days suggests the season pools are mis-defined for the target geography (e.g., wrong hemisphere).
5. **Build the SHELF and verify balance.** For each non-zero category: `sum_slices(sum_hours(LF) × days[slice]) = 1.000` (within 1e-9). If not, the slice assignment has duplicates or gaps.

---

## Global / non-US application status (as of 2026-05-22)

The legacy international pipeline at `energy_timeslice_pipeline.py` has 12 country presets: **United States, Canada, Mexico, Brazil, United Kingdom, France, Germany, China, South Korea, Japan, India, Australia**. As of 2026-05-22 it has been **consolidated to use the same clustering implementation** as the US national + per-state pipelines:

- `energy_timeslice_pipeline.cluster_timeslices` is now a thin wrapper that internally calls `state_pipeline.builders.clustering_repday.cluster_days_repday`.
- The legacy return signature `(hourly_labels, KMeans, mapping, representative_dates)` is preserved for backward compatibility with downstream code in that file.
- The previous pandas-heavy implementation (~50× slower) is kept as `_cluster_timeslices_legacy_impl` and used only as a fallback when `state_pipeline` is not importable.

**Hemisphere awareness.** Brazil, Argentina, Chile, New Zealand, South Africa, Australia, Peru, Uruguay, Paraguay, and Bolivia are recognized as Southern Hemisphere — for these countries `summer_months = [12, 1, 2]` and `winter_months = [6, 7, 8]` by default. The helper `_hemisphere_season_months(country)` in `energy_timeslice_pipeline.py` returns the correct defaults; pass `country=` to `cluster_timeslices` or `run_pipeline` to activate. Northern Hemisphere countries continue to use `summer = [6, 7, 8]` / `winter = [11, 12, 1, 2]` defaults. If a user supplies explicit `summer_months` / `winter_months` they always override the country-derived defaults.

Verified by smoke test (2026-05-22):
- US synthetic net-load series → Summer Peak rep date in July ✓
- Brazil synthetic net-load series (same data, different `country=` arg) → Summer Peak rep date in December ✓

This means all 12 country presets in the project share the same canonical clustering algorithm and methodology. Re-running any non-US preset (e.g., `python energy_timeslice_pipeline.py` with the China preset selected) will use `cluster_days_repday` under the hood.

**What still needs work for non-US:**
- The legacy pipeline's downstream SHELF/SYSHECF build is single-script (not the rich self-contained-workbook pattern we used for the US national). Future work could port `scripts/build_shelf_workbook.py` and `scripts/build_syshecf_workbook.py` patterns to a country-parameterized form.
- Country-specific data sources (Mendeley end-use, DemandCast demand, Ember capacity factors, Renewables.ninja weather) are still configured per the legacy `generate_full_pipeline_for_country` interface — that machinery is unchanged.

---

## Per-region data sources and how the methodology differs

**The clustering step is identical across every region.** All geographies run through the same
`cluster_days_repday` (rep-day reconstruction on net load, fixed rep profiles, NRMSE-std scoring,
no peak-day cap, hemisphere-aware season months). What differs by region is everything **upstream**
of clustering — how the hourly demand shape is built, how it is calibrated to observed totals, and
which hemisphere's season-month defaults apply. The table below is the canonical reference for those
inputs. *(Verify every source against its primary publisher before using derived outputs in any work
product.)*

| Region / preset | Demand-shape source | Observed-demand calibration source | Default calibration method | VRE (weather) source | Annual CF target | Hemisphere |
|---|---|---|---|---|---|---|
| **United States** (international preset, `demand_shape_source='efs'`) | NREL Electrification Futures Study (Reference × Moderate); RECS `CE8.2.M`/`CE8.3.M` heating/cooling split | EIA Hourly Electric Grid Monitor (v2 API) | `level_seasonal` (US uses EFS shapes; Zapata methods available if `eps_prior_path` set) | Renewables.ninja MERRA-2 | Ember | Northern |
| **South Korea** | Mendeley/Zapata, region `Korea` | DemandCast → KROGD manual files (`KRO*` in `data/manual_downloads/`) | `zapata_ridge_nnls` | Renewables.ninja MERRA-2 | Ember | Northern |
| **China** | Mendeley/Zapata, region `China +` | DemandCast → Wu et al. 2023 Zenodo (**2018 only**) | `zapata_ridge_nnls` | Renewables.ninja MERRA-2 | Ember | Northern |
| **Canada, Japan, India, Germany, France, United Kingdom, Mexico** | Mendeley/Zapata | DemandCast (programmatic: ENTSO-E for EU, CENACE for MX, etc.) | `zapata_ridge_nnls` (needs `eps_prior_path`) else `level_seasonal` | Renewables.ninja MERRA-2 | Ember | Northern |
| **Australia, Brazil** | Mendeley/Zapata | DemandCast | `zapata_ridge_nnls` / `level_seasonal` | Renewables.ninja MERRA-2 | Ember | **Southern** |

### Two distinct US lineages — do not conflate

There are **two** US treatments in this repository, with different data sources and different intended
consumers:

1. **Canonical US EPS pipeline** — `state_pipeline/` + `rebuild_us_national_v2.py`. Buildings from
   **ResStock/ComStock**, industry/transport from **EFS**, net load + VRE from **Cambium**, SYSHECF
   CFs calibrated to **EIA Table 4.8.B (national)** or **EIA State Electricity Profiles (per-state)**.
   This is the lineage that produces the US EPS model's SHELF/SYSHECF files. See `CLAUDE.md` §1.
2. **International-pipeline US preset** — `energy_timeslice_pipeline.py` with the `united states`
   preset (`demand_shape_source='efs'`). Uses **EFS** demand shapes + **EIA hourly** calibration +
   **RECS** heating/cooling split. It exists for cross-country methodological consistency, not as the
   source of record for the US EPS files.

Both now share the same clustering engine, but their **inputs and outputs are different**. Use lineage
1 for US EPS deliverables.

### Non-US calibration methods (`CALIBRATION_METHOD`)

The non-US demand-shape calibration (and its data sources) operates exactly as it did on the prior
`develop` branch — only the downstream **use of the calibrated net load in clustering** changed (now
the consolidated, hemisphere-aware `cluster_days_repday`). The three methods, selectable per run in
`run_pipeline.py`:

- **`zapata_ridge_nnls`** *(default for non-US)* — regenerate the four climate-sensitive end-uses
  (residential cooling/heating/lighting + service cooling) from country weather + HETUS occupancy +
  Forsythe daylength (Zapata et al. 2022 stylized functions), align all 11 basis columns to
  EPS-extracted per-end-use MWh/year priors, then solve a ridge-regularized NNLS anchored to the EPS
  prior (`LAMBDA_RIDGE`, default 1.0). Eliminates the basis-collinearity zero-flips that plain NNLS
  produces, and is self-consistent with how EPS consumes SHELF (EPS supplies magnitudes, the SHELF
  supplies shape). **Requires** the preset's `eps_prior_path` (CSVs in `data/eps_priors/`, built by
  `parse_eps_extract.py`).
- **`zapata_nnls`** — same shape regeneration, plain monthly NNLS, no EPS-prior anchoring. Can drive
  some end-uses to zero in a timeslice (NaN/0 SHELF cells). Retained for diagnosis/comparison.
- **`level_seasonal`** — legacy multiplicative annual scaling + per-month/per-peak adjustment; the
  synthetic shape is unchanged. Annual mean matches by construction. This is the U.S. default.

### What is the same vs. different — summary

| Stage | Same across regions? | Notes |
|---|---|---|
| Day clustering (rep-day on net load, fixed profiles, no cap) | **Same** | `cluster_days_repday` |
| Season-month defaults | Hemisphere-dependent | `_hemisphere_season_months(country)`; SH = Australia, Brazil (+ Argentina, Chile, etc. when added) |
| Demand-shape construction | **Differs** | EFS (US) vs Zapata/Mendeley (non-US) |
| Calibration to observed totals | **Differs** | EIA hourly (US) vs DemandCast (non-US); `level_seasonal` vs `zapata_*` |
| VRE / weather | Same source family | Renewables.ninja MERRA-2 → CF, calibrated to Ember annual |
| SHELF/SYSHECF export format | **Same** | 6 slices × 24 hours; EPS-ready CSV + workbooks |

See `DECISIONS.md` (2026-06-03 entry) and `INTERNATIONAL_INTEGRATION_PLAN.md` for the integration
decision that brought the non-US calibration layer onto this trunk while keeping the consolidated
clustering.

---

## Adapting to a new geography (global pipeline)

For applying this methodology to a different country / region:

### 1. Geographic / climate adjustments

- **Hemisphere:** Southern Hemisphere needs `summer_months=(12,1,2)` and `winter_months=(6,7,8)` flipped. Tropical countries may have minimal seasonality and the season-naming heuristic (mean DOY → Winter/Spring/Summer/Fall) becomes meaningless — consider using descriptive labels like "Wet Peak" / "Dry Peak" instead.
- **Single dominant peak season** (e.g., tropics with year-round AC peaks): the algorithm still works but Winter Peak might be empty or trivial. Consider running with just one peak slice and 5 total timeslices, or document the asymmetry.
- **Bimodal load shape** (some places have summer cooling + winter heating both significant): the rep-day approach handles this correctly because each peak slice has its own rep day.

### 2. Source data

You need three 8,760-hour series with consistent units:
- **Hourly demand:** TSO/ISO published, or national grid operator. ENTSO-E for EU; CAISO / ERCOT / etc. for US ISOs; national equivalents elsewhere.
- **Hourly solar generation:** if not published, derive from solar PV CF × installed capacity. `renewables.ninja` API for synthetic CFs from MERRA-2 weather.
- **Hourly wind generation:** same idea — synthetic from MERRA-2 + installed capacity if no published data.

If solar and wind are both negligible in a country (low VRE penetration), you can pass zero series — the clustering then runs on gross demand (which is fine when VRE doesn't change the peak shape).

### 3. Calendar alignment

If your demand series uses a different weather year than your VRE series, you must reindex both to a common reference. We use a common 2018 calendar (`pd.date_range('2018-01-01', periods=8760, freq='h')`) because ResStock TMY3 is on 2018.

### 4. Feature weights

`feature_weight_mode='netload_focus'` works well for grids where net peak drives capacity. Alternatives in `state_pipeline/builders/clustering.py::FEATURE_WEIGHTS`:
- `'uniform'`: equal weighting (no opinion about what defines peak)
- `'netload_ramp_focus'`: emphasizes ramp_max — useful for grids where ramping (e.g., evening solar drop-off) is the constraint
- Custom: pass `search_seeds` and a custom weights dict (would require code change)

### 5. Number of timeslices

Currently hardcoded to 6 (4 seasonal + 2 peak). If the target model uses a different number:
- 4 timeslices (no peaks): set `peak_top_n=0` and reduce K-means to 4. Not currently supported by `cluster_days_repday`; would need a code branch.
- More peaks (e.g., Summer Peak + Shoulder Peak): would need to add slice names + pinning logic.

---

## Files to copy / port

If you're moving this to another project or session, you need:
- `state_pipeline/builders/clustering.py` — defines `ClusteringResult`, `SLICE_NAMES`, feature weights, helpers (`_build_daily_features`, `_name_clusters_by_doy`)
- `state_pipeline/builders/clustering_repday.py` — the rep-day implementation (`cluster_days_repday`)

These two files together are ~400 lines of pure Python (numpy + sklearn + pandas, no project-specific imports). Standalone-portable.

Dependencies: `numpy`, `pandas`, `scikit-learn` (`sklearn.cluster.KMeans`, `sklearn.preprocessing.StandardScaler`).

---

## Common pitfalls

1. **Don't use `cluster_days` (slice-mean) with `max_peak_days=365`.** It will produce 50–80 day peak slices. Either use `cluster_days_repday` (preferred) or keep `cluster_days` with `max_peak_days=10` cap (band-aid).

2. **Don't conflate the clustering NRMSE with output quality.** The NRMSE measures rep-day reconstruction error during optimization. Final SHELF/SYSHECF quality is measured separately via balance check + peak preservation + LDC fit.

3. **Don't run clustering on gross demand if there's substantial VRE.** Solar in particular can invert the peak shape — gross peaks at 3 PM, net peaks at 7 PM. The capacity-meaningful peak is net.

4. **Don't forget to validate that peak slice days are in the right season.** A bug in feature weighting or season pool definition can cause Summer Peak to grab a January day. If you see that, something's wrong.

5. **Don't add peak slices unboundedly even when uncapped.** If `len(sp_top_days) > 30`, suspect:
   - Wrong rep-day selection (maybe centroid instead of extreme)
   - Score-on-gross instead of score-on-net
   - Feature weights too uniform (not focused on peakiness)
   - The geography genuinely has many similar extreme days (rare; investigate)

6. **Don't apply EIA-style annual CF calibration to SHELF.** SHELF is purely a shape table (LFs sum × days = 1 per category). The annual energy comes from the model's own BCEU/AEO inputs. Calibration applies only to SYSHECF VRE techs where we want hourly shape × annual EIA observed CF.

---

## References

- Project repo (US-focused, includes per-state pipeline): `Global Electricity File Creator` (Energy Innovation internal)
- Canonical methodology doc: `CLAUDE.md` at project root
- Decision history: `DECISIONS.md` at project root
- Skill for building self-contained input workbooks: `~/.claude/skills/build-input-xlsx/SKILL.md`
- Literature: Poncelet et al. 2017 (representative-day selection for capacity-expansion models); Mallapragada et al. 2020; NREL ReEDS clustering validation methodology

---

*Maintained by Energy Innovation modeling team. All clustering choices documented here should be reviewed by EI staff and verified against the project's CLAUDE.md and the literature references above before being used in any work product.*
