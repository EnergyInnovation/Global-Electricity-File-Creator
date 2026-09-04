# Calibration Decisions Ledger

Running log of model-calibration decisions for the SHELF + SYSHECF pipeline.
Most-recent first. Each entry includes context, decision, and rationale —
designed to survive context summarization across Claude sessions.

See `CLAUDE.md` for the canonical methodology that these decisions inform.

---

## 2026-09-04 — VRE levels: preset CF targets (utility + distributed solar) and offshore wind no longer derated by the onshore fleet

### Context
Investigating eps-southkorea's solar (+21-28% vs KESIS) and offshore-wind (0.18 vs ~0.30) capacity
factors traced both to the Ember calibration step, not to the weather/site physics:

- **Solar.** The raw PV series averages 0.205 and is scaled to the Ember target, 0.1565 for KR
  (mean 2021-24 generation / mean year-end capacity). Ember/IRENA Korea capacity tracks KEA's
  grid-connected 사업용 fleet (17.9 GW end-2021 vs KEA total 21.2) while Ember generation is the KEA
  TOTAL including self-consumption 자가용, so the statistic is full-fleet output over partial-fleet
  capacity. KEA's own split gives a metered utility CF of 0.147/0.155/0.146/0.143 (2021-24, average
  capacity basis) and an imputed self-consumption CF of ~0.14 (KEA books 자가용 output as capacity x
  ~15.5%). The EPS maps the two exactly: SYSHECF-solar-pv drives BHRaSYC+BPMCCS capacity (= 사업용),
  SYSHECF-solar-pv-dist drives BDESC capacity (= 자가용).
- **Offshore wind.** The ninja site simulations (V164 8 MW @ 140 m) average 0.321 for Buan/Sinan/Ulsan,
  in line with Korean evidence (KEEI / 10th Plan 30%, Tamra 29% since 2017). The code scaled BOTH type
  series by the factor the 95%-onshore blend needed to hit the Ember fleet 0.186 (x0.5625), so the
  offshore table carried the old onshore fleet's derate: 0.321 -> 0.180. In the EPS, 43 GW of mandated
  offshore by 2038 then dispatched at 0.21-0.24.

### Decision
1. **Preset CF-target keys** (all optional; Ember remains the fallback):
   - `solar_cf_target`: number or `{'value', 'basis', 'source'}` — overrides the Ember utility solar
     target. Basis and source travel into the run log and the SYSHECF About sheet.
   - `distributed_solar_cf`: `{'target': cf, ...}` (national distributed-PV CF, converted to a ratio
     against the utility target) or `{'ratio': r}`. The run now emits a `solar_dist_cf` series =
     utility shape x ratio; `SYSHECF-solar-pv-dist` takes it when present and falls back to the legacy
     `0.70 x solar_cf` otherwise, so presets without the key are unchanged.
   - `wind_offshore_calibration`: `'uncalibrated'` (new default), `'blend_scale'` (legacy), or an
     explicit offshore target. Implemented by `resolve_wind_type_targets`: offshore keeps its raw
     simulated mean (or the given target) and onshore is set so the capacity-weighted blend of the two
     type means still equals the Ember fleet target (`on = (fleet - w_off x off) / w_on`). The blended
     `wind_cf` behind net load/clustering is still calibrated to the fleet target as before. Degenerate
     residuals fall back to `blend_scale` with a warning; an implied onshore multiplier outside
     [0.25, 1.5] warns.
2. **South Korea preset**: `solar_cf_target` 0.148 (KEA 사업용, 2021-24), `distributed_solar_cf`
   target 0.140 (KEA 자가용, imputed), `wind_offshore_calibration` 'uncalibrated'.
3. About sheet items 3-5 now state the actual levelling used (from `run_metadata`).

### Rationale / rejected
- Hand-scaling the CSVs in eps-southkorea (the original handoff) gives the same numbers once but
  diverges from the pipeline and is overwritten at the next migration (Robbie, 2026-09-04: fix it in
  the pipeline so Korea and other regions inherit it).
- Calibrating offshore to the fleet target directly was rejected: the fleet target is an onshore
  number wherever offshore is a few percent of capacity.
- Using the 11th Basic Plan's implied solar CF (13.8-14.3%) was rejected as the basis: those ratios
  are on year-end capacity and understate the average-capacity CF the EPS effectively applies.

