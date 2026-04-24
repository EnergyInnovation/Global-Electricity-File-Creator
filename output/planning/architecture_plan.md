# Architecture Plan: Subnational Extension of the Timeslice Pipeline

**Target file:** `energy_timeslice_pipeline.py`
**Scope:** Refactor from country-atomic runs to support US states / ISO-RTOs, Chinese grid regions, and a Korea data-source swap, without breaking existing country presets.
**Status:** Design only. No code is changed by this document.

---

## 0. Problem Statement (restated)

The current pipeline is country-atomic: a single string key (e.g. `'united states'`) routes every stage — demand fetch, weather load, Ember calibration, clustering, export filename — through one preset dict. To add `US-CA`, `US-CAISO`, `CN-grid-north`, etc., we need:

1. a richer entity identity (not just "country name"),
2. source-dispatch that varies by (entity, stage), not by country alone,
3. correct time-zone handling across heterogeneous data sources, and
4. a way to downscale national sources when subnational ones don't exist.

All of this must ship in phases that preserve the existing `United States`, `China`, and `South Korea` runs byte-identical at first and then re-route them to the new adapters after per-phase validation.

---

## 1. Entity Model

### 1.1 Recommendation: flat `region_code` keys with an explicit `parent_iso` field (no deep hierarchy)

**Options considered:**

- **Option A — Flat codes with parent reference:** `region_code` strings such as `US`, `US-CA`, `US-CAISO`, `CN`, `CN-GRID-NORTH`, `KR`. Each preset carries a `parent_iso` and inherits defaults through a shallow merge, not through a class hierarchy.
- **Option B — Hierarchical registry:** Nested dicts like `PRESETS['US']['subregions']['CA']`. Inheritance by tree walk.
- **Option C — Two registries:** `COUNTRY_PRESETS` + `SUBNATIONAL_PRESETS` sharing nothing.

**Recommend Option A.** Reasons:

- Flat keys match the filename conventions downstream (`US-CA_timeslice_results.xlsx`), match how BA codes are already published (EIA uses flat `CAISO`, `ERCOT`), and avoid ambiguity for pan-country regions like `CN-GRID-SOUTHERN` which span provinces.
- Hierarchy (B) forces every fetch function to know the tree depth. The current code only needs one lookup call; flat keys preserve that.
- A `parent_iso` pointer is enough to implement "fall back to national Ember if subnational unavailable" without a full tree.

**Code-naming convention:**

- Country-level: ISO-3166-1 alpha-2 (e.g. `US`, `CN`, `KR`, `DE`).
- First-order subregion: `{ISO2}-{SUBCODE}` where `SUBCODE` is:
  - US states: ISO-3166-2 subdivision (`US-CA`, `US-TX`, `US-NY`)
  - US ISO/RTO: uppercase BA code (`US-CAISO`, `US-ERCOT`, `US-PJM`, `US-MISO`, `US-SPP`, `US-NYISO`, `US-ISONE`)
  - China grid regions: `CN-GRID-NORTH`, `CN-GRID-NORTHEAST`, `CN-GRID-EAST`, `CN-GRID-CENTRAL`, `CN-GRID-NORTHWEST`, `CN-GRID-SOUTHERN`
  - Provinces (future): ISO-3166-2 (e.g. `CN-GD` for Guangdong)

### 1.2 Preset schema v2

