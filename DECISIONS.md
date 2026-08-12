# Calibration Decisions Ledger

Running log of model-calibration decisions for the SHELF + SYSHECF pipeline.
Most-recent first. Each entry includes context, decision, and rationale —
designed to survive context summarization across Claude sessions.

See `CLAUDE.md` for the canonical methodology that these decisions inform.

---

## 2026-08-12 — Amendment: wind blend weights from EPS start-year capacities

### Context
The onshore/offshore SYSHECF split (2026-08-11 entry below) left the blended
`wind_cf` weighted by **site count** — 7 onshore + 3 offshore files for CN, 2 + 3
for KR. Those are artifacts of the fetch list in `scripts/fetch_ninja_sites.py`,
not of either fleet, and the blend is what anchors both per-type series to the
Ember fleet-wide wind CF. With `w_offshore` = 0.30 (CN) / 0.60 (KR) instead of
single-digit reality, the scale factor `Ember_target ÷ raw_blend` was off, biasing
**both** per-type levels: CN ~0.8% low, KR ~4.7% high.

Ember publishes no onshore/offshore breakdown (the yearly full release's
`Variable` column has only aggregate `Wind`), so `CF_fleet = w_on·CF_on +
w_off·CF_off` cannot be closed from the pipeline's own inputs — the site sims give
the CF ratio, but `w` must come from elsewhere.

