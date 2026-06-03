# Calibration Decisions Ledger

Running log of model-calibration decisions for the SHELF + SYSHECF pipeline.
Most-recent first. Each entry includes context, decision, and rationale —
designed to survive context summarization across Claude sessions.

See `CLAUDE.md` for the canonical methodology that these decisions inform.

---

## 2026-06-03 — Plan: integrate develop's non-US calibration layer onto master (control surface + calibration defaults)

> **Status: IMPLEMENTED ON FEATURE BRANCH `feature/international-onto-master` — for staff review; NOT
> yet merged to `master`.** The develop→master merge plus integration fixups are committed on the
> feature branch (one merge commit). Verified on synthetic data and structurally (see Verification
> below); full end-to-end country runs with real external data and the US EPS regression remain to be
> run in an environment with those inputs + network access. See `INTERNATIONAL_INTEGRATION_PLAN.md`
> for the full plan and the verified Phase 0 findings.

### Context
The branches diverged at `d4ef526`. `master` carries the clustering consolidation (the hemisphere-aware
`cluster_timeslices` wrapper → `cluster_days_repday`), the `state_pipeline/` package, and the
methodology docs. `develop` carries a self-contained international calibration layer that `master`
lacks: physically-based Zapata end-use shape regeneration, monthly NNLS / ridge-NNLS calibration to
EPS per-end-use priors, weather caching, DemandCast manual-source mirroring, calibration/cluster
diagnostic plots, and the `run_pipeline.py` user-facing control script. The goal is to bring develop's
non-US capability onto `master` without losing master's clustering or US/state pipeline.

A Phase 0 audit (2026-06-03) found that a `git merge origin/develop` produces a **textually clean tree
with no conflicts and no "hybrid" function bodies**: `cluster_timeslices` resolves to master's wrapper
(intended), `generate_full_pipeline_for_preset`/`for_country` resolve to develop's (the international
orchestrator), and develop's new helper functions + `run_pipeline.py` + `data/eps_priors/` are imported
additively. The one verified functional gap is that develop's `run_pipeline()` does not forward
`country` into the clustering call, so the Southern-Hemisphere season flip would not engage without a
one-line fix.

### Decision (proposed)
1. Make `master` the single trunk carrying both lineages.
2. **`run_pipeline.py` is the user-facing control surface** for the international pipeline, intended to
   be usable by **any team member** who clones the repo. All execution code stays in
   `energy_timeslice_pipeline.py`; users edit only the documented CONFIG blocks. It selects the country
   and all key run settings.
3. **Diagnostic cluster-vs-actual plots are retained**, gated by the `MAKE_DIAGNOSTIC_PLOTS` boolean in
   `run_pipeline.py` (per-timeslice PNGs: all assigned days as grey lines + IQR band + cluster mean +
   representative day overlaid on net load).
4. **Non-US calibration default = `zapata_ridge_nnls`**, selectable per run via `CALIBRATION_METHOD`
   (`zapata_ridge_nnls` / `zapata_nnls` / `level_seasonal`), with `LAMBDA_RIDGE` for prior anchoring.
5. **Non-US calibration and its data sources operate identically to `develop`** (DemandCast observed
   demand, Mendeley/Zapata end-use shapes, Ember annual CFs, Renewables.ninja weather). Only their
   **downstream use in clustering changes** — the calibrated net load now flows through master's
   consolidated, hemisphere-aware `cluster_days_repday` instead of develop's inline implementation.
6. **Surface US-specific choices on `run_pipeline.py` with inline documentation** — EFS electrification
   × technology-advancement scenario and the RECS heating/cooling split. (Enhancement over `develop`,
   where these are preset-locked and explicitly non-overridable from the runner.)
7. **Large data files committed into `master`'s history** (CN/KR MERRA-2 weather CSVs, literature PDFs)
   per staff direction 2026-06-03. Git LFS noted as an optional future refinement, not this round.

### Rationale
- One source of truth for both clustering and the international calibration; future fixes to
  `cluster_days_repday` benefit all geographies automatically.
- Keeps master's superior rep-day clustering (develop's inline version was algorithmically equivalent
  but slower and not hemisphere-aware) while keeping develop's proven, validated calibration.
- A single documented control surface lowers the barrier for any team member to produce files for a
  new country or scenario without editing pipeline internals.

