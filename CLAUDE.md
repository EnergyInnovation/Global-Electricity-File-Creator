# Global Electricity File Creator — Project Methodology

This file is the canonical reference for how the SHELF and SYSHECF files
in this pipeline are built. Read it before writing or modifying any pipeline
code. It supersedes any default assumptions about data sources or clustering.

The pipeline produces files for the EPS (Energy Policy Simulator) Vensim
model, dropped into `eps-us/InputData/elec/SHELF/` and
`eps-us/InputData/elec/SYSHECF/`.

---

## 1. Data sources — canonical (DO NOT deviate)

### SHELF demand-shape sources (per category)

| EPS SHELF category | Source | Reader / notes |
|---|---|---|
| `residential-heating`, `-cooling`, `-lighting`, `-appliances`, `-other` | **ResStock** (NREL detailed building stock) | `state_pipeline/readers/resstock_reader.py`. State files at `ResStock SHELF/ResStock_Upgrade0/state=XX/`. 49 states + DC available. |
| `commercial-heating`, `-cooling`, `-lighting`, `-appliances`, `-other` | **ComStock** (NREL commercial stock) | `state_pipeline/readers/comstock_reader.py`. State files at `ResStock SHELF/ComStock_tmy_release1/XX/`. 51 state folders incl. AK, HI, DC. |
| `industry` | **EFS** Industrial subsector (machine drives + process heat + other) | `state_pipeline/readers/efs_reader.py`. Three shape modes available: `efs`, `flat`, `cambium_residual` (see `apply_industry_shape_mode`). State pipeline default: `flat`. |
| `LDVs`, `HDVs`, `rail` | **EFS** Transportation subsectors *(state pipeline uses `transport_calculator.py`; national rebuild uses EFS Transportation directly)* | LDV → light-duty; HDV → medium-duty + heavy-duty; rail → ~40% of EFS "other transport" |
| `aircraft`, `ships`, `motorbikes` | **Zero** (EPS convention) | Always-zero SHELF |
| `residential-envelope`, `commercial-envelope` | **Zero** (EPS convention) | Always-zero SHELF |
| `datacenters` | **Flat 24/7 shape** (LF = 1/8760 every cell) | Data centers run continuously; flat is the most defensible default. Annual energy comes from BCEU/AEO inputs in eps-us. SP peak contribution = `annual_TWh / 8.76 GW`. |
| `district-heat-hydrogen`, `geoeng` | **Zero** in start year | Currently zero in eps-us; ramps up post-2030 in some scenarios. |

### NEVER use EFS for residential or commercial. EFS national load profiles are too flat (industry-weighted, pre-data-center vintage) and dilute peakiness. Real shape diversity comes from ResStock/ComStock.

### Net-load clustering + VRE generation sources

- **National:** `data/cambium24_midcase_national/Cambium24_MidCase_hourly_usa_2025.csv`
- **State:** `data/cambium22_midcase_state_hourly/Cambium22_MidCase_hourly_XX_2024.csv`
- Both files have `busbar_load`, `net_load_busbar`, per-tech `*_MWh`, `variable_generation`.

### SYSHECF capacity-factor sources

- **Variable techs** (solar-pv, solar-pv-dist, solar-thermal, onshore-wind, offshore-wind, hydro, pumped-hydro, nuclear, combined-cycle, natural-gas-peaker, hard-coal, biomass, geothermal, petroleum): **Cambium hourly** `*_MWh / *_MW` from the annual file.
- **Non-variable techs** (lignite, lignite-CCS, hydrogen-CC, hydrogen-CT, SMR, MSW, steam-turbine, combined-cycle-CCS, hard-coal-CCS, heavy-or-residual-oil, crude-oil): legacy templates in eps-us, do not overwrite.

### Non-US wind CF source — use Renewables.ninja *site simulation output*, NOT the 2 m weather variable

For non-US presets the wind CF comes from `energy_timeslice_pipeline.py`, not Cambium. Two sources exist:

- ❌ **2 m `wind_speed` weather product** (`ninja-weather-country-*-wind_speed_*.csv`), extrapolated to hub height in `compute_wind_capacity_factor_from_weather`. The MERRA-2 2 m field (U2M/V2M) has an **inverted diurnal cycle** vs hub height (afternoon max instead of overnight max) and forces huge calibration multipliers (China 7.18×). Do **not** use it for wind shape. (Solar still uses the ninja weather product — that's fine.)
- ✅ **Per-site wind *simulation* output** — hub-height, power-curve, bias-corrected. Fetch with `scripts/fetch_ninja_sites.py` (token-auth API; sites/years editable at the top) → `data/weather/ninja_sim/<ISO2>/<site>_<year>.csv`, where `electricity` (fetched with `capacity=1`) IS the hourly CF. Averaged across sites by `load_site_wind_capacity_factors`, reduced to a **day-of-year × hour climatology**, converted UTC→preset timezone, mapped onto the run calendar, and calibrated to the **Ember** annual wind CF (`cap_redistribute`).

Enable per preset with `wind_cf_source: 'ninja_sites'` (default `'weather'`). **China and South Korea** use `ninja_sites` as of 2026-07-10 (see DECISIONS.md). The wind window is **decoupled from `last_n_years`** (which governs demand + Ember): wind uses its own `wind_cf_years` (preset key; runner override `WIND_CF_YEARS` in `run_pipeline.py`), defaulting to **7** (= 2018–2024, the site archive). The loader takes the most recent `n_years` available on disk, so a preset can request 7 even if fewer years are fetched (uses what exists, reports the shortfall). Other countries still use the 2 m path pending their own site downloads. Caveats for staff review: placeholder site coordinates must be replaced with verified fleet-region coordinates; and a single blended `wind_cf` currently feeds BOTH onshore- and offshore-wind SYSHECF (per-tech site separation is a follow-up).

### EIA annual CF calibration targets

**National pipeline uses EIA Table 4.8.B (national capacity-weighted) targets.** State pipeline uses **state-specific EIA CFs from EIA State Electricity Profiles** (Sheet 15 + Sheet 19, 2024 column), pulled by `scripts/fetch_eia_state_cfs.py` and stored in `data/eia_state_cfs.csv`. State pipeline auto-loads per-state targets via `state_iso2` key.

Targets (national, EIA Table 4.8.B capacity-weighted national average for most recent year):

| Tech | National target annual CF |
|---|---|
| solar-pv | 0.232 |
| solar-pv-dist | 0.170 |
| solar-thermal | 0.250 |
| onshore-wind | 0.343 |
| offshore-wind | 0.420 |

Applied as a flat scalar over the entire 6×24 SYSHECF table so annual-weighted CF matches the target. Preserves hourly shape.

**State pipeline targets:** loaded from `data/eia_state_cfs.csv` (columns: `state_iso2`, `tech`, `cf_target_2024`, `capacity_mw_2024`). `state_pipeline/run.py` filters by `state_iso2` and passes to `build_all_syshecf(..., state_cf_targets=...)`. Same calibration math (flat scalar to match annual target). State targets capture state-specific resource quality (e.g., ND onshore-wind 0.388, CA solar-pv 0.263, VA solar-pv 0.202 vs national 0.343/0.232).

To refresh the state CF lookup (e.g., when EIA publishes new annual data):
```
python scripts/fetch_eia_state_cfs.py
```

---

## 2. Clustering methodology

### Use `state_pipeline/builders/clustering_repday.cluster_days_repday` — NOT `clustering.cluster_days`

Two implementations exist:

- ❌ `clustering.cluster_days` — slice-MEAN reconstruction on GROSS demand. **Broken for capacity-planning peaks** when uncapped: optimizer absorbs the entire hot/cold half of the year into peak slices because that minimizes mean-fit error.
- ✅ `clustering_repday.cluster_days_repday` — representative-day reconstruction on NET load, NRMSE-std normalization, FIXED rep profiles. Optimizer naturally converges to ~10–15 day peak slices without any cap. This matches the legacy `energy_timeslice_pipeline.cluster_timeslices` methodology.

### Parameters

- `peak_top_n=1` — initial pinned days per peak slice (most-extreme by net peak per season)
- `max_peak_days=365` — effectively no cap (optimizer self-terminates)
- `feature_weight_mode='netload_focus'` — weights `net_p95` and `net_min` heavily
- `summer_months=(6, 7, 8)`, `winter_months=(11, 12, 1, 2)` — for pinned-peak season pools

### Why rep-day not slice-mean

Slice-mean reconstruction means a slice's "predicted profile" is the mean of all assigned days. Adding more days flattens that mean. The optimizer can lower NRMSE by absorbing similar-shape days into peak slices — so uncapped, it pulls the entire "hot half" into Summer Peak.

Rep-day reconstruction means the predicted profile is a single fixed day's actual profile (the most extreme day for peak slices; the centroid-closest day for non-peak). Adding a day to a peak slice doesn't change the rep profile — it only changes what's reconstructed using that profile. So the optimizer only adds days whose shape matches the extreme — i.e., truly extreme days.

### Do not impose a peak-day cap

The natural rep-day optimum is ~10–15 days per peak slice. Capping at 10 (`max_peak_days=10`) is unnecessary and slightly suboptimal. Capping below the natural optimum produces capacity-relevant but slightly NRMSE-suboptimal results. The default in `cluster_days_repday` is `max_peak_days=365` (effectively uncapped) and that's correct.

---

## 3. National pipeline (US national rebuild)

Entry point: `rebuild_us_national_v2.py` at project root.

### Data flow

1. **Cambium 2024 hourly** → net load + VRE generation series for clustering
2. **ResStock aggregation across 49 state folders** → residential SHELF inputs *(time-zone corrected)*
3. **ComStock aggregation across 51 state folders** → commercial SHELF inputs *(time-zone corrected)*
4. **EFS national** → industry + transport SHELF inputs (already national, no TZ correction needed)
5. **`cluster_days_repday`** on Cambium 2024 net load
6. **`build_shelf_for_category`** per category
7. **Cambium 2024 per-tech hourly + EIA calibration** → SYSHECF
8. **Write to** `eps-us/InputData/elec/SHELF/` and `SYSHECF/`

### TIME ZONE CORRECTION — critical for ResStock/ComStock aggregation

ResStock and ComStock files use **local standard time per state** (verified empirically: NY cooling peaks at hr 16 file-label, CA at hr 19 file-label, TX at hr 17 file-label; difference = real timezone offset). When summing across states, raw aggregation mixes 5pm-PT with 5pm-ET (three hours apart in real time), smearing the aggregate national peak.

The Cambium 2024 busbar load is on ET. Aggregation must shift each state's hourly series forward to ET before summing:

| Offset (LST → ET) | States |
|---|---|
| +0 (ET) | CT, DE, DC, FL, GA, IN, KY, ME, MD, MA, MI, NH, NJ, NY, NC, OH, PA, RI, SC, VT, VA, WV |
| +1 (CT) | AL, AR, IA, IL, KS, LA, MN, MS, MO, NE, ND, OK, SD, TN, TX, WI |
| +2 (MT) | AZ, CO, ID, MT, NM, UT, WY |
| +3 (PT) | CA, NV, OR, WA |
| +4 (AKT) | AK *(ComStock only)* |
| +5 (HST) | HI *(ComStock only)* |

Implementation: `np.roll(state_hourly_array, +offset, axis=0)` with wraparound. Multi-TZ states (TX, FL, KY, IN, etc.) use the majority TZ.

EFS national is already on a single national reference and does not need TZ correction.

### Annual demand calibration

The model's per-category annuals come from the **eps-us BCEU / AEO inputs**, NOT from ResStock/ComStock/EFS magnitudes. The SHELF LFs from ResStock/ComStock/EFS provide *shape only*. Absolute values in raw ResStock files don't represent state totals (they're sample-weighted) — the demand_assembler normalization step rescales by actual annual.

The 2025 EPS model end-use demand should be in the range **4,160–4,400 TWh** (EIA 2025 retail-equivalent + losses). If your model's demand is well below this, peak will come in low regardless of SHELF shape.

---

## 4. State pipeline (per-state US runs and other countries)

Entry point: `python -m state_pipeline.run --state US-XX`

### Data flow

1. **BCEU + Industry CSV + Transport calculator** → per-category annual MWh
2. **ResStock state hourly** → residential shape
3. **ComStock state hourly** → commercial shape
4. **EFS state hourly** → industry shape (mode chosen in preset)
5. **Cambium state hourly + annual** → net load + VRE + capacities
6. **`cluster_days`** on net load (currently uses slice-mean version; should migrate to rep-day eventually)
7. **`build_shelf_for_category` + `build_all_syshecf`** → SHELF + SYSHECF tables
8. **Write to** `output/<state>/` directory + Excel workbooks

### Preset YAML

Each state has a YAML at `state_pipeline/presets/US-XX.yml` specifying:
- `state_iso2`, `display_name`, `output_slug`
- `sources`: paths to BCEU, ResStock, ComStock, EFS, Cambium, transport, industry CSVs
- `outputs`: SHELF dir, SYSHECF dir, workbook paths
- `calendar_year` (typically 2018 — matches ResStock TMY3)
- `cambium_year` (typically 2024 — annual file year)
- `industry_shape_mode` (default `flat`)
- `peak_top_n_days: 1`, `max_peak_days: 365` (rep-day clustering self-terminates; no cap needed)
- `curtailment_addback` (per-tech CF scaling factors for high-VRE states)
- `external_refs` (EIA SEDS cross-check values)

### Calendar alignment

All hourly inputs are reindexed to a common 2018 calendar (`pd.date_range('2018-01-01', periods=8760, freq='h')`). This is non-leap and starts Monday. ResStock uses 2018 TMY by design.

### State pipeline uses `cluster_days_repday` (same as national, as of 2026-05-15)

The state pipeline was migrated to rep-day clustering on 2026-05-15 to match the national methodology. `state_pipeline/run.py` imports `cluster_days_repday as cluster_days`, and preset YAMLs use `peak_top_n_days: 1` and `max_peak_days: 365` (effectively uncapped). Datacenters SHELF is populated with a flat 24/7 profile (LF = 1/8760) automatically by the run script.

State and national pipelines now share:
- Same clustering function (`cluster_days_repday`)
- Same peak-day handling (`peak_top_n=1`, no cap)
- Same datacenters SHELF treatment (flat 24/7)
- Same EIA CF calibration logic for SYSHECF (where applicable)

Cambium vintage still differs: state pipeline uses Cambium 2022 per-state; national uses Cambium 2024. State-level Cambium 2024 data not yet in repo.

---

## 5. Output destinations

### National (US)
- `C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SHELF\` — 22 `SHELF-*.csv` + `SHELF-days-per-timeslice.csv`
- `C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SYSHECF\` — variable techs only

**ALWAYS BACK UP** the eps-us SHELF and SYSHECF folders before overwriting. Use `_backup_*` subfolders.

### State / other
- `output/<state>_timeslice_results_*.csv` (legacy national format)
- `output/<state>/SHELF/`, `output/<state>/SYSHECF/`, Excel workbooks

---

## 6. SHELF + SYSHECF format

### SHELF
- One file per category, 22 files total.
- Header row: `Unit: dimensionless (ratio of electricity demand in this hour to annual demand),Hour0,Hour1,...,Hour23`
- 6 data rows: `Winter`, `Spring`, `Summer`, `Fall`, `Summer Peak`, `Winter Peak`
- Values are LF where `LF[slice, hour] = (mean demand in slice at that hour) / annual demand`
- **Balance check:** `sum_slices(sum_hours(LF[slice, hour]) × days_per_slice[slice]) = 1.0` for non-zero categories.
- 8 categories are intentionally zero (see table above).
- Days-per-timeslice file: `SHELF-days-per-timeslice.csv` — 6 rows of `slice,days`.

### SYSHECF
- One file per tech, 25 files total (lots of templates for non-Cambium techs).
- Header row: `<tech display name>,Hour0,...,Hour23` (display name like "natural gas combined cycle")
- 6 data rows (same slices as SHELF)
- Values are capacity factors (0–1).
- **VRE techs are EIA-calibrated:** the table's annual-weighted CF = EIA target.
- Non-variable techs preserved as legacy templates.

---

## 7. Common mistakes to avoid

1. **Don't use EFS for residential or commercial.** Use ResStock and ComStock.
2. **Don't use slice-mean reconstruction (`cluster_days`) for clustering** if you want capacity-meaningful peak slices. Use `cluster_days_repday`.
3. **Don't cap `max_peak_days`** at a low value when using `cluster_days_repday`. The optimizer self-terminates.
4. **Don't aggregate ResStock/ComStock across states without TZ correction.** It will smear the aggregate national peak.
5. **Don't change `SHELF-days-per-timeslice.csv` without rebuilding the LF values.** Breaks SHELF balance.
6. **Don't overwrite eps-us files without backing up first.**
7. **Don't reinvent the pipeline** — extend `state_pipeline` or write a thin wrapper. Read `state_pipeline/run.py` end-to-end before writing new pipeline code.
8. **Don't use SHELF aggregate magnitudes as a sanity check on peak GW.** Raw values are sample-weighted, not state totals. The actual model peak depends on SHELF LFs × the model's BCEU/AEO annual energy.

---

## 8. Sanity-check reference values for 2025 US national

When debugging, compare to:

- **EIA 2024 actual net generation**: 4,308.6 TWh (EPA Table 1.1)
- **EIA 2025 retail sales**: 4,058 TWh (Electric Power Monthly)
- **EIA 2025 implied net generation**: ~4,400 TWh (retail × 1.084 for T&D + own-use)
- **EIA 2024 coincident peak**: 745 GW @ Jul 15 (EIA-930)
- **EIA 2025 coincident peak**: 759 GW @ Jul 29 (EIA-930, +1.9% over 2024)
- **Cambium 2024 MidCase 2025 annual gross peak**: 781.9 GW (single hour, Jul 7 hr 15)
- **Cambium 2024 MidCase 2025 SP slice gross peak**: 745.8 GW @ hr 15 (11-day mean)
- **Cambium 2024 MidCase 2025 SP slice net peak**: 607.8 GW @ hr 19 (11-day mean)
- **Cambium 2024 MidCase 2025 annual VRE generation**: 1,062 TWh
- **Cambium 2024 MidCase 2025 implied loss/own-use rate**: 5.56%

The model's gross SP slice peak should be within ~5% of 745 GW (i.e., 710–780 GW). Net depends on the model's VRE capacity which may be lower than Cambium MidCase under no-IRA scenarios.

---

## 9. Workflow notes for AI assistants

- **All project files belong in the project folder.** Working scripts go to `scripts/`. Output data files go to `scripts/data_outputs/` or to the canonical pipeline destination (`output/`, `eps-us/InputData/elec/`, `state-eps-data-repository/<state>/elec/`, etc.). Never write project files to `Downloads/`. External cross-session caches (e.g., `Downloads/ninja_cache/`) are OK to leave outside the project — but anything new the project produces belongs in the project.
- **Before writing new pipeline code:** read `state_pipeline/run.py`, `state_pipeline/categories.py`, and the relevant reader. Ask "can I extend rather than replace?"
- **When the user says the previous state was working:** revert first, then make targeted edits. Do not rebuild from scratch.
- **When the user gives a one-line course-correction** (e.g., "use ResStock for residential"): treat it as the highest-priority signal. Apply it before continuing other debugging.
- **All derived outputs should be verified** against ResStock, ComStock, EFS, Cambium 2024, and EIA primary documentation before use in any work product.

---

## 10. Open issues / TODOs

### Completed (kept for context)
- [x] ~~**Migrate state pipeline to `cluster_days_repday`.**~~ Done 2026-05-15 — `state_pipeline/run.py` and presets (US-VA, US-MO) updated. Same methodology as national.
- [x] ~~**Populate datacenters SHELF.**~~ Done 2026-05-15 — flat 24/7 shape (LF = 1/8760 per cell). Annual energy comes from BCEU/AEO.
- [x] ~~**DECISIONS.md.**~~ Created 2026-05-15. See `DECISIONS.md` at project root for calibration-decision history.
- [x] ~~**State-specific EIA CF calibration for state SYSHECFs.**~~ Done 2026-05-15. `scripts/fetch_eia_state_cfs.py` downloads all 51 state XLSX files, parses Sheet 15 + Sheet 19, writes `data/eia_state_cfs.csv`. `state_pipeline/builders/syshecf_builder.build_all_syshecf` accepts `state_cf_targets` parameter; `state_pipeline/run.py` auto-loads per state from the CSV. State pipeline now applies state-specific EIA calibration (e.g., ND onshore-wind 0.388, CA solar-pv 0.263, VA solar-pv 0.202).
- [x] ~~**National SYSHECF + SHELF self-contained workbooks.**~~ Done 2026-05-22. `scripts/build_syshecf_workbook.py` and `scripts/build_shelf_workbook.py` produce the canonical eps-us xlsx files (`Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx` and `Seasonal Hourly Equipment Load Factors by End Use.xlsx`) with About tab, source-data tabs, computed-formula output tabs, dark-blue tab colors. Verified: 5e-11 (SYSHECF) and 5e-14 (SHELF) max abs diff vs CSV ground truth.
- [x] ~~**Consolidate clustering across US + non-US pipelines.**~~ Done 2026-05-22. `energy_timeslice_pipeline.cluster_timeslices` now wraps `state_pipeline.builders.clustering_repday.cluster_days_repday`. Added Southern Hemisphere support via `_hemisphere_season_months(country)` + `SOUTHERN_HEMISPHERE_COUNTRIES` set. See DECISIONS.md 2026-05-22 entry.

### Open — to pick up next (loosely highest-leverage first)

- [ ] **Run a full end-to-end non-US pipeline to verify the clustering consolidation.** China, South Korea, Brazil, or Australia would be the smoke test. Needs external data: DemandCast (real demand), Mendeley dataset (end-use shapes), Ember (annual CFs), Renewables.ninja (weather → VRE). Entry point: `energy_timeslice_pipeline.generate_full_pipeline_for_preset(country='Brazil', ...)`. The clustering layer is consolidated (single canonical algorithm with hemisphere awareness) but no non-US run has been executed since the consolidation. **Quickest validation:** pick Brazil (smallest data footprint of the SH presets) and run a single year end-to-end. Verify (1) no exceptions, (2) Summer Peak DOYs fall in Dec–Feb (SH summer), (3) days_per_timeslice sums to 365.

- [ ] **Port the self-contained-workbook pattern to non-US.** Currently only the US national has the rich "About + raw-source-tabs + computed-formula output tabs" treatment (`scripts/build_syshecf_workbook.py`, `scripts/build_shelf_workbook.py`). Non-US still uses the legacy CSV-write pattern in `energy_timeslice_pipeline.py::export_to_excel`. Approach: parameterize the build script(s) by country + source-data paths, drop into per-country output directories. See `build-input-xlsx` skill at `~/.claude/skills/build-input-xlsx/SKILL.md` for the canonical workbook pattern.

- [ ] **Port self-contained-workbook pattern to the 48 US states.** Currently state runs only produce the simpler per-CSV-tab xlsx files (via `scripts/build_xlsx_per_csv.py`). For full parity with the US national workbooks, would need per-state Cambium 2022 hourly + per-state ResStock/ComStock pasted into each state's workbook. File-size implications: ~1M cells × 48 states is a lot of disk; consider whether each state needs the full Cambium paste, or just summary source columns.

- [ ] **Extend `SOUTHERN_HEMISPHERE_COUNTRIES` set as new presets are added.** Current list (10 countries): Argentina, Australia, Bolivia, Brazil, Chile, New Zealand, Paraguay, Peru, South Africa, Uruguay. Anything outside this set defaults to Northern Hemisphere season months. Edit `energy_timeslice_pipeline.py::SOUTHERN_HEMISPHERE_COUNTRIES` to add. For mixed-hemisphere countries (none in current preset list), case-by-case judgment needed.

- [ ] **Annual category totals tab in SHELF workbook is informational only.** Edits to it don't propagate into the LF math (LFs are self-normalized per category, so the workbook's outputs are independent of the annual totals). If you want this tab to drive demand normalization downstream, that requires model integration — currently the EPS model uses its own BCEU/AEO annual values, not the SHELF workbook's totals. Document this clearly if a user expects edits to flow through.

- [ ] **Re-run state-level Cambium when 2024 state-level files become available.** State pipeline currently uses Cambium 2022 per-state. National uses Cambium 2024. Once Cambium 2024 state files become available from NREL data lake, update state presets' `cambium_hourly_csv` paths and re-run `python scripts/run_all_states.py`. SYSHECFs in particular benefit because state-level Cambium 2024 will reflect 2024 fleet + 2012 weather rather than 2022 fleet projections.

- [ ] **Bump 2025 end-use demand 4,170 → 4,300 TWh.** Captures additional data-center / electrification growth not in current AEO Reference vintage. Adds ~17 GW to SP slice peak. Deferred — currently within calibration tolerance.

- [ ] **Verify VRE capacity matches no-IRA scenario.** If eps-us 2025 BAU uses Cambium 2024 MidCase VRE buildout (~160 GW UPV, ~181 GW wind), that reflects with-IRA scenario. No-IRA should be lower (~100 GW UPV, ~140 GW wind). Less VRE → less subtraction → higher net peak (~+30–40 GW). Deferred pending modeling-team confirmation of intended VRE capacity vintage.

- [ ] **Revise the Limited/Reference supply-curve deployment scalars.** See DECISIONS.md 2026-05-15 entry "Limited/Reference supply curve ratios are misleading for deployment scaling." Solar's × 0.45 multiplier is dramatically over-constraining at any realistic deployment level. Recommendation (with user concurrence that "Limited Access ≈ reality"): drop solar scalar entirely (or use × 0.95 token); keep onshore wind at × 0.53 OR switch to deployment-tier scaling (× 0.90 below 500 GW, × 0.70 from 500–1500 GW, × 0.50 above); keep offshore wind at × 0.74. Analysis script: `scripts/analyze_supply_curve_bins.py`. No code change made yet — this needs to be wired into the EPS Vensim model's deployment-projection logic.

- [ ] **Refine commercial-lighting / commercial-other split.** ComStock provides both, but EFS-derived fallback uses identical shape for both. Currently using ComStock at national level; check state pipeline.

- [ ] **Industry shape mode default.** State pipeline uses `flat`; consider `cambium_residual` for high-VRE states where industry residual matches Cambium busbar minus buildings.

- [ ] **Add national preset YAML** under `state_pipeline/presets/US.yml` so `rebuild_us_national_v2.py` becomes a thin entry point matching the state pattern.

### Notes for picking up these TODOs

- Anything touching the SHELF/SYSHECF workbook structure → use the `build-input-xlsx` skill at `~/.claude/skills/build-input-xlsx/SKILL.md`. The skill encodes the conventions (About tab format, VLOOKUP not XLOOKUP, dark-blue output tabs, etc.) that took several iterations to land.
- Anything touching clustering → read `CLUSTERING_METHODOLOGY.md` at project root first. It's the canonical methodology reference.
- Before running any non-US pipeline, verify the data fetcher dependencies are accessible (DemandCast, Mendeley, Ember, Renewables.ninja). Some require API keys or paid access; check `data/manual_downloads/` for already-downloaded artifacts.
- Validate all derived outputs against primary sources before use in any work product. The verification scripts (`scripts/verify_syshecf_workbook.py`, `scripts/verify_shelf_workbook.py`) are templates for this pattern.

---

## 11. Latest calibration state — 2026-05-15

US national reference run (BAU 2025, no-IRA scenario):

| Metric | Value | Reference |
|---|---|---|
| Annual end-use demand | 4,170 TWh | EIA 2025 retail-equiv. ~4,160 TWh ✓ |
| SP slice gross peak | ~640 GW @ hr 16 | Cambium 745 GW; gap -13% |
| SP slice net peak | **577 GW** | Cambium ref 608; gap -5% |
| Implied VRE subtraction @ SP peak | ~63 GW | Cambium has 144 GW (more VRE) |
| `days_per_timeslice` | 61/121/112/50/11/10 | from `cluster_days_repday` |
| SYSHECF annual CFs | Calibrated to EIA Table 4.8.B targets | (see §1) |
| SHELF balance | 1.000 for all 14 non-zero categories | ✓ |

Calibration considered **complete for this round.** Remaining gap items in TODOs are deferred — within tolerance for reliability-mechanism analysis.

See `DECISIONS.md` for the decision history that produced this state.

---

*Last updated: 2026-05-15*
*Maintained by: Energy Innovation modeling team. All derived inputs are for staff review and should be verified against primary sources before use in any work product.*
