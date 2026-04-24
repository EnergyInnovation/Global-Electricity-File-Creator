# Timezone Audit — China, South Korea, United States

**Scope.** Quantify (not fix) a timezone mismatch in `energy_timeslice_pipeline.py` between demand (local-time indexed for CN and KR) and Renewables.ninja weather / CF series (UTC). Based on cached data in `data/weather/` and `data/manual_downloads/`.

## Task A — Data-flow trace

| # | File : line | Operation | Resulting tz |
|---|---|---|---|
| 1 | `energy_timeslice_pipeline.py:1581` | `pd.date_range(..., tz='Asia/Shanghai')` — CN real demand index | Asia/Shanghai |
| 2 | `energy_timeslice_pipeline.py:838` | `pd.to_datetime(df_var['time'], utc=True)` — weather for all countries | UTC |
| 3 | `energy_timeslice_pipeline.py:1648-1649` | `compute_capacity_factors_from_weather` returns `cf_df` on weather (UTC) index | UTC |
| 4 | `energy_timeslice_pipeline.py:3060-3064` (`calibrate_synthetic_load`) | If `df_synthetic` index is naive, `tz_localize` to real-demand tz | CN → Asia/Shanghai; KR → Asia/Seoul; US → UTC |
| 5 | `energy_timeslice_pipeline.py:1798-1810` (`calibrate_capacity_factors`) | Scales each CF column by a single scalar to match Ember annual mean — **no hourly alignment** | Level-only |
| 6 | `energy_timeslice_pipeline.py:2347-2355` | `gen_df['hour'] = gen_df.index.hour` (UTC) → group by `(doy, hour)` → lookup via `zip(df_calibrated.index.dayofyear, df_calibrated.index.hour)` (local tz) | **MISMATCH POINT** |

**First concat/merge point.** Modeled and observed series are first aligned in `_align_modeled_and_real_series` (line 1828), which does call `tz_convert` (line 1827). But that path is only used for RMSE diagnostics in `build_run_metrics`. The production path that assigns CF into the demand frame (lines 2347-2362) bypasses it and performs an implicit `.hour` join that never crosses a tz_convert. A `tz_convert` there would shift the alignment by exactly the UTC offset.

**Calibration type.** Scalar (annual mean) only. Annual MWh is correct; diurnal shape is shifted. Pure shape bug.

## Task B — Reproduction (China)

Script: `output/tz_audit/china_tz_repro.py` (read-only w.r.t. pipeline)
Raw output: `output/tz_audit/china_tz_findings.md`

Method: load `ninja-weather-country-CN-*.csv` (MERRA-2, UTC, 2020-2024), compute simplified PV CF (GHI/1000 × PR), compare diurnal shape as (a) UTC series treated-as-local (pipeline behavior) vs. (b) `tz_convert`'d to `Asia/Shanghai`.

| Country | Peak CF hr (buggy) | Peak CF hr (fixed) | Phase shift | 08-18 mean CF (buggy) | 08-18 mean CF (fixed) | Delta |
|---|---|---|---|---|---|---|
| China | **05:00** | **13:00** | **8 h** | 0.070 | 0.419 | **-0.349** |

Under the buggy alignment, China's country-level solar CF peaks at 05:00 Beijing time and the 08:00-18:00 "daytime" mean collapses to **0.07** vs. a physically-sensible **0.42**. Solar generation is booked almost entirely into overnight hours of the demand frame. Demand used for correlation was a synthetic local double-peak profile (no cached CN demand file is present — DemandCast's `wu_et_al` is a runtime fetch).

## Task C — Extension

### South Korea (cached KEPCO, KST)

Cached demand loaded from `data/manual_downloads/KRO_demand_{2021,2023,2024,2025}.csv` (cp949 / latin1 encoded).

| Peak CF hr (buggy) | Peak CF hr (fixed) | Shift | 08-18 mean CF (buggy) | 08-18 mean CF (fixed) | Delta |
|---|---|---|---|---|---|
| **03:00** | **12:00** | **9 h** | 0.014 | 0.388 | **-0.374** |

**Verdict: broken, not accidentally correct.** KST = UTC+9, so the shift is worse than China. Solar CF peak lands at 03:00 local; the 08-18 local daytime mean collapses to 0.014 (effectively invisible during the Korean load day).

### United States

US demand is explicitly UTC on fetch (line 2957-2959; `_fetch_eia_respondent_series` line 1417+; `.tz_localize('UTC')` at line 1473). Weather is UTC. Both sides of the `.hour` join share the same clock.

| Peak CF hour (UTC) | Implied effective local offset | Bug? |
|---|---|---|
| **18:00 UTC** | local = UTC−6 (Central) | **No index-mismatch bug** |

A solar-CF peak at 18:00 UTC places solar noon in a notional UTC-6 zone, consistent with an area-weighted centroid near the central US. "US local time" in outputs is therefore effectively Central; East Coast (UTC-5) runs ~1 h early on that axis, West Coast (UTC-8) runs ~2 h late. Modelling simplification, not a bug.

## Verdicts

| Country | Bug? | Shape or level? | Severity |
|---|---|---|---|
| China | Yes | Shape-only (annual level preserved via scalar calibration) | **Material** — solar booked overnight |
| South Korea | Yes | Shape-only | **Material** — 9 h shift, worse than CN |
| United States | No | n/a | Cosmetic: single-clock simplification for a 4-TZ country |

"Material" = representative-day profiles (SHELF / SYSHECF outputs) encode solar against the wrong hour of the load day, biasing clustering, net-load peaks, storage-duration sizing, and any downstream capacity-expansion model reading SYSHECF. Annual MWh / mean CF unaffected because calibration (1798-1810) is a scalar anchor.

## Files produced

- `output/tz_audit/china_tz_repro.py` — standalone read-only reproduction script
- `output/tz_audit/china_tz_findings.md` — per-country summary table + 24-hour diurnal CF table + US effective-offset note

## What's missing / would go further

1. A cached CN demand file (DemandCast `wu_et_al`) — would replace synthetic CN demand with a real correlation number.
2. A one-line experimental patch at line 2347 (tz_convert `gen_df.index` into the local demand tz before extracting `.dayofyear`/`.hour`) and a diff of resulting SYSHECF vs. the current `output/China_timeslice_results_SYSHECF.csv` would quantify the bug's footprint in the published representative days.
