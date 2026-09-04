# Global Electricity File Creator

This project builds country-specific representative-day electricity inputs for EPS-style power-sector modeling.

Two lineages live in this repository and share **one** clustering implementation
(`state_pipeline/builders/clustering_repday.cluster_days_repday` — see
[`CLUSTERING_METHODOLOGY.md`](CLUSTERING_METHODOLOGY.md)):

- **International / country pipeline** — `energy_timeslice_pipeline.py`, driven by the user-facing
  runner `run_pipeline.py`. Builds SHELF + SYSHECF for any built-in country preset (United States,
  China, South Korea, and 9 more) from Zapata/Mendeley (non-US) or NREL EFS (US) demand shapes.
- **US national + per-state EPS pipeline** — `rebuild_us_national_v2.py` and the `state_pipeline/`
  package. Builds the canonical US EPS SHELF/SYSHECF from ResStock/ComStock/EFS/Cambium with EIA
  calibration. See [`CLAUDE.md`](CLAUDE.md).

The two main scripts are:

- `energy_timeslice_pipeline.py` — all international execution code
- `run_pipeline.py` — **the user-facing runner for the international pipeline; the only file you
  normally edit.** Designed to be usable by any team member who clones the repo: edit the documented
  CONFIG blocks at the top, then `python run_pipeline.py`.

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs the pipeline's own dependencies (pandas, scikit-learn, openpyxl, xlsxwriter,
matplotlib, etc.), the parquet cache backend (`pyarrow`), the Deflate64 codec for the EFS archive
(`inflate64`), and **DemandCast's transitive runtime dependencies** (`pycountry`,
`pycountry-convert`, `countryinfo`, `entsoe-py`, `timezonefinder`).

DemandCast is used as a git clone under `.vendor/demandcast/` rather than as an installable package —
its declared dependencies (~38 packages in `demandcast/pyproject.toml`) are not picked up
automatically. We pin only the subset needed for the currently verified country presets (United
States, South Korea, China). If you bring a new country preset online and see an error like
`No module named 'XYZ'`, add `XYZ` to `requirements.txt` and reinstall.

### 2. Stage data not auto-downloaded by the pipeline