### Affected files / variables
- `energy_timeslice_pipeline.py` — one-line `country=country` forward in `run_pipeline()`; surfacing of
  US-specific EFS settings in the runner.
- Imported from develop: `run_pipeline.py`, `requirements.txt`, `zipfile_deflate64.py`,
  `data/eps_priors/`, `data/weather/` (CN/KR), `data/output_demand_ninja/china_*`, `literature/`.
- Docs: `README.md`, `CLUSTERING_METHODOLOGY.md` (new per-region section), `DECISIONS.md` (this entry),
  `INTERNATIONAL_INTEGRATION_PLAN.md` (new).

### Verification
**Done (this round, synthetic / structural — no external data needed):**
- Merge is textually clean; merged `energy_timeslice_pipeline.py` parses, imports, and has no duplicate
  function defs; `cluster_timeslices` is master's wrapper.
- Hemisphere smoke test (`scripts/verify_international_merge_smoke.py`) **PASS**: United States Summer
  Peak representative day in July; Brazil Summer Peak in January (austral summer); `days_per_timeslice`
  sums to 365 for both. Confirms the `country=` flip works through the merged wrapper.
- R3 EFS-override routing **PASS**: US runner override beats preset default; `None` falls back to
  preset; non-US presets ignore the EFS args without error.
- US/state pipeline source (`state_pipeline/`, `rebuild_us_national_v2.py`, workbook scripts) is
  **unchanged by the merge** (0 source insertions/deletions) — so US EPS outputs cannot have changed.

**Still to run (needs an environment with external data + network):**
- Full end-to-end country runs: Brazil / South Korea / China via `run_pipeline.py` with real
  DemandCast / Mendeley / Ember / Renewables.ninja inputs and `zapata_ridge_nnls`.
- US EPS regression diff (state_pipeline / national rebuild) against a saved baseline.

Validate all derived outputs against primary sources before any work-product use.

### Effect on model output
None to existing US EPS files — the US/state pipeline source is untouched by the merge. Non-US outputs
are not regenerated in this round; when re-run, non-US clustering moves to the consolidated rep-day +
hemisphere methodology (numerical shifts expected vs prior develop runs; see plan §9).

---

## 2026-05-15 — Finding: Limited/Reference supply curve ratios are misleading for deployment scaling

### Context
EPS currently projects renewable deployments based on profitability, then scales down by the Limited Access / Reference Access supply curve total-resource ratio per tech (solar 0.45, onshore wind 0.53, offshore wind 0.74) to capture siting friction. User flagged that 0.45 for solar seemed overly constraining.

### Finding
The total-resource ratio (0.45 solar) reflects siting friction across the *entire* supply curve, including marginal high-cost sites that wouldn't be deployed anyway. At realistic deployment levels, the actual cost penalty from Limited Access siting is much smaller. Analysis using NREL Lopez et al. 2030/2035 supply curve files (now in `data/nrel_supply_curves/`):

**Solar PV (2035), LCOE required to reach a deployment milestone:**

| Deploy GW | Reference LCOE | Limited LCOE | Δ |
|---|---|---|---|
| 100 | $26.7/MWh | $26.7/MWh | +$0.1 |
| 500 | $27.0 | $27.2 | +$0.2 |
| 1,000 | $27.3 | $27.4 | +$0.1 |
| 2,000 | $27.6 | $27.7 | +$0.2 |
| 3,000 | $27.7 | $28.0 | +$0.3 |

**Onshore wind (2030), same metric:**

| Deploy GW | Reference LCOE | Limited LCOE | Δ |
|---|---|---|---|
| 100 | $23.9 | $24.9 | +$1.0 |
| 500 | $25.8 | $27.7 | +$1.9 |
| 1,000 | $27.2 | $30.0 | +$2.7 |
| 2,000 | $29.4 | $34.2 | +$4.8 |
| 3,000 | $31.5 | $39.7 | +$8.2 |

