"""
Minimal reproduction of the China timezone bug in energy_timeslice_pipeline.py.

This script is READ-ONLY: it does not modify the main pipeline or any cached
data. It loads the existing Renewables.ninja weather CSV for China (UTC),
computes a simplified solar capacity factor, and then shows the shape of the
hourly-of-day CF curve under the two alignments:

  (a) "buggy"  : treat the UTC weather index as if it were local time
                 (this mirrors the current pipeline, which groups on .hour
                 of a UTC-indexed series and looks it up by .hour of an
                 Asia/Shanghai-indexed demand series)
  (b) "fixed"  : tz_convert the weather to Asia/Shanghai before grouping

Then we build a stylized Chinese demand curve (morning+evening double peak,
plausible for national residential+commercial load) LOCAL to Asia/Shanghai,
and compute solar-demand correlation under each alignment.

We do the same for South Korea (Asia/Seoul) and for the United States
(UTC, but with multiple local TZs in the underlying aggregation) as a
control for Task C.

Outputs are appended to ``china_tz_findings.md`` in the same folder.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\RobbieOrvis\Models\Global Electricity File Creator")
WEATHER_DIR = ROOT / "data" / "weather"
OUT_DIR = ROOT / "output" / "tz_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CAL_YEARS = (2020, 2024)


def load_weather_utc(country_iso2: str) -> pd.DataFrame:
    """Load Renewables.ninja weather (country-aggregated, UTC)."""
    variables = {
        "irradiance_surface": f"ninja-weather-country-{country_iso2}-irradiance_surface_area_wtd-merra2.csv",
        "temperature": f"ninja-weather-country-{country_iso2}-temperature_area_wtd-merra2.csv",
        "wind_speed": f"ninja-weather-country-{country_iso2}-wind_speed_area_wtd-merra2.csv",
    }
    frames = []
    for var, fname in variables.items():
        path = WEATHER_DIR / fname
        # Detect comment-prefixed header rows, same logic as pipeline
        skip = 0
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith('"#'):
                    skip += 1
                else:
                    break
        df = pd.read_csv(path, skiprows=skip)
        df = df.rename(columns={df.columns[0]: "time"})
        df["time"] = pd.to_datetime(df["time"], utc=True)
        df = df.set_index("time")
        # country aggregate is the first column after "time"
        df = df[[country_iso2]].rename(columns={country_iso2: var})
        frames.append(df)
    return pd.concat(frames, axis=1)


def simple_pv_cf(ghi: pd.Series, temp: pd.Series) -> pd.Series:
    """Simplified PV CF model (direct, tz-agnostic).

    Good enough for a diurnal shape check. Not used for any calibration.
    Nominal system, constant temperature coefficient, clipped to [0, 1].
    """
    rated_ghi = 1000.0
    pr = 0.85 - 0.004 * (temp - 25.0).clip(lower=-25, upper=40)
    cf = (ghi / rated_ghi) * pr
    return cf.clip(lower=0, upper=1)


def simple_wind_cf(wind: pd.Series) -> pd.Series:
    """Simplified wind CF model. Not used here for shape alignment; kept
    for completeness if one wants to inspect the wind-demand correlation.
    """
    cut_in, rated, cut_out = 3.0, 12.0, 25.0
    cf = np.where(
        wind < cut_in, 0.0,
        np.where(wind < rated, ((wind - cut_in) / (rated - cut_in)) ** 3,
                 np.where(wind < cut_out, 1.0, 0.0))
    )
    return pd.Series(cf, index=wind.index).clip(lower=0, upper=1)


def stylized_local_demand(local_index: pd.DatetimeIndex, country: str) -> pd.Series:
    """A rough but realistic local-time demand profile.

    China: morning peak ~10:00, evening peak ~20:00 (summer A/C, lighting).
    Korea: morning peak ~11:00, evening peak ~20:00.
    US (national): flatter morning, evening peak ~18:00 local.

    This is SYNTHETIC but is labeled local time. Only the diurnal shape
    affects the correlation analysis.
    """
    hr = local_index.hour + local_index.minute / 60.0
    if country == "CN":
        base = (
            0.55
            + 0.12 * np.sin((hr - 10) * np.pi / 12) ** 2     # morning hump
            + 0.30 * np.exp(-((hr - 20) ** 2) / (2 * 2.5**2))  # evening peak
        )
    elif country == "KR":
        base = (
            0.55
            + 0.15 * np.sin((hr - 11) * np.pi / 12) ** 2
            + 0.28 * np.exp(-((hr - 20) ** 2) / (2 * 2.0**2))
        )
    else:  # US national, aggregated across TZs -> flatter, smeared
        base = (
            0.55
            + 0.10 * np.sin((hr - 10) * np.pi / 12) ** 2
            + 0.25 * np.exp(-((hr - 18) ** 2) / (2 * 3.0**2))
        )
    # weekday dip; weekly seasonal modest swing
    dow = local_index.dayofweek
    weekday_factor = np.where(dow >= 5, 0.92, 1.0)
    season = 1.0 + 0.08 * np.cos((local_index.dayofyear - 200) * 2 * np.pi / 365)
    return pd.Series(base * weekday_factor * season, index=local_index, name="load")


def load_korean_demand() -> Optional[pd.Series]:
    """Load cached KRO daily-hourly CSVs into an hourly series tz'd to Asia/Seoul."""
    paths = sorted((ROOT / "data" / "manual_downloads").glob("KRO_demand_*.csv"))
    if not paths:
        return None
    pieces = []
    for p in paths:
        try:
            df = pd.read_csv(p, encoding="cp949")
        except Exception:
            df = pd.read_csv(p, encoding="latin1")
        date_col = df.columns[0]
        hour_cols = list(df.columns[1:])
        if len(hour_cols) != 24:
            continue
        long = df.melt(id_vars=[date_col], value_vars=hour_cols,
                       var_name="hour_label", value_name="load")
        long["hour"] = np.arange(len(long)) % 24  # 1..24 -> 0..23
        # build timestamps: midnight local + hour
        dates = pd.to_datetime(long[date_col], errors="coerce")
        ts = dates + pd.to_timedelta(long["hour"], unit="h")
        s = pd.Series(long["load"].values, index=ts, name="load").dropna()
        s.index = s.index.tz_localize("Asia/Seoul", nonexistent="shift_forward",
                                      ambiguous="NaT")
        s = s[~s.index.isna()]
        pieces.append(s)
    if not pieces:
        return None
    return pd.concat(pieces).sort_index()