### Decision
Take `w` from each region's own EPS model: sum the `onshore wind` and `offshore
wind` rows of `InputData/elec/BHRaSYC/BHRaSYC-StartYearCapacities.csv` across all
vintage columns (that sum *is* the technology's start-year capacity).

- New `scripts/fetch_eps_wind_capacity_split.py` extracts them and writes
  `data/eps_wind_capacity_split.csv`. Model checkouts live outside this repo at
  per-machine paths, so they're passed as `--model ISO2=PATH` rather than
  hardcoded; provenance is recorded as the model *folder name* plus the
  model-relative path so the checked-in CSV stays portable.
- New `load_eps_wind_capacity_split(iso2)` reads that lookup. Resolution order in
  `generate_full_pipeline_for_country`: explicit preset key `wind_capacity_split`
  → the CSV (by `iso2`) → site-count weighting. A status line reports which was
  used, with the MW and the source model.
- This follows the existing `scripts/fetch_eia_state_cfs.py` → `data/eia_state_cfs.csv`
  → auto-load-by-key pattern, so no shares are hardcoded in the presets.

Extracted (2026-08-12): **CN** 404,977 / 36,770 MW → 0.9168 / 0.0832
(`eps-china-igdp`, vintages 1998–2023); **KR** 1,708 / 94 MW → 0.9476 / 0.0524
(`eps-southkorea`, vintages 2016–2021).

### Rationale
The EPS model's start-year fleet is the *right* weighting rather than merely an
available one: these SYSHECF tables are dispatched against exactly that capacity
mix, so anchoring the blend to it keeps the fleet-average CF the model sees
consistent with the Ember observation. It is also an in-repo, re-derivable
number — no external citation to defend, and it updates automatically when the
model's capacities do. Sanity check against reality: CN's 441.7 GW total / 36.8 GW
offshore matches published end-2023 Chinese wind capacity, and KR's 1.80 GW
matches ~2021 — worth re-verifying against the model documentation, but the
magnitudes are right.

Note the vintage windows (CN through 2023, KR through 2021) differ from the
pipeline's Ember capacity window. That does not compound: only the *share* is
taken from the EPS model, while the CF *level* still comes from Ember.

### Affected files / variables
- `scripts/fetch_eps_wind_capacity_split.py` (new), `data/eps_wind_capacity_split.csv` (new).
- `energy_timeslice_pipeline.py`: new `DEFAULT_WIND_CAPACITY_SPLIT_CSV`,
  `load_eps_wind_capacity_split`; the `ninja_sites` branch resolves the split
  before calling the loader; CN + KR preset comments point at the lookup.

### Effect on model output
Per-type hourly annual-mean CFs — CN onshore 0.2157 → **0.2175**, offshore 0.2236
→ **0.2253**; KR onshore 0.1967 → **0.1867**, offshore 0.1790 → **0.1702**. The
blended `wind_cf` still lands on its Ember target (CN 0.2181, KR 0.1861) and the
offshore/onshore ratio is unchanged (CN 1.036, KR 0.910), as intended.

Because the blend's *shape* also changed, clustering moved: CN
`days_per_timeslice` 117/52/70/79/22/25 → **112/69/52/81/24/27** (sum 365); KR
68/83/92/40/18/64 → **68/83/93/40/18/63**, i.e. essentially unchanged. Net-load
annual mean is identical in both (CN 545,185 MW; KR 58,754 MW) — only the tails
shift. Every SHELF/SYSHECF table therefore differs slightly from the 2026-08-11
run for CN; re-export anything already handed off. Verified: both regions run
end-to-end, `SYSHECF-{onshore,offshore}-wind` reproduce exactly (0.0e+00) from a
rep-day reconstruction of `workbook_sources/cf_hourly_source.csv`, and
`scripts/verify_run_workbooks.py` passes 26/26 with the wind tabs derived from
their respective site-type columns. Inputs for staff review.

---

## 2026-08-11 — Separate onshore and offshore wind capacity factors in SYSHECF

### Context
`SYSHECF-onshore-wind` and `SYSHECF-offshore-wind` were written from the *same*
blended `wind_cf` column, so both EPS technologies received an identical 6×24
capacity-factor table. The Renewables.ninja per-site simulation outputs already
distinguish the two — `scripts/fetch_ninja_sites.py` picks a different turbine and
hub height per site (`Vestas V112 3000` @ 100 m onshore vs `V164 8000` @ 140 m
offshore) from each site's `type` — but the pipeline averaged all sites into one
series and discarded the distinction. This flagged in the CLAUDE.md caveat "a
single blended `wind_cf` currently feeds BOTH onshore- and offshore-wind SYSHECF
(per-tech site separation is a follow-up)."

The two site groups are not interchangeable. For China (10 sites × 2018–2024) the
annual levels are close (onshore 0.363, offshore 0.376 raw) but the *shapes* are
materially different: onshore has a pronounced overnight-max / mid-morning-min
diurnal cycle (0.392 at hr 0 vs 0.303 at hr 8) while offshore is much flatter
diurnally and peaks in the early morning; seasonally, onshore peaks in spring
(Apr–May ≈ 0.44) whereas offshore peaks in the winter monsoon (Dec ≈ 0.50) and
collapses in May (0.32). SYSHECF exists to carry exactly that shape into the
dispatch model.

### Decision
Classify every site file onshore vs offshore and carry three CF series instead of
one, for **all** regions on the `ninja_sites` wind path (China and South Korea
today, any future preset automatically):

1. **Classification** — `classify_wind_site(iso2, site_name)` reads the `type`
   field from `scripts/fetch_ninja_sites.py::SITES`, the same table that selected
   each site's turbine, so the type is never restated. Sites absent from that
   table fall back to a filename marker (`_OSW`, `Offshore`); unmarked → onshore.
2. **Loader** — `load_site_wind_capacity_factors` now returns a DataFrame:
   `wind_cf` (blended, unchanged definition when no capacity split is supplied),
   `wind_onshore_cf`, `wind_offshore_cf`. Per-type means are computed over that
   type's site-years only.
3. **Export** — `EPS_SYSHECF_FILE_MAP` routes onshore/offshore wind through a
   `first_available` spec: the site-type column when the run has one, else the
   blended `wind_cf`. Presets on the legacy 2 m-weather path are unaffected.
4. **Calibration** — Ember publishes only a fleet-wide wind CF, so the blend stays
   the anchored quantity. The per-type series are calibrated to `raw_type_mean ×
   (Ember_target ÷ raw_blend_mean)` — the *same* scale factor the blend needed —
   rather than each to the fleet target. Each still runs through
   `cap_redistribute`, so both stay bounded in [0, 1].
5. **New preset key / lookup** `wind_capacity_split` sets the installed-capacity
   weights for the blended `wind_cf`. See the 2026-08-12 amendment below for where
   those weights come from.

### Rationale
Calibrating each type independently to the Ember fleet CF would have forced
onshore and offshore to the same annual mean — reintroducing the problem in the
level dimension while only splitting the shape. Scaling both by the blend's factor
preserves the offshore/onshore CF ratio the site simulations imply, which is the
only physically grounded information available about their relative resource
quality, and keeps the capacity-weighted blend on the Ember anchor. The capacity
split is the one input that genuinely cannot be derived from the site data
(fleet-CF = capacity-weighted average of the two), so it is exposed as an explicit
preset key rather than assumed.

### Affected files / variables
- `energy_timeslice_pipeline.py`: new `WIND_SITE_TYPES`,
  `WIND_SITE_TYPE_CF_COLUMNS`, `_fetcher_wind_site_types`, `classify_wind_site`,
  `resolve_direct_cf_spec`; `load_site_wind_capacity_factors` returns a DataFrame
  and takes `capacity_split`; `generate_full_pipeline_for_country` takes
  `wind_capacity_split` and carries the per-type columns through `cf_df` →
  `cf_scaled` → `gen_df` → `cf_cols`; `EPS_SYSHECF_FILE_MAP` onshore/offshore
  entries; CN + KR preset comments.
- `scripts/build_run_workbooks.py`, `scripts/verify_run_workbooks.py`: use
  `resolve_direct_cf_spec` so the wind tabs stay formula-derived from the "CF
  hourly source" tab instead of being misclassified as borrowed tables.

### Effect on model output
China: `SYSHECF-onshore-wind` and `SYSHECF-offshore-wind` now differ by up to
0.128 CF (max|diff| across the 6×24 grid); hourly annual means 0.2158 / 0.2236
against the blended Ember target 0.2181. South Korea: max|diff| 0.083, means
0.1964 / 0.1788 against target 0.1861. Both tables reproduce exactly (0.0e+00)
from a rep-day reconstruction of `workbook_sources/cf_hourly_source.csv`.
Everything else — SHELF, clustering (CN 117/52/70/79/22/25), net load, solar — is
unchanged.

Two caveats for staff review, both pre-existing: (a) the placeholder site
coordinates in `fetch_ninja_sites.py::SITES` still need replacing with verified
fleet-region coordinates, and the onshore/offshore *classification* is only as
good as that site list; (b) the days-weighted annual CF of a 6-day rep-day table
differs from the hourly annual mean (CN offshore −12.5%, KR wind −25%, solar
+16–24%) — this is representative-day sampling error that has always applied to
every SYSHECF series, not a new artifact, but it is larger for offshore because
its seasonal cycle is stronger.

---

## 2026-07-10 — Fix: Zapata demand basis fails when target year is beyond the weather archive

### Context
`run_pipeline.py` for South Korea (default_year 2025, `zapata_ridge_nnls`) crashed in
`build_zapata_hybrid_basis` with "weather_df cannot be aligned to mendeley_df index without
NaN after reindex." Root cause: the Renewables.ninja weather archive ends in 2024, but the
Zapata shape regeneration filtered weather to the exact target year (`index.year == year`).
For year 2025 that yielded only the ~9 tz-spillover hours (UTC 2024 tail → local 2025), which
could not cover the full-year Mendeley demand index. China (target 2018, in-archive) was
unaffected, which is why only KR — and by extension every preset with a future target year —
was broken.

### Decision
Added `_zapata_weather_for_year(weather_naive, target_year, mendeley_index)` and routed both
Zapata branches (`zapata_nnls`, `zapata_ridge_nnls`) through it. If the target year is fully
present in the archive it is used as before (China bit-identical). Otherwise the most recent
full weather year (≤ target) is selected as a proxy and its calendar is relabeled to the
target year, aligned by (month, day, hour) so leap-year differences are handled; residual gaps
(e.g. a leap-day target against a non-leap proxy) are interpolated. A status line reports the
substitution.

### Rationale
The Zapata regeneration needs a representative weather *year* for the climate-sensitive shape,
not literally the model year — using the latest available weather year as a proxy is the
standard weather-year approach and keeps the demand shape physically grounded. Aligning by
month/day/hour rather than exact timestamp makes it robust to any target year.

### Affected files / variables
- `energy_timeslice_pipeline.py`: new `_zapata_weather_for_year`; both Zapata branches in
  `generate_full_pipeline_for_country` call it instead of the raw `index.year == year` filter.

### Effect on model output
South Korea now runs end-to-end: Zapata basis built on 8,760 hours (2024 weather relabeled to
2025); wind from 5 ninja sites × 2018–2024 calibrated to Ember 0.1861; days_per_timeslice
68/83/92/40/18/64 = 365; SHELF 23 + SYSHECF 26 written. China (target 2018) unchanged. All
"mapped" presets with default_year 2025 are similarly unblocked. Inputs for staff review.

---

## 2026-07-10 — Wind CF from Renewables.ninja per-site simulation outputs (China)

### Context
The non-US wind CF was built from the Renewables.ninja **weather** product — the 2 m
`wind_speed` variable — extrapolated to hub height with a log-shear profile and pushed
through a cubic power curve (`compute_wind_capacity_factor_from_weather`). QC of the raw
2 m series (`data/weather/wind speeds qc.xlsx`; full-record check across CN/KR/US)
confirmed the 2 m field has the **textbook near-surface diurnal cycle — afternoon max,
pre-dawn min** — which is *inverted* relative to turbine hub height (~100 m), where land
wind peaks overnight (nocturnal boundary-layer decoupling / low-level jet). This is a
MERRA-2 variable-choice issue, not a bug: U2M/V2M is a 2 m diagnostic dominated by surface
stability and carries none of the hub-height behavior. Extrapolating it up cannot recover
the correct time-of-day shape, and the calibration multipliers it forced were large
(China 7.18×; see 2026-07-08 entry). The area-weighting further dilutes toward non-windy
land rather than the actual fleet.

### Decision
For wind, stop translating 2 m wind speed to CF. Instead read the Renewables.ninja **wind
simulation output** for hand-picked sites in the main wind regions (hub-height, power-curve,
bias-corrected), average across sites, and use the `electricity` column (fetched with
`capacity=1`, so it IS the hourly CF) as `wind_cf`. **Solar is unchanged** (still the
weather product). Starting with **China**.

- New fetcher: `scripts/fetch_ninja_sites.py` — token-auth bulk download of the per-site
  wind API, one CSV per (site, year), 2018–2024, cached/resumable. China sites (7 onshore
  bases + 3 coastal offshore placeholders) live in `data/weather/ninja_sim/CN/`.
- New loader: `energy_timeslice_pipeline.load_site_wind_capacity_factors(iso2, n_years,
  sites_dir, country_timezone)` — selects the most recent `n_years` of site data actually
  present on disk, averages all site×year `electricity` series at each **UTC** hour, then
  `tz_convert`s to the preset timezone so it aligns with the localized weather.
- **Wind window is decoupled from the demand window** (amended same day — see below): wind
  uses its own `wind_cf_years` (default 7 = all of 2018–2024), independent of `last_n_years`
  (demand + Ember). The multi-year series is reduced to a day-of-year × hour climatology and
  mapped onto the run's calendar, so wind and demand need not use the same number of years.
- New preset keys: `wind_cf_source` (`'weather'` default | `'ninja_sites'`),
  `wind_sites_dir`, and `wind_cf_years`. **China and South Korea** set to `'ninja_sites'`
  with `wind_cf_years=7`. Runner override: `WIND_CF_YEARS` in `run_pipeline.py`.
- Calibration: site CF gives the **shape**; the annual mean is still calibrated to the
  **Ember** national wind CF via `cap_redistribute` (staff decision 2026-07-10, matching the
  US→EIA / non-US→Ember convention). The `ninja_sites` branch runs *before* the
  `speed_rescale` dispatch and takes precedence over it (speed_rescale is inapplicable —
  there is no wind-speed series for site CFs). Solar keeps the run's requested mode.

### Rationale
The site simulation output is the physically correct wind source: sheared to hub height and
bias-corrected against Global Wind Atlas / observations, so its diurnal and seasonal shape
is right where the 2 m product's is inverted. Averaging real fleet-region sites captures
siting; Ember calibration corrects the remaining prime-site high bias in the annual level.
UTC→local conversion keeps the wind index consistent with the localized demand/SHELF side.

### Affected files / variables
- `energy_timeslice_pipeline.py`: new `DEFAULT_WIND_SITES_DIR`,
  `load_site_wind_capacity_factors`; `wind_cf_source` + `wind_sites_dir` params on
  `generate_full_pipeline_for_country`; pass-through in `generate_full_pipeline_for_preset`;
  wind-CF swap after `compute_capacity_factors_from_weather`; new leading calibration branch;
  China preset keys.
- `scripts/fetch_ninja_sites.py` (new), `scripts/plot_wind_sites.py` (new country-generic QC map).
- Legacy 2 m path (`compute_wind_capacity_factor_from_weather`, `speed_rescale`) untouched
  and still the default for every other preset (`wind_cf_source='weather'`).

### Effect on model output
Verified end-to-end China 2018 run (with `CF_CALIBRATION_MODE='speed_rescale'` deliberately
set, to confirm the new branch overrides it). Site-averaged raw wind CF = 0.368 across 7
onshore sites; 8 boundary hours (0.09%) filled at the tz-offset window edge; Ember
calibration scaled the annual mean to the target 0.2181 with a **0.59× multiplier**
(vs the old 7.18× *up*-scale), residual +0.0000, 0% of hours pinned at cap. Resulting
onshore-wind SYSHECF now **peaks in the evening/overnight** (Summer hr 22, Fall hr 23,
Summer-Peak hr 18) and is seasonally winter-heavy (Winter 0.374 vs Summer 0.132) — the
correct hub-height climatology — vs the old 2 m path that peaked hr 11–15 with Spring pinned
at CF = 1.000. days_per_timeslice = 96/65/69/119/9/7 (sums to 365). Only China is switched;
all other presets are bit-identical. **All values are inputs for staff review** — the
placeholder site coordinates and the keep-Ember-calibration choice should be verified
against primary sources before use. Offshore CN sites and other countries (start with KR)
are follow-ups.

### Amendment (2026-07-10, same day) — decouple wind years via `wind_cf_years`; enable KR
The initial cut tied the wind window to the demand `last_n_years` (China = 1 year, 2018).
Superseded: wind now has its own `wind_cf_years` (preset key; runner override `WIND_CF_YEARS`),
defaulting to **7** for China and South Korea, independent of `last_n_years`. The loader takes
`n_years` and selects the most recent `n_years` **available** site-years (the ninja archive is
a weather climatology, not anchored to the model year); the multi-year series is reduced to a
day-of-year × hour climatology and mapped onto the run's calendar (which also removes the
UTC↔local boundary gap — the tz-shifted year tail wraps to fill opening hours, 0 NaN).
**South Korea** enabled with the same settings (KR currently has only 2022 on disk, so it
uses whatever years are present until more are fetched). China's full archive is now on disk:
**10 sites** (7 onshore + 3 offshore) × 2018–2024. Note the single blended `wind_cf` still
feeds BOTH onshore- and offshore-wind SYSHECF tables (offshore sites are now mixed into the
onshore table); per-tech onshore/offshore site separation is a follow-up. 7-year CN
climatology raw wind CF ≈ 0.367; diurnal peak hr 21 / trough hr 8 (smoother than the 1-year
cut). Affected: `load_site_wind_capacity_factors` signature (`n_years`); `wind_cf_years` param
+ climatology mapping in `generate_full_pipeline_for_country`; resolution/pass-through in
`generate_full_pipeline_for_preset`; `WIND_CF_YEARS` in `run_pipeline.py`; China + KR presets.

---

## 2026-07-08 — New CF calibration mode 'speed_rescale': calibrate wind in wind-speed space

### Context
The international pipeline's wind CF calibration multipliers are large (China 7.18×,
US 29.7×) because the synthetic wind CF is built by pushing a single **area-averaged
national wind speed** through a cubic power curve — compounding site-selection bias and
power-curve-of-the-mean (Jensen) averaging bias. `cap_redistribute` bounds the output but
pins 5.8% of China's hours at CF = 1.0 and distorts the shape linearly; `multiplicative`
produces CF > 1. HANDOFF.md → "Weather Data Improvements" ranks the causes.

### Decision
Add `cf_calibration_mode='speed_rescale'` (`calibrate_wind_cf_speed_rescale` in
`energy_timeslice_pipeline.py`): solve for the scalar `k` such that
`mean(power_curve(k × hub-height speed))` equals the Ember target, then recompute the wind
CF series from the rescaled speeds. Solar falls back to `cap_redistribute` under this mode
(its multiplier is ~1 and irradiance has no analogous "speed"). Solver detail: the mean CF
is **not monotone in k** (extreme k pushes speeds past the 25 m/s cut-out and the mean
collapses — for China 2018 it peaks near k≈4), so the solver grid-brackets the first upward
crossing of the target on a log-spaced k grid, then bisects; if no k reaches the target it
returns the max-mean series and flags `mean_unreachable`.

Not made a preset default anywhere — enable per run via `CF_CALIBRATION_MODE =
'speed_rescale'` in `run_pipeline.py` or a preset `cf_calibration_mode` field. Switching
China (or others) to it as default is a methodology decision for staff review.

### Rationale
The calibration acts where the biases act (the speed distribution, before the power
curve), so: output is bounded [0,1] by construction; calm hours stay near zero and the
ramp region stretches physically through the cubic curve instead of a linear stretch or
hour-pinning; and the remaining diagnostic (`speed_scale_k`) is interpretable as a
wind-speed bias factor.

### Affected files / variables
- `energy_timeslice_pipeline.py`: new `calibrate_wind_cf_speed_rescale`; dispatch in
  `generate_full_pipeline_for_country`; `speed_scale_k` added to the calibration
  diagnostic rows in `build_run_metrics`.
- `run_pipeline.py`: `CF_CALIBRATION_MODE` docs list the new mode.
- Existing modes untouched; runs not using `speed_rescale` are bit-identical.

### Effect on model output
China 2018 test (scratch run, not the delivered China outputs): k = 1.555 replaces the
7.18× CF-space multiplier; annual wind CF mean hits the Ember target 0.2181 to 3e-8;
max CF = 1.0 with 1.7% of hours at cap (vs 5.8% under cap_redistribute); zero-CF hours
preserved. Net-load clustering shifts as expected with the different wind shape (days
117/78/39/98/19/14 vs 112/61/52/104/24/12). Workbook-source verification passes unchanged
(worst 1e-16). All values remain inputs for staff review — a k of 1.55 still signals the
area-averaged wind-speed product underestimates fleet wind speeds ~35%; per-preset hub
height / power-curve updates and fleet-weighted weather remain the root-cause fixes
(HANDOFF.md).

---

## 2026-07-07 — Pin the US preset in run_pipeline.py to master-parity behavior (per-preset overrides)

### Context
After the develop→master international merge (feature branch), a US run via `run_pipeline.py`
produced different clustering outputs than the same run on `master` (net-load rep-day
reconstruction NRMSE 0.486 vs master's 0.389). The clustering algorithm itself
(`cluster_timeslices` → `cluster_days_repday`) is byte-identical between branches; the
divergence came entirely from changed *inputs and configuration*:
1. The US preset gained `'timezone': 'America/Chicago'`, so renewables.ninja weather was
   localized to CST before CF computation (master kept it in UTC) — shifting solar/wind
   hour-of-day profiles by 6 h and trimming the calibration window (17,544 → 17,538 hours).
2. `calibrate_capacity_factors` default changed from pure `'multiplicative'` scaling (master)
   to `'cap_redistribute'`. US wind's implied multiplier is ~29.7×, so cap-and-redistribute
   pins ~9% of hours at CF = 1.0 — a materially different wind shape, hence different net
   load, hence different day clusters.
3. `run_pipeline.py` defaulted `CALIBRATION_METHOD = 'zapata_ridge_nnls'` for every country,
   including the US (master only had level+seasonal demand calibration).

### Decision
Pin the US preset to master behavior via per-preset settings, resolved runner-override →
preset → global default (same pattern as the EFS overrides):
- US preset: no `'timezone'` key (weather stays UTC) + `'allow_utc_weather': True` to
  suppress the no-timezone warning for this deliberate opt-out;
  `'cf_calibration_mode': 'multiplicative'`; `'calibration_method': 'level_seasonal'`.
- South Korea / China presets: explicit `'calibration_method': 'zapata_ridge_nnls'` so they
  keep Zapata-ridge when the runner defers to preset defaults.
- `run_pipeline.py`: `CALIBRATION_METHOD = None` and `CF_CALIBRATION_MODE = None` now mean
  "use preset default"; non-None values still override for a run.
All international logic (timezone localization, cap_redistribute, Zapata calibration,
caching) is unchanged for non-US presets.

### Rationale
The US baseline from this script must stay comparable with the historical master outputs.
The canonical US EPS inputs come from the Cambium-based national pipeline
(`rebuild_us_national_v2.py` / `scripts/build_*_workbook.py`), not from this script, so
physical-validity concerns with multiplicative scaling (wind CF > 1.0 at 29.7× multiplier)
are accepted for baseline continuity here. If this script's US SYSHECF is ever handed
downstream, revisit the multiplicative pin.

### Affected files / variables
- `energy_timeslice_pipeline.py`: US/KR/CN preset dicts; `generate_full_pipeline_for_preset`
  (resolution of `cf_calibration_mode` / `calibration_method` / `allow_utc_weather`);
  `generate_full_pipeline_for_country` (new `allow_utc_weather` param gating the UTC warning).
- `run_pipeline.py`: `CALIBRATION_METHOD` / `CF_CALIBRATION_MODE` default to None (= preset).
- No changes to `state_pipeline/` or the US national rebuild.

### Effect on model output
US run from `run_pipeline.py` now reproduces the master US workflow **exactly**. Verified
2026-07-07 two independent ways:
1. A/B module capture: master's `energy_timeslice_pipeline.py` (byte copy) and the branch
   module were run side-by-side in the same environment with the clustering input DataFrame
   and hourly slice labels captured — all 29 input columns max-abs-diff 0.0, all 8,760
   labels identical, same days-per-timeslice (27/71/62/166/23/16). Clustering confirmed
   deterministic (identical across repeated runs and across processes).
2. The branch run's metric rows match the 2026-07-01 master baseline run
   (`C:\glb-elec-master\output\UnitedStates_master_baseline_Metrics.csv`) digit-for-digit,
   including clustering net-load NRMSE 0.5379105017265517.

Provenance warnings recorded while verifying (for staff review):
- The `UnitedStates` rows previously committed in `output/timeslice_run_metrics_summary.csv`
  (net-load NRMSE 0.3891...) came from the `UnitedStates_EFS_test` experiment run in
  `C:\glb-elec-master\output\`, NOT from the master baseline. Do not treat them as the
  master reference.
- eps-us `InputData/elec/SHELF/` (repo `eps-us`, branch as of 2026-07-07): the *committed*
  `SHELF-days-per-timeslice.csv` is the canonical Cambium-national clustering
  (61/121/112/50/11/10, matching the SHELF workbook's Clustering tab). The working tree has
  *uncommitted* modifications dated 2026-07-07 09:39 changing it to 45/78/75/136/18/13 — a
  clustering that matches no run found in either repo. Provenance unknown; verify before
  committing or using.
- The `run_pipeline.py` US workflow (EFS + DemandCast + renewables.ninja + Ember) is a
  different methodology from the Cambium-based national pipeline; its clustering is not
  expected to equal the Cambium national days (61/121/112/50/11/10). Canonical US EPS files
  still come from the national pipeline.

Non-US runs are bit-identical to before this change when the runner previously set
zapata_ridge_nnls / cap_redistribute explicitly (now the preset defaults).

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