### Amendment 2 (same day): the split is EX POST; the clustering input does not change
Robbie's point: only combined (fleet) generation is observed, and Ember's fleet CF x Ember capacity
IS the reported generation, so the fleet series behind net load is right in energy terms whatever
the CF/capacity attribution. The utility/distributed solar and onshore/offshore wind levels are an
ex-post disaggregation from other sources and belong on the exported tables only. Solar was
restructured to match wind: `solar_cf` stays Ember-levelled and drives net load/clustering; the
run emits `solar_utility_cf` (= fleet x solar_cf_target / Ember) and `solar_dist_cf` for the two
exported tables. Net load is therefore identical to the August run and the clustering reproduces
57/83/68/88 + 30/39 with no pin; the KR preset pin was removed (the key and the saved assignment
remain available). The re-clustering that the earlier version triggered also scored WORSE on its
own objective (net-load reconstruction NRMSE 0.396 vs 0.389 for the August assignment), which says
the 9-seed k-means search is not robust; adding the previous assignment as a search candidate is
the durable fix, not done here.

### Amendment (same day): pinned day-to-slice assignment, and a runner pin that broke reproduction
Re-running Korea after the CF change moved the clustering from 57/83/68/88 + 30/39 peak days to
83/68/41/93 + 17/63: the k-means seed search flips on a ~0.2 GW mean net-load change (solar
0.157 -> 0.148 on 22 GW). Every SHELF table would have moved with it, and eps-southkorea's
dispatch calibration (coal SYSHECF override, RAF, hydro scaling) was fit on the old slices. Two
things were needed to make a CF re-level a SYSHECF-only change:

1. **`pinned_clustering_csv` preset key / `PINNED_CLUSTERING_CSV` runner setting.** Points at a
   saved `workbook_sources/clustering.csv`; `labels_from_pinned_clustering` rebuilds the labels
   and representative days from it and k-means is skipped. KR pins
   `data/clustering_pins/KR_clustering_2026-08-13.csv` (the assignment behind the migrated
   files). With the pin, the new run reproduces every SHELF day count and changes the four VRE
   SYSHECF tables by a pure per-table scalar: solar-pv x0.946, solar-pv-dist -> 0.140 mean,
   onshore x0.958, offshore x1.778 (max cell 0.44). Set the runner to `'recluster'` to re-cluster
   deliberately.
2. **`run_pipeline.py` had `YEAR = 2023` / `LAST_N_YEARS = 4` left over from the China work
   (commit 8fc261c).** A Korea run with that pin uses a 2020-2023 calibration window and does
   not reproduce the August files at all (88/58/46/135/18/20 even in legacy CF mode). Restored
   to `YEAR = None` (preset default); with that and legacy CF mode the pipeline reproduces the
   eps-southkorea VRE SYSHECF tables to 1e-10, so the pipeline itself is deterministic.

Known, not fixed here: several eps-southkorea SHELF CSVs differ from the pipeline's current
SHELF output beyond float formatting (e.g. commercial-lighting annual sum 0.0159 vs 0.0135,
LDVs 0.0173 vs 0.0031) - either hand-edited after migration or from a category mapping that has
since changed. Reconcile before any SHELF re-migration.

### Effect
- KR: SYSHECF-solar-pv mean 0.157 -> 0.148; solar-pv-dist 0.110 (0.70 derate) -> 0.140; offshore wind
  0.180 -> 0.321; onshore 0.186 -> ~0.179 (absorbs the offshore residual). Shapes unchanged.
- **China changes at its next run** through the new default: its offshore table will rise from the
  blend-scaled level to the raw Rudong/Yangjiang/Putian simulation mean and onshore will drop
  slightly (8% offshore share). Set `'wind_offshore_calibration': 'blend_scale'` on the CN preset to
  freeze the old behaviour if a re-run must reproduce the historical files.
- Presets on the 2 m-weather wind path (no site split) are untouched.

## 2026-08-20 — China gets two observed-demand sources, selected by run configuration

### Context
The China preset calibrated against DemandCast's `wu_et_al` source, which covers
**2018 only** (`.vendor/demandcast/.../wu_et_al.yaml`: `start_date 2018-01-01`,
`end_date 2018-12-31`). That single-year coverage is the reason the preset pinned
`default_year: 2018, last_n_years: 1` — a much narrower calibration window than any
other verified preset, so weather-driven demand variability is never averaged out.

Claire supplied a provincial hourly load workbook covering **2015–2024**, which turns
out to be the published dataset behind Yi et al. 2026 (*Scientific Data* 13, 978). It
is the only source that can serve a multi-year window or a post-2018 target year.

An impact test was run first (`scripts/test_china_demand_source.py`, results in
`output/china_demand_source_test/RESULTS.md`). The two sources are **not**
interchangeable:

- 2018 annual energy matches to 0.01 % (6,899 vs 6,900 TWh) — same underlying
  2018 NDRC anchor — but hourly correlation is only **0.83** (NRMSE 7.7 % of mean).
- February energy differs by **+17.8 %**; the annual peak moves Aug 8 → Jul 20;
  minimum load is 34 % higher; winter peak is 8.8 % lower.