def diurnal_mean(cf: pd.Series) -> pd.Series:
    """Mean CF by hour-of-day (0..23)."""
    return cf.groupby(cf.index.hour).mean()


def report_country(
    country_iso2: str,
    local_tz: str,
    label: str,
    cal_years=CAL_YEARS,
    demand_series: Optional[pd.Series] = None,
    demand_tz: Optional[str] = None,
) -> dict:
    """Return a dict of metrics for the country under the two alignments."""
    w = load_weather_utc(country_iso2)
    w = w[(w.index.year >= cal_years[0]) & (w.index.year <= cal_years[1])]
    solar_cf_utc = simple_pv_cf(w["irradiance_surface"], w["temperature"])

    # (a) buggy: as-if local. This is what the pipeline effectively does
    # when it groups on the UTC-indexed CF .hour and then looks it up using
    # the local-tz demand .hour.
    solar_cf_aslocal = solar_cf_utc.copy()
    solar_cf_aslocal.index = solar_cf_aslocal.index.tz_convert("UTC").tz_localize(None)

    # (b) fixed: tz_convert to the real local TZ
    solar_cf_local = solar_cf_utc.tz_convert(local_tz)
    solar_cf_local_naive = pd.Series(
        solar_cf_local.values,
        index=solar_cf_local.index.tz_localize(None),
        name="solar_cf_local",
    )

    peak_buggy = int(diurnal_mean(solar_cf_aslocal).idxmax())
    peak_fixed = int(diurnal_mean(solar_cf_local_naive).idxmax())

    # Daytime mean 08:00-18:00 (inclusive of 08..17)
    def daytime_mean(s: pd.Series) -> float:
        return float(s[(s.index.hour >= 8) & (s.index.hour < 18)].mean())

    dt_buggy = daytime_mean(solar_cf_aslocal)
    dt_fixed = daytime_mean(solar_cf_local_naive)

    # Demand for correlation
    if demand_series is None:
        # synthesize a local-time demand on the overlap
        local_idx = solar_cf_local_naive.index
        demand = stylized_local_demand(local_idx, country_iso2)
        demand_source = "synthetic"
    else:
        demand = demand_series
        if demand.index.tz is None and demand_tz is not None:
            demand.index = demand.index.tz_localize(demand_tz, nonexistent="shift_forward", ambiguous="NaT")
            demand = demand[~demand.index.isna()]
        demand_source = "cached"

    # Buggy correlation: take the UTC cf values but *index them as local
    # naive*, then intersect with the local naive demand. This simulates
    # the pipeline's (doy, hour) lookup mis-alignment.
    if demand.index.tz is not None:
        demand_naive = pd.Series(demand.values,
                                 index=demand.index.tz_localize(None),
                                 name="load")
    else:
        demand_naive = demand

    common_buggy = solar_cf_aslocal.index.intersection(demand_naive.index)
    common_fixed = solar_cf_local_naive.index.intersection(demand_naive.index)
    corr_buggy = float(solar_cf_aslocal.loc[common_buggy].corr(demand_naive.loc[common_buggy]))
    corr_fixed = float(solar_cf_local_naive.loc[common_fixed].corr(demand_naive.loc[common_fixed]))

    # Average diurnals for the output table
    du_buggy = diurnal_mean(solar_cf_aslocal).round(4).to_dict()
    du_fixed = diurnal_mean(solar_cf_local_naive).round(4).to_dict()

    return {
        "country": label,
        "iso2": country_iso2,
        "local_tz": local_tz,
        "demand_source": demand_source,
        "peak_hour_buggy": peak_buggy,
        "peak_hour_fixed": peak_fixed,
        "peak_shift_hours": min((peak_buggy - peak_fixed) % 24,
                                 (peak_fixed - peak_buggy) % 24),
        "daytime_mean_buggy": round(dt_buggy, 4),
        "daytime_mean_fixed": round(dt_fixed, 4),
        "daytime_mean_delta": round(dt_buggy - dt_fixed, 4),
        "corr_solar_demand_buggy": round(corr_buggy, 4),
        "corr_solar_demand_fixed": round(corr_fixed, 4),
        "diurnal_buggy": du_buggy,
        "diurnal_fixed": du_fixed,
    }


