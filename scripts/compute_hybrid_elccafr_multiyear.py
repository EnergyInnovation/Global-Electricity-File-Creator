"""Compute hybrid ELCCAfR using multi-year US weather data, capacity-weighted by state.

Data source: local Renewables.ninja country-aggregated weather files
(per-state hourly columns, 1980-2024).

CF conversion uses Pfenninger & Staffell methodology.
States weighted by ~2024 capacity distribution to approximate fleet exposure.
"""
import csv
import datetime as dt
from pathlib import Path
import numpy as np
import pandas as pd

WEATHER_DIR = Path(r"C:\Users\RobbieOrvis\Models\Global Electricity File Creator\data\weather")
OUTPUT_DIR = Path(__file__).parent / "data_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# EPS hybrid parameters
BATTERY_MW_PER_VRE = 0.5
DURATION_HR = 4
ROUND_TRIP_EFF = 0.85

WINTER_MONTHS = {10, 11, 12, 1, 2, 3}
SUMMER_MONTHS = {4, 5, 6, 7, 8, 9}
N_SUMMER_PEAK = 27
N_WINTER_PEAK = 20

YEARS_TO_USE = list(range(2010, 2025))

SLICE_ROWS = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']
HOUR_COLS = [f'Hour{h}' for h in range(24)]


# Capacity weights by US state (~2024 distribution, approximate)
WIND_WEIGHTS = {
    'US.TX': 0.24, 'US.IA': 0.08, 'US.OK': 0.07, 'US.KS': 0.05,
    'US.IL': 0.04, 'US.CA': 0.04, 'US.MN': 0.03, 'US.CO': 0.03,
    'US.NM': 0.02, 'US.ND': 0.03, 'US.SD': 0.02, 'US.NE': 0.02,
    'US.IN': 0.02, 'US.WY': 0.01, 'US.MI': 0.02, 'US.OR': 0.02,
    'US.WA': 0.01, 'US.MO': 0.01, 'US.PA': 0.01,
    # Pool for remaining states (~23%)
    'US.NY': 0.02, 'US.MT': 0.01, 'US.OH': 0.01, 'US.WI': 0.01,
    'US.ME': 0.005, 'US.WV': 0.005, 'US.VT': 0.003, 'US.NH': 0.002,
}

SOLAR_WEIGHTS = {
    'US.CA': 0.27, 'US.TX': 0.13, 'US.FL': 0.08, 'US.NC': 0.06,
    'US.AZ': 0.05, 'US.NV': 0.04, 'US.GA': 0.04, 'US.NJ': 0.03,
    'US.NY': 0.03, 'US.VA': 0.03, 'US.MA': 0.02, 'US.SC': 0.02,
    'US.MN': 0.02, 'US.UT': 0.02, 'US.CO': 0.02, 'US.IL': 0.02,
    'US.IN': 0.02, 'US.NM': 0.01, 'US.MD': 0.01, 'US.OR': 0.01,
    'US.PA': 0.01, 'US.OH': 0.01, 'US.MI': 0.01, 'US.TN': 0.01,
    'US.AR': 0.01, 'US.LA': 0.01, 'US.MS': 0.005, 'US.ID': 0.005,
}

# Offshore wind: weighted toward Atlantic coast states
OFFSHORE_WEIGHTS = {
    'US.MA': 0.35, 'US.RI': 0.15, 'US.NY': 0.20,
    'US.NJ': 0.10, 'US.VA': 0.10, 'US.MD': 0.05, 'US.NC': 0.05,
}


def read_weighted_weather(var: str, weights: dict) -> pd.Series:
    """Read weather file and compute capacity-weighted average across states."""
    path = WEATHER_DIR / f"ninja-weather-country-US-{var}_area_wtd-merra2.csv"
    df = pd.read_csv(path, skiprows=3)
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')
    # Normalize weights
    total_w = sum(weights.values())
    weighted = sum(df[state] * w for state, w in weights.items() if state in df.columns) / total_w
    return weighted


def compute_solar_cf(ghi: pd.Series, temp: pd.Series,
                      orientation_factor: float = 1.1) -> pd.Series:
    """Pfenninger & Staffell methodology."""
    ghi = ghi.clip(lower=0)
    i_poa = ghi * orientation_factor
    t_cell = temp + 0.025 * i_poa
    eta = 1.0 + (-0.004) * (t_cell - 25.0)
    cf = (i_poa / 1000.0) * eta
    return cf.clip(0, 1)


