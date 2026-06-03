# Clustering logic — master vs. develop branch comparison

*Generated 2026-06-02. For staff review. Verify claims against actual files in both branches before acting on the plan.*

**One framing note up front:** master already completed this consolidation in May 2026 (per [CLAUDE.md](CLAUDE.md) §10) — the wrapper that develop needs already exists on master, so this is more "merge master's clustering refactor into develop" than "design a port from scratch." That makes the work substantially easier than it might appear.

---

## Where each branch lives today

| | Master | Develop |
|---|---|---|
| **Canonical entrypoint** | `cluster_days_repday(total_demand, solar_gen, wind_gen, *, …)` in `state_pipeline/builders/clustering_repday.py` | `cluster_timeslices(net_load, timestamps=None, …)` inline in `energy_timeslice_pipeline.py:~5597` |
| **Compat wrapper for non-US callers** | `cluster_timeslices(...)` in `energy_timeslice_pipeline.py:3487-3578` delegates to `cluster_days_repday` and repacks output into the legacy 4-tuple | (no wrapper; the inline impl IS the function) |
| **Hemisphere handling** | `SOUTHERN_HEMISPHERE_COUNTRIES` set + `_hemisphere_season_months(country)` at `energy_timeslice_pipeline.py:3469-3484` | NH months hardcoded; `latitude_deg` exists in presets (AU=-33, BR=-15) but is **never consulted** — Brazil/Australia silently get boreal-winter peaks |
| **Methodology docs** | `CLAUDE.md`, `CLUSTERING_METHODOLOGY.md`, `DECISIONS.md` | `README.md`, `HANDOFF.md` |
| **File size of `energy_timeslice_pipeline.py`** | 4,995 lines | 6,911 lines (most divergence is Mendeley/DemandCast/Ember/calibration — orthogonal to clustering) |
| **Legacy fallback** | `_cluster_timeslices_legacy_impl` at `energy_timeslice_pipeline.py:3635-3839` — runs when `state_pipeline` import fails. Roughly equivalent to develop's current impl. | n/a |

---

## Differences in the clustering algorithm itself

| Aspect | Master (`cluster_days_repday`) | Develop (`cluster_timeslices`) | Material? |
|---|---|---|---|
| **Algorithm class** | Rep-day reconstruction on net load; k-means on non-peak days; greedy peak-day growth | Same | Same intent |
| **Feature space** | `net_mean, net_min, net_p95, net_ramp_max` per day | Same | Identical |
| **Feature weights (`netload_focus`)** | mean×2.5, min×4.0, p95×6.0, ramp×4.0 | Identical | Same |
| **Pinned peaks** | `peak_top_n=1`, top day per season by net peak | Same default | Same |
| **Peak-growth termination** | Greedy hill-climb on NRMSE-std, no cap (`max_peak_days=365`) | Same | Same |
| **Multi-seed search** | `[0,1,2,3,4,5,10,20,99]`, `n_init=10` | Same | Same |
| **Rep-profile during growth** | Computed once at init, **never recomputed** during greedy moves (lines 60-61, 205-225) | Recomputes via `_select_representative_dates` after every candidate move (lines 5777, 5784) — wasted work since pinned reps are preserved by `pinned_label_map` | Master ~50× faster per its legacy_impl docstring; results effectively identical |
| **Integer label semantics** | Wrapper hard-codes DOY order: 0=Winter, 1=Spring, 2=Summer, 3=Fall, 4=Summer Peak, 5=Winter Peak | Sorted by `net_p95` centroid ascending: 0=lowest p95 … n-3=highest; pinned slices get 4/5 | **Yes — breaks `assign_seasonal_labels`** if not handled |
| **Input contract** | Caller passes gross demand + VRE separately; net computed inside | Caller passes pre-computed net load | Solvable via wrapper |
| **Return shape** | `ClusteringResult` dataclass (`slice_assignment` by DOY, `days_per_timeslice`, `sp_top_days`, `wp_top_days`, `nrmse`, `best_seed`, …) | `(hourly_Series, KMeans, mapping_dict, representative_dates_dict)` | Wrapper exists on master to bridge these |
| **`KMeans` model in return tuple** | Master's wrapper returns a placeholder (dummy fit) | Develop returns the real model | Low risk if no downstream caller uses `cluster_centers_` / `inertia_` — must grep |
| **Edge-case guard for empty seasonal pools** | Implicit (assumes `summer_pool`/`winter_pool` non-empty) | Explicit `if not summer_candidates: …` (lines 5749, 5751) | Minor; matters only for extreme latitudes or partial-year data |

---

## Differences in the data feeding clustering

Both pipelines call clustering on a net-load series — but how that series is built is fundamentally different.