- Holding year and window fixed at 2018/1, the swap alone moves the EPS-prior-weighted
  **summer** peak-slice system shape **+12.0 %** and the **winter** peak-slice shape
  **−26.6 %**; Summer Peak days go 11 → 21 and Winter Peak 32 → 57. Summer
  peak-to-average rises 1.82 → 2.04, winter falls 1.43 → 1.05. **It moves the binding
  peak season** — the material result for a capacity-planning run.
- Representative-day reconstruction *improves*: net-load NRMSE 0.555 → 0.492 from the
  source swap, → 0.480 once the window widens to four years at the same target year
  (load NRMSE 0.510 → 0.404 → 0.363).
- Per-category diurnal shape barely moves (every category's peak hour is unchanged in
  every variant). The change flows through the monthly ridge-NNLS end-use weights and
  through which days the clustering assigns to which slice.
- SYSHECF: only the pipeline-derived VRE tables change value (solar-pv 5.0 %, offshore
  wind 4.9 %, onshore wind 2.9 %). The legacy-template techs are byte-identical but
  their **days-weighted annual CF still shifts** because days-per-timeslice changes —
  hard coal 0.4308 → 0.4476 (+3.9 %) and hydro 0.3481 → 0.3542 from the source swap
  alone, with no change to the tables themselves.

### Decision
Keep both sources and select between them from the run configuration, rather than
replacing one with the other:

| Run configuration | Source |
|---|---|
| `year == 2018` **and** `last_n_years == 1` | DemandCast → Wu et al. 2023 |
| any other year or window | Yi et al. 2026 provincial CSV |

Implemented as generic preset machinery, not a China special case:
- `demand_series_csv` (preset key) — path to a staged hourly demand CSV.
- `demandcast_pin` (preset key) — a `{year, last_n_years}` dict; when a run matches
  every field named, DemandCast is used instead of the CSV. Either field may be
  omitted.
- `demand_series_citation` (preset key) — printed in the run log and written into the
  workbook About tab via `run_metadata`.
- `resolve_demand_series_csv(preset, year, last_n_years, override)` — the rule.
- `load_local_demand_series(...)` — the CSV reader (local-time timestamps, MW).
- `DEMAND_SERIES_CSV` in `run_pipeline.py` — per-run override: `'demandcast'`, a path,
  or `None` to apply the rule.

### Rationale
The pinned default is about reproducibility, not about which source is better. The
historical EPS-China run was calibrated on Wu et al. 2018; silently repointing the
default would have changed every existing China output with no signal in the run
config. Conversely, asking for a different target year or a wider window is already a
request that Wu et al. *cannot* satisfy, so treating that request as selecting the
multi-year source needs no extra setting. The runner override exists for the case where
someone deliberately wants the non-default pairing — that is how variant B of the
impact test isolated the source effect at the pinned configuration.

`demandcast_pin` was written generically because the same situation will recur: any
region whose DemandCast coverage is narrower than a newly staged local record.

Regression check: with no override, a default China run took the DemandCast path and
reproduced the then-current production outputs (`output/China_timeslice_results_EPS/`) to
**1e-16** across all 49 SHELF + SYSHECF files — i.e. the new plumbing is inert when the
pin fires. That check was run before the priors were re-extracted (entry below); the
committed production outputs now differ from a fresh default run because the CN prior
changed, not because of anything here.

### Citation (required in any derived output)
> Yi, B., Luo, Q., Zhang, S., Ji, Y., Yu, S. & Fan, Y. (2026). Hourly electricity load
> curve dataset for Chinese provinces derived from meteorological variables.
> *Scientific Data* **13**, 978. https://doi.org/10.1038/s41597-026-07327-8
> Data: figshare https://doi.org/10.6084/m9.figshare.29832701

License is **CC BY-NC-ND 4.0** — non-commercial, no derivatives. Stricter than every
other source in `data/manual_downloads/`; confirm it permits the intended use before
publishing anything derived from it. Recorded in `data/manual_downloads/README.md`,
`CLAUDE.md` §1, `README.md` → China, and `CLUSTERING_METHODOLOGY.md`.

The published workbook is ~42 MB and is **not committed**; convert your own copy with
`scripts/build_china_hourly_demand.py`, which sums the 31 provinces, converts GWh/h →
MW, and writes a per-year coverage report (hours vs expected, missing cells, annual
TWh, mean/peak GW) for the sanity-check.

### Rejected alternatives
- **Replace DemandCast outright.** Rejected: breaks reproducibility of every existing
  China output, and the impact test shows the two disagree enough that the change must
  be visible in the run configuration.
- **A boolean preset flag (`use_new_demand_source: true`).** Rejected: the constraint is
  really about coverage, so deriving it from `year`/`last_n_years` cannot fall out of
  sync with what the sources can actually serve.