```python
{
    # --- identity ---
    'region_code': 'US-CA',                  # primary key (new)
    'parent_iso': 'US',                      # ISO-2 of containing country (new)
    'subregion_type': 'state',               # 'country' | 'state' | 'province' | 'iso_rto' | 'ba' | 'grid_region' (new)
    'display_name': 'California',            # for metadata, About sheet, filenames
    'output_slug': 'US-CA',                  # filename-safe; used in output path
    'aliases': ['california', 'ca'],

    # --- geography / time ---
    'tz': 'America/Los_Angeles',             # IANA name (new, required)
    'dst_policy': 'keep_local_clock',        # 'keep_local_clock' | 'pure_utc' | 'ignore_dst' (new)
    'bbox': [-124.5, 32.5, -114.1, 42.0],    # [west, south, east, north] WGS84 (new, optional)
    'shapefile_ref': 'data/geo/us_states/CA.geojson',  # optional override to bbox (new)
    'solar_offset_hours': None,              # e.g. override solar-time for multi-TZ regions (new)

    # --- data-source bindings (new structure) ---
    'sources': {
        'demand_observed': {'adapter': 'eia_ba', 'respondent': 'CISO'},
        'demand_shape':    {'adapter': 'efs_state', 'state': 'CA', 'fallback': {'adapter': 'efs_national_share', 'share_key': 'eia_annual_load'}},
        'weather':         {'adapter': 'nsrdb_bbox'},
        'ember':           {'adapter': 'ember_country_share', 'share_key': 'eia_state_generation'},
        'recs_split':      {'adapter': 'recs_census_region', 'region': 'Pacific'},
    },

    # --- calibration / clustering parameters ---
    'ember_calibration_mode': 'share_of_national',   # 'subnational' | 'share_of_national' | 'skip'
    'season_months': {                                # auto-defaulted from latitude if absent
        'winter': [12, 1, 2],
        'summer': [6, 7, 8],
    },
    'n_timeslices': 6,

    # --- run controls (existing) ---
    'default_year': 2023,
    'last_n_years': 3,
    'status': 'draft',  # 'verified' | 'mapped' | 'draft'
}
```

### 1.3 Inheritance / defaults

A new resolver `resolve_preset(region_code)`:

1. Look up the region's preset dict.
2. If `parent_iso` present and any of `{tz, season_months, sources.ember, sources.recs_split, ...}` missing, shallow-merge from the parent preset. Parent merge is one-deep — no recursion needed for now.
3. Back-fill `season_months` from latitude if still absent (see §6).
4. Back-fill `tz` by raising a loud error. TZ is mandatory; silent defaults caused the current bug.

### 1.4 Backwards compatibility

Keep `COUNTRY_PRESETS` untouched by name; add a new `REGION_PRESETS` dict. The `get_country_preset(country)` function wraps `resolve_preset` and translates the legacy keys (`'united states'` → `'US'`, `'south korea'` → `'KR'`) through an alias table. Existing callers continue to work.

---

## 2. Data-Source Dispatch

### 2.1 Current state (problem)

Every stage has a hardcoded if/elif branch on country:

- `demand_shape_source == 'efs'` vs `'mendeley'` at line ~1395.
- `demand_country_code='USA'` hardcoded at line 1517 inside `_fetch_eia_us_national_series`.
- Weather uses `country_iso2` directly for a renewables.ninja URL.

### 2.2 Proposed: adapter registry keyed by (source_role, adapter_name)

```
SOURCE_ROLES = {
    'demand_observed',   # historical calibration target
    'demand_shape',      # synthetic hourly shape by end-use
    'weather',           # hourly weather for CF computation
    'ember',             # annual CF calibration
    'recs_split',        # heating/cooling ratio for EFS-style shapes
}
```

Each adapter is a class/function pair implementing a small protocol. Example signatures:

```python
class DemandObservedAdapter(Protocol):
    def fetch(self, preset: Preset, start_year: int, end_year: int) -> pd.Series:
        """Return tz-aware UTC Series named by region_code."""

class WeatherAdapter(Protocol):
    def load(self, preset: Preset, variables: Iterable[str], years: range) -> pd.DataFrame:
        """Return tz-aware DataFrame in UTC indexed hourly."""

class EmberAdapter(Protocol):
    def annual_cf(self, preset: Preset, variables: Iterable[str], last_n_years: int
                  ) -> tuple[dict[str, float], dict[str, float]]:
        """(capacity_GW, cf) dicts; may apply sub-national share internally."""
```

Registry lookup:

```python
ADAPTERS = {
    ('demand_observed', 'eia_national'): EiaNationalDemandAdapter(),
    ('demand_observed', 'eia_ba'):       EiaBaDemandAdapter(),        # NEW
    ('demand_observed', 'demandcast'):   DemandcastAdapter(),
    ('demand_observed', 'kpx'):          KpxAdapter(),                # NEW (Korea)
    ('demand_observed', 'cec_china_region'): CecChinaRegionAdapter(), # NEW

    ('demand_shape', 'efs_national'):    EfsNationalShapeAdapter(),
    ('demand_shape', 'efs_state'):       EfsStateShapeAdapter(),      # NEW if EFS state layer exists
    ('demand_shape', 'efs_national_share'): EfsNationalSharedAdapter(), # NEW downscale
    ('demand_shape', 'mendeley'):        MendeleyShapeAdapter(),

    ('weather', 'renewables_ninja_iso2'): NinjaCountryWeatherAdapter(),
    ('weather', 'nsrdb_bbox'):            NsrdbBboxWeatherAdapter(),  # NEW
    ('weather', 'era5_bbox'):             Era5BboxWeatherAdapter(),   # NEW

    ('ember', 'ember_country'):           EmberCountryAdapter(),
    ('ember', 'ember_country_share'):     EmberSharedAdapter(),       # NEW downscale via share key
    ('ember', 'ember_skip'):              EmberSkipAdapter(),

    ('recs_split', 'recs_national'):      RecsNationalSplitAdapter(),
    ('recs_split', 'recs_census_region'): RecsCensusRegionSplitAdapter(), # NEW
    ('recs_split', 'uniform'):            UniformSplitAdapter(),
}
```

### 2.3 Downscaling when subnational data is missing

The `*_share` adapters implement downscaling by applying a **share key** to a national or aggregate dataset:

```python
class EfsNationalSharedAdapter:
    def build(self, preset, year):
        national = EfsNationalShapeAdapter().build({'parent_iso': 'US'}, year)  # 8760 x sectors
        share_key = load_share_key(preset['sources']['demand_shape']['share_key'])
        # e.g. {'US-CA': {'residential': 0.12, 'industry': 0.08, ...}} or a single scalar
        return national.mul(share_key_for(preset['region_code']))
```

Share-key sources (catalogued in a new `data/share_keys/` directory, loaded on demand):

- `eia_state_generation`: per-state share of US generation from EIA Form 923 (annual).
- `eia_state_retail_sales`: state share of retail electricity sales by sector from EIA Form 861 (annual).
- `cec_china_region_generation`: China Electricity Council regional generation shares.

A share key is conceptually a CSV of `(region_code, sector, share)`. A scalar share is a degenerate case.

### 2.4 Where the dispatch is invoked

`generate_full_pipeline_for_preset` becomes thin:

```
preset = resolve_preset(region_code)
demand_obs = ADAPTERS[('demand_observed', preset['sources']['demand_observed']['adapter'])].fetch(...)
demand_shape = build_demand_shape(preset, year)   # handles adapter + fallback internally
weather = ADAPTERS[('weather', preset['sources']['weather']['adapter'])].load(...)
ember_caps, ember_cf = build_ember(preset, ...)
```

No more `if demand_shape_source == 'efs'` branches.

---

## 3. Time-Zone Correctness

### 3.1 Current bug surface

- `_fetch_eia_respondent_series` returns tz-aware UTC — good.
- `download_weather_files` pulls renewables.ninja files which are in UTC, parsed tz-aware at line 838 — good.
- Mendeley loader's timestamps are naive wall-clock, assumed to be local without any TZ tagging — bad.
- EFS `LocalHourID 1..8760` is mapped to a naive `pd.date_range(..., freq='h')` at line 1181 — interpreted as "local standard time" with no TZ stamp. Good enough for a flat-clock year but breaks the moment you merge with EIA data.
- Synthetic-year calibration merges by DOY+hour (`gen_df.groupby(['doy', 'hour'])` at line 2350) without checking TZ alignment.