def compute_wind_cf(wind_10m: pd.Series, hub_height: float = 100.0,
                     ref_height: float = 10.0, roughness: float = 0.03,
                     cut_in: float = 3.0, rated: float = 12.0,
                     cut_out: float = 25.0) -> pd.Series:
    """Power curve with log-law scaling."""
    v_ref = wind_10m.clip(lower=0)
    v = v_ref * np.log(hub_height / roughness) / np.log(ref_height / roughness)
    cf = np.where(
        v < cut_in, 0.0,
        np.where(
            v < rated, ((v - cut_in) / (rated - cut_in)) ** 3,
            np.where(v < cut_out, 1.0, 0.0)
        )
    )
    return pd.Series(cf, index=wind_10m.index)


def compute_offshore_cf(wind_10m: pd.Series) -> pd.Series:
    return compute_wind_cf(wind_10m, hub_height=140.0, roughness=0.0002,
                            cut_in=3.5, rated=10.5, cut_out=25.0)


def dispatch_battery_day(cf_profile: np.ndarray,
                          peak_window=(17, 21),
                          battery_power: float = BATTERY_MW_PER_VRE,
                          battery_energy: float = BATTERY_MW_PER_VRE * DURATION_HR,
                          eff: float = ROUND_TRIP_EFF) -> np.ndarray:
    cf = cf_profile.copy().astype(float)
    discharge_hours = list(range(peak_window[0], peak_window[1]))
    pre_peak_hours = list(range(peak_window[0]))
    pre_peak_cfs = sorted(pre_peak_hours, key=lambda h: -cf[h])
    charge_hours = pre_peak_cfs[:4]

    battery_state = 0.0
    charge_arr = np.zeros(24)
    for h in sorted(charge_hours):
        avail = min(battery_power, cf[h])
        room = battery_energy - battery_state
        actual_charge = min(avail, room)
        if actual_charge > 0:
            battery_state += actual_charge * eff
            charge_arr[h] = actual_charge

    discharge_arr = np.zeros(24)
    for h in sorted(discharge_hours):
        actual_discharge = min(battery_power, battery_state)
        if actual_discharge > 0:
            battery_state -= actual_discharge
            discharge_arr[h] = actual_discharge

    return cf - charge_arr + discharge_arr


def synthetic_load_profile():
    summer = np.array([0.72, 0.69, 0.67, 0.66, 0.66, 0.69, 0.74, 0.80, 0.84, 0.88,
                       0.91, 0.93, 0.94, 0.95, 0.97, 0.99, 1.00, 1.00, 0.98, 0.95,
                       0.91, 0.85, 0.79, 0.74])
    winter = np.array([0.78, 0.76, 0.75, 0.74, 0.75, 0.79, 0.86, 0.93, 0.97, 0.97,
                       0.95, 0.94, 0.92, 0.90, 0.89, 0.90, 0.94, 0.99, 1.00, 0.98,
                       0.95, 0.91, 0.86, 0.81])
    return summer, winter


def reshape_year_day_hour(cf_series: pd.Series):
    by_year = {}
    for year in cf_series.index.year.unique():
        year_data = cf_series[cf_series.index.year == year]
        non_leap = year_data[~((year_data.index.month == 2) & (year_data.index.day == 29))]
        if len(non_leap) < 365 * 24:
            continue
        by_year[int(year)] = non_leap.values[:365*24].reshape(365, 24)
    return by_year


def identify_pinned_peak_days(cf_by_year: dict, n_sp: int, n_wp: int):
    summer_load, winter_load = synthetic_load_profile()
    result = {}
    for year, cfs in cf_by_year.items():
        day_months = []
        for d in range(365):
            day_date = dt.date(year, 1, 1) + dt.timedelta(days=d)
            day_months.append(day_date.month)
        day_months = np.array(day_months)

        peak_net = np.zeros(365)
        for d in range(365):
            load_profile = summer_load if day_months[d] in SUMMER_MONTHS else winter_load
            peak_net[d] = (load_profile - cfs[d]).max()

        sp_days = [d for d in range(365) if day_months[d] in SUMMER_MONTHS]
        wp_days = [d for d in range(365) if day_months[d] in WINTER_MONTHS]
        sp_sorted = sorted(sp_days, key=lambda d: -peak_net[d])[:n_sp]
        wp_sorted = sorted(wp_days, key=lambda d: -peak_net[d])[:n_wp]
        result[year] = (sp_sorted, wp_sorted)
    return result


