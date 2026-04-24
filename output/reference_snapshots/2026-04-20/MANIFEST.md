# Reference Snapshot - 2026-04-20

Frozen copy of the most recent completed pipeline runs under `output/` as of 2026-04-20.

- Snapshot location: `output/reference_snapshots/2026-04-20/`
- Total files (excluding MANIFEST): 130
- Total bytes: 2,394,711
- Python: `Python 3.14.4`
- Git commit: (no commits yet on branch `master`; git log says: `fatal: your current branch 'master' does not have any commits yet`)

### git status --short at capture time

```
?? .env
?? .idea/
?? .vendor/
?? HANDOFF.md
?? README.md
?? __pycache__/
?? data/
?? energy_timeslice_pipeline.py
?? output/
```

## Headline numbers

NRMSE values; dimensionless unless noted. `pinned` / `unpinned` refer to the `clustering_comparison` rows comparing representative-day reconstructions of net load with and without peak-day pinning (where available).

| Run | Demand hourly (raw -> scaled -> seas-cal) NRMSE | Demand monthly-mean (raw/scaled/seas-cal) NRMSE | Demand monthly-peak (raw/scaled/seas-cal) NRMSE | Net-load pinned NRMSE | Net-load unpinned NRMSE |
|---|---|---|---|---|---|
| China 2018 | 14169.1799 / 0.2772 / 0.2693 | 13627.0336 / 0.0675 / 1.13e-16 | 15628.4284 / 0.1610 / 0.1568 | n/a | n/a |
| SouthKorea 2025 | 19470.7502 / 0.2954 / 0.2859 | 18375.3646 / 0.0658 / 1.30e-16 | 20060.9504 / 0.1288 / 0.0952 | 0.1523 | 0.7625 |
| UnitedStates 2025 (timeslice) | 16043.2808 / 0.4297 / 0.4228 | 14873.5016 / 0.0552 / 1.37e-16 | 17893.2818 / 0.2216 / 0.2021 | 0.3335 | 0.2740 |
| UnitedStates 2025 (EFS_test) | 0.2082 / 0.2038 / 0.2017 | 0.0758 / 0.0262 / 1.22e-16 | 0.0685 / 0.0685 / 0.0611 | 0.3891 | 0.3473 |

### Demand calibration RMSE stages (absolute RMSE, units match the underlying series)

| Run | raw_hourly RMSE | scaled_hourly RMSE | seasonally_calibrated_hourly RMSE | seas-cal monthly_mean RMSE | seas-cal monthly_peak RMSE |
|---|---|---|---|---|---|
| China 2018 | 11160701648.39 | 218357.37 | 212151.88 | 8.89e-11 | 147707.63 |
| SouthKorea 2025 | 1255916104.19 | 19053.09 | 18442.67 | 8.40e-12 | 8020.24 |
| UnitedStates 2025 (timeslice) | 7870240939.47 | 210818.51 | 207419.84 | 6.72e-11 | 125870.70 |
| UnitedStates 2025 (EFS_test) | 99465.48 | 97358.91 | 96389.86 | 5.82e-11 | 36738.07 |

## Runs included

### China_timeslice_results

China (year 2018): 7 CSVs only. No xlsx exported. No `*_EPS/` directory. Metrics file lacks `clustering_comparison` (pinned vs unpinned) rows - only the single `representative_day_hourly_reconstruction` clustering stage is present.

### SouthKorea_timeslice_results

SouthKorea (year 2025): full run - 1 xlsx, 6 CSVs, plus `_EPS/` directory containing EPS_export_coverage.csv, 2 EPS xlsx workbooks, SHELF/ (23 CSVs) and SYSHECF/ (25 CSVs). Metrics file includes pinned/unpinned clustering comparison.

### UnitedStates_timeslice_results

UnitedStates (year 2025, timeslice): 6 CSVs. No xlsx, no EPS directory. Metrics file includes pinned/unpinned clustering comparison.

### UnitedStates_EFS_test

UnitedStates (year 2025, EFS test): 2 timestamped xlsx workbooks (`UnitedStates_EFS_test.xlsx` from 2026-03-17 16:10 and `UnitedStates_EFS_test_20260317_163102.xlsx` from 16:31), Metrics.csv (2026-03-17 16:37), and `_EPS/` directory with EPS_export_coverage.csv, 2 EPS xlsx workbooks, SHELF/ (23 CSVs) and SYSHECF/ (25 CSVs). Note: this run has two xlsx outputs; the Metrics.csv mtime is later than either xlsx, suggesting metrics were regenerated after the second xlsx export.