### 3.2 Recommendation: pure-UTC internal pipeline, local TZ only at export

Rules:

1. **Every hourly Series or DataFrame in the pipeline MUST be `tz='UTC'` by the time it leaves its adapter.** Naive timestamps are a bug.
2. Each adapter is responsible for: reading raw data in whatever TZ it natively uses; `.tz_localize(preset['tz'])` if naive; `.tz_convert('UTC')` before returning.
3. A shared helper `assert_utc_hourly(series, name)` is called at every merge point (net load, calibration, clustering input). If anything fails, it raises with the source/adapter name.
4. Clustering, Ember calibration, and net-load all operate on UTC-indexed data. Seasonal month-labeling (`daily['timestamp'].dt.month`) uses `tz_convert(preset['tz'])` **only at the clustering step** for season assignment, nowhere else. This avoids e.g. labeling a California hour as July when it is still June in UTC.
5. At export, `TimesliceInfo` records the local timestamps (converted back). The CF/LF matrices are 24-hour-by-season and do not carry timestamps, so no conversion needed there.

### 3.3 DST handling

**Recommend: "pure-UTC internally, local-TZ at export"** — i.e. the pipeline never sees a 23- or 25-hour day. The EFS `LocalHourID` data, which currently represents a synthetic non-DST year, gets localized as `Etc/GMT+8` (standard time) for CA and converted to UTC. This treats EFS as a standard-time-year synthetic profile, which is what it actually is.

For observed data that genuinely has DST (EIA, KPX):

- Read in UTC from the API (EIA is already UTC).
- Never do `tz_localize` with `ambiguous='raise'`; use `'infer'` or hand the adapter a DST-handling flag.

Present seasons in local TZ but cluster in UTC — season boundaries are month-granular, so the off-by-one-hour at midnight on season boundaries is irrelevant.

### 3.4 China multi-TZ problem

All of China officially uses `Asia/Shanghai` (UTC+8). But in actual solar terms, Xinjiang (part of `CN-GRID-NORTHWEST`) is ~3 hours behind Shanghai. This matters for solar CF aggregation:

- Solar irradiance files (NSRDB/ERA5) come in local-solar or UTC, not civil time.
- If we treat `CN-GRID-NORTHWEST` as `Asia/Shanghai` and cluster against it, the solar CF peak will be at "hour 15" in the representative day instead of hour 13, which looks weird in the About text but is *correct* for a grid-operator-facing model (civil-time operations).

**Recommendation:** add an optional `solar_offset_hours` field on the preset. When set, the `weather` adapter shifts the resulting solar CF series by that offset *after* UTC localization and *before* the net-load computation. Default None (= use civil TZ). Document clearly.

For China specifically:

```
CN-GRID-NORTHWEST: tz=Asia/Shanghai, solar_offset_hours=None   # civil-time view (recommended default)
```

Do not paper over the issue by retagging as local solar time; that would make civil-time operations (demand) misalign.

---

## 4. Weather Pipeline

### 4.1 Current

`download_weather_files(country_code, variables, ...)` hits `renewables.ninja/country_downloads/{ISO2}/...`. There is no subnational path.

### 4.2 Target architecture

Keep renewables.ninja as the **country-level fallback**. Add two new adapters:

1. **NSRDB bbox adapter** (`nsrdb_bbox`) — NREL National Solar Radiation Database, covers the Americas at 4 km resolution. Fetch via the NREL API with a bounding box, area-weight pixels to an hourly series for the region. Good for US states.