- **Widen the default to `year=2024, last_n_years=4`.** Rejected for now: 2024 is a leap
  year and the run's days-per-timeslice sums to **366**, not the 365 EPS requires
  (confirmed a leap-year artifact — the same run at 2023 sums to 365). 2023 is the
  defensible multi-year target year until leap handling is fixed.

### Open — for the modeling team
- **Leap-year days-per-timeslice (366).** Blocks a 2024 target year.
- **A one-hour label discrepancy between the two sources.** The DemandCast wrapper
  (`_retrieve_demandcast_series_from_source`) hard-codes the Wu et al. series to start
  at `2018-01-01 01:00:00`; the Yi et al. workbook carries explicit `00:00`-based
  timestamps. Positional alignment maximizes correlation, so the two label the same
  underlying hours one apart. Whichever is wrong shifts the entire China SHELF diurnal
  shape by an hour. Needs checking against the sources' own documentation.
- **Several China SHELF categories fail the 1.0 balance check** in the baseline too
  (transport 0.155–0.190, commercial appliances/lighting/other 0.657–0.686). Pre-existing.
- **Prior-coverage interaction.** The re-extracted CN prior (entry below) spans
  **2024–2060**, so target years 2018 and 2023 both take the nearest-year 2024
  magnitudes. This weakens the case for 2023-over-2024 on prior grounds and should be
  settled alongside the leap-year fix — moving the China run year off 2018 changes both
  the demand source *and* the prior year, and those are two decisions. All numbers above
  were produced against this re-extracted prior; an earlier pass on the pre-re-extraction
  prior (span 2019–2060) reached the same qualitative conclusions with smaller
  magnitudes (+5.4 % / −15.6 % rather than +12.0 % / −26.6 %), which is itself a sign
  that the peak-season conclusion is robust to the prior vintage.
- **Variant E (2023) moves hard-coal effective CF +18 %** (0.4308 → 0.5084) purely
  through day reweighting. Worth understanding before adopting 2023.

---

## 2026-08-20 — Amendment: staff edits to the KR ELCCAfR workbook, ported to the builder

### Context
Claire hand-edited `ELCCAfR ELCC Adjustment for Reliability.xlsx` after the 2026-08-18
build. The edits were diffed cell-by-cell against a fresh build and ported into
`scripts/build_run_workbooks.py` (and, where they change output values, into
`energy_timeslice_pipeline.py`) so every region gets them. Excel round-trip artifacts —
colour alpha `00xxxxxx` → `FFxxxxxx`, explicit `sz=11.0`, autofit row heights, collapsed
column-width runs, freeze-pane position — were identified as such and **not** ported.

### Decisions

1. **`_xlfn.MINIFS`, not `MINIFS`.** OOXML must store functions added after the original
   spec with the `_xlfn.` prefix; a bare `MINIFS` written by openpyxl opens as `#NAME?`
   in Excel. Excel itself rewrites it to the prefixed form on save, which is how this
   surfaced. **This is a correctness fix, not cosmetics** — the 2026-08-18 build's Step 2
   block may have been broken on open. Verified in the stored XML: 432 `_xlfn.MINIFS`,
   zero bare occurrences. `scripts/verify_run_workbooks.py` now asserts the prefix.

2. **Numeric hour row on `Peak CF statistics`.** Row 3 is `Hour (Numeric)`: `B3 = 0`,
   `C3:Y3 = <prev>+1`. Every AVERAGEIFS/MINIFS takes its hour criterion from `B$3:Y$3`
   instead of a hardcoded literal, so a block can be filled across and the criterion is
   visible on the sheet rather than buried in 24 separate formulas. SYSHECF keeps the
   literal-hour form (`_slice_mean_cf`); the reference form is a separate helper
   (`_slice_mean_cf_ref`) used only by the ELCCAfR stats tab.

3. **Solar thermal mirrors solar PV.** `ELCCAfR-solar-thermal` peak rows now point at
   `ELCCAfR-solar-pv` instead of sitting at 1.0. CSP shares the solar resource, so
   crediting it as fully firm at the binding peak hour overstates its capacity value.
   **This changes a deployed CSV**, so it is implemented in the pipeline too
   (`EPS_ELCCAfR_MIRRORS`), not just the workbook. Applied only when the tech is not
   independently derived AND its mirror target is — a region that derives solar thermal
   keeps its own values. No numeric effect for KR (eps-southkorea's
   `SYSHECF-solar-thermal` is all zeros, so there is no CSP capacity to credit); it will
   matter for any region with CSP.

4. **Per-tab footnote dropped on derived tabs**, kept on constant, mirrored and
   demand-altering tabs. The "how the cell is built" explanation lives once on the
   `Peak CF statistics` and relationship tabs; repeating it on every derived tab crowded
   the grid. The one sentence worth keeping — that non-peak rows are 1.0 by definition —
   moved into the About tab's non-peak note.

