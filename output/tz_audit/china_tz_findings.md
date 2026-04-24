# China TZ bug reproduction — findings

This document is produced by ``china_tz_repro.py`` and is read-only with respect to the main pipeline. Weather series are the cached Renewables.ninja country-aggregate CSVs (MERRA-2, UTC). The solar CF model here is a simplified (GHI/1000)·PR clip; not identical to the pipeline's model, but the diurnal *shape* only depends on the timestamp alignment, which is what we are testing.

Calibration window: 2020-2024 inclusive.

## Summary table

| Country | ISO2 | Local TZ | Demand | Peak CF hr (buggy) | Peak CF hr (fixed) | Shift (hrs) | 08-18 mean CF (buggy) | 08-18 mean CF (fixed) | Delta | corr(solar, demand) buggy | corr(solar, demand) fixed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| China | CN | Asia/Shanghai | synthetic | 5 | 13 | 8 | 0.0698 | 0.4187 | -0.3489 | -0.296 | -0.2821 |
| South Korea | KR | Asia/Seoul | cached | 3 | 12 | 9 | 0.0137 | 0.3881 | -0.3744 | -0.0559 | -0.0574 |
| United States (UTC label) | US | UTC | synthetic | 18 | 18 | 0 | 0.1582 | 0.1582 | 0.0 | 0.8618 | 0.8618 |

## Diurnal CF by hour (buggy vs fixed, country-aggregate)

| Hour | CN buggy | CN fixed | KR buggy | KR fixed | US buggy | US fixed |
|---|---|---|---|---|---|---|
| 0 | 0.1827 | 0.0000 | 0.3709 | 0.0000 | 0.0903 | 0.0903 |
| 1 | 0.3128 | 0.0000 | 0.4785 | 0.0000 | 0.0448 | 0.0448 |
| 2 | 0.4397 | 0.0000 | 0.5450 | 0.0000 | 0.0223 | 0.0223 |
| 3 | 0.5358 | 0.0000 | 0.5647 | 0.0000 | 0.0123 | 0.0123 |
| 4 | 0.5876 | 0.0009 | 0.5366 | 0.0000 | 0.0069 | 0.0069 |
| 5 | 0.5893 | 0.0060 | 0.4640 | 0.0030 | 0.0035 | 0.0035 |
| 6 | 0.5419 | 0.0261 | 0.3550 | 0.0339 | 0.0014 | 0.0014 |
| 7 | 0.4526 | 0.0812 | 0.2248 | 0.1118 | 0.0005 | 0.0005 |
| 8 | 0.3351 | 0.1827 | 0.1038 | 0.2380 | 0.0001 | 0.0001 |
| 9 | 0.2098 | 0.3128 | 0.0307 | 0.3709 | 0.0002 | 0.0002 |
| 10 | 0.1044 | 0.4397 | 0.0025 | 0.4785 | 0.0018 | 0.0018 |
| 11 | 0.0384 | 0.5358 | 0.0000 | 0.5450 | 0.0122 | 0.0122 |
| 12 | 0.0094 | 0.5876 | 0.0000 | 0.5647 | 0.0451 | 0.0451 |
| 13 | 0.0009 | 0.5893 | 0.0000 | 0.5366 | 0.1130 | 0.1130 |
| 14 | 0.0000 | 0.5419 | 0.0000 | 0.4640 | 0.2103 | 0.2103 |
| 15 | 0.0000 | 0.4526 | 0.0000 | 0.3550 | 0.3170 | 0.3170 |
| 16 | 0.0000 | 0.3351 | 0.0000 | 0.2248 | 0.4094 | 0.4094 |
| 17 | 0.0000 | 0.2098 | 0.0000 | 0.1038 | 0.4727 | 0.4727 |
| 18 | 0.0000 | 0.1044 | 0.0000 | 0.0307 | 0.4997 | 0.4997 |
| 19 | 0.0000 | 0.0384 | 0.0000 | 0.0025 | 0.4876 | 0.4876 |
| 20 | 0.0009 | 0.0094 | 0.0030 | 0.0000 | 0.4386 | 0.4386 |
| 21 | 0.0060 | 0.0009 | 0.0339 | 0.0000 | 0.3585 | 0.3585 |
| 22 | 0.0261 | 0.0000 | 0.1118 | 0.0000 | 0.2623 | 0.2623 |
| 23 | 0.0812 | 0.0000 | 0.2380 | 0.0000 | 0.1658 | 0.1658 |

## US effective offset

Peak-hour of solar CF in the US country-aggregate weather (as-is, UTC) is **hour 18 UTC**. If solar noon falls at 12:00 local under a single notional TZ, this implies local = UTC-6h — i.e. the area-weighted US solar CF behaves like a time series in 'UTC-6'.
For context: Eastern = UTC-5, Central = UTC-6, Mountain = UTC-7, Pacific = UTC-8. The US area-weighted centroid falls ~UTC-6 (central US). Because the US pipeline's demand is ALSO UTC (fetched from EIA and explicitly tz_localized to UTC), solar CF and demand are aligned on the same index and there is no index-mismatch bug — the diurnal profiles are coherent UTC profiles. The only 'cost' is that both profiles are expressed in UTC, which distorts what 'hour-of-day' means for a country that spans multiple zones; this is a modelling choice, not a bug.