def format_table(rows: list[dict]) -> str:
    cols = [
        ("country", "Country"),
        ("iso2", "ISO2"),
        ("local_tz", "Local TZ"),
        ("demand_source", "Demand"),
        ("peak_hour_buggy", "Peak CF hr (buggy)"),
        ("peak_hour_fixed", "Peak CF hr (fixed)"),
        ("peak_shift_hours", "Shift (hrs)"),
        ("daytime_mean_buggy", "08-18 mean CF (buggy)"),
        ("daytime_mean_fixed", "08-18 mean CF (fixed)"),
        ("daytime_mean_delta", "Delta"),
        ("corr_solar_demand_buggy", "corr(solar, demand) buggy"),
        ("corr_solar_demand_fixed", "corr(solar, demand) fixed"),
    ]
    header = "| " + " | ".join(h for _, h in cols) + " |"
    sep = "|" + "|".join(["---"] * len(cols)) + "|"
    lines = [header, sep]
    for r in rows:
        lines.append("| " + " | ".join(str(r[k]) for k, _ in cols) + " |")
    return "\n".join(lines)


def diurnal_table(rows: list[dict]) -> str:
    lines = ["| Hour | " + " | ".join(f"{r['iso2']} buggy | {r['iso2']} fixed" for r in rows) + " |"]
    lines.append("|" + "|".join(["---"] * (1 + 2 * len(rows))) + "|")
    for h in range(24):
        cells = [str(h)]
        for r in rows:
            cells.append(f"{r['diurnal_buggy'].get(h, '--'):.4f}" if isinstance(r['diurnal_buggy'].get(h), float) else str(r['diurnal_buggy'].get(h, '--')))
            cells.append(f"{r['diurnal_fixed'].get(h, '--'):.4f}" if isinstance(r['diurnal_fixed'].get(h), float) else str(r['diurnal_fixed'].get(h, '--')))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    rows = []

    # China: no cached native demand; use synthetic local profile
    rows.append(report_country("CN", "Asia/Shanghai", "China"))

    # Korea: real KEPCO hourly demand cached
    kr_demand = load_korean_demand()
    rows.append(
        report_country(
            "KR", "Asia/Seoul", "South Korea",
            demand_series=kr_demand,
        )
    )

    # US: UTC aggregation; compute "effective" offset from peak hour
    rows.append(
        report_country(
            "US", "UTC", "United States (UTC label)",
        )
    )
    # Re-analyze US with an equivalent-single-TZ guess: effective offset =
    # peak_hour_fixed - 12 (solar noon); negative implies UTC lags local by
    # that many hours. For a contiguous-US weighted mean, solar noon in
    # weighted local time is ~17:30 UTC (i.e. ~-5.5h avg).
    us_peak_utc = rows[-1]["peak_hour_fixed"]
    # Solar noon is ~12:00 local, so local_hour = UTC_hour - offset_hours.
    # If peak_UTC = 18, local noon is at UTC 18 -> local = UTC - 6 -> offset = -6.
    implied_offset = 12 - us_peak_utc  # hours: local = UTC + implied_offset

    # Write findings
    findings_md = OUT_DIR / "china_tz_findings.md"
    with open(findings_md, "w", encoding="utf-8") as fh:
        fh.write("# China TZ bug reproduction — findings\n\n")
        fh.write("This document is produced by ``china_tz_repro.py`` and is read-only ")
        fh.write("with respect to the main pipeline. Weather series are the cached ")
        fh.write("Renewables.ninja country-aggregate CSVs (MERRA-2, UTC). The solar ")
        fh.write("CF model here is a simplified (GHI/1000)·PR clip; not identical to ")
        fh.write("the pipeline's model, but the diurnal *shape* only depends on the ")
        fh.write("timestamp alignment, which is what we are testing.\n\n")
        fh.write(f"Calibration window: {CAL_YEARS[0]}-{CAL_YEARS[1]} inclusive.\n\n")
        fh.write("## Summary table\n\n")
        fh.write(format_table(rows))
        fh.write("\n\n")
        fh.write("## Diurnal CF by hour (buggy vs fixed, country-aggregate)\n\n")
        fh.write(diurnal_table(rows))
        fh.write("\n\n")
        fh.write("## US effective offset\n\n")
        fh.write(f"Peak-hour of solar CF in the US country-aggregate weather ")
        fh.write(f"(as-is, UTC) is **hour {us_peak_utc} UTC**. If solar noon ")
        fh.write("falls at 12:00 local under a single notional TZ, this implies ")
        fh.write(f"local = UTC{implied_offset:+d}h — i.e. the area-weighted US ")
        fh.write(f"solar CF behaves like a time series in 'UTC{implied_offset:+d}'.\n")
        fh.write("For context: Eastern = UTC-5, Central = UTC-6, Mountain = UTC-7, ")
        fh.write("Pacific = UTC-8. The US area-weighted centroid falls ~UTC-6 ")
        fh.write("(central US). Because the US pipeline's demand is ALSO UTC ")
        fh.write("(fetched from EIA and explicitly tz_localized to UTC), solar ")
        fh.write("CF and demand are aligned on the same index and there is no ")
        fh.write("index-mismatch bug — the diurnal profiles are coherent UTC ")
        fh.write("profiles. The only 'cost' is that both profiles are expressed ")
        fh.write("in UTC, which distorts what 'hour-of-day' means for a country ")
        fh.write("that spans multiple zones; this is a modelling choice, not a bug.\n")
    print(f"Wrote {findings_md}")


if __name__ == "__main__":
    main()