5. **About tab drops the borrowed-non-VRE source block.** A bug: `build_elccafr` passed an
   empty `Path()` as `borrow_dir`, so `cf_sources_for` emitted a block reading
   `EPS model input files ()`. ELCCAfR borrows nothing, so the block should never have
   been there. `elccafr_sources_for` now filters it out and takes no `borrow_dir`.

6. **Relationship tab** gains "Clusters are defined around net peak load shapes so both
   SYSHECF and SHELF impact clusters." **About** column A widened to 18.

### Verification after porting
Rebuilt Korea and re-diffed against the hand-edited file: the only remaining differences
are the build date and two About-tab notes that my port *extends* to document the new
mirror. Full verifier passes (0 failures, including a new mirror check that the CSV equals
the mirrored tech's CSV and the tab references it by formula rather than holding a stale
copy). End-to-end formula evaluation — resolving the slice VLOOKUP, the numeric hour row,
the AVERAGEIFS/MINIFS chain and the mirror indirection — reproduces all four non-constant
CSVs to 4.9e-05 (4dp CSV rounding).

The pre-port copy of the hand-edited workbook is in the session scratchpad
(`scratchpad/edited/ELCCAfR_edited.xlsx`) if the original wording needs to be recovered.

---

## 2026-08-18 — ELCCAfR added to the international pipeline (South Korea first)

### Context
`InputData/elec/ELCCAfR/` holds 25 CSVs on the same 6×24 grid as SHELF/SYSHECF: 24
generation files (one per member of the EPS `Electricity Source` subscript) plus
`ELCCAfR-demand-altering-techs.csv`. EPS multiplies them into the **reliability**
branch only, never dispatch — `Last Year Hourly Bid Electricity Capacity Factors for
Reliability by Plant Type` ([EPS.mdl:35482 in eps-us](../eps-us/EPS.mdl)) and the
peak-load-reduction term in `Total Electricity Demand by Hour Plus Reserve Margin
After Demand Altering Technologies`. Both feed `...in Binding Hour by Plant Type`,
summed over `Binding Peak Hour for Reliability Additions[peak day electricity
timeslice!, Hour!]`, so only the two peak slices can ever bind.

The pipeline did not produce these files. Verified 2026-08-18 by md5: **`eps-southkorea`
and `eps-china-igdp\eps-china-igdp` both carried byte-identical copies of the eps-us
tables**, and all three `.mdl` files reference ELCCAfR 83 times — live inputs, not
dormant folders. Korea's offshore wind was being credited 3.1× (Summer Peak) to 4.4×
(Winter Peak) less firm capacity than its own CF data supports.

### Decision
Emit ELCCAfR from the pipeline as a third family alongside SHELF and SYSHECF.

```
ELCCAfR[slice, hour] = <low statistic> CF / mean CF     over the days the clustering
                                                        assigned to that slice
                     = 1.0                              on the four non-peak slices
```

The denominator is the **same slice mean that becomes the SYSHECF cell** (CLAUDE.md §6),
over the **same day set**, so:

```
SYSHECF[slice, hour] × ELCCAfR[slice, hour] = the worst-day CF at that hour
```

Verified for the KR run: the workbook's Step 1 block equals the deployed SYSHECF CSVs to
2e-16, and the identity holds to 2e-05 (CSV 4-decimal rounding).

### Rationale
- **No new data.** ELCCAfR is a second statistic (`MINIFS`) over the identical hourly
  column that already produces SYSHECF (`AVERAGEIFS`). Everything needed is already in
  `workbook_sources/cf_hourly_source.csv`.
- **Keeping both statistics over the same day set is what makes the identity hold.**
  Computing ELCCAfR over a separately pinned top-N-by-net-load set — which is what the
  eps-us files appear to use — breaks it.
- **Techs whose SYSHECF is a borrowed constant get exactly 1.0**, because their min and
  mean over a slice's days coincide by construction. 21 of 24 for KR.
- **Calibration multipliers cancel in the ratio**, so only the day-to-day *shape* of a CF
  series moves ELCCAfR — not its level.

### Rejected alternatives
- **`p05` as the default statistic.** Recommended for cross-region comparability but not
  adopted as the default: `min` is the documented eps-us methodology and changing it is a
  modeling-team call. Exposed as the preset key `elccafr_statistic`; `'p05'` switches both
  the CSVs and the workbook formulas (which then use `PERCENTILE(IF(...))`, needing
  dynamic-array Excel). For KR offshore wind, `p05` gives SP 0.425 / WP 0.615 vs `min`'s
  0.288 / 0.502.
- **Deriving ELCCAfR for the borrowed techs from their expanded `CF_<tech>` columns.**
  Mathematically identical to 1.0 but introduces float noise; emit the exact constant.
