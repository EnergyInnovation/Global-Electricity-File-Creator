# Updating File Structure — Non-US Workbook-Source CSV Export

*Drafted 2026-07-06. **Implemented 2026-07-07** — see "As built" below for the
final design, which refines the original plan in two places.*

## Goal

Update how the pipeline outputs data from `run_pipeline.py` so that its hourly
source data is saved in the **same format as the source tabs in the eps-us
xlsx files** at `C:\Users\Claire Trevisan\GitHub\eps-us\InputData\elec`:

- Hourly end-use demand → same layout as the **ResStock national source** tab
  in `Seasonal Hourly Equipment Load Factors by End Use.xlsx` (SHELF workbook).
- Hourly capacity factors → same layout as the **Cambium hourly source** tab in
  `Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx`
  (SYSHECF workbook), including the timestamp column and all `CF_<tech>`
  columns populated with the hourly CFs calculated by the international
  workflow.

The outputs are CSVs that can be manually copied into the workbooks, or
consumed by the `build-input-xlsx` skill to build per-region workbooks.

## As built (2026-07-07)

`export_workbook_source_csvs(...)` in `energy_timeslice_pipeline.py`, called
automatically at the end of every `run_pipeline` run (all regions, US and
non-US), writes to `output/<Country>_timeslice_results_EPS/workbook_sources/`:

| File | Contents |
|---|---|
| `demand_hourly_source.csv` | `timestamp` (`YYYY-MM-DD HH:MM`), **raw pipeline end-use columns** (`residential_heating`, `service_cooling`, `transport_ldv`, …), then `day_of_year`, `hour_of_day`, `slice` (EPS label). ResStock-tab layout. |
| `cf_hourly_source.csv` | `timestamp`, `load`, `net_load`, `solar_gen`, `wind_gen`, `solar_cf`, `wind_cf`, derived columns, then **one `CF_<tech>` column per SYSHECF tech** (26): hourly series for pipeline-derived techs (solar-pv, solar-pv-dist ×0.70, onshore-wind, offshore-wind), template 6×24 tables expanded to hourly via each hour's (slice, hour_of_day) for the rest. Cambium-tab layout, single header row. |
| `clustering.csv` | `doy`, `slice` (365 rows) plus per-slice `slice_name`, `days`, `rep_doy` in the first six rows. Feeds the workbook Clustering tab (slice VLOOKUP + representative-day lookups). |
| `annual_category_totals.csv` | Informational annual MWh per demand column. |

Verification: `python scripts/verify_workbook_sources.py [<run>_EPS dir]`
re-applies the representative-day math to the source CSVs and compares every
cell against the exported `SHELF-*.csv` / `SYSHECF-*.csv` (max abs diff must be
float noise, NaN-blank ≡ 0 for all-zero categories).

Workbook building: `scripts/build_us_run_workbooks.py` consumes these CSVs and
builds the two self-contained USA workbooks (About / Clustering / source tabs /
dark-blue formula-driven output tabs, verified to 1e-16). Parameterizing it
for other countries is the remaining open step (see below).

### Refinements vs. the original plan

1. **The export math is representative-day, not slice-mean.** Each SHELF/
   SYSHECF cell is the slice's representative day's hourly value (SHELF:
   divided by the column's annual sum) — so workbook formulas use
   `SUMIFS`/`AVERAGEIFS` keyed on `day_of_year = rep_doy(slice)`, not
   slice-hour averages, and `clustering.csv` carries `rep_doy` per slice.
2. **`demand_hourly_source.csv` holds raw pipeline columns, not per-category
   resolved series.** Under rep-day math, `template_split` categories
   (commercial-lighting/appliances/other; aircraft/rail/ships/motorbikes)
   cannot be represented as a single pre-resolved hourly column whose
   `pick/SUM` reproduces the published CSV — the aggregate is a *sum of
   individually normalized* load factors, weighted per cell by the EPS
   template tables. Resolution therefore stays in the workbook formulas
   (aggregate LF × template weight), with the EPS template tables pasted into
   a "Split templates" tab. `EPS_export_coverage.csv` documents which
   mode produced each file for a given run.

### Decision points (as resolved)

1. **One demand source CSV** (single calibrated demand source per region). ✔
2. **All techs get a `CF_` column** — template techs expanded hourly so the
   whole SYSHECF workbook derives from one source tab. ✔
3. **No Cambium-style 6-row metadata preamble** — single header row. ✔

## Region-generic workbook builder (done 2026-07-08)

`scripts/build_run_workbooks.py <country>` builds both self-contained
workbooks for any region from its `workbook_sources/` CSVs (e.g.
`python scripts/build_run_workbooks.py China`). It resolves each SHELF
category from `EPS_SHELF_FILE_MAP` against the columns actually present in the
region's demand CSV — verified to match the pipeline's own resolution
(`EPS_export_coverage.csv`) 22/22 for China — and reuses the US builder's tab
helpers (About / Clustering / Split templates / hourly source / dark-blue
formula tabs). SYSHECF tabs are formula-driven for the derived techs and
static for template techs. Built + verified for China 2026-07-08
(`scripts/verify_workbook_sources.py`: worst diff 1e-16, zero failures).
`scripts/build_us_run_workbooks.py` remains as the US-specific original.

---

*Outputs are inputs for staff review — verify derived values against primary
sources (Mendeley, DemandCast, Ember, Renewables.ninja, NREL EFS) before use
in any work product.*