2. **ERA5 bbox adapter** (`era5_bbox`) — Copernicus ERA5 hourly reanalysis (global, 0.25 deg). Use Climate Data Store API with `shapefile_ref` or `bbox`. Good for China grid regions, Korea (if KPX doesn't provide weather), and anywhere NSRDB doesn't cover.

### 4.3 Minimal integration spec

Both adapters output the same schema as the existing renewables.ninja loader:

```
pd.DataFrame(
    index=DatetimeIndex tz='UTC' hourly,
    columns=['irradiance_surface', 'temperature', 'wind_speed']
)
```

This means `compute_capacity_factors_from_weather` (line 1593) does not need to change. Only the loader does.

Common helper: `aggregate_weather_over_region(raw_grid_ds, bbox_or_shapefile, weights='area')`. Uses `xarray` for grid data. Cache aggregated results to `data/weather/{region_code}/` keyed by `{region_code}-{var}-{year}.nc` so re-runs don't re-aggregate.

Fallback chain, resolved at runtime:

```
if preset.sources.weather.adapter == 'renewables_ninja_iso2':
    try: ninja for ISO2
else:
    try: NSRDB or ERA5 for bbox
    except NoDataInRegion: fall back to ninja for parent_iso, warn loudly in metadata
```

The warning is recorded in the EPS export coverage report.

---

## 5. Calibration and Ember

### 5.1 Options

(a) **Share-of-national Ember** — multiply national Solar/Wind capacity and generation by a regional share key (state Solar installations from EIA Form 860; province Solar capacity from CEC for China). CF stays the national average.

(b) **Native subnational data** — use EIA Form 923 for US state generation + Form 860 for capacity → compute a true state-level CF. Use CEC regional capacity and generation for China. Preferred when data exists.

(c) **Skip Ember calibration** — trust the weather-modeled CF directly.

### 5.2 Recommendation: default (a) with opt-in (b), fall back to (c) only as escape hatch

- For US states / ISOs: start with (a) share-of-national. Validate by year and technology that the share is stable. Move to (b) when we integrate EIA-923 as a share-key source — that same data can become a full CF source with one more step.
- For Chinese grid regions: start with (a). Upgrade to (b) if CEC regional capacity/generation is machine-readable.
- For Korea national: (c) is fine — national Ember already works; the change is only the demand-observed swap.

**Tradeoffs:**

| Option | Pros | Cons |
|--------|------|------|
| (a) share | Cheap, reuses existing Ember data | Regional solar in the Southwest has a higher CF than US average — using national CF under-predicts CA solar |
| (b) native | Physically correct | New data integrations; more failure modes |
| (c) skip | Simplest | No anchor for CF, may drift with weather-model assumptions |

The `preset.ember_calibration_mode` field makes this switchable per preset. The `EmberSharedAdapter` handles (a); a new `EmberSubnationalAdapter` handles (b) when wired; `EmberSkipAdapter` is a noop.

---

## 6. Clustering and Seasons

### 6.1 Season parameterization

The current `winter_months = [11, 12, 1, 2]` and `summer_months = [6, 7, 8]` are hardcoded in `cluster_timeslices` (lines 3478–3481). This is wrong for the Southern Hemisphere (Australia, Brazil).

Proposed:

- `preset.season_months` is a mapping `{'winter': [...], 'summer': [...]}`.
- Default derivation by latitude (from bbox centroid):
  - `lat > 23.5`: Northern default `{winter: [12,1,2], summer: [6,7,8]}`
  - `lat < -23.5`: Southern default `{winter: [6,7,8], summer: [12,1,2]}`
  - `|lat| <= 23.5`: tropical — default both seasons to all 12 months and log a warning. Peak-day pinning still works (picks absolute peak regardless), but the "summer vs winter" season labels become less meaningful. Leave the mechanism in place and make the About sheet state "equatorial region — peak slices retained, season labels are nominal."
- `cluster_timeslices` loses the hardcoded defaults in favor of required kwargs populated from the preset.

### 6.2 Number of timeslices

Keep default 6 for downstream EPS compatibility. Make `n_timeslices` a preset field so future presets could request 8 or 12 if the downstream EPS structure is extended. **Recommendation: freeze at 6 for this refactor.** The downstream EPS workbook structure expects exactly `Winter, Spring, Summer, Fall, Summer Peak, Winter Peak` — changing timeslice count is an EPS-side refactor, out of scope here.

### 6.3 Solar-offset interaction

If `preset.solar_offset_hours` is set, it is applied to the weather data before CF derivation (see §3.4). Clustering itself operates on UTC-indexed net load; season-month tagging uses local civil TZ regardless of solar offset.

---

## 7. Export Layout

### 7.1 Current

`resolve_output_path` (line 1294) defaults to `output/{output_country}_timeslice_results.xlsx`. Filename = country-in-CamelCase. Subdirectory for EPS: `output/{base}_EPS/`.

### 7.2 Recommendation: nested by region, filename uses region code

```
output/
  US/
    US_timeslice_results.xlsx
    US_timeslice_results_EPS/...
    CA/
      US-CA_timeslice_results.xlsx
      US-CA_timeslice_results_EPS/...
    TX/
      US-TX_timeslice_results.xlsx
    CAISO/
      US-CAISO_timeslice_results.xlsx
  CN/
    CN_timeslice_results.xlsx
    GRID-NORTH/
      CN-GRID-NORTH_timeslice_results.xlsx
  KR/
    KR_timeslice_results.xlsx
```

**Rationale for `output/US/CA/` over flat `output/US-CA/`:**

- One parent directory per country keeps file explorers usable when there are 50 US states.
- The subregion-type slug (`CA`, `TX`, `CAISO`, `GRID-NORTH`) is unambiguous within its parent.
- Filenames still carry the full `region_code` (`US-CA_...`) so there is no ambiguity when files are moved.

A `resolve_output_path(region_code, output_path=None)` wrapper handles both shapes. Legacy country outputs stay in `output/` with the old filenames (§9) for transition.

### 7.3 EPS downstream labels

The EPS workbook `About` sheet, Coverage, TimesliceInfo, and EPS_Label_Map tabs all currently embed the country name. Make `_build_methodology_sheet` template-driven:

- A new module-level `EPS_ABOUT_TEMPLATES` dict keyed by preset.demand_shape adapter (`efs_national`, `efs_state`, `mendeley`, `kpx`, ...) supplies the methodology paragraphs.
- `run_metadata` (already passed around in `export_eps_input_tables`) is extended with `region_code`, `subregion_type`, `demand_observed_adapter`, `weather_adapter`, `ember_calibration_mode`, `tz`, `season_months`. The template interpolates these.
- The About sheet becomes: "Region: California (US-CA). Subregion type: state. Demand shape: EFS national profiles, downscaled to CA using EIA Form 861 sector shares. Observed demand: EIA BA CISO. Weather: NSRDB aggregated over CA bbox. Ember calibration: share of US national totals by state generation share. Time zone: America/Los_Angeles."

---

## 8. Migration Plan

Staged so that each phase is independently shippable and reversible. Existing country runs stay working at every step.

### Phase 1: Preset schema v2 (additive only)

**Changes:** introduce `REGION_PRESETS` with existing countries lifted over as `US`, `CN`, `KR`, `DE`, `FR`, ... Each new preset carries the new fields (`tz`, `subregion_type='country'`, `sources.*` adapters pointing at existing behavior). Keep `COUNTRY_PRESETS` and `get_country_preset` as a thin alias layer.

**Blast radius:** none — new data structure, old code untouched.
**Breaks:** nothing.
**Tests:** golden-file test that `United States`, `China`, `South Korea` runs produce byte-identical output pre/post this phase.

### Phase 2: TZ enforcement layer

**Changes:** add `assert_utc_hourly`. Audit every hourly series produced in the pipeline and ensure it is tz-aware UTC by the time it leaves its producer. Fix EFS and Mendeley loaders to emit tz-aware Series. Clustering seasonal labels compute in local tz explicitly.

**Blast radius:** medium. Every fetch + merge point.
**Breaks:** edge cases where the existing pipeline silently relied on naive-timestamp behavior. Expected surface: the `gen_df.groupby(['doy', 'hour'])` alignment at line 2350 will need to be either DOY-in-UTC or DOY-in-local; pick local (matches civil-year concept), document.
**Tests:**
- Assertion test that every intermediate Series in a KR, US, CN run is tz-aware UTC.
- Regression test on net-load peak timestamps for each country against the pre-refactor baseline (should move by at most a handful of hours for Mendeley-based presets; note and accept).
- New test: feed a synthetic Southern-Hemisphere preset (Australia) and verify summer/winter are swapped via §6.

### Phase 3: US ISO/state adapter

**Changes:** implement `EiaBaDemandAdapter`, `NsrdbBboxWeatherAdapter`, `EfsNationalSharedAdapter`, `EmberSharedAdapter`, `RecsCensusRegionSplitAdapter`. Add presets for US-CA, US-TX, US-NY, US-CAISO, US-ERCOT, US-PJM, US-MISO, US-SPP, US-NYISO, US-ISONE. Add share-key CSVs under `data/share_keys/`.

**Blast radius:** large but isolated — all new code behind a new adapter dispatch. The US national run uses the old adapters and is unaffected.
**Breaks:** nothing for existing presets.
**Tests:**
- Fetch test against EIA BA for CAISO for a known date range; check totals ≈ recorded CAISO daily MWh.
- End-to-end smoke test for US-CA, US-CAISO: produce SHELF + SYSHECF + EPS workbook, confirm coverage report has no missing mandatory files.
- Share-key sanity: sum(state shares) ≈ 1.0 ± tolerance for each sector.

### Phase 4: China grid-region adapter

**Changes:** implement `CecChinaRegionAdapter` (even if initially only CEC annual totals as a share key, use Mendeley national shape + downscale). Add 6 `CN-GRID-*` presets with bbox and `solar_offset_hours=None`. ERA5 weather adapter.

**Blast radius:** contained to new adapters + new presets.
**Breaks:** nothing.
**Tests:**
- Net-load peak day for CN-GRID-NORTH lands in summer (air-conditioning driven); CN-GRID-NORTHEAST in winter (heating driven). If not, calibration is wrong.
- Sum of 6 grid regions ≈ national China run to within share-key residual.

### Phase 5: Korea observed-data swap

**Changes:** implement `KpxAdapter`. Change `KR` preset's `sources.demand_observed` from `demandcast` to `kpx`. No subnational split.

**Blast radius:** one preset, one adapter. Completely isolated.
**Breaks:** the existing Korea run's calibration results will shift — this is expected and the *goal*. Metrics before/after should be recorded.
**Tests:**
- KPX fetcher returns 8760-ish hourly rows for a given year, correctly tz-localized from `Asia/Seoul`.
- Compare raw-demand annual total KPX vs. previous DemandCast/Mendeley source; delta documented in the run's Metrics CSV.

### Phase sequencing

```
Phase 1 ─────► Phase 2 ─┬─► Phase 3 ──► [ship]
                        ├─► Phase 4 ──► [ship]
                        └─► Phase 5 ──► [ship]
```

Phases 3, 4, 5 are independent after Phase 2 lands.

---

## 9. Backwards-Compatibility

### 9.1 Existing filenames

The downstream EPS workbook reads by filename. Concrete current outputs include `UnitedStates_EFS_test.xlsx`, `SouthKorea_timeslice_results.xlsx`, `China_timeslice_results_*`.

**Recommendation: dual-write for one release cycle.**

- After Phase 1–2, country runs write to both the old path (`output/UnitedStates_EFS_test.xlsx`) and the new nested path (`output/US/US_timeslice_results.xlsx`).
- The new path is added to the EPS model's reader; once confirmed, remove the old path in a later minor release.
- Subnational runs write *only* to the new nested path — there is no legacy consumer to support.

Implementation: `resolve_output_path` grows a `legacy_alias` kwarg. `generate_full_pipeline_for_preset` computes both paths for country-level runs and calls `export_to_excel` twice with different targets (cheap — same in-memory data). Mark the legacy copy as deprecated in the About sheet.

### 9.2 Preset name aliases

All current strings (`'south korea'`, `'united states'`, ...) continue to resolve — they map to `KR`, `US`, etc. in the alias table. No user-facing break at the CLI.

### 9.3 Metrics summary CSV

`output/timeslice_run_metrics_summary.csv` gets a new `region_code` column appended. Old rows are backfilled with the country name converted to ISO2. Downstream consumers of this CSV (if any — check) should use `region_code` going forward; `country` stays as a legacy column for one release.

---

## 10. Open Questions

These need answers from the data-inventory investigation or from the user before implementation begins:

1. **EFS state breakouts.** Does `EFSLoadProfile_Reference_Moderate.zip` contain a state-indexed column I missed? If yes, `EfsStateShapeAdapter` is a straight pivot; if no, we commit to `EfsNationalSharedAdapter` + EIA-861 share keys.

2. **EIA BA data completeness.** For CAISO/ERCOT/PJM/MISO/SPP/NYISO/ISONE, does the EIA API (same endpoint used at line 1452) return a clean hourly series back to 2015+? Any BAs with known gaps we should pre-fill?

3. **NSRDB access.** Do we have an NREL API key? NSRDB free tier rate-limits heavily; industrial-scale pulls may need a paid key or a pre-downloaded cache.

4. **ERA5 access.** Do we have a CDS API registration? Retrieval is rate-limited and queued; plan for ~minutes-per-request rather than seconds.

5. **CEC China data.** Is CEC regional capacity/generation available in a machine-readable form, or is it PDF only? If PDF-only, we commit to static share-key CSVs maintained by hand.

6. **KPX API credentials.** Is there a maintained KPX endpoint accessible outside Korea? Or do we need to use a cached dataset?

7. **Downstream EPS filename contract.** How hard is the EPS reader coupled to `UnitedStates_EFS_test.xlsx` specifically? If it is configurable, the dual-write migration in §9.1 is unnecessary.

8. **State-vs-BA preference for US.** Users might want `US-CA` (state administrative) and `US-CAISO` (balancing authority — overlaps ~75% with CA). Do we maintain both in parallel (recommended) or pick one? What should the EPS model consume?

9. **Solar-offset policy for China.** §3.4 recommends civil-TZ default with optional solar offset. Does the modeling team prefer the civil-TZ representation, or do they want solar-aligned representative days for investment realism in solar-heavy regions like the Northwest?

10. **Pinned-peak logic under tropical seasons.** If `winter_months == summer_months == range(1,13)`, the current pinned-peak reassignment code (lines 3611–3644) still works mechanically but "season" becomes meaningless. Do we keep the 6-slice schema or collapse to fewer for equatorial regions? Out of scope but flag before a Brazil/Indonesia preset ships.

11. **Cross-BA weather weighting.** CAISO covers most of California but also bits of NV and MX. Does the NSRDB bbox adapter use the BA footprint shapefile, the state shapefile, or a custom polygon? A `shapefile_ref` field is in the schema for this reason; we need the actual shapefiles.

---

## Appendix: Critical Files for Implementation

- `energy_timeslice_pipeline.py` — every module-level change lands here in phase 1; later phases may split this into a package (`pipeline/adapters/`, `pipeline/presets/`, `pipeline/clustering.py`, etc.). Splitting is optional; the file is already 208 KB and becoming hard to navigate, so a move to a package is advised when Phase 3 lands.
- `data/demandcast/demandcast/retrievals/electricity_demand_data_sources/*.yaml` — source of EIA subdivision codes already used at lines 1402–1414; will be re-used by `EiaBaDemandAdapter`.
- `data/share_keys/` (new) — share-key CSVs for state/region downscaling. Hand-maintained for v1.
- `data/geo/` (new) — shapefiles / GeoJSON for regions where bbox is insufficient.
- `output/timeslice_run_metrics_summary.csv` — add `region_code` column; consumer expectations should be re-verified.