- **Adding `solar-pv-dist` and `pumped-hydro` files.** Both are in `EPS_SYSHECF_FILE_MAP`
  but neither is a member of `Electricity Source`, so EPS never reads such a file.

### Open items for staff review
1. **`min` is sample-size dependent.** The KR run's peak slices hold 30 (Summer) and 39
   (Winter) days; eps-us holds 11 and 10. A straight minimum takes the worst of however
   many days a slice happens to contain, so a longer slice gets a deeper derate for
   reasons that are a clustering artifact, not physics.
2. **Wind CF is a climatology.** On the `ninja_sites` path the hourly CF is a
   day-of-year × hour average across sites and 7 years. That averaging removes interannual
   and cross-site variability, so the measured spread — and therefore the derate — is
   narrower than a single-weather-year fleet series would give. The KR wind numbers are
   likely too generous. Verify against unaveraged site-year data.
3. **Hydro lands at 1.0** because its SYSHECF is borrowed. Correct for thermal (outage risk
   lives elsewhere in EPS) but questionable for hydro, whose real capacity credit varies
   between wet and dry years. Relevant for China and Brazil.
4. **Demand-altering 0.9** is carried over from eps-us; it is a judgment parameter about
   demand-response reliability, not derivable from CF data. Preset key
   `elccafr_demand_altering`.
5. **The eps-us file itself looks stale.** Its workbook records Cambium22 as the source
   while eps-us now ships days-per-timeslice 11/10 derived from Cambium24, and the peak-day
   set behind the shipped values is not recorded anywhere. Worth regenerating.

### Implementation
- `energy_timeslice_pipeline.py` — `EPS_ELCCAfR_FILE_MAP`, `EPS_ELCCAfR_HEADERS`,
  `build_elccafr_table`, `build_all_elccafr_tables`, `elccafr_run_metadata`;
  `export_eps_input_tables` writes an `ELCCAfR/` folder and workbook.
- `scripts/build_run_workbooks.py` — `build_elccafr` writes the 25 CSVs (so runs made
  before this change get them without re-running `run_pipeline.py`) plus the
  self-contained workbook.
- `scripts/verify_run_workbooks.py` — `check_elccafr`: range, non-peak-row, A1-header and
  shape invariants; CSV values against an independent pandas recomputation; the
  SYSHECF × ELCCAfR identity; and formula wiring checked against the stats tab's own
  block labels rather than hardcoded rows.

**Not deployed.** The files live in `output/SouthKorea_timeslice_results_EPS/ELCCAfR/`.
Copying them into `eps-southkorea` changes reliability-driven capacity build; back up
`InputData/elec/ELCCAfR/` and diff first (CLAUDE.md §5).

---

## 2026-08-13 — EPS priors re-extracted from live models, with provenance

### Context
`SHELF-residential-other.csv` for the KR run exported **entirely blank**. Tracing it:
`eps_prior_KR.csv` carried `residential_other = 0.0` for every year →
`align_basis_to_prior` scales a zero-prior basis column by `s = 0` →
the calibrated hourly series is identically zero → the SHELF load factor is
`hourly / annual` with `annual = 0`, and `annual_totals.replace(0, np.nan)`
([energy_timeslice_pipeline.py:7472](energy_timeslice_pipeline.py:7472)) turns the
whole table into NaN.

That raised a second question: the priors are **static committed files**. Nothing in
the run path regenerates them — `load_eps_magnitude_prior` is a plain `read_csv`, and
`parse_eps_extract.py` is a manual CLI fed by a Vensim `vdf2tab` export. All three
priors landed in one commit (`b26466c`, 2026-06-02) and had driven calibration
unchanged for over two months, with no record in the files of which model snapshot
they came from.

### Decision
Re-extracted all three regional priors from fresh headless BAU runs, added a
**generation-capacity prior** alongside each demand prior, and stamped every file
with provenance.

| Region | Source model | Version | Span | Branch @ commit | Tree at run |
|---|---|---|---|---|---|
| US | `eps-us` | 4.0.5 | 2025–2050 | `main` @ `9b3a6514` | clean |
| CN | `eps-china-igdp\eps-china-igdp` (**inner** clone) | 4.0.5 | 2024–2060 | `4.0-data-2024IT` @ `60e3b64` | clean |
| KR | `eps-southkorea` | 4.0.4 | 2021–2050 | `develop_4.0.5` @ `45acd7e` | clean (26 files stashed for the run) |

New/changed files:
- `data/eps_priors/eps_capacity_<ISO2>.csv` — **new**, `tech,year,eps_mw` from
  `BAU Electricity Generation Capacity[Electricity Source]` plus
  `BAU Distributed Electricity Source Capacity` summed over building types and
  suffixed `(distributed)`. Tech names are raw EPS `Electricity Source` subscripts,
  not remapped — the SYSHECF side already speaks EPS tech names.