See [Per-Country Manual Setup](#per-country-manual-setup) for the country you plan to run. Most data
files auto-download on first use; renewables.ninja weather CSVs, the EPS template tree, and the KROGD
demand files for South Korea must be staged manually.

### 3. Configure and run

Edit the settings at the top of [`run_pipeline.py`](run_pipeline.py) (country, year, calibration
method, plot toggle, cache toggle, etc.), then:

```bash
python run_pipeline.py
```

Outputs land under `output/<country>_timeslice_results*` and `output/<country>_timeslice_results_EPS/`.

> **Treat all citations, calibrated values, and derived capacity factors as starting points for
> review.** Verify against primary sources before treating any output as an EI deliverable. Contact
> **IT & Systems (itsystems@energyinnovation.org)** before installing new external dependencies or
> automating new data fetches.

## Configuring a run (`run_pipeline.py`)

`run_pipeline.py` is the single control surface for the international pipeline. All execution logic
lives in `energy_timeslice_pipeline.py`; you edit only the documented CONFIG blocks at the top of
`run_pipeline.py`. Every setting is documented inline in the file. The most-changed settings:

| Setting | Purpose | Default |
|---|---|---|
| `COUNTRY` | Which preset to build (name or alias, e.g. `'China'`, `'KR'`) | `'China'` |
| `YEAR` | Target year; `None` = preset default | `None` |
| `N_CLUSTERS` | Representative timeslices (EPS expects 6) | `6` |
| `CALIBRATION_METHOD` | Non-US demand-shape calibration (see below) | `'zapata_ridge_nnls'` |
| `LAMBDA_RIDGE` | EPS-prior anchoring strength for ridge NNLS | `1.0` |
| `MAKE_DIAGNOSTIC_PLOTS` | **Boolean** — write per-cluster plots comparing each representative day against the actual days in that cluster | `True` |
| `COMPARE_PINNED_UNPINNED` | Boolean — also report the unpinned NRMSE baseline | `False` |
| `CALIBRATION_ONLY` | Boolean — stop after calibration + overview plot | `False` |
| `USE_CACHE` / `VERBOSITY` / `DATA_DIR` | Performance / logging / data paths | — |

**Diagnostic cluster plots (kept by design).** With `MAKE_DIAGNOSTIC_PLOTS = True` the run writes
PNGs under `output/<country>_timeslice_results_plots/` showing, per timeslice, every assigned day as
a thin grey line, a 25–75th-percentile band, the cluster-mean profile, and (on the net-load plot) the
representative day overlaid in red. This is the visual "clusters vs. actual data" check, and it is
controlled solely by that boolean selector.

**Non-US calibration methods** (`CALIBRATION_METHOD`, applies to Zapata/Mendeley countries — the
default is `zapata_ridge_nnls`):
- `'zapata_ridge_nnls'` *(default)* — regenerate the four climate-sensitive end-uses (residential
  cooling/heating/lighting + service cooling) from country weather + HETUS occupancy + Forsythe
  daylength, align all 11 basis columns to EPS per-end-use MWh/year priors, then solve a
  ridge-regularized NNLS anchored to the EPS prior (`LAMBDA_RIDGE`). Requires the preset's
  `eps_prior_path`.
- `'zapata_nnls'` — same shape regeneration, plain monthly NNLS, no EPS-prior anchoring (can produce
  basis-collinearity zero-flips).
- `'level_seasonal'` — legacy multiplicative annual + seasonal scaling; shape unchanged.

The non-US calibration math and its data sources (DemandCast observed demand, Mendeley/Zapata
end-use shapes, Ember annual CF targets, Renewables.ninja weather) operate exactly as on the prior
`develop` branch. What changed in this trunk is only how the calibrated net-load series is **clustered**:
it now flows through the consolidated, hemisphere-aware `cluster_days_repday` (see
[`CLUSTERING_METHODOLOGY.md`](CLUSTERING_METHODOLOGY.md)).

**US-specific choices.** For United States runs the demand-shape source is NREL EFS, and the EFS
electrification × technology-advancement scenario and the RECS-based heating/cooling split are
US-only choices. These are surfaced in `run_pipeline.py` (Section 3 — EFS settings) with inline
documentation so a US run is configured from the same control surface as any other country.

## Primary Goals

The work in this thread focused on four overlapping goals:

1. Build representative-day electricity inputs for major countries.
2. Preserve investment-relevant reliability conditions, especially summer and winter peak or net-peak days.
3. Export results in the exact EPS-style `SHELF` and `SYSHECF` formats used by the downstream Vensim/EPS model.
4. Keep the workflow reproducible, automated, and country-driven.

## Current High-Level Workflow

The script now does the following:

1. Resolve a built-in country preset.
2. Choose a demand-shape source:
   - `United States` -> `EFS`
   - non-U.S. countries -> `Zapata/Mendeley`
3. Fetch real-world historical demand for calibration using DemandCast or the custom U.S. EIA path.
4. Download weather data and Ember annual data.
5. Build solar and wind hourly capacity factors and calibrate them to observed annual values.
6. Compute net load.
7. Cluster days into 6 representative timeslices.
8. Keep summer and winter peak days pinned.
9. Export generic outputs plus EPS-ready `SHELF` and `SYSHECF` files.
10. Report calibration and clustering RMSE/NRMSE metrics.

## Country Presets

The script has a built-in preset registry in `energy_timeslice_pipeline.py`.

Verified countries in this thread:

- `South Korea`
- `China`
- `United States`

Mapped but not fully revalidated in this thread:

- `Australia`
- `Brazil`
- `Canada`
- `France`
- `Germany`
- `India`
- `Japan`
- `Mexico`
- `United Kingdom`

### Capacity-factor levels (preset keys, added 2026-09-04)

The hourly SHAPES of the VRE tables come from weather / site simulations; their annual LEVELS
are set by a calibration target. By default that target is Ember (mean generation over mean
year-end capacity, last `last_n_years`), which is wrong wherever the Ember/IRENA capacity basis
does not match the generation basis (South Korea: capacity excludes self-consumption solar,
generation includes it). Three optional preset keys override the defaults; every value should
carry a `basis` and `source` so the About sheet and run log record where it came from.

| Key | Values | Effect |
|---|---|---|
| `solar_cf_target` | number, or `{'value', 'basis', 'source'}` | Annual level of the exported `SYSHECF-solar-pv` (utility-scale, i.e. the capacity the EPS holds in BHRaSYC/BPMCCS). Applied EX POST: net load and clustering keep the Ember fleet series, whose generation total is right. Falls back to Ember. |
| `distributed_solar_cf` | `{'target': cf, 'basis', 'source'}` or `{'ratio': r}` | Annual level of `SYSHECF-solar-pv-dist` (the EPS BDESC behind-the-meter capacity): the utility shape scaled to the national distributed CF, or by a fixed ratio. Falls back to the legacy `0.70 x` utility derate. |
| `wind_offshore_calibration` | `'uncalibrated'` (default), `'blend_scale'` (legacy), or an offshore CF target | With per-site simulations, Ember gives ONE fleet CF that is mostly onshore. Default keeps offshore at its raw hub-height simulation mean and levels onshore so the capacity-weighted blend still equals the fleet target; `blend_scale` scales both by the same factor (the pre-2026-09-04 behaviour, which stamped Korea's onshore fleet derate onto offshore: 0.32 -> 0.18). |
| `pinned_clustering_csv` | path to a saved `workbook_sources/clustering.csv` (runner: `PINNED_CLUSTERING_CSV`, `'recluster'` to override) | Freezes the day-to-slice assignment so a CF re-level changes only SYSHECF/ELCCAfR; SHELF stays byte-identical. South Korea pins `data/clustering_pins/KR_clustering_2026-08-13.csv`, the assignment its EPS dispatch calibration was fit on. |

Where to find national bases: South Korea — KEA/KNREC 신재생에너지 보급통계 splits solar capacity and
generation into 사업용 (utility, metered) and 자가용 (self-consumption; generation imputed at ~15.5%
utilisation). United States — EIA-923/860 utility-scale vs EIA-861M small-scale estimates. Other
countries — the national TSO/statistics office; IRENA alone cannot supply the split. See
`DECISIONS.md` 2026-09-04.

## Per-Country Manual Setup

The pipeline auto-downloads most inputs (Mendeley end-use shapes, Ember annual statistics, DemandCast for most non-U.S. demand series). A few inputs cannot be retrieved automatically and must be staged by hand. This section documents the manual steps for each country whose preset has been verified end-to-end.

> **Treat all citations and source URLs as starting points for review.** Verify license terms, dataset coverage, and unit conventions against the primary publishers before relying on derived results in any work product. If you need help arranging access or automating any of these fetches, contact **IT & Systems (itsystems@energyinnovation.org)**.

### Common to every country

These apply regardless of which country preset you run.

| Input | Manual? | Where it goes | Notes |
|---|---|---|---|
| Mendeley end-use dataset (Zapata/Khanna) | Auto | `data/mendeley/pmd2dchk44-1/` | Downloaded by the pipeline on first use. Source: `https://data.mendeley.com/datasets/pmd2dchk44/1` |
| Ember annual electricity data | Auto | `data/ember/yearly_full_release_long_format.csv` | Downloaded by the pipeline on first use. Source: `https://ember-energy.org/data/yearly-electricity-data/` |
| DemandCast helper repo | Auto (clone) — but its Python deps are **manual** | `.vendor/demandcast/` | The pipeline clones DemandCast on first use. Its transitive Python dependencies (`pycountry`, `pycountry-convert`, `countryinfo`, `entsoe-py`, `timezonefinder`) are pinned in `requirements.txt`. If you add a new DemandCast retriever, you may need to add its imports too. Source: `https://github.com/open-energy-transition/demandcast` |
| EPS template tree (`SHELF/`, `SYSHECF/`, RECS workbook) | **Manual** | `../EPS Structure Testing/InputData/elec/` (sibling of repo) | Provided by the EPS team — ask the colleague who set up your EPS Vensim environment. Required for U.S. heating/cooling split and for any template-based EPS export. |
| Renewables.ninja weather CSVs | **Manual** | `data/weather/ninja-weather-country-{ISO2}-{var}_area_wtd-merra2.csv` | Auto-download is blocked by the renewables.ninja server. Three files per country: `irradiance_surface`, `temperature`, `wind_speed`. Source portal: `https://www.renewables.ninja/`. License: CC-BY 4.0 (verify on the site). |

### United States

**Demand-shape source:** NREL Electrification Futures Study (EFS), Reference electrification × Moderate technology advancement.

**Manual steps:**

| # | Step | Notes |
|---|---|---|
| 1 | Set `EIA_API_KEY` in `.env` at the repo root | Free key from `https://www.eia.gov/opendata/`. Used by `_fetch_eia_us_national_series` to assemble hourly U.S. demand for calibration. |
| 2 | Download the three U.S. renewables.ninja files into `data/weather/` | `ninja-weather-country-US-temperature_area_wtd-merra2.csv`, `_wind_speed_`, `_irradiance_surface_`. ~400 MB total. |
| 3 | Confirm the EPS template tree is at `../EPS Structure Testing/InputData/elec/` | Specifically the SHELF folder containing `Seasonal Hourly Equipment Load Factors by End Use.xlsx` — this is the source of the RECS `CE8.2.M` and `CE8.3.M` tabs used to split EFS space-conditioning into heating vs. cooling. |
| 4 | (Optional) Pre-download `data/efs/EFSLoadProfile_Reference_Moderate.zip` | The pipeline auto-downloads this from `https://data.nlr.gov/system/files/126/EFSLoadProfile_Reference_Moderate.zip` (~291 MB) on first use. Pre-downloading saves the wait on first run. |
| 5 | Install `inflate64` (already in `requirements.txt`) | Needed by the `zipfile_deflate64.py` shim to read the EFS archive's Deflate64 entries. The shim ships with the repo. |

**Citations to verify against primary sources:**

- EFS dataset: NREL, *Electrification Futures Study*, OpenEI submission [`https://data.openei.org/submissions/8199`](https://data.openei.org/submissions/8199). Direct archive URL is hosted on the NREL data catalog.
- RECS tables: U.S. EIA, *Residential Energy Consumption Survey* monthly tables `CE8.2.M` (heating) and `CE8.3.M` (cooling). Original source: `https://www.eia.gov/consumption/residential/data/`.
- EIA hourly demand: U.S. EIA, *Hourly Electric Grid Monitor* via the v2 API.

**Known caveats to flag for staff:**

- The EFS dataset only contains the calendar years 2018, 2020, 2024, 2030, 2040, 2050. Other years are mapped to the nearest available year (e.g. a 2025 request resolves to 2024).
- The heating/cooling split currently uses **national** RECS multipliers and is applied identically to commercial space conditioning. This is a documented simplification — region- or census-division-specific multipliers would require additional RECS tabs.
- The pinned-peak-day clustering on the U.S. EFS run currently underperforms unpinned on annual net-load reconstruction NRMSE (`0.3891` vs `0.3473`). Pinned is preferred for investment realism, but this trade-off should be revisited if peak coverage matters less for a downstream use case.

### South Korea

**Demand-shape source:** Mendeley (Zapata/Khanna), region `Korea`.
**Demand calibration source:** DemandCast → KROGD (Korean Open Government Data).

**Manual steps:**

| # | Step | Notes |
|---|---|---|
| 1 | Download the three Korean renewables.ninja files into `data/weather/` | `ninja-weather-country-KR-temperature_area_wtd-merra2.csv`, `_wind_speed_`, `_irradiance_surface_`. |
| 2 | Download annual KROGD hourly demand CSVs into `data/manual_downloads/` | One file per calendar year of calibration history. File names must start with `KRO` (e.g. `KRO_demand_2025.csv`). The pipeline auto-mirrors them into the DemandCast clone on the next run — see below. |

**Single source of truth:** Maintain KRO files only in `data/manual_downloads/`. Each pipeline run automatically mirrors files matching the configured prefixes (currently `KRO`) into the DemandCast clone's manual-downloads folder via `_sync_manual_downloads_to_demandcast` in [`energy_timeslice_pipeline.py`](energy_timeslice_pipeline.py). The mirror is one-way (canonical → DemandCast clone), idempotent, and refreshes the destination only when source size or mtime changed. To bring a different DemandCast manual source online (e.g. Turkey EPIAS, India NITI), add the appropriate filename prefix to `DEMANDCAST_MANUAL_FILE_PREFIXES`.

**Why DemandCast is "manual" for Korea:**

DemandCast uses programmatic APIs for most non-U.S. countries (ENTSO-E for Europe, CENACE for Mexico, etc.) but its *only* registered Korean source is `krogd.py`, a manual-file-drop module. The Korea Power Exchange dataset on data.go.kr does not expose a clean public API, so DemandCast's authors implemented the source as "look in a folder for files starting with `KRO`." See the docstring at [`.vendor/demandcast/demandcast/retrievals/electricity_demand_data_sources/krogd.py`](.vendor/demandcast/demandcast/retrievals/electricity_demand_data_sources/krogd.py).

**Citations to verify against primary sources:**

- KROGD dataset: Korea Power Exchange (한국전력거래소 / KPX), *시간별 전력수요량* ("Hourly Electricity Demand"), data.go.kr dataset ID `15065266`, page: `https://www.data.go.kr/data/15065266/fileData.do`.
- File format: EUC-KR-encoded CSV. Header: `날짜,1시,2시,…,24시` (Date, Hour 1, …, Hour 24). One row per day; columns hold MW.
- DemandCast's stated coverage for KROGD: 2013-01-01 to 2024-12-31 (per krogd.py docstring). Files for 2025+ are extensions your team has done manually beyond what DemandCast tracks.

**Known caveats to flag for staff:**

- Each new calibration year requires a fresh manual download. The 4-year calibration window (`last_n_years=4` in the South Korea preset) means the calibration mean will lag the real most-recent-year by however long it's been since you last refreshed.
- Sanity-check each newly-downloaded file before committing it: confirm the first data row's date matches the filename year (data.go.kr exports have been observed to be mislabeled in past sessions), and strip any trailing all-comma blank row. If you strip blank rows manually, do it in **byte mode** to preserve the EUC-KR encoding of the Korean column headers.
- The DemandCast clone copy is now refreshed automatically by `_sync_manual_downloads_to_demandcast` on every run, so you only maintain `data/manual_downloads/`. If you ever notice that the clone copy has drifted (it shouldn't — the sync is idempotent), delete files in `.vendor/demandcast/demandcast/data/electricity_demand/manual_downloads/` and the next run will repopulate them from the canonical location.

### China

**Demand-shape source:** Mendeley (Zapata/Khanna), region `China +`.
**Demand calibration source:** **two sources, selected automatically from the run configuration.**

| Run configuration | Observed-demand source |
|---|---|
| `YEAR = 2018` **and** `LAST_N_YEARS = 1` (the China preset defaults) | DemandCast → Wu et al. (2023) Zenodo, auto-downloaded at runtime. Covers 2018 only, which is the only configuration it can serve. Kept as the default so the historical EPS-China run stays reproducible. |
| any other year or window | Yi et al. (2026) provincial hourly load, staged at `data/manual_downloads/CN_hourly_demand_2015_2024.csv`. Covers 2015–2024, so it is the only source that can serve a multi-year window or a post-2018 target year. |

The rule lives in `energy_timeslice_pipeline.resolve_demand_series_csv` and is driven by
the China preset's `demand_series_csv` + `demandcast_pin` keys. Override it for a single
run with `DEMAND_SERIES_CSV` in `run_pipeline.py` (`'demandcast'`, or a CSV path). The run
log prints which source was used, with its citation.

**Manual steps:**

| # | Step | Notes |
|---|---|---|
| 1 | Download the three Chinese renewables.ninja files into `data/weather/` | `ninja-weather-country-CN-temperature_area_wtd-merra2.csv`, `_wind_speed_`, `_irradiance_surface_`. ~260 MB total. |
| 2 | *(only if you need a year or window other than 2018/1)* Download the Yi et al. workbook from figshare and convert it | `python scripts/build_china_hourly_demand.py --source "<path>/Data output.xlsx"` → writes `data/manual_downloads/CN_hourly_demand_2015_2024.csv` plus a per-year coverage report. The source workbook is ~42 MB and is not committed. |

Step 1 is the only manual step for the default (2018) configuration — that calibration
demand series auto-downloads from Zenodo on first use.

**Citations to verify against primary sources:**

- China hourly demand, 2018 only: Wu, Y. et al., *Hourly electric power load dataset for China*, Zenodo, `https://zenodo.org/records/8322210`. License: CC-BY 4.0. Coverage **2018 only** (Jan 1 – Dec 31, 2018) — this is why the China preset's `default_year` is 2018 with `last_n_years=1`.
- China hourly demand, 2015–2024: Yi, B., Luo, Q., Zhang, S., Ji, Y., Yu, S. & Fan, Y. (2026). *Hourly electricity load curve dataset for Chinese provinces derived from meteorological variables.* **Scientific Data 13, 978.** https://doi.org/10.1038/s41597-026-07327-8 — data: figshare https://doi.org/10.6084/m9.figshare.29832701. License: **CC BY-NC-ND 4.0** (non-commercial, no derivatives — confirm this permits your intended use before publishing anything derived from it). 31 provincial-level regions, hourly, 2015–2024, GWh per hour.
- DemandCast retrieval module: [`.vendor/demandcast/demandcast/retrievals/electricity_demand_data_sources/wu_et_al.py`](.vendor/demandcast/demandcast/retrievals/electricity_demand_data_sources/wu_et_al.py).

**Known caveats to flag for staff:**

- **The two sources disagree on hourly shape even in 2018, the year they share.** Annual energy matches to 0.01 % (6,899 vs 6,900 TWh) but hourly correlation is only 0.83 (NRMSE 7.7 % of mean); February energy differs by +17.8 %, and the annual peak moves from Aug 8 to Jul 20. Switching sources makes China materially more summer-peaking. Full quantification: [`output/china_demand_source_test/RESULTS.md`](output/china_demand_source_test/RESULTS.md).
- **Both sources are reconstructions anchored to the same limited 2018 NDRC load data**, not independent measurements. Yi et al. extend it with meteorological regression (BAIT-based heating/cooling degree-days, province-specific power coefficients); Wu et al. use a different method. Neither is a metered national series.
- **Leap-year target years are currently broken.** `YEAR = 2024` produces a days-per-timeslice file summing to 366 rather than the 365 EPS expects. Prefer `YEAR = 2023` until that is fixed.
- The default configuration still uses **a single calibration year (2018)**, much narrower than other countries, so weather-driven demand variability is not averaged out. Widening the window (`LAST_N_YEARS = 4`) automatically switches to the Yi et al. source.
- The Mendeley region key is `China +`, not `China`. The trailing `+` reflects how the Zapata/Khanna dataset names a regional aggregate that includes a small set of neighbouring areas. Worth confirming that aggregate matches your modeling boundary before publication.

## Demand-Shape Source Logic

### Non-U.S.

Non-U.S. countries use the Zapata/Mendeley end-use dataset:

- Mendeley dataset URL:
  - `https://data.mendeley.com/public-api/zip/pmd2dchk44/download/1`

This source is used to build hourly end-use load shapes by sector and service/end use.

### United States

The U.S. now uses NREL Electrification Futures Study load-shape data:

- OpenEI source:
  - `https://data.openei.org/submissions/8199`
- Archive used:
  - `EFSLoadProfile_Reference_Moderate.zip`

Scenario choice:

- Electrification: `Reference`
- Technology advancement: `Moderate`

Available EFS years confirmed in the archive:

- `2018`
- `2020`
- `2024`
- `2030`
- `2040`
- `2050`

Current rule:

- if the requested U.S. year is not directly available, use the nearest EFS year
- example: a `2025` request maps to `2024`

### U.S. Heating/Cooling Split

EFS combines residential and commercial space conditioning, so heating and cooling must be split before export.

The current split method is:

- use EIA RECS monthly tables `CE8.2.M` and `CE8.3.M`
- derive monthly heating vs cooling multipliers from those tables
- apply the same monthly multipliers to commercial space conditioning

The RECS tables were read from:

- `C:\Users\RobbieOrvis\Models\EPS Structure Testing\InputData\elec\SHELF\Seasonal Hourly Equipment Load Factors by End Use.xlsx`
- tabs:
  - `RECS CE8.2.M`
  - `RECS CE8.3.M`

This is a monthly split, not yet submonthly or region-specific.

## Historical Demand Calibration

The script calibrates synthetic demand to real-world demand in two stages:

1. Simple level scaling to match observed average demand.
2. Seasonal calibration to better match observed monthly means and seasonal peaks.

This is stronger than the original annual-only scaling, but it is still not a full econometric weather-demand model.

## Capacity Factors

The script computes weather-based:

- `solar_cf`
- `wind_cf`

and calibrates them to observed annual values using Ember.

These calibrated renewable capacity factors are what feed `SYSHECF`.

## Clustering and Reliability Logic

The representative-day clustering is day-based, not hour-based.

Important current choices:

- exactly `6` timeslices
- `24` hours per representative day
- `Summer Peak` and `Winter Peak` are pinned

The clustering objective is now aligned with the earlier U.S.-only script:

- reconstruct the full hourly year from representative days
- evaluate `net_load` RMSE
- use normalized RMSE based on `std(original net_load)`

### Pinned-Day Improvement

Originally, pinned peak days only represented themselves.

This thread added a statistical reassignment step:

- keep pinned summer and winter peak days fixed as representative days
- test assigning additional same-season days into those pinned slices
- only accept a reassignment if it improves full-year net-load reconstruction NRMSE

This improved the pinned U.S. EFS case.

Recent U.S. result:

- pinned `year net-load NRMSE`: `0.3891`
- unpinned `year net-load NRMSE`: `0.3473`

So pinned still performs worse than unpinned on annual reconstruction, but materially better than before, while preserving reliability-relevant peak slices.

## Metrics

Metrics are written both to the terminal and to CSV.

Key metrics include:

- demand RMSE by stage:
  - raw
  - scaled
  - seasonally calibrated
- monthly mean RMSE
- monthly peak RMSE
- clustering reconstruction RMSE/NRMSE
- pinned vs unpinned net-load NRMSE comparison

Files:

- per-run:
  - `<run>_Metrics.csv`
- global summary:
  - `output/timeslice_run_metrics_summary.csv`

## Generic Outputs

The generic output set includes:

- `*_SYSHECF.csv`
- `*_SHELF.csv`
- `*_TimesliceInfo.csv`
- `*_TimesliceMap.csv`
- `*_Metrics.csv`

These are written under:

- `output/`

## EPS Export Work

The script now exports EPS-ready inputs in the exact family/file structure expected by the downstream model.

### SHELF

It writes:

- one CSV per end-use category
- fixed rows:
  - `Winter`
  - `Spring`
  - `Summer`
  - `Fall`
  - `Summer Peak`
  - `Winter Peak`
- columns:
  - `Hour0` ... `Hour23`

It also writes:

- `SHELF-days-per-timeslice.csv`

### SYSHECF

It writes:

- one CSV per technology
- same 6 row labels
- same 24 hourly columns

### EPS Workbooks

The script also writes two `.xlsx` workbooks:

- `Seasonal Hourly Equipment Load Factors by End Use.xlsx`
- `Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx`

Each workbook now includes:

- `About`
- all target EPS tabs
- `Coverage`
- `TimesliceInfo`
- `EPS_Label_Map`

### About Sheets

The `About` tabs were updated to explain the methodology used for each workbook.

For the U.S. `SHELF` workbook, the `About` sheet now explicitly states:

- EFS is the U.S. load-shape source
- RECS monthly multipliers are used to split heating/cooling
- demand is calibrated to observed data
- peak days are pinned

## EPS Mapping Rules Added

The EPS export mapping is now tighter than it was originally.

### SHELF mappings

Generated directly or derived:

- residential heating
- residential cooling
- residential lighting
- residential appliances
- residential other
- commercial heating
- commercial cooling
- commercial lighting
- commercial appliances
- commercial other
- `LDVs`
- `HDVs`
- `aircraft`
- `rail`
- `ships`
- `motorbikes`
- `industry`
- `district-heat-hydrogen`
- `geoeng`
- `datacenters`

Special rules:

- `datacenters`:
  - uniform annual load
  - every hour = `1/8760`
- `district-heat-hydrogen`:
  - follows industry
- `geoeng`:
  - follows industry
- residential/commercial envelope:
  - explicit zero tables

### SYSHECF mappings

Generated directly:

- `onshore-wind`
- `offshore-wind`
- `solar-pv`
- `solar-pv-dist`

Current distributed solar rule:

- `solar-pv-dist = solar_cf * 0.70`

This is an inferred rooftop-vs-utility derate chosen as a practical default, not a final region-specific rooftop model.

Many non-variable technologies in `SYSHECF` are still template-based rather than fully derived.

## Coverage Status

### SHELF

At this point, all `SHELF` files are generated.

The only intentionally zero categories are:

- `SHELF-residential-envelope`
- `SHELF-commercial-envelope`

### SYSHECF

Only a subset are currently generated from modeled data:

- wind-related tabs
- solar-related tabs

Most other `SYSHECF` tabs still copy the EPS template values.

## Data/Environment Work Done

### Installed or added

- Mendeley runtime download support
- DemandCast local bootstrap
- EIA API support for U.S. demand retrieval
- `openpyxl`
- `xlsxwriter`
- `zipfile-deflate64` for reading the EFS Deflate64 archive

### Local files used

- `.env` contains the EIA API key used in this thread
- project output goes to:
  - `output/`

## Important Output Examples

Representative recent output folders/files:

- `output/SouthKorea_timeslice_results_EPS/`
- `output/UnitedStates_EFS_test_EPS/`
- `output/UnitedStates_EFS_test.xlsx`
- `output/UnitedStates_EFS_test_Metrics.csv`

## Key Modeling Assumptions to Know

1. Representative days are a compression of the full year, not a full chronological production-cost model.
2. Pinned peak days are retained because the modeling goal is investment realism, not just average-year fit.
3. Non-U.S. load shapes still rely on Zapata/Mendeley.
4. U.S. load shapes now rely on EFS, but heating/cooling are split with national RECS monthly multipliers.
5. Distributed solar is still a simplified rooftop derate, not a dedicated rooftop solar model.
6. Many dispatchable/non-variable `SYSHECF` technologies are still template-based.

## What Another Thread Should Likely Do Next

Good next tasks:

1. Improve `SYSHECF` derivations for non-variable technologies instead of relying on templates.
2. Consider a better rooftop/distributed PV treatment than the current flat `0.70` derate.
3. Decide whether U.S. heating/cooling should use more granular regional or submonthly RECS-style splits.
4. Tune or constrain how many days pinned peak slices can absorb.
5. Continue hardening country presets for more major countries.
6. If needed, connect the EPS/Vensim-side model updates in a separate repository/thread.

## Short Summary

This repository now has:

- country presets
- automated downloads
- U.S.-specific EFS demand shapes
- non-U.S. Zapata/Mendeley demand shapes
- observed-demand calibration
- observed renewable calibration
- representative-day clustering with pinned peak logic
- RMSE/NRMSE reporting
- EPS-ready CSV and workbook exports
- methodology and coverage documentation embedded in the workbooks

This README is intended as a handoff document for a follow-up thread.
