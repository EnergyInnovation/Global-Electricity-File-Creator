# Validation report - US-FL

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **251.6 TWh**
- Peak hour: **2018-07-03 11:00:00** at **43.6 GW**
- Cluster NRMSE: **0.418**

## Days per timeslice

- Winter: 75
- Spring: 54
- Summer: 118
- Fall: 98
- Summer Peak: 6
- Winter Peak: 14

## Top-5 peak days

- Summer Peak: [159, 176, 177, 178, 240, 241]
- Winter Peak: [2, 5, 19, 40, 51, 305, 306, 307, 309, 324, 339, 354, 355, 359]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 6415514.07 | 6415514.07 | 0.0 | 0.0 |
| residential-cooling | 34678839.39 | 34678839.39 | -0.0 | -0.0 |
| residential-lighting | 6141872.8 | 6141872.8 | 0.0 | 0.0 |
| residential-appliances | 36999970.69 | 36999970.69 | -0.0 | -0.0 |
| residential-other | 52054894.49 | 52054894.49 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 305413.25 | 305413.25 | -0.0 | -0.0 |
| commercial-cooling | 31960140.68 | 31960140.68 | -0.0 | -0.0 |
| commercial-lighting | 9359642.44 | 9359642.44 | 0.0 | 0.0 |
| commercial-appliances | 17336137.16 | 17336137.16 | 0.0 | 0.0 |
| commercial-other | 38494138.34 | 38494138.34 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 446938.06 | 446938.06 | 0.0 | 0.0 |
| HDVs | 6634.52 | 6634.52 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 18286.49 | 18286.49 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 17343346.25 | 17343346.25 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.076114 | 1602.17 | 8760 |
| Winter | 0.08682 | 1658.08 | 1800 |
| Spring | 0.078625 | 1502.68 | 1296 |
| Summer | 0.0909 | 1970.18 | 2832 |
| Fall | 0.064756 | 1221.82 | 2352 |
| Summer Peak | 0.029119 | 567.09 | 144 |
| Winter Peak | 0.099532 | 1690.68 | 336 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.110498 | 773.99 | 6415514.07 |
| residential-cooling | 0.173977 | 1630.96 | 34678839.39 |
| residential-lighting | 0.06361 | 84.86 | 6141872.8 |
| residential-appliances | 0.081075 | 356.34 | 36999970.69 |
| residential-other | 0.110956 | 344.62 | 52054894.49 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.077904 | 31.29 | 305413.25 |
| commercial-cooling | 0.112607 | 668.88 | 31960140.68 |
| commercial-lighting | 0.161817 | 119.83 | 9359642.44 |
| commercial-appliances | 0.077047 | 184.54 | 17336137.16 |
| commercial-other | 0.173797 | 306.78 | 38494138.34 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.058588 | 7.42 | 446938.06 |
| HDVs | 0.078557 | 0.04 | 6634.52 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.058588 | 0.3 | 18286.49 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.203457 | 366.38 | 17343346.25 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 41450.17 | 43365.46 | 0.9558 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 41450.17 | 41450.17 | 1.0 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 35808.21 | 36160.24 | 0.9903 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 9978.81 | 12006.91 | 0.8311 |  |
| category_peak_commercial-cooling | 9195.93 | 9696.27 | 0.9484 |  |
| category_peak_residential-heating | 4327.04 | 9725.32 | 0.4449 |  |
| category_peak_commercial-heating | 300.7 | 642.33 | 0.4681 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.88 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 42078.75 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 39499.43 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 42547.87 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 38658.41 | 38042.52 | 1.0162 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 37761.38 | 37022.04 | 1.02 |  |
| winter_peak_net_load | 34053.89 | 34280.28 | 0.9934 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 2011.05 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 1525.95 | 438 | top 5% of LDC = top ~438 hours |
| overall | 746.39 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.0871 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 199 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 39000.33 | shifted gen by -14d; peak hour 2018-09-21 17:00:00 |
| net_load_peak_shift_-7d | 38712.33 | shifted gen by -7d; peak hour 2018-09-21 17:00:00 |
| net_load_peak_shift_0d | 38232.92 | shifted gen by 0d; peak hour 2018-10-02 17:00:00 |
| net_load_peak_shift_7d | 39611.75 | shifted gen by 7d; peak hour 2018-07-03 16:00:00 |
| net_load_peak_shift_14d | 38705.82 | shifted gen by 14d; peak hour 2018-07-10 16:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| FL_total_annual_TWh | 251.56 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| FL_solar_pv_annual_TWh | 51.9655 | 51.9655 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| FL_wind_annual_TWh | 0.0 | 0.0 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 20461.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 1957.3 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2732 | 0.2732 | 0.5372 | 0.5372 |
| solar-pv-dist | 0.1745 | 0.1745 | 0.3583 | 0.3583 |
| onshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.087

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 39000 | 2018-09-21 17:00:00 | 22785 |
| -7 | 38712 | 2018-09-21 17:00:00 | 22785 |
| 0 | 38233 | 2018-10-02 17:00:00 | 22785 |
| 7 | 39612 | 2018-07-03 16:00:00 | 22785 |
| 14 | 38706 | 2018-07-10 16:00:00 | 22785 |

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
| efs | 17343.3 | 3000 | 1980 | 506 | 1.52 |
| flat | 17343.3 | 1980 | 1980 | 0 | 1.00 |
| cambium_residual | 17343.3 | 6102 | 1980 | 773 | 3.08 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