### Implication
- **Solar:** 0.45 multiplier is dramatically over-constraining. At any realistic 2050 deployment (~1,000–2,000 GW per NREL Standard Scenarios), the Limited Access LCOE delta is <$0.30/MWh. Recommend replacing the scalar with either (a) a small flat LCOE adder (~$0.50/MWh) or (b) using Reference Access directly with a capacity cap that only binds at multi-thousand-GW levels.
- **Onshore wind:** more nuanced. Real cost premium of $1–3/MWh at typical deployment levels, growing to $5–8/MWh at 2,000–3,000 GW. Replacing 0.53 scalar with deployment-level-dependent LCOE adder (~$1/MWh @ 100 GW → $5/MWh @ 2,000 GW) is more defensible than the flat multiplier.
- **Offshore wind (0.74):** smaller resource base, more genuinely binding at projected deployment levels — current scalar approach probably defensible.

### Status
**Analysis only — no methodology change made yet.** Recommendation left for downstream policy/modeling team to incorporate into the EPS profitability-driven deployment logic when prioritized. Script: `scripts/analyze_supply_curve_bins.py`.

### Data
NREL supply curves now in `data/nrel_supply_curves/`:
- `solar_limited_access_2035_moderate_supply_curve.csv` + `solar_reference_access_2035_moderate_supply_curve.csv`
- `lbw_limited_access_2035_moderate_115hh_170rd_supply_curve.csv` (2035 wind limited; reference 2035 not yet available locally)
- `limited_access_2030_moderate_115hh_170rd_supply-curve.csv` + `reference_access_2030_moderate_115hh_170rd_supply-curve.csv` (wind 2030)

---

## 2026-05-22 — Consolidate clustering across US + non-US pipelines; add Southern Hemisphere support

### Context
Two clustering implementations existed in the project:
- `state_pipeline/builders/clustering_repday.cluster_days_repday` — used by US national + per-state pipelines; numpy-vectorized; canonical methodology (rep-day on net load with fixed rep profiles, no peak-day cap)
- `energy_timeslice_pipeline.cluster_timeslices` — used by the 12 international country presets (Canada, Mexico, Brazil, UK, France, Germany, China, South Korea, Japan, India, Australia, plus the older US-via-EFS path); pandas-heavy and slow but algorithmically identical to the canonical version

Both used rep-day reconstruction on net load with fixed rep profiles, NRMSE-std scoring, and no `max_peak_days` cap. The implementations were duplicated and could drift over time.

Additionally, the legacy `cluster_timeslices` defaulted to Northern Hemisphere season months (`summer = [6,7,8]`, `winter = [11,12,1,2]`) regardless of country. Running it for Brazil or Australia (Southern Hemisphere) would put their actual summer peak days into the Winter pool and vice versa — a latent bug since no non-US runs had been executed recently.

### Decision
Refactor `cluster_timeslices` into a thin wrapper around `cluster_days_repday`:
- Same legacy signature and return tuple (hourly labels Series, KMeans placeholder, mapping dict, representative_dates dict) preserved for backward compatibility
- New optional `country` parameter on `cluster_timeslices` and `run_pipeline` drives hemisphere-aware season-month defaults via a new helper `_hemisphere_season_months(country)`
- Southern Hemisphere countries recognized: Argentina, Australia, Bolivia, Brazil, Chile, New Zealand, Paraguay, Peru, South Africa, Uruguay
- The original pandas implementation is kept as `_cluster_timeslices_legacy_impl` and used only as a fallback if `state_pipeline` is not importable

### Rationale
- Single source of truth for clustering methodology across all geographies in this project. Bug fixes and improvements to `cluster_days_repday` automatically benefit international runs.
- ~50× speed-up for non-US runs (numpy vs pandas).
- Fixes Southern Hemisphere season-pool defaults so Brazil / Australia / etc. correctly identify their summer peaks in December–February instead of falsely placing them in the Northern Hemisphere summer window.
- Backward compatibility preserved — existing call sites in `run_pipeline` and `compare_pinned_unpinned_clustering` don't need code changes, only the `country=` kwarg threading.

### Affected files
- `energy_timeslice_pipeline.py` (12 country presets) — `cluster_timeslices` refactored; `_hemisphere_season_months` + `SOUTHERN_HEMISPHERE_COUNTRIES` added; `run_pipeline` passes `country=` through
- `CLUSTERING_METHODOLOGY.md` — new "Global / non-US application status" section
- `scripts/verify_clustering_equivalence.py` — new harness for head-to-head comparison (legacy left in place as fallback; can be re-run if equivalence is ever questioned)