def compute_elccafr_grid(cf_by_year: dict, peak_days_by_year: dict):
    sp_samples = {hr: [] for hr in range(24)}
    wp_samples = {hr: [] for hr in range(24)}

    for year, cfs in cf_by_year.items():
        if year not in peak_days_by_year:
            continue
        sp_days, wp_days = peak_days_by_year[year]
        for d in sp_days:
            hybrid_day = dispatch_battery_day(cfs[d])
            for hr in range(24):
                sp_samples[hr].append(hybrid_day[hr])
        for d in wp_days:
            hybrid_day = dispatch_battery_day(cfs[d])
            for hr in range(24):
                wp_samples[hr].append(hybrid_day[hr])

    grid = {sl: [1.0]*24 for sl in SLICE_ROWS}
    diagnostics = {}
    for slice_name, samples in [('Summer Peak', sp_samples), ('Winter Peak', wp_samples)]:
        for hr in range(24):
            vals = np.array(samples[hr])
            if len(vals) == 0:
                continue
            mean_v = float(vals.mean())
            worst_v = float(vals.min())
            ratio = worst_v / mean_v if mean_v > 1e-3 else 1.0
            ratio = min(max(ratio, 0.0), 1.0)
            grid[slice_name][hr] = round(ratio, 4)
            if hr in [17, 18, 19, 20]:
                diagnostics[f"{slice_name} hr{hr}"] = {
                    "n": len(vals), "mean": mean_v,
                    "worst": worst_v, "ratio": ratio,
                }
    return grid, diagnostics


def write_csv(tech_label: str, grid: dict, path: Path):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([tech_label] + HOUR_COLS)
        for sl in SLICE_ROWS:
            row = [sl] + [f"{v:.4f}" for v in grid[sl]]
            w.writerow(row)


def main():
    print("Reading weather data (45 years, per-state)...")
    # Read per-state weather for each tech's capacity-weighted exposure
    solar_ghi = read_weighted_weather("irradiance_surface", SOLAR_WEIGHTS)
    solar_temp = read_weighted_weather("temperature", SOLAR_WEIGHTS)
    wind_speed = read_weighted_weather("wind_speed", WIND_WEIGHTS)
    offshore_speed = read_weighted_weather("wind_speed", OFFSHORE_WEIGHTS)

    # Filter to requested years
    mask = solar_ghi.index.year.isin(YEARS_TO_USE)
    solar_ghi = solar_ghi[mask]
    solar_temp = solar_temp[mask]
    wind_speed = wind_speed[mask]
    offshore_speed = offshore_speed[mask]

    print(f"  Solar: GHI mean = {solar_ghi.mean():.1f} W/m², temp mean = {solar_temp.mean():.1f} °C")
    print(f"  Wind 10m mean = {wind_speed.mean():.2f} m/s (capacity-weighted)")
    print(f"  Offshore 10m mean = {offshore_speed.mean():.2f} m/s")
    print()

    print("Computing CFs...")
    solar_cf = compute_solar_cf(solar_ghi, solar_temp)
    wind_cf = compute_wind_cf(wind_speed)
    offshore_cf = compute_offshore_cf(offshore_speed)
    print(f"  Solar mean annual CF: {solar_cf.mean():.3f}  (EIA observed ~0.23)")
    print(f"  Wind mean annual CF:  {wind_cf.mean():.3f}  (EIA observed ~0.34)")
    print(f"  Offshore mean annual CF: {offshore_cf.mean():.3f}  (EIA observed ~0.42)")
    print()

    solar_yd = reshape_year_day_hour(solar_cf)
    wind_yd = reshape_year_day_hour(wind_cf)
    offshore_yd = reshape_year_day_hour(offshore_cf)
    print(f"Years with complete data: {len(solar_yd)}")

    solar_peaks = identify_pinned_peak_days(solar_yd, N_SUMMER_PEAK, N_WINTER_PEAK)
    wind_peaks = identify_pinned_peak_days(wind_yd, N_SUMMER_PEAK, N_WINTER_PEAK)
    offshore_peaks = identify_pinned_peak_days(offshore_yd, N_SUMMER_PEAK, N_WINTER_PEAK)

    print(f"\nComputing multi-year hybrid ELCCAfR ({len(solar_yd)} years × pinned peak days):")
    print(f"{'Tech':<18}{'Slice':<14}{'Hr':>4}{'N':>6}{'Mean':>9}{'Min':>9}{'Ratio':>8}")
    print("-"*70)

    results = {}
    for tech_label, slug, cf_by_year, peaks in [
        ('solar pv',      'solar-pv',      solar_yd, solar_peaks),
        ('onshore wind',  'onshore-wind',  wind_yd,  wind_peaks),
        ('offshore wind', 'offshore-wind', offshore_yd, offshore_peaks),
    ]:
        grid, diag = compute_elccafr_grid(cf_by_year, peaks)
        for key, d in diag.items():
            slice_part = key.rsplit(' hr', 1)[0]
            hr = key.rsplit(' hr', 1)[1]
            print(f"{tech_label:<18}{slice_part:<14}{hr:>4}{d['n']:>6}{d['mean']:>9.4f}"
                  f"{d['worst']:>9.4f}{d['ratio']:>8.4f}")
        print()
        results[tech_label] = grid
        out_path = OUTPUT_DIR / f"ELCCAfR-hybrid-{slug}-multiyear.csv"
        write_csv(tech_label, grid, out_path)
        print(f"  written: {out_path}\n")


if __name__ == "__main__":
    main()