| | Master | Develop |
|---|---|---|
| **Demand series** | Cambium 2024 MidCase `busbar_load` (single fixed deterministic dataset) | Mendeley synthetic end-use shapes (per-country, per-SSP) calibrated to DemandCast observed annual via NNLS / level-seasonal |
| **VRE series** | Cambium per-tech: `upv + distpv` (solar), `wind-ons + wind-ofs` (wind) — single-model | Renewables.ninja weather → physical PV/wind CFs → calibrated to Ember annual CF targets → multiplied by Ember installed-capacity (GW) |
| **Net-load construction** | `busbar_load – (solar + wind)` (single aggregate) | `(residential + service + industry + transport) – (solar + wind)` (sector totals) |
| **Calendar alignment** | Cambium 2025 data forcibly re-indexed to 2018 calendar (non-leap, Monday start) for consistency with ResStock TMY3 | Preset default year or user-specified year; uses that year's actual calendar |
| **Timezone handling** | ResStock/ComStock LST → ET via `np.roll`; Cambium is ET | Renewables.ninja UTC → `tz_convert(country_timezone)` if set, else left in UTC with a warning |
| **Production maturity** | Fixed, versioned inputs | Upstream-dependent (DemandCast cloned per run; Renewables.ninja/Ember cached); higher drift risk |

For clustering, **none of these data-source differences matter to the algorithm itself** — `cluster_days_repday` just wants three pandas Series with matching DatetimeIndex. The differences only matter for what numbers come *out* (which peak days, what nrmse).

---

## Implementation plan: bring master's clustering into develop

Complexity: **low** — a few hours of careful work, because master's wrapper layer was designed precisely to be backward-compatible with the legacy `cluster_timeslices` 4-tuple shape that develop's downstream code already consumes.

**Recommended path: copy + vendor (don't try to share code across branches).** Develop is a single-file pipeline; staying that way is simpler than introducing a `state_pipeline/` package on develop just to host one function.

### Step 1 — Audit develop's downstream consumers (30 min)

Before any code moves, run on develop:

- `grep -n "cluster_timeslices(" energy_timeslice_pipeline.py run_pipeline.py` — confirm only the two known call sites (line ~6822 in `run_pipeline`, line ~2709 in `compare_pinned_unpinned_clustering`).
- `grep -nE "\.(cluster_centers_|inertia_|labels_|predict)" energy_timeslice_pipeline.py` — confirm nothing downstream actually uses the `KMeans` model object (master's wrapper returns a placeholder; will break anything that introspects the model).
- Read `assign_seasonal_labels` (develop ~line 5953) to confirm the assumption "low timeslice indices ↔ low net load" and figure out how to rewrite it once labels become DOY-ordered.

### Step 2 — Vendor the algorithm into develop's `energy_timeslice_pipeline.py` (1–2 hours)

Port these three things from master into a new section of develop's `energy_timeslice_pipeline.py` (or a sibling module `clustering_repday.py` if you'd prefer one extra file):

1. The helpers from `state_pipeline/builders/clustering.py`: `ClusteringResult` dataclass, `SLICE_NAMES`, `FEATURE_WEIGHTS`, `_build_daily_features`, `_name_clusters_by_doy`.
2. The body of `cluster_days_repday` from `state_pipeline/builders/clustering_repday.py`.
3. The wrapper machinery from master's `energy_timeslice_pipeline.py:3465-3632`: `SOUTHERN_HEMISPHERE_COUNTRIES`, `_hemisphere_season_months`, the new `cluster_timeslices` that delegates, and `_cluster_timeslices_via_repday`.

**Keep develop's existing `cluster_timeslices` as `_cluster_timeslices_legacy_impl`** (rename it). That mirrors master's graceful-degradation pattern and gives you a one-line revert if anything goes sideways.

### Step 3 — Reconcile the integer-label semantics (30 min)

This is the only real correctness pitfall. Master's wrapper assigns labels by DOY order (Winter=0 … Winter Peak=5); develop's `assign_seasonal_labels` assumes labels are p95-rank ordered. Pick one:

- **Option A (preferred): rewrite `assign_seasonal_labels`** to look up slice names from the wrapper's metadata instead of inferring from label rank. The wrapper can expose a `slice_name_by_int` dict on the side.
- **Option B**: have the wrapper preserve develop's p95-rank ordering. Means editing master's wrapper to skip `_name_clusters_by_doy` for the develop branch — slightly muddies master's behavior but minimizes churn elsewhere in develop.

Recommend Option A — it's a localized cleanup and matches master's mental model.

### Step 4 — Wire the `country` argument through `run_pipeline` (15 min)

Develop's call at `energy_timeslice_pipeline.py:~6822` doesn't pass `country`, `winter_months`, or `summer_months`. After the port, pass `country=preset['country']` (or whatever the preset key is) so `_hemisphere_season_months` can flip Brazil/Australia to austral seasons. This is the "free win" — fixes a silent SH bug that already exists on develop.

### Step 5 — Update or add `SOUTHERN_HEMISPHERE_COUNTRIES` (5 min)

Master has 10 countries: Argentina, Australia, Bolivia, Brazil, Chile, New Zealand, Paraguay, Peru, South Africa, Uruguay. Cross-check against develop's `COUNTRY_PRESETS` (presets at `develop:energy_timeslice_pipeline.py:294-484`) and add any SH presets master doesn't have.

### Step 6 — Verify (1 hour)

Smoke test, per the existing TODO at `CLAUDE.md` §10:

1. Pick **Brazil** (smallest non-US data footprint per the master TODO).
2. Run `generate_full_pipeline_for_preset('Brazil', ...)` end-to-end.
3. Check (a) no exceptions, (b) Summer Peak DOYs fall in Dec–Feb (austral summer), (c) `days_per_timeslice` sums to 365, (d) NRMSE comparable to develop's old result (use `compare_pinned_unpinned_clustering` as the diagnostic — it already exists on develop at line ~2709).
4. Diff one SHELF and one SYSHECF csv vs the develop-only run. Numerical differences should be small (label permutation + the ~50× speedup from not recomputing reps); structural differences should be only in the slice ordering.

### Step 7 — Documentation (15 min)

- Bring master's `CLUSTERING_METHODOLOGY.md` over to develop (it's the canonical methodology reference).
- Add a short section to develop's `README.md` pointing at the new clustering entrypoint and the SH fix.
- Strongly consider porting `CLAUDE.md` too — develop has been evolving without that document and a future merge will be smoother if both branches share it.