### Verification
Smoke-tested with synthetic net-load data:
- `cluster_timeslices(net_series, country='UnitedStates')` → Summer Peak rep date in July ✓
- `cluster_timeslices(net_series, country='Brazil')` → Summer Peak rep date in December ✓ (months flipped)

### Open items
- Full end-to-end re-run of China / South Korea / Brazil / Australia presets to verify nothing else broke. Not done in this session because the legacy pipeline needs external data (DemandCast, Mendeley, Ember, Renewables.ninja) and we'd be reproducing existing artifacts; deferred until a non-US run is actually needed.
- The legacy downstream SHELF/SYSHECF build for non-US doesn't use the rich self-contained-workbook pattern from `scripts/build_shelf_workbook.py` / `scripts/build_syshecf_workbook.py`. Porting that pattern to non-US is a separate task.

---

## 2026-05-15 — State pipeline rerun for all 48 lower-48 states with state-specific EIA calibration

### Context
After implementing state-specific EIA CF calibration (see entry below), all 48 lower-48 state pipelines were rerun using the new methodology: rep-day clustering, no peak-day cap, flat datacenters SHELF, state-specific EIA CFs applied per-tech.

### Outcome
48/48 states completed successfully. Generated SHELF + SYSHECF + days_per_timeslice files for each state at `state-eps-data-repository/<state>/elec/<SHELF|SYSHECF>/_python_pipeline/`. Excel workbooks + validation reports also produced.

| Metric | Min | Mean | Max |
|---|---|---|---|
| NRMSE | 0.291 | 0.524 | 0.892 |
| Summer Peak days | 3 | 18.4 | 46 |
| Winter Peak days | 3 | 12.4 | 26 |
| State peak GW | 1.0 (VT) | — | 82.4 (TX) |

State-by-state results in `scripts/data_outputs/all_states_run_log.csv`. Variation in Summer Peak day count (3–46) reflects different climate consistency — Arkansas at 46 SP days has many similarly-extreme hot summer days that fit the rep day's shape; Arizona at 16 has a sharper extreme-day signature; Vermont at 3 has few extreme summer days.

### Affected
- 48 state SHELF folders populated (`state-eps-data-repository/<state>/elec/SHELF/_python_pipeline/`)
- 48 state SYSHECF folders populated
- 48 Excel workbooks generated
- 48 validation reports
- AK, HI, DC excluded (lack Cambium 2022 / ResStock coverage)

### Next steps available (not pursued in this round)
- Update each state's EPS Vensim model to point to `_python_pipeline/` SHELF + SYSHECF rather than legacy directories, or copy `_python_pipeline/` outputs over the legacy state SHELF/SYSHECF folders if those are the production paths.
- Refresh `data/eia_state_cfs.csv` annually when EIA publishes new state profiles.

---

## 2026-05-15 — EIA CF calibration asymmetry between national and state SYSHECFs (intentional)

### Context
During the state-pipeline alignment to national methodology (rep-day clustering, no peak cap, flat datacenters), the SYSHECF EIA CF calibration was NOT propagated to state pipeline. Spot-checking revealed:

- National: applies EIA Table 4.8.B targets (0.232 solar-pv, 0.170 solar-pv-dist, 0.343 onshore-wind, 0.420 offshore-wind, 0.250 solar-thermal) as a flat scalar to each VRE SYSHECF table.
- State: writes Cambium per-state CFs directly to SYSHECF without scaling.

### Decision
**Keep this asymmetry intentionally.** Do not apply EIA *national* CF calibration to state SYSHECFs.

### Rationale
EIA Table 4.8.B values are **national capacity-weighted averages**. State-level resource quality varies substantially:
- North Dakota onshore wind raw CF ~0.48 (best US wind resource)
- Pennsylvania onshore wind raw CF ~0.30 (worse)
- Forcing both to 0.343 national average would distort state-specific peak/load behavior

Cambium per-state files already encode state-specific resource quality. Scaling them to a national average would be a regression for state-level accuracy.

### Open / deferred
Add state-specific EIA CF calibration in the future. **Concrete data source identified:**

EIA State Electricity Profiles, per-state. URL pattern:
`https://www.eia.gov/electricity/state/<state-slug>/state_tables.php`

Examples: `/virginia/`, `/north-carolina/`, `/california/`. Each state page provides a downloadable XLSX containing 19 tables. The two relevant ones:
- **Table 4A** — Electric power industry capacity by primary energy source (MW)
- **Table 5** — Electric power industry generation by primary energy source (MWh)