## File manifest

All paths relative to `output/reference_snapshots/2026-04-20/`.

| Relative path | Size (bytes) | SHA-256 |
|---|---:|---|
| `timeslice_run_metrics_summary.csv` | 9986 | `169022e8bb88d11ca1533cbf264559624286a0703baea0dc9f20c5c24c853875` |
| `China_timeslice_results/China_timeslice_results_Metrics.csv` | 2497 | `b0a9b07819052a1a5570c2878ceee3686f40388e1475afcb4fd4a50f77183cc9` |
| `China_timeslice_results/China_timeslice_results_SHELF.csv` | 51476 | `ab118670f57b6844c8e32a10e7b8cd7b1d717f581e2e5ec9ddbc8ff7ee85d220` |
| `China_timeslice_results/China_timeslice_results_SHELF_SUMMARY.csv` | 6226 | `1acbc30cfd5699f1c3a176d529887f134e45bed5498cb87447deeb4c0f0e8611` |
| `China_timeslice_results/China_timeslice_results_SYSHECF.csv` | 7868 | `9807d3a4013d7a99c543ab3fd5d4f04088172eab51f71fb0bc44b16eda5981e1` |
| `China_timeslice_results/China_timeslice_results_SYSHECF_SUMMARY.csv` | 354 | `04f280884ff99cbee93caf852251ba856df561d4a6555a4151fd1d288ceaf99e` |
| `China_timeslice_results/China_timeslice_results_TimesliceInfo.csv` | 615 | `189918bda514b395e7da92f96eed274f1084888990e3f1c66232618206ce874a` |
| `China_timeslice_results/China_timeslice_results_TimesliceMap.csv` | 377799 | `04deb4e8de5c13f7739ac797f98fd05fef45db5a55c8523cd68952e5bdebc77e` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results.xlsx` | 170750 | `d7b35cdd8c58615b96767fccaa235838d91b6aa3739dbd563ab1ae150b188d00` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_Metrics.csv` | 2893 | `4f7d5a173b13bf52b74404237c11e5ae0dd39a54bb09210d11767aabecb89a20` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_SHELF.csv` | 51570 | `418da9428d04c9fab623d4aecb12d0848ddf81abe17601a0b121571a4bdbb448` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_SHELF_SUMMARY.csv` | 6214 | `0587fb59ea7e9939688a430b3f2c89197994dc251e83ebc2be1c08fbb1e31091` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_SYSHECF.csv` | 7429 | `24a550f4d0a422673c21056449935a6e2c6fe671562efe0f77469fcec67d18ef` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_SYSHECF_SUMMARY.csv` | 356 | `f5345ed81054f956371ef4a92594c461fd0e8517a5fa827c8eb4dd0f6e29030d` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_TimesliceInfo.csv` | 700 | `f6f0413d1881a05f582c7cd073c9f37e89b4db2671113dfb27f27c3c7dd86702` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_TimesliceMap.csv` | 386583 | `03ea15f73fc31395096c3fcad7a1a08fe78de73aa435306872e46b9afbfb3ac3` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/EPS_export_coverage.csv` | 15300 | `00e430023c46568c9bbc4495d86be5ce7c35a38b11f356ac5378c0ece6d5b671` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/Seasonal Hourly Equipment Load Factors by End Use.xlsx` | 60351 | `322cc4a5aec2429cf4ddfdbc62fb6549633aaffda6ec66e6af137dc15a128fb8` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx` | 50846 | `e2c831923604a4a628b8e02f810945fe8a67eeaf13f8add0e90575ee5695fa18` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-HDVs.csv` | 3545 | `01c31c2b9acb33b5bd25e81d56db25a4fc500f4d8b3c893191932cf69e9f251c` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-LDVs.csv` | 3523 | `59f98ccd5c3771da9ba43524e15753d1c9e146f26a2a5528b1c28b1cbf0e61a6` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-aircraft.csv` | 3535 | `add7d974b59d814400eb9b55c2e91281c59e18c4faf26a45cdd6003b62678266` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-commercial-appliances.csv` | 3526 | `f65bf52f626747ab7d614c8b41bd84842aef8dd9a096e570cb036efefd74797b` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-commercial-cooling.csv` | 3500 | `9991a4870c5eb07ffd01e66910fbaea57eb219287b8597ca8993e8e009f9f159` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-commercial-envelope.csv` | 871 | `85c96cf02a96652318b1962c5b478702073e1458f8851db23f7b9b968c44dbb8` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-commercial-heating.csv` | 3515 | `ca5c962e9eec22d7dad1a0eba50bbfbd138fa6eff75877cef5a411b1efcb9bd3` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-commercial-lighting.csv` | 3522 | `810509b5dfdb4122df7f4e7c9c8d874be984e484207469eba35e312c107da2d1` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-commercial-other.csv` | 3522 | `810509b5dfdb4122df7f4e7c9c8d874be984e484207469eba35e312c107da2d1` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-datacenters.csv` | 3607 | `2f1e4f84f03dc1c5bea714d75b0b6a906a7a155c2f42fdbccb0ebaec3e3b3f2d` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-days-per-timeslice.csv` | 105 | `6fde47d409c4079bd4f7b955f9afce61b982cb2aa50e028d055e5d9da05107f9` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-district-heat-hydrogen.csv` | 3550 | `654517e8e1b6441f452ad4c81be512ca8e12d129f95a9e330e4aa6ae7c854b43` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-geoeng.csv` | 3550 | `654517e8e1b6441f452ad4c81be512ca8e12d129f95a9e330e4aa6ae7c854b43` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-industry.csv` | 3550 | `654517e8e1b6441f452ad4c81be512ca8e12d129f95a9e330e4aa6ae7c854b43` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-motorbikes.csv` | 3523 | `59f98ccd5c3771da9ba43524e15753d1c9e146f26a2a5528b1c28b1cbf0e61a6` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-rail.csv` | 3535 | `add7d974b59d814400eb9b55c2e91281c59e18c4faf26a45cdd6003b62678266` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-residential-appliances.csv` | 3542 | `0c95d5722f81c7402410c28b2c6045f474fb6cd3b4bdd41cb822287bcdf7452e` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-residential-cooling.csv` | 3519 | `0595242e7fc1d4f39b1d73343b423b77dac5a084a1f588f538c1e8e09a79c25b` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-residential-envelope.csv` | 871 | `85c96cf02a96652318b1962c5b478702073e1458f8851db23f7b9b968c44dbb8` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-residential-heating.csv` | 3514 | `a5817b55ecd50720a5804ff15594de51d424c9b56c988e8b7e9eee2fbda239bb` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-residential-lighting.csv` | 3494 | `a6361d9e9ed76faf3c9c4ad7935ec7f7e3b6b6e1362f5c16147e290657732ffd` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-residential-other.csv` | 3542 | `5986cd7795cf57451dfcc6a656ca24e72106a729bdb3306306478464af45840b` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SHELF/SHELF-ships.csv` | 3535 | `add7d974b59d814400eb9b55c2e91281c59e18c4faf26a45cdd6003b62678266` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-MSW.csv` | 2014 | `e10636914fbdd7e836db3ccd7c379831f89c212d4aeaa8f2b16ee2bc2bc6cc9f` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-SMR.csv` | 2007 | `28232ef7a0acd88df2e854b41999166b589f23fa534a5eaf670c885a89c91fa0` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-biomass-CCS.csv` | 1015 | `1227f1e025754803fd10ce038318a422255cc4489d015a14edb9c807a08e3bd1` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-biomass.csv` | 2014 | `e10636914fbdd7e836db3ccd7c379831f89c212d4aeaa8f2b16ee2bc2bc6cc9f` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-combined-cycle-CCS.csv` | 1015 | `1227f1e025754803fd10ce038318a422255cc4489d015a14edb9c807a08e3bd1` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-combined-cycle.csv` | 2008 | `8faee51e32d5b295b5e80cead58747bba6fadb781e33ffd8f6950a056d4b7c94` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-crude-oil.csv` | 583 | `3daad1764ce4684f6742df80c176d413035f537b7a1edd9199539469e9063703` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-geothermal.csv` | 2023 | `ca5188d7a76fbc8043b4ffcda2976550b1522eaead55b15162a2cb864f926c8f` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-hard-coal-CCS.csv` | 1015 | `1227f1e025754803fd10ce038318a422255cc4489d015a14edb9c807a08e3bd1` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-hard-coal.csv` | 2011 | `0bc8ad6a8ed442c577d221e0e41b6d4f18b758c7012b1dbc74fcbdecce5bcce6` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-heavy-or-residual-oil.csv` | 583 | `3daad1764ce4684f6742df80c176d413035f537b7a1edd9199539469e9063703` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-hydro.csv` | 2010 | `1f2e0916c61dd9da4ac7a307c315d91b1a3073dd70c0ee1c01feea4e87c882e1` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-hydrogen-CC.csv` | 2008 | `bf79b656122ad95d7ce1efd895d122ea8cafc8e664b77eb1c0868897a8b6316a` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-hydrogen-CT.csv` | 2006 | `c1097b66c815afc91b1f96cabdd8e14021d0c1db97bae54976f50b6a21f52563` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-lignite-CCS.csv` | 1015 | `1227f1e025754803fd10ce038318a422255cc4489d015a14edb9c807a08e3bd1` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-lignite.csv` | 2009 | `7804005416475e3d2e6589b525b6986eff64f962d7e84afa579f6bcd3f0add4d` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-natural-gas-peaker.csv` | 2016 | `3b81a3bec42d0f205279ca89f7394719ca3ae9a11b427dc50ea3c3e52a5f82ee` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-nuclear.csv` | 2007 | `28232ef7a0acd88df2e854b41999166b589f23fa534a5eaf670c885a89c91fa0` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-offshore-wind.csv` | 3175 | `5427a65864a416d975d9c898bc0c4bd0674d4323f7192ba938e8543e9298fd17` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-onshore-wind.csv` | 3175 | `5427a65864a416d975d9c898bc0c4bd0674d4323f7192ba938e8543e9298fd17` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-petroleum.csv` | 2006 | `c1097b66c815afc91b1f96cabdd8e14021d0c1db97bae54976f50b6a21f52563` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-pumped-hydro.csv` | 1413 | `0aeccf70698f52f698e296ea2d1cafb7691d794402870a3cdb269351e2aff22a` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-solar-pv-dist.csv` | 2073 | `cc34fda7c7554383873f13543aa009da98b574771115b190f267412d72095172` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-solar-pv.csv` | 2060 | `2d8300e5d9bb420eb1a09acfd18c9b092a6197700ce8be278034d0d02dbb8263` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-solar-thermal.csv` | 1282 | `44b528ec86461ae4539142a537819faedcaac81337b77335b5dd6178eb0b2ac1` |
| `SouthKorea_timeslice_results/SouthKorea_timeslice_results_EPS/SYSHECF/SYSHECF-steam-turbine.csv` | 2008 | `8faee51e32d5b295b5e80cead58747bba6fadb781e33ffd8f6950a056d4b7c94` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test.xlsx` | 183324 | `0de02274749f94269c23d232552844e5a6ee86d400a571acf683c04e6503ee58` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_20260317_163102.xlsx` | 183620 | `44dfea33a6684175fd056000541a76738d21432ef0f08bb9ac0bd9b406c2994d` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_Metrics.csv` | 2978 | `5471fe3ced23a9f3d985ad0d362b40d01b6e022de94b8ed25145e376d56c5b3b` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/EPS_export_coverage.csv` | 15843 | `55b8e65077edab08229d67d5598b490681a1bc6b78673f377d8acbbd46d97ed2` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/Seasonal Hourly Equipment Load Factors by End Use.xlsx` | 60433 | `c40ee24d09f80dc09065575902b2aca2721387ed3fe8667b742c8ea900acfb90` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx` | 51902 | `03a50d9d9a7177a9817cac2b0ab4e9ea7a9ae874483a3851d52439e982ec95d6` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-HDVs.csv` | 3564 | `ad3321fe567cb78670dfc5ac12d79d2343b3c80bbef4379a6a1235db6233adf5` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-LDVs.csv` | 3520 | `a04a457b9a0b0dbbfb0887cf004603a813135331583034c46a4255c72c1d70d1` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-aircraft.csv` | 3535 | `de931adf486c2fd3ba5e3bb886fcdec26eb39d0deddc13f85727a85917e30452` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-commercial-appliances.csv` | 3506 | `f598ac2cd607426d60eb4aa8a92df043688ace0e598c660d7aac33226dd395dc` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-commercial-cooling.csv` | 3512 | `959d3cbcd2d6d0c689c4502d2bea304d96b5e1396f833a1d4021997a7f921150` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-commercial-envelope.csv` | 871 | `85c96cf02a96652318b1962c5b478702073e1458f8851db23f7b9b968c44dbb8` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-commercial-heating.csv` | 3521 | `9bc606f69f0957c2a4826059d3cc72bd70280150831345dff8866ff9e67493e9` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-commercial-lighting.csv` | 3466 | `d5cd38d8186f07348006dda77d8963411a576c8b528f810dee1067354f9a26de` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-commercial-other.csv` | 3466 | `d5cd38d8186f07348006dda77d8963411a576c8b528f810dee1067354f9a26de` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-datacenters.csv` | 3607 | `2f1e4f84f03dc1c5bea714d75b0b6a906a7a155c2f42fdbccb0ebaec3e3b3f2d` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-days-per-timeslice.csv` | 106 | `bfb90b08728e2c28195b6a5953b44b8daef2b6bac3f2eaf899d6423334abb938` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-district-heat-hydrogen.csv` | 3571 | `cad18d3c2eb159580acdc98879dc6307377540e8e405e8b528334ef58dec2084` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-geoeng.csv` | 3571 | `cad18d3c2eb159580acdc98879dc6307377540e8e405e8b528334ef58dec2084` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-industry.csv` | 3571 | `cad18d3c2eb159580acdc98879dc6307377540e8e405e8b528334ef58dec2084` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-motorbikes.csv` | 3507 | `0766eec0bec3b9ee4328d40f314ce9c4ecf669b5b9b40a96b98598599af8fb6d` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-rail.csv` | 3535 | `de931adf486c2fd3ba5e3bb886fcdec26eb39d0deddc13f85727a85917e30452` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-residential-appliances.csv` | 3552 | `67c459b14920961a3421b0461023283579a06c587b39ef01fae3148d46053e86` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-residential-cooling.csv` | 3527 | `6763dcc53a7db125264772724322975437b927198dee741611d03c34347a6e3e` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-residential-envelope.csv` | 871 | `85c96cf02a96652318b1962c5b478702073e1458f8851db23f7b9b968c44dbb8` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-residential-heating.csv` | 3496 | `7d2ab9835e4342fbd5f9a8e662bd3c5bf0a830c9450e61d85f16dfd232aab7a3` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-residential-lighting.csv` | 439 | `8626a87c5f55a81524713d77438267c0deb837a047caa5256c4265be2d398a32` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-residential-other.csv` | 3524 | `7c933ed6ded141e65c403b477ef5b5434c9b346d4393185bfe98b8708592b050` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SHELF/SHELF-ships.csv` | 3535 | `de931adf486c2fd3ba5e3bb886fcdec26eb39d0deddc13f85727a85917e30452` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-MSW.csv` | 2014 | `e10636914fbdd7e836db3ccd7c379831f89c212d4aeaa8f2b16ee2bc2bc6cc9f` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-SMR.csv` | 2007 | `28232ef7a0acd88df2e854b41999166b589f23fa534a5eaf670c885a89c91fa0` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-biomass-CCS.csv` | 1015 | `1227f1e025754803fd10ce038318a422255cc4489d015a14edb9c807a08e3bd1` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-biomass.csv` | 2014 | `e10636914fbdd7e836db3ccd7c379831f89c212d4aeaa8f2b16ee2bc2bc6cc9f` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-combined-cycle-CCS.csv` | 1015 | `1227f1e025754803fd10ce038318a422255cc4489d015a14edb9c807a08e3bd1` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-combined-cycle.csv` | 2008 | `8faee51e32d5b295b5e80cead58747bba6fadb781e33ffd8f6950a056d4b7c94` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-crude-oil.csv` | 583 | `3daad1764ce4684f6742df80c176d413035f537b7a1edd9199539469e9063703` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-geothermal.csv` | 2023 | `ca5188d7a76fbc8043b4ffcda2976550b1522eaead55b15162a2cb864f926c8f` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-hard-coal-CCS.csv` | 1015 | `1227f1e025754803fd10ce038318a422255cc4489d015a14edb9c807a08e3bd1` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-hard-coal.csv` | 2011 | `0bc8ad6a8ed442c577d221e0e41b6d4f18b758c7012b1dbc74fcbdecce5bcce6` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-heavy-or-residual-oil.csv` | 583 | `3daad1764ce4684f6742df80c176d413035f537b7a1edd9199539469e9063703` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-hydro.csv` | 2010 | `1f2e0916c61dd9da4ac7a307c315d91b1a3073dd70c0ee1c01feea4e87c882e1` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-hydrogen-CC.csv` | 2008 | `bf79b656122ad95d7ce1efd895d122ea8cafc8e664b77eb1c0868897a8b6316a` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-hydrogen-CT.csv` | 2006 | `c1097b66c815afc91b1f96cabdd8e14021d0c1db97bae54976f50b6a21f52563` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-lignite-CCS.csv` | 1015 | `1227f1e025754803fd10ce038318a422255cc4489d015a14edb9c807a08e3bd1` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-lignite.csv` | 2009 | `7804005416475e3d2e6589b525b6986eff64f962d7e84afa579f6bcd3f0add4d` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-natural-gas-peaker.csv` | 2016 | `3b81a3bec42d0f205279ca89f7394719ca3ae9a11b427dc50ea3c3e52a5f82ee` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-nuclear.csv` | 2007 | `28232ef7a0acd88df2e854b41999166b589f23fa534a5eaf670c885a89c91fa0` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-offshore-wind.csv` | 3145 | `b6127b2218c6ba94b9d834c776bc9bff955a042ac41110784bbfc3421e64dc94` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-onshore-wind.csv` | 3145 | `b6127b2218c6ba94b9d834c776bc9bff955a042ac41110784bbfc3421e64dc94` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-petroleum.csv` | 2006 | `c1097b66c815afc91b1f96cabdd8e14021d0c1db97bae54976f50b6a21f52563` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-pumped-hydro.csv` | 1413 | `0aeccf70698f52f698e296ea2d1cafb7691d794402870a3cdb269351e2aff22a` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-solar-pv-dist.csv` | 2822 | `084a5a14180e24beb86016e99cd7e3daa8fbc35e8e9f2ec28fbf54eea43e0efd` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-solar-pv.csv` | 2805 | `0feebb5cc1f8f39741217b4f9c6a79d9d8a59e2c4e74ba5ce370672983c4765d` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-solar-thermal.csv` | 1282 | `44b528ec86461ae4539142a537819faedcaac81337b77335b5dd6178eb0b2ac1` |
| `UnitedStates_EFS_test/UnitedStates_EFS_test_EPS/SYSHECF/SYSHECF-steam-turbine.csv` | 2008 | `8faee51e32d5b295b5e80cead58747bba6fadb781e33ffd8f6950a056d4b7c94` |
| `UnitedStates_timeslice_results/UnitedStates_timeslice_results_Metrics.csv` | 2978 | `4eba36aac6439c10d1140a081f758160df48825eb160a224fcc2b7c95a0f8ad5` |
| `UnitedStates_timeslice_results/UnitedStates_timeslice_results_SHELF.csv` | 51527 | `e0bdbc7b3b9d63faffca7d44415ad62a84448cfa6bb2fffa4eb3f46cf277cdfd` |
| `UnitedStates_timeslice_results/UnitedStates_timeslice_results_SHELF_SUMMARY.csv` | 6231 | `130f26348c8b3b09c01c4a5b8dc86f5ed510619023eb64519570368d80eec6bc` |
| `UnitedStates_timeslice_results/UnitedStates_timeslice_results_SYSHECF.csv` | 8144 | `dd524aa72d8506982ba04b26aa53439514d9d535dd7cc6e043452cbd52f00074` |
| `UnitedStates_timeslice_results/UnitedStates_timeslice_results_SYSHECF_SUMMARY.csv` | 354 | `67935a40de05be6181ddff307b705035be09824a821f8a49808709ef7c4ea5b0` |
| `UnitedStates_timeslice_results/UnitedStates_timeslice_results_TimesliceInfo.csv` | 696 | `55a762a5817721fffcb4465caca01e6624617e5e7a5bba1723092ff38a5ff4e1` |
| `UnitedStates_timeslice_results/UnitedStates_timeslice_results_TimesliceMap.csv` | 380463 | `67490dd4381289cc84a248355566d2e8b6a9f9a9e49880a88586b9499b3c81f1` |

## Known issues at time of snapshot

This snapshot captures outputs of a pipeline with known, unfixed defects. Future regressions should be evaluated against this baseline with these caveats in mind:

- **China timezone phase-shift**: the China run applies a time-zone handling path that phase-shifts the hourly load series relative to the true local clock, biasing diurnal patterns in `China_timeslice_results_*`.
- **Naive EFS index**: the EFS export (`UnitedStates_EFS_test_EPS/*`, `SouthKorea_timeslice_results_EPS/*`) is built on a naive (timezone-unaware) datetime index and does not round-trip DST/tz boundaries correctly.
- **No state/sub-region support**: the pipeline produces country-level outputs only. Sub-national (state, province, ISO) regional disaggregation is not implemented; any downstream use that relies on state-level resolution is out of scope here.

Readers should treat this snapshot as a frozen reference for **regression comparison only**, not as a validated scientific product.