---

## Strategic question worth raising before executing

The task as posed assumes a one-direction port (master → develop). But the two branches have diverged ~2,500 lines in `energy_timeslice_pipeline.py`, and most of that divergence is **on develop** (Mendeley/DemandCast/Ember/calibration work that master doesn't have). Doing the clustering port without a broader merge plan means develop's clustering matches master, but everything else still diverges further every week.

Before executing the port, it's worth deciding with the team: is the intent to (a) eventually merge develop into master (so master gets non-US capability), (b) keep develop as the non-US fork indefinitely, or (c) settle on one trunk? The clustering port is straightforward either way, but the answer changes whether you should also start consolidating the rest.

---

## Verified findings supporting the above

(From the parallel-branch inspection workflow run 2026-06-02. Each finding has a file-line citation in the workflow output.)

- Master's `cluster_days_repday` signature: `(total_demand, solar_gen, wind_gen, *, peak_top_n=1, max_peak_days=365, feature_weight_mode='netload_focus', search_seeds=None, n_init=10, summer_months=(6,7,8), winter_months=(11,12,1,2))`. Net load is computed internally at `state_pipeline/builders/clustering_repday.py:123-124`.
- Master ALREADY consolidated clustering. `energy_timeslice_pipeline.cluster_timeslices` (master) is a backward-compat wrapper that delegates to `cluster_days_repday` via `_cluster_timeslices_via_repday` and repacks results into the legacy `(Series, KMeans, mapping, representative_dates)` tuple. Documented in CLAUDE.md §10 (Completed, 2026-05-22).
- Develop's `cluster_timeslices` is an in-place implementation — not a wrapper. It does NOT delegate. The `state_pipeline` package does not exist on develop (`git ls-tree develop state_pipeline` returns empty).
- Develop has zero hemisphere reversal logic. `winter_months`/`summer_months` default to NH; SH presets exist (`Australia: latitude_deg=-33`, `Brazil: latitude_deg=-15`) but `latitude_deg` is never consulted by `cluster_timeslices`. Develop's `run_pipeline` call at line 6822 does not pass `country`, `winter_months`, `summer_months`, or `pin_extremes`.
- Master's `cluster_days_repday` fixes the per-slice representative profile at initialization and never recomputes during greedy growth (lines 60-61 docstring; lines 205-225 implementation). Develop's `_improve_pinned_assignments` re-runs `_select_representative_dates` after every candidate move (line 5777 and 5784); pinned reps stay fixed via `pinned_label_map` but non-peak reps thrash needlessly.
- Feature weights are identical across branches.
- Multi-seed defaults are identical: `[0,1,2,3,4,5,10,20,99]`, `n_init=10`.
- Develop's file is 6,911 lines vs master's 4,995. Diff: 2,223 insertions / 307 deletions. Most divergence is develop-only preset data, weather processing, Mendeley/DemandCast/Ember calibration logic — **NOT in clustering**.
- `CLAUDE.md`, `CLUSTERING_METHODOLOGY.md`, `DECISIONS.md` exist on master but NOT on develop.

---

*Maintained by: Energy Innovation modeling team. All derived claims are for staff review and should be verified against primary sources (the actual files on both branches) before any port is executed.*