State per-tech CF = `Table 5 generation_MWh / (Table 4A capacity_MW × 8760)`.

Implementation sketch when prioritized:
1. Write `scripts/fetch_eia_state_cfs.py` — download all 50 + DC state_tables.xlsx files, parse Tables 4A and 5, compute per-state per-tech CFs, write `data/eia_state_cfs.csv`.
2. Extend `state_pipeline/builders/syshecf_builder.build_all_syshecf` with `state_cf_targets: dict[tech, float] | None` parameter.
3. In `state_pipeline/run.py`, load state targets from preset YAML (`eia_cf_targets:` block) or shared lookup keyed by `state_iso2`.
4. Apply via the same `calibrate_to_eia` flat-scalar method as national.
5. Re-run all state presets.

### Affected files
- `CLAUDE.md` §1 (SYSHECF section clarified: national vs state)
- `CLAUDE.md` §10 (new TODO with EIA source pointers)

### Effect on outputs
None. State SYSHECF outputs remain as written by the 2026-05-15 state runs — Cambium per-state raw CFs.

---

## 2026-05-15 — State pipeline aligned with national methodology

### Context
The 2026-05-15 US national calibration round established a methodology (rep-day clustering, no peak-day cap, flat datacenters SHELF) that differed from what the state pipeline was using (slice-mean clustering with `max_peak_days=10` cap, all-zero datacenters SHELF). State EPS analyses would inherit the older methodology and be inconsistent with the national.

### Decision
Migrate `state_pipeline` to use the same methodology as national:
- `state_pipeline/run.py` imports `cluster_days_repday as cluster_days` (was `cluster_days` from `clustering.py`)
- Preset YAMLs (`US-VA.yml`, `US-MO.yml`) set `peak_top_n_days: 1` and `max_peak_days: 365` (effectively uncapped)
- `state_pipeline/run.py` populates `shelf_tables['datacenters']` with a flat 24/7 profile (LF = 1/8760 in every cell) after `build_all_shelf`. This automatically writes a flat datacenters SHELF regardless of preset.

### Rationale
State and national should share methodology so results are comparable, the codebase has one canonical clustering implementation, and CLAUDE.md doesn't have to maintain divergent guidance. Rep-day clustering is the correct objective for capacity-meaningful peak slices; the old slice-mean + cap was a compromise.

### Affected files
- `state_pipeline/run.py` (imports, default peak-day parameters, flat datacenters insertion)
- `state_pipeline/presets/US-VA.yml`, `state_pipeline/presets/US-MO.yml` (peak_top_n_days, max_peak_days)

### Effect on outputs
State runs re-executed on 2026-05-15 with the new methodology.

| State | Days per timeslice (W/Sp/Su/F/SP/WP) | NRMSE | Annual TWh | Peak GW |
|---|---|---|---|---|
| US-VA | 36 / 90 / 154 / 63 / **15 / 7** | 0.597 | 137.0 | 25.7 |
| US-MO | 47 / 81 / 100 / 92 / **33 / 12** | 0.446 | 81.1 | 14.1 |
| US national (reference, from earlier in this round) | 61 / 121 / 112 / 50 / **11 / 10** | 0.4252 | 4,408 (gross) | 781.9 (gross) |

State-level peak-slice day counts vary noticeably across climates: MO (continental, consistent hot summers) lands at 33 days in Summer Peak vs VA (more humid mid-Atlantic, fewer truly extreme days) at 15 vs national aggregate at 11. This is the rep-day optimizer's correct behavior — peak slices grow as long as adding days matches the rep day's shape closely; consistent climates have more "matching" days. Lower NRMSE for MO (0.446) than VA (0.597) reflects MO's higher shape consistency.

SHELF + SYSHECF files written to each state's `state-eps-data-repository/<state>/elec/` directory (under `_python_pipeline/` subfolder). Datacenters SHELF populated with flat profile in both states.

### Open items
- Cambium 2024 state-level data is not yet in the repo. State pipeline continues to use Cambium 2022 per-state. When Cambium 2024 state files become available, update presets to point to them.
- The presets currently have `industry_shape_mode: efs` (VA, MO). Consider revisiting per state — `flat` is more defensible for bulk industry; `cambium_residual` is interesting for high-VRE states.