- `data/eps_priors/eps_provenance.py` — **new**, reads version / base+final year /
  git branch, commit, date, remote / working-tree state out of the checkout itself.
- Provenance is a `#` comment block above the CSV header; `load_eps_magnitude_prior`
  and `scripts/test_china_demand_source.py` now pass `comment='#'`.
- `scripts/compare_eps_priors.py` — **new**, diffs a re-extraction against the prior
  snapshot and cross-checks capacity against `data/eps_wind_capacity_split.csv`.

### Rationale for the two judgment calls
**China: inner clone over parent.** The parent (`eps-china-igdp`, 4.0.0, IT 2019) matched
the old prior's 2019–2060 span, but is 263 commits behind, last touched 2024-09-30, and
**lacks three needed variables** (`BAU Data Center Load`,
`BAU Hydrogen Sector Grid Electricity Demand`, `BAU Distributed Electricity Source Capacity`).
The inner clone is current, clean, and complete. Cost: the CN prior's span moves to
2024–2060, and the China preset's `default_year: 2018` now resolves to nearest-year 2024
instead of 2019 — a pre-existing mismatch, now larger.

**KR: stashed to clean HEAD.** The 26 uncommitted files in `eps-southkorea` are
`InputData/elec/SHELF` + `SYSHECF` CSVs *written by this pipeline*. Demand is computed
upstream of the hourly SHELF allocation, so the demand prior is unaffected either way —
but SHELF/SYSHECF feed dispatch and capacity expansion, so extracting a capacity prior
from that tree would have fed this pipeline's own output back into its own calibration
anchor. Stashed for the run, restored immediately after.

### What the re-extraction showed
1. **KR `residential_other` is still exactly 0.0** — from a fresh clean-HEAD run of the
   current model. The zero is a genuine property of eps-southkorea, not a stale snapshot.
   Every KR buildings end-use is bit-identical to the June snapshot (+0.0%), i.e. the KR
   buildings input data has not changed since. `residential_lighting` and
   `residential_cooling` are also *exactly* equal (12,803,180 MWh), which still looks like
   a placeholder allocation in the KR residential end-use split. **Open question for the
   modeling team — see TODO.**
2. **Data-center load has arrived in the newer models.** `other_sectors` (district heat +
   hydrogen + data centers): US 15.3 → 224.0 TWh (+1360%), KR 0.003 → 3.9 TWh. CN went the
   other way (97.2 → 12.4 TWh), reflecting the 4.0.0 → 4.0.5 rebuild rather than a trend.
3. **`data/eps_wind_capacity_split.csv` is now stale for CN.** It was built from the 4.0.0
   parent: 404,977 / 36,770 MW onshore/offshore (shares 0.9168 / 0.0832). The inner 4.0.5
   model's 2024 capacity is 480,647 / 40,750 MW (shares 0.9218 / 0.0782). KR is close
   (1,772 vs 1,708 MW onshore, +3.7%; offshore matches exactly). **Not refreshed here** —
   those weights set the level of both per-type wind CF series and the shape of the blended
   `wind_cf`, so changing them moves net load and clustering. Deliberately left for a
   separate, reviewed change.
4. **The old parser had a latent layout bug.** `parse_tsv` assumed a run-name column between
   the variable name and the first year (`parts[2:]`). The exports produced here have no such
   column, so it silently returned **zero rows** rather than erroring. It now locates year
   columns from the `Time` header row. If the June extraction used a different VDF2TAB
   invocation, the two snapshots were not produced by equivalent parsing.

### Rejected alternatives
- **Sidecar `.provenance.json` files.** Keeps the CSV schema untouched, but provenance you
  have to open a second file to see is provenance nobody reads. The `#` block is visible on
  open and costs one `comment='#'` argument.
- **Provenance as extra CSV columns.** Repeats 14 constant fields on every one of ~400 rows.
- **Folding distributed capacity into the grid-connected totals.** SYSHECF treats distributed
  solar as its own technology with its own derate (`DISTRIBUTED_SOLAR_CF_DERATE`); merging
  them would destroy that split.
- **Fixing `align_basis_to_prior` to treat a zero prior as "not tracked"** (the one-line
  `if col not in prior or prior[col] <= 0` change). Deliberately **not** bundled here —
  finding 1 shows the KR zero is real model behavior, so whether to override it with a
  fallback magnitude is a modeling decision, not a data-refresh decision. Still open.

### Reproduce
```
python data/eps_priors/parse_eps_extract.py <PriorExtract.tab> <ISO2> <IT> <FT> \
    --model-dir <model checkout> --vensim "<path to vendss64.exe>"
python scripts/compare_eps_priors.py --before <dir of previous eps_prior_*.csv>
```
Vensim DSS on this machine is at `C:\Program Files\Vensim\vendss64.exe`, **not** the
`Vensim DSS x64` path the `eps-run` skill defaults to; pass `-Exe` explicitly.

