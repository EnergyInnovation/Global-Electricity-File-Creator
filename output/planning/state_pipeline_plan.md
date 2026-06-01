# State-Level SHELF + SYSHECF + Clustering Pipeline — Final Plan

**Status:** Plan v3 — locked; Sprint 1 ready to start.

---

## TL;DR

Build a Python pipeline (`state_pipeline/` package in this repo) that produces SHELF + SYSHECF CSVs and an annotated Excel workbook for each state by:

1. Reading **annual** electricity demand by end-use from the existing per-state EPS input files (BCEU, BIFUbC, trans/* calculator inputs)
2. Applying **hourly shapes** from ResStock TMY3 + ComStock TMY3 + EFS for non-building sectors
3. Reading **Cambium 2022 Mid-case state hourly + annual capacity** (anchor year 2024) for renewable CFs
4. **Internally computing** 8760 hourly net load from demand × shapes − renewable_gen
5. **Clustering** days into 6 timeslices with pinned peak days (top-5 average for robustness)
6. Outputting per-state SHELF + SYSHECF CSVs and an annotated Excel workbook

**No Vensim integration required** — pipeline reads EPS *input* files (not EPS outputs), so no chicken-egg with SHELF.

---

## Architecture

```
EPS state input files → annual demand by end-use         ─┐
                                                          ├─→ hourly demand
ResStock + ComStock + EFS → hourly shapes (LFs)           ─┘       ↓
                                                                   ↓
Cambium 2022 hourly + capacity → hourly renewable gen ─────────────┤
                                                                   ↓
                                                            net load (8760 h)
                                                                   ↓
                                                           clustering (6 slices,
                                                           pinned peaks via top-5 avg)
                                                                   ↓
                                                  SHELF + SYSHECF + days-per-timeslice
                                                                   ↓
                                                  CSV outputs + annotated Excel workbook
```

---

## Locked design decisions

### Category structure
- **22 SHELF categories** matching existing EPS conventions (5 residential building + 1 envelope + 5 commercial building + 1 envelope + 6 transportation + 1 industry + 3 other-sector)
- **26 SYSHECF categories** for generation techs (variable techs from Cambium, non-variable as templates)
- Defined in `state_pipeline/categories.py`

### EPS BCEU AEO mapping (locked)
| BCEU bucket | AEO end uses |
|---|---|
| residential-heating | Space Heating |
| residential-cooling | Space Cooling + **Furnace Fans** |
| residential-lighting | Lighting |
| residential-appliances | Water Heating + Refrigeration + Cooking + Clothes Dryers + Freezers + Clothes Washers + Dishwashers |
| residential-other | Other Uses + TVs + Computers |
| commercial-heating | Space Heating |
| commercial-cooling | Space Cooling + **Ventilation** |
| commercial-lighting | Lighting |
| commercial-appliances | Refrigeration + Cooking + Water Heating |
| commercial-other | Computing + Office Equipment + Other Uses |

### Demand sources by sector
| Sector | Input source | Annual extraction |
|---|---|---|
| Buildings (residential + commercial) | `state-eps-data-repository/{STATE}/InputData/bldgs/BCEU/BAU Components Energy Use.xlsx` | Direct read of BCEU-{urban,rural}-{residential,commercial}-{heating,cooling,lighting,appl,other} tabs for start year |
| Industry | `state-eps-data-repository/{STATE}/indst/BIFUbC/BIFUbC-electricity.csv` | Sum across NAICS/ISIC categories for start year |
| Transportation | `state-eps-data-repository/{STATE}/trans/*` | **Computed**: stock × loading × distance / fuel_economy × electricity_share, aggregated to 6 SHELF transportation categories (LDVs, HDVs, aircraft, rail, ships, motorbikes); MDVs aggregated into HDVs |
| Other (district-heat-hydrogen, geoeng, datacenters) | Various input folders (`dist-heat/`, `hydgn/`, `geoeng/`, `ccs/`, plus per-state DC source TBD) | Architected as input pipeline; values **= 0 for start year v1**, pipeline supports population once data integrated |

### Hourly shape sources
| Bucket | Shape source | Weather basis |
|---|---|---|
| Residential buildings | ResStock_Upgrade0 (state-level, 5 building types summed) | TMY3 |
| Commercial buildings | ComStock_tmy_release1 (state-level, 14 prototype types summed) | TMY3 |
| Industry | EFS Industrial subsectors (machine drives + other + process heat) | 2012 actual |
| Transportation | EFS Transportation per vehicle type | 2012 actual |
| Other (district-heat-hydrogen, geoeng) | Industry shape (existing pipeline convention) | 2012 actual |
| Data centers | Flat 1/8760 | n/a |

### SYSHECF source (Cambium 2022 Mid-case)
- **Hourly state CFs**: `data/cambium22_midcase_state_hourly/Cambium22_MidCase_hourly_{STATE}_2024.csv` (48 contiguous states; one file per state)
- **Annual capacity**: `data/cambium22_midcase_state_hourly/Cambium22_MidCase_annual_state.csv` (all states × all years)
- **CF derivation**: `cf[h, tech] = generation_<tech>_MWh[h] / capacity_<tech>_MW`
- **Curtailment**: state hourly file does not include explicit curtailment columns. v1 accepts post-curtailment generation as availability proxy. (Acceptable smell-test bias for VA where curtailment is low; flag for review on high-VRE states like CA/TX in validation.)
- **Variable techs** map to Cambium columns: `solar-pv ↔ upv_MWh`, `solar-pv-dist ↔ distpv_MWh`, `solar-thermal ↔ csp_MWh`, `onshore-wind ↔ wind-ons_MWh`, `offshore-wind ↔ wind-ofs_MWh`, `hydro ↔ hydro_MWh`, `pumped-hydro ↔ phs_MWh`, `nuclear ↔ nuclear_MWh`, `combined-cycle ↔ gas-cc_MWh`, `combined-cycle-CCS ↔ gas-cc-ccs_MWh`, `natural-gas-peaker ↔ gas-ct_MWh`, `hard-coal ↔ coal_MWh`, `hard-coal-CCS ↔ coal-ccs_MWh`, `biomass ↔ biomass_MWh`, `biomass-CCS ↔ beccs_MWh`, `geothermal ↔ geothermal_MWh`, `petroleum ↔ o-g-s_MWh`
- **Template-only** (non-variable, no Cambium counterpart): `lignite`, `lignite-CCS`, `heavy-or-residual-oil`, `crude-oil`, `hydrogen-CC`, `hydrogen-CT`, `SMR`, `MSW`, `steam-turbine`

### Time / calendar convention (locked)
- **Local Standard Time, hour-beginning**, no DST, **8760 hours/year**, **2018 non-leap calendar**
- Cambium files are re-indexed from "starts on Sunday 2012" convention to match
- ResStock/ComStock helper scripts already use this convention

### Weather year mismatch
- ResStock + ComStock = TMY3 (1991–2005 synthesized "typical" year)
- Cambium 2022 = 2012 actual weather
- **Accept and document** in Excel About sheet; revisit if validation flags issues
- v2 alternatives: NSRDB TMY3 + WIND Toolkit derived TMY (most rigorous) or ReEDS multi-year-mean (county-level, 2007–2013 + 2016–2023 averaged)

### Clustering
- 6 timeslices: Winter / Spring / Summer / Fall + Summer Peak + Winter Peak
- k-means on daily features: mean, max, p95, ramp_max
- Pinned peak days: **top-5 day average** per slice (not single coincident day) for robustness against weather-year noise
- Net load = total demand − (solar generation + wind generation)
- Output: timeslice assignment per day + days-per-timeslice + per-category SHELF (averaged over days within each slice)

### Coverage
| Geography | ResStock | ComStock | Cambium 2022 | Plan |
|---|---|---|---|---|
| 48 contiguous states | ✓ | ✓ | ✓ | Phases 1–4 |
| DC | ✓ | ✓ | ✗ (treat as MD/PJM proxy) | Phase 5 |
| HI | ✗ (need OEDI S3 fetch) | ✓ | ✗ (own grid) | Phase 5, custom SYSHECF |
| AK | ✗ (need OEDI S3 fetch) | ✓ | ✗ (own grid) | Phase 5, custom SYSHECF |

---

## Package structure

```
state_pipeline/
├── __init__.py                   # version + docstring
├── categories.py                 # 22 SHELF + 26 SYSHECF category registry (locked)
├── presets/
│   ├── US-VA.yml                 # VA preset (locked)
│   └── ... (US-CA.yml, US-TX.yml, etc.)
├── readers/
│   ├── bceu_reader.py            # BCEU.xlsx → annual demand by end-use
│   ├── industry_reader.py        # BIFUbC-electricity.csv → annual industry total
│   ├── transport_calculator.py   # trans/* → per-veh-type annual electricity → 6 SHELF transport categories
│   ├── resstock_reader.py        # ResStock state files → hourly residential by AEO bucket
│   ├── comstock_reader.py        # ComStock state files → hourly commercial by AEO bucket
│   └── efs_reader.py             # EFS state slice → hourly industry/transport shapes
├── fetchers/
│   └── cambium.py                # Cambium 2022 hourly + annual → CFs by tech
├── builders/
│   ├── demand_assembler.py       # combines annuals × shapes → 8760 hourly demand by category
│   ├── clustering.py             # net-load clustering, 6 slices, pinned peaks via top-5 avg
│   ├── shelf_builder.py          # clustering output → per-category SHELF LFs
│   └── syshecf_builder.py        # Cambium CFs → variable SYSHECF; templates → non-variable
├── exports/
│   ├── csv_writer.py             # write SHELF/SYSHECF/days-per-timeslice CSVs
│   └── excel_writer.py           # write annotated workbook per state
└── run.py                        # CLI: python -m state_pipeline.run --state US-VA
```

### Excel workbook per state (deliverable)

Tabs:
1. **About** — methodology, data sources, weather-year caveat, time-zone convention
2. **Sources** — vintage and URLs for ResStock release, ComStock release, Cambium 2022 release, EFS release
3. **Summarized Data** — hourly state-aggregated end-use loads (8760 rows × ~25 cols), with `EPS Timeslice Day` column from clustering
4. **Renewable CFs** — hourly Cambium-derived state-level CFs by tech with curtailment notes
5. **Net Load** — demand − renewable generation (clustering input)
6. **Timeslice Map** — per-day assignment + calendar date + system peak load
7. **SHELF-{category}** — one tab per SHELF category, mirrors the CSV
8. **SHELF-days-per-timeslice** — mirrors CSV
9. **SYSHECF-{tech}** — one tab per generation tech, mirrors CSV
10. **Validation** — annual energy by category vs EIA SEDS; peak day vs Cambium 2022; coverage notes

---

## Sprints

### Sprint 1 — Foundation + VA pilot (~2 weeks)
Build all 12 modules and run end-to-end for VA. Validate against existing VA prototype output and existing state-eps-data-repository VA SYSHECF. Output to `state-eps-data-repository/VA/elec/SHELF/_python_pipeline/` (parallel to existing files for safe A/B testing).

Order of implementation:
1. `readers/bceu_reader.py`
2. `readers/industry_reader.py`
3. `readers/transport_calculator.py`
4. `readers/resstock_reader.py`
5. `readers/comstock_reader.py`
6. `readers/efs_reader.py`
7. `fetchers/cambium.py`
8. `builders/demand_assembler.py`
9. `builders/clustering.py`
10. `builders/shelf_builder.py`
11. `builders/syshecf_builder.py`
12. `exports/csv_writer.py` + `exports/excel_writer.py`
13. `run.py` CLI

### Sprint 2 — Phase 1 states (~1 week)
Run pipeline for NC, CA, TX, NY. Per-state validation report. Iterate on edge cases:
- CA: high VRE, curtailment may be material → flag for v2 curtailment add-back
- TX: ERCOT, hot-summer-dominant
- NY: NYISO, winter-peaking electrification growth
- NC: VA's climate twin, sanity check

### Sprint 3 — Phase 2 states (~2 weeks)
Run remaining ~44 states + DC. Spot-check validation outputs. Fix state-specific issues.

### Sprint 4 — HI/AK (~1 week)
- Add OEDI S3 fetcher for ResStock HI/AK
- Custom SYSHECF for HI/AK (different grid, no Cambium coverage) — possibly use NSRDB TMY3 directly for these two
- Run + validate

### Sprint 5 — Migration tooling (~1 week)
- Diff tool: legacy workbook output vs new pipeline output by state
- One-shot regenerate-all-states script
- Coverage CSV with per-state status + last-run + validation flags
- Documentation pass; legacy workbook deprecation notice

### Sprint 6 (deferred) — Refinements
- v2 curtailment add-back if v1 validation flags issues
- v2 weather-year alignment (NSRDB TMY3 / ReEDS multi-year-mean) if needed
- Per-vehicle-type detailed transportation calculation refinements
- Population of district-heat-hydrogen, geoeng, data center demand inputs

---

## Validation strategy

Per state, automated checks:

1. **Annual energy by end-use vs EIA SEDS / Form 861** — tolerance ±10%; flag larger gaps
2. **Peak day shape vs Cambium 2022 hourly state load** — peak hour, peak/mean ratio
3. **Annual generation vs Ember / EIA-923 by tech**
4. **Internal balance**: Σ (LF × days_per_timeslice) per category ≈ 1.0
5. **Clustering quality**: full-year reconstruction NRMSE from representative days vs original 8760 (target < 0.4)
6. **Coverage check**: every SHELF + SYSHECF file present and non-empty

Output: `output/validation/{STATE}/validation_report.md`
Top-level dashboard: `output/coverage.csv`

---

## What's preserved from legacy

- EPS BCEU AEO end-use mapping (locked)
- 6 timeslice structure with pinned summer + winter peak days
- Days-per-timeslice file format (zero days for peak slices, capacity-only)
- CSV file naming convention (`SHELF-{category}.csv`, `SYSHECF-{tech}.csv`)
- Excel workbook accessibility for non-Python users (improved with explicit Sources + Validation tabs)

## What changes

- **Source of SHELF shapes**: EFS Medium 2018 regression-based → ResStock TMY3 + ComStock TMY release 1 (physics-based)
- **Generator**: per-state Excel macros / formulas → Python pipeline producing both CSVs and annotated Excel
- **Maintenance**: ~50 separate workbooks → single pipeline + per-state YAML preset
- **Validation**: ad-hoc → automated per-state report

## What's the same

- SYSHECF approach (Cambium 2022 state-level CFs) — unchanged
- EPS-side BCEU and SHELF consumption — unchanged
- Output schema at the CSV level — unchanged so EPS reads work without modification
- Per-state Excel workbook — re-implemented but user-facing structure preserved

---

## Open / deferred items

- **Curtailment add-back** (v2 if needed) — Cambium state hourly doesn't include curtailment columns; accept post-curtailment generation as availability proxy for v1
- **Weather-year alignment** (v2 if needed) — ResStock TMY3 vs Cambium 2012 mismatch documented; v2 paths identified (NSRDB TMY3 or ReEDS multi-year-mean)
- **District-heat-hydrogen, geoeng, data center inputs** — pipeline architected to accept these; values = 0 for start year v1; populate as inputs become available
- **Vensim integration** (deferred) — not needed for v1 since we read EPS input files directly. Could add later for future-year scenario analysis where EPS-internal values diverge from input files.

---

## Status: ready to start Sprint 1

- ✓ Cambium 2022 Mid-case 2024 hourly + annual capacity at `data/cambium22_midcase_state_hourly/`
- ✓ ResStock + ComStock state-level data on disk
- ✓ EFS state data at `data/efs/`
- ✓ Per-state EPS input files at `state-eps-data-repository/{STATE}/`
- ✓ Package skeleton created (`state_pipeline/`)
- ✓ Categories registry locked (`state_pipeline/categories.py`)
- ✓ VA preset locked (`state_pipeline/presets/US-VA.yml`)
- → Next: build readers, fetchers, builders, exports per Sprint 1 order

First module to build: **`readers/bceu_reader.py`** — read BCEU.xlsx for VA, return annual electricity demand by end-use bucket × residential/commercial × urban/rural for the start year.