---

## 2026-05-15 — US national SHELF + SYSHECF calibration round

### Final calibration state

- **Model net peak (Summer Peak slice, 2025): 577 GW**
- Within 5% of Cambium 2024 MidCase SP slice net peak reference (608 GW)
- Gap remaining ~31 GW vs Cambium MidCase ref, ~60 GW vs no-IRA-scenario expected (640 GW). Within calibration tolerance for reliability-mechanism analysis.
- Total improvement from starting state: 532 GW → 577 GW (+45 GW, +8.4%)

### Decision 1: Switch national clustering source from Cambium 2022 → Cambium 2024

**Context:** Cambium 2022 was the legacy clustering input but was anchored to AEO 2022 load forecasts (pre-data-center surge). Aggregate gross peak in 2025 was 712.6 GW (SP slice mean), well below EIA 2025 actual coincident peak (759 GW).

**Decision:** Adopt Cambium 2024 MidCase national hourly (`data/cambium24_midcase_national/Cambium24_MidCase_hourly_usa_2025.csv`) for national clustering and SYSHECF. State pipeline continues to use Cambium 2022 per-state.

**Rationale:** Cambium 2024 ties out to EIA 2025 actual peak within 3% (745.8 GW SP slice mean vs 759 GW EIA coincident). Weather year 2012 in both vintages.

### Decision 2: Restore ResStock + ComStock as canonical residential/commercial SHELF sources

**Context:** Initial round of rebuild work used EFS national load profiles for all building categories. This was wrong — EFS Reference/Moderate is national-aggregated and pre-data-center-vintage, producing flatter and less realistic load shapes when weighted by EPS's cooling-heavy annuals. Result: 810 GW gross peak in the model (too peaky by 9%), 720 GW net peak (overshoot).

**Decision:** Use ResStock for residential SHELFs and ComStock for commercial SHELFs, aggregated across all 49/51 state folders. Use EFS only for `industry`, `LDVs`, `HDVs`, `rail`.

