# Validation report - US-TX

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **472.4 TWh**
- Peak hour: **2018-08-03 14:00:00** at **82.4 GW**
- Cluster NRMSE: **0.639**

## Days per timeslice

- Winter: 90
- Spring: 64
- Summer: 118
- Fall: 59
- Summer Peak: 8
- Winter Peak: 26

## Top-5 peak days

- Summer Peak: [191, 192, 193, 194, 222, 227, 235, 241]
- Winter Peak: [2, 5, 8, 10, 11, 18, 20, 24, 30, 32, 37, 40, 41, 48, 305, 311, 312, 318, 320, 325, 331, 333, 340, 359, 362, 363]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 16670222.74 | 16670222.74 | 0.0 | 0.0 |
| residential-cooling | 35086459.55 | 35086459.55 | 0.0 | 0.0 |
| residential-lighting | 6884900.35 | 6884900.35 | 0.0 | 0.0 |
| residential-appliances | 37128282.53 | 37128282.53 | 0.0 | 0.0 |
| residential-other | 78474677.61 | 78474677.61 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 2327652.4 | 2327652.4 | 0.0 | 0.0 |
| commercial-cooling | 47171746.78 | 47171746.78 | 0.0 | 0.0 |
| commercial-lighting | 16842203.99 | 16842203.99 | 0.0 | 0.0 |
| commercial-appliances | 26566178.19 | 26566178.19 | 0.0 | 0.0 |
| commercial-other | 68850527.55 | 68850527.55 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 701313.29 | 701313.29 | 0.0 | 0.0 |
| HDVs | 18767.11 | 18767.11 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 83438.76 | 83438.76 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 135620404.45 | 135620404.45 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.105095 | 4159.52 | 8760 |
| Winter | 0.129018 | 4438.99 | 2160 |
| Spring | 0.11986 | 4719.55 | 1536 |
| Summer | 0.11101 | 4210.96 | 2832 |
| Fall | 0.112211 | 4092.36 | 1416 |
| Summer Peak | 0.023746 | 677.13 | 192 |
| Winter Peak | 0.091023 | 2804.07 | 624 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.163505 | 1945.77 | 16670222.74 |
| residential-cooling | 0.199669 | 2635.94 | 35086459.55 |
| residential-lighting | 0.069695 | 107.6 | 6884900.35 |
| residential-appliances | 0.095292 | 439.72 | 37128282.53 |
| residential-other | 0.126025 | 523.7 | 78474677.61 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.106866 | 257.83 | 2327652.4 |
| commercial-cooling | 0.148532 | 1595.07 | 47171746.78 |
| commercial-lighting | 0.187328 | 269.44 | 16842203.99 |
| commercial-appliances | 0.106197 | 390.45 | 26566178.19 |
| commercial-other | 0.192653 | 730.78 | 68850527.55 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.069196 | 12.78 | 701313.29 |
| HDVs | 0.101483 | 0.15 | 18767.11 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.069196 | 1.52 | 83438.76 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.189763 | 2497.84 | 135620404.45 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 78818.46 | 81873.53 | 0.9627 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 78818.46 | 79020.35 | 0.9974 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 64402.14 | 65196.36 | 0.9878 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 15407.2 | 16917.8 | 0.9107 |  |
| category_peak_commercial-cooling | 15993.57 | 16751.36 | 0.9548 |  |
| category_peak_residential-heating | 8243.98 | 15181.47 | 0.543 |  |
| category_peak_commercial-heating | 1750.84 | 3256.49 | 0.5376 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.18 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 78996.82 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 69884.63 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 80094.26 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 65207.82 | 64049.03 | 1.0181 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 65021.2 | 58255.55 | 1.1161 |  |
| winter_peak_net_load | 56932.12 | 49999.93 | 1.1386 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 4970.18 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 6211.85 | 438 | top 5% of LDC = top ~438 hours |
| overall | 2026.6 | 8760 | full 8760 LDC |