All extracted values are model output for staff review — verify against the models' own
documentation and primary sources before use in any work product.

---

## 2026-08-12 — SHELF/SYSHECF exports switch from representative-day to slice-mean (Option A)

### Context
A `Checker` tab added to the KR SHELF workbook computed, per category,
`Σ_slices days × Σ_hours LF` — the fraction of annual demand the six timeslices
reproduce. It must be 1.0. It was not: 0.8404 (residential heating), 0.9449
(residential cooling), 1.6208 (service other), **2.2442** (service heating).

Root cause: the exported tables were built from a single **representative day**
per slice (`LF = rep-day hour value ÷ annual`), so the balance only equals 1 if
the day-weighted rep-day energies happen to reproduce annual energy. They don't.
Substituting the slice mean into the identical arithmetic returns exactly 1.0000
for every non-zero category.

The error varies wildly by category because representative days are chosen on
**net-load** shape — the clustering objective — not per-category energy. A
category whose seasonality doesn't track net load (service heating) gets a rep
day that is wildly unrepresentative *for it*, then multiplied by up to 93 days.
Aggregate demand came out at 1.0047, so the errors partly cancel in total, which
is why this survived unnoticed.

This contradicted two existing references: CLAUDE.md §6 defines the LF as
"(**mean** demand in slice at that hour) / annual demand" with the balance equal
to 1.0, and the canonical eps-us workbooks compute every output cell as
`AVERAGEIFS(col, slice, …, hour_of_day, …)` — a slice mean. The archived
`build-input-xlsx` skill likewise documents "Slice-mean over hourly data" as the
output-tab pattern. The rep-day form had leaked from the clustering objective
into the export.

### Decision
Option A, chosen by staff: **the exported values are slice means.** Rep-day
selection remains the *clustering* objective — it is what makes the optimizer
place only genuinely extreme days in the peak slices — but it no longer
determines cell values. Peakiness survives because a peak slice contains only
extreme days, so their mean is still extreme; this is also why the eps-us
reference figures are quoted as slice means ("SP slice gross peak … 11-day mean").

Applies to both families:
- SHELF   `LF[slice,hour] = AVERAGEIFS(col, slice, hour) / SUM(col)`
- SYSHECF `CF[slice,hour] = AVERAGEIFS(cf col, slice, hour) × mult`, clamped to
  [0,1] via `IFERROR(MAX(0,MIN(1,…)),0)` exactly as the eps-us cells do.

### Affected files / variables
- `energy_timeslice_pipeline.py`: `run_pipeline` no longer passes
  `representative_dates` to `compute_hourly_capacity_profiles` /
  `compute_hourly_load_profiles` (both already had a slice-mean branch);
  docstrings record why the parameter exists but is unused in production.
- `scripts/build_us_run_workbooks.py`: `_repday_lf` → `_slice_mean_lf`; new
  `_slice_mean_cf` and `_cf_cell` (the eps-us IFERROR/MAX/MIN wrapper); SHELF and
  SYSHECF cell writers use them. Shared by both builders, so the US run workbook
  changes with it.
- `scripts/build_run_workbooks.py`: same switch; new builder-generated `Checker`
  tab covering all 22 SHELF categories (previously hand-added).
- `scripts/verify_run_workbooks.py`: formula regexes updated for AVERAGEIFS; the
  ground-truth section now **asserts** the balance is 1.0 per category instead of
  printing it as a note.

### Effect on model output
Every SHELF and SYSHECF value changes. Verified on the South Korea run
(7 wind sites, capacity-weighted):

- SHELF balance = **1.0000000000** for all 14 non-zero categories (was
  0.84–2.24). Exported CSVs match an independent pandas slice-mean to 1e-17.
- SYSHECF days-weighted annual CF now equals the calibrated hourly annual mean
  to **0.00%** — previously off by −22% (onshore wind), −28% (offshore), +24%
  (solar). The model will now generate the annual energy the Ember calibration
  intended.
- Onshore and offshore wind remain distinct (max|diff| 0.0334 across the 6×24
  grid); hourly means 0.1861 / 0.1803 against the Ember fleet target 0.1861.
- `verify_run_workbooks.py`: 0 failures.

**Known remaining divergence (pre-existing, not introduced here):** the
pipeline's own `EPS_SHELF_FILE_MAP` still resolves some categories via
`template_split`, whose CSVs balance to that category's *share* of a shared
aggregate (transport's six modes total 1.0; the commercial trio totals 2.0
because it splits two aggregate columns). The workbook builder's `SHELF_MAP` is
all-direct — per the 2026-07-14 staff reclassification it is the authoritative
mapping — so every category in the delivered workbook balances to exactly 1.0.
Worth reconciling the CSV path to match.

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