**Rationale:** ResStock and ComStock are NREL detailed building-stock models with per-end-use load profiles. They capture real building behavior diversity. EFS is appropriate only for industry (where ResStock/ComStock don't apply) and as a fallback for transport.

**Affected:** All `SHELF-residential-*` and `SHELF-commercial-*` files in eps-us are now from ResStock/ComStock national aggregation. EFS still used for industry + LDVs + HDVs + rail.

### Decision 3: Switch clustering from slice-mean to representative-day reconstruction

**Context:** The `state_pipeline/builders/clustering.cluster_days` function uses slice-mean reconstruction on gross demand. When peak day cap is removed, the optimizer pulls the entire "hot half" and "cold half" of the year into peak slices (53/76 days at uncapped) because that minimizes mean-fit error. This produces semantically meaningless peak slices.

**Decision:** Use `state_pipeline/builders/clustering_repday.cluster_days_repday`. Uses representative-day reconstruction on net load with FIXED rep profiles (peak slice rep = most-extreme pinned day; non-peak slice rep = closest to feature centroid). NRMSE-std normalization.

**Rationale:** With fixed rep profiles, the optimizer only adds days to a peak slice whose actual shape matches the extreme rep day. It naturally converges to 10-15 day peak slices without any cap. Matches legacy `energy_timeslice_pipeline.cluster_timeslices` methodology.

**Affected:** National rebuild script (`rebuild_us_national_v2.py`). State pipeline still uses slice-mean clustering with `max_peak_days=10` cap — see Open Issues.

### Decision 4: Remove peak day cap in national clustering

**Context:** Previously imposed `max_peak_days=10` cap on each peak slice's iterative growth. Necessary when using slice-mean reconstruction to prevent semantic drift. With rep-day reconstruction, the optimizer self-terminates.

**Decision:** Run `cluster_days_repday` with `max_peak_days=365` (effectively uncapped). Optimizer converges to 11 SP / 10 WP days for Cambium 2024 MidCase 2025.

**Final days_per_timeslice:** Winter 61, Spring 121, Summer 112, Fall 50, Summer Peak 11, Winter Peak 10.

### Decision 5: Apply timezone correction in ResStock/ComStock national aggregation

**Context:** ResStock and ComStock files are in **local standard time per state** (verified empirically: NY cooling peaks at file-label hr 16, CA at hr 19, TX at hr 17 — exactly the LST offsets). Raw aggregation summed states' local-hour values together, mixing 5pm-PT with 5pm-ET at the same label and smearing the aggregate.

**Decision:** Shift each state's hourly series forward by its LST→ET offset before summing. Offsets: 0 for ET states, +1 for CT, +2 for MT, +3 for PT, +4 for AKT (AK), +5 for HST (HI). Multi-TZ states use majority TZ.

**Implementation:** `np.roll(state_hourly_array, +offset, axis=0)` with wraparound. See `STATE_TZ_OFFSET_TO_ET` dict in `rebuild_us_national_v2.py`.

**Rationale:** Cambium 2024 busbar load is on ET. Aggregation should align state loads to the same reference frame so the resulting shape captures coincident-grid peak (which is what utilities measure).

**Effect:** Made aggregate peak hour shift slightly earlier (commercial cooling hr 16 → hr 14 ET, residential cooling hr 18 → hr 17 ET). Magnitude shifted ~4 GW. Physically correct but doesn't itself fix the magnitude gap to Cambium reference — the gap was from missing data center load (see Decision 7).

### Decision 6: Use EIA Table 4.8.B annual CFs for SYSHECF VRE calibration

**Context:** Cambium 2024 raw annual CFs for VRE tend to be 10-20% above EIA observed values because they reflect projected new-fleet performance. EIA observed CFs better represent actual operating fleet performance for the model start year.

**Decision:** Calibrate SYSHECF VRE annual CFs to EIA Table 4.8.B (capacity-weighted national average for the most recent year):
- solar-pv: 0.232
- solar-pv-dist: 0.170
- solar-thermal: 0.250
- onshore-wind: 0.343
- offshore-wind: 0.420

Apply as flat scalar over the full 6×24 SYSHECF table. Preserves hourly shape; scales annual CF to target.

### Decision 7: Populate SHELF-datacenters with flat 24/7 profile

**Context:** `SHELF-datacenters.csv` in eps-us was all-zero in both the pre-rebuild backup and (initially) the rebuilt version. The model had explicit data center annual demand in BCEU/AEO inputs but multiplied by zero LFs in every hour — so data center load was invisible to hourly demand calculations. This zeroing-out accounted for the largest single chunk of the remaining peak-load gap.

**Decision:** Populate `SHELF-datacenters.csv` with a flat 24/7 profile: LF = 1/8760 = 1.142e-4 in every (slice, hour) cell. Balance check: `sum_slices(LF × 24 × days_per_slice) = 1.000`.

**Rationale:** Data centers are designed to run continuously near maximum utilization. Intra-day workload variation is typically <10%. A flat shape is the most defensible default. If precise intra-day shape matters later, refine with a daytime-peakish profile (~5-10% midday lift).

**Effect:** Model net peak rose 549 GW → 577 GW (+28 GW). Inferred data center annual: ~245 TWh (28 GW ÷ 0.1142 GW/TWh), consistent with EIA's 2025 data center load estimates (~250 TWh).

### Acknowledged remaining gap (do not address now; flag for next round)

- **Annual demand under-stated by ~3%.** Model 4,170 TWh end-use; EIA-implied 2025 is ~4,200-4,300 TWh once data centers properly counted. A ~3% bump adds ~17 GW to peak.
- **Model VRE capacity may be too high for no-IRA scenario.** If the model uses Cambium 2024 MidCase capacities for 2025 (~160 GW UPV, ~181 GW onshore wind), that reflects with-IRA buildout. No-IRA scenario should have meaningfully less VRE (~100 GW UPV, ~140 GW wind), meaning less VRE subtraction at peak → higher net peak. Could add 30-40 GW.

These items are within reasonable calibration tolerance for the reliability-mechanism analysis and were not pursued in this round.

---

## Template for future entries

```
## YYYY-MM-DD — short description

### Context
Why this came up.

### Decision
What was decided.

### Rationale
Why.

### Affected files / variables
What changed in the repo and in eps-us.

### Effect on model output
Quantitative before/after.
```

---

*Maintained by Energy Innovation modeling team. All decisions documented here
represent inputs for staff review. Calibration values and source data should
be verified against EIA, NREL Cambium, NREL ResStock/ComStock, EFS, and AEO
primary documentation before being used in any work product.*