## Section 8: SHELF Balance Check

Sum LF*days across non-peak slices = 1.0 +/- tolerance.

| category | shelf_balance_sum | deviation_from_1 | note |
|---|---|---|---|
| residential-heating | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| residential-cooling | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| residential-lighting | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| residential-appliances | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| residential-other | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| residential-envelope | 0.0 | 0.0 | category has zero annual energy |
| commercial-heating | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| commercial-cooling | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| commercial-lighting | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| commercial-appliances | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| commercial-other | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| commercial-envelope | 0.0 | 0.0 | category has zero annual energy |
| LDVs | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| HDVs | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| aircraft | 0.0 | 0.0 | category has zero annual energy |
| rail | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| ships | 0.0 | 0.0 | category has zero annual energy |
| motorbikes | 0.0 | 0.0 | category has zero annual energy |
| industry | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| district-heat-hydrogen | 0.0 | 0.0 | category has zero annual energy |
| geoeng | 0.0 | 0.0 | category has zero annual energy |
| datacenters | 0.0 | 0.0 | category has zero annual energy |

## Section 9: Weather-Year Alignment Diagnostics

Daily summer correlation; net-load peak under +/-7d, +/-14d shifts.

| metric | value | note |
|---|---|---|
| summer_daily_corr_buildings_vs_solar_cf | 0.0845 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 201 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 67808.7 | shifted gen by -14d; peak hour 2018-09-04 18:00:00 |
| net_load_peak_shift_-7d | 67614.8 | shifted gen by -7d; peak hour 2018-09-04 18:00:00 |
| net_load_peak_shift_0d | 65773.58 | shifted gen by 0d; peak hour 2018-09-11 18:00:00 |
| net_load_peak_shift_7d | 64834.06 | shifted gen by 7d; peak hour 2018-09-05 18:00:00 |
| net_load_peak_shift_14d | 65467.53 | shifted gen by 14d; peak hour 2018-05-31 19:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| TX_total_annual_TWh | 472.43 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| TX_solar_pv_annual_TWh | 90.7939 | 90.7939 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| TX_wind_annual_TWh | 146.0954 | 146.0954 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 38752.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 2052.1 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 42838.8 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2585 | 0.2585 | 0.6753 | 0.6753 |
| solar-pv-dist | 0.1685 | 0.1685 | 0.4251 | 0.4251 |
| onshore-wind | 0.3893 | 0.3893 | 0.2415 | 0.2415 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.084

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 67809 | 2018-09-04 18:00:00 | 26888 |
| -7 | 67615 | 2018-09-04 18:00:00 | 26888 |
| 0 | 65774 | 2018-09-11 18:00:00 | 26888 |
| 7 | 64834 | 2018-09-05 18:00:00 | 26888 |
| 14 | 65468 | 2018-05-31 19:00:00 | 26888 |

Lowest peak indicates best alignment. Pipeline retains shift=0 for v1; this table is informational. Fundamental fix (NSRDB TMY3 / ReEDS multi-year-mean) is deferred to v2 per the plan.

## Industry shape mode

**Active mode:** `efs` (set in preset YAML via `industry_shape_mode`).

**Options:**
- `efs`: original EFS Industrial subsector hourly shape (weather-driven regression).
- `flat`: constant per hour. Simplest, most defensible for bulk industry (~24/7 manufacturing/mining).
- `cambium_residual`: industry shape = busbar_load - resstock - comstock; falls back to flat if residual produces > 5% negative hours.

**Comparison (industry annual = same; hourly stats differ):**

| mode | annual_GWh | peak_MWh | mean_MWh | std_MWh | peak_to_mean |
|---|---|---|---|---|---|
| efs | 135620.4 | 22831 | 15482 | 3424 | 1.47 |
| flat | 135620.4 | 15482 | 15482 | 0 | 1.00 |
| cambium_residual | 135620.4 | 32092 | 15482 | 4170 | 2.07 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
