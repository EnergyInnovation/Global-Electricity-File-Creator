"""
Compute hybrid ELCCAfR values via Option A.

Methodology:
1. Read Cambium 2024 national hourly data
2. Identify pinned peak days based on net load (top 27 SP, top 20 WP)
3. For each VRE tech, simulate stylized 4hr battery dispatch per day
4. Compute worst-day/mean ratio per (slice, hour) for the hybrid profile

Battery parameters match the EPS model:
  - 0.5 MW battery per MW VRE (HESBCpUEC)
  - 4 hour duration (GBSC)
  - ~85% round-trip efficiency
"""
import csv
import os
import datetime as dt
from pathlib import Path

import numpy as np

CAMBIUM_HOURLY_DIR = r"C:\Users\RobbieOrvis\Models\State EPS Code\data\cambium22_midcase_national_hourly"
CAMBIUM_ANNUAL = r"C:\Users\RobbieOrvis\AppData\Local\Temp\Cambium22_MidCase_annual_national.csv"
OUTPUT_DIR = Path(__file__).parent / "data_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Match EPS model parameters
BATTERY_MW_PER_VRE = 0.5
DURATION_HR = 4
ROUND_TRIP_EFF = 0.85

# Half-year peak pools (matches State EPS conventions)
WINTER_MONTHS = {10, 11, 12, 1, 2, 3}
SUMMER_MONTHS = {4, 5, 6, 7, 8, 9}

# K6 days per slice (must sum to 365)
N_SUMMER_PEAK = 27
N_WINTER_PEAK = 20

# Cambium tech mapping
HYBRID_TECHS = {
    'solar pv':       'upv_MWh',
    'onshore wind':   'wind-ons_MWh',
    'offshore wind':  'wind-ofs_MWh',
}

SLICE_ROWS = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']
HOUR_COLS = [f'Hour{h}' for h in range(24)]


def read_cambium_annual_capacities(year: int = 2024) -> dict:
    """Read Cambium national annual file and return capacities for VRE techs."""
    with open(CAMBIUM_ANNUAL) as f:
        lines = f.readlines()
    header = lines[5].strip().split(",")
    col = {n: i for i, n in enumerate(header)}
    caps = {}
    for line in lines[6:]:
        parts = line.strip().split(",")
        if len(parts) < len(header):
            continue
        try:
            y = int(parts[col["t"]])
        except (ValueError, KeyError):
            continue
        if y == year:
            caps = {
                'upv_MWh': float(parts[col["upv_MW"]]),
                'wind-ons_MWh': float(parts[col["wind-ons_MW"]]),
                'wind-ofs_MWh': float(parts[col["wind-ofs_MW"]]),
            }
            break
    return caps


def read_cambium_hourly(year: int = 2024):
    """Return (header, list of rows) for hourly file."""
    fp = Path(CAMBIUM_HOURLY_DIR) / f"Cambium22_MidCase_hourly_usa_{year}.csv"
    with open(fp) as f:
        for _ in range(5):
            f.readline()
        header = f.readline().strip().split(",")
    col = {n: i for i, n in enumerate(header)}

    needed = ['timestamp', 'busbar_load', 'upv_MWh', 'distpv_MWh',
              'wind-ons_MWh', 'wind-ofs_MWh']
    for n in needed:
        if n not in col:
            raise RuntimeError(f"missing col: {n}")

    # 8760 hours x 24 columns of interest. Apply +24h shift per Cambium convention.
    timestamps = []
    data = {n: [] for n in needed if n != 'timestamp'}
    with open(fp) as f:
        for _ in range(6):
            f.readline()
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < len(header):
                continue
            ts = dt.datetime.strptime(parts[col['timestamp']], "%Y-%m-%d %H:%M:%S")
            timestamps.append(ts)
            for n in data:
                try:
                    data[n].append(float(parts[col[n]]))
                except (ValueError, IndexError):
                    data[n].append(0.0)

    arrays = {n: np.array(v) for n, v in data.items()}
    return timestamps, arrays


def identify_pinned_peak_days(timestamps, busbar_load, upv, distpv, wind_ons, wind_ofs,
                                n_sp: int, n_wp: int):
    """Find top-N net-load days for summer peak and winter peak pools.

    Net load = busbar load - solar - wind. Highest net load = worst stress.
    Returns (sp_day_indices, wp_day_indices) as 0-indexed lists.
    """
    net_load = busbar_load - upv - distpv - wind_ons - wind_ofs
    # Reshape to 365x24
    nl = net_load.reshape(365, 24)
    daily_peak_net = nl.max(axis=1)  # max net load per day

    # Categorize by month
    day_month = np.array([timestamps[i*24].month for i in range(365)])
    sp_mask = np.isin(day_month, list(SUMMER_MONTHS))
    wp_mask = np.isin(day_month, list(WINTER_MONTHS))

    # Top N within each pool
    sp_pool_days = np.where(sp_mask)[0]
    wp_pool_days = np.where(wp_mask)[0]

    sp_sorted = sp_pool_days[np.argsort(-daily_peak_net[sp_pool_days])]
    wp_sorted = wp_pool_days[np.argsort(-daily_peak_net[wp_pool_days])]

    return sp_sorted[:n_sp].tolist(), wp_sorted[:n_wp].tolist()


def dispatch_battery_day(cf_profile: np.ndarray,
                          peak_window=(17, 21),
                          battery_power: float = BATTERY_MW_PER_VRE,
                          battery_energy: float = BATTERY_MW_PER_VRE * DURATION_HR,
                          eff: float = ROUND_TRIP_EFF) -> np.ndarray:
    """Simulate stylized battery dispatch.

    Input: 24-hour CF profile (cf in [0, 1]), per 1 MW VRE installed.
    Battery: 0.5 MW power, 2 MWh energy (4hr × 0.5 MW), 85% round-trip eff.

    Strategy:
    - Discharge during peak_window (default hours 17-20, evening peak)
    - Charge during 4 highest-CF hours before peak_window
    - Limited by available VRE output and battery power/energy

    Returns: 24-hour hybrid output profile (still in MW per MW VRE).
    """
    cf = cf_profile.copy().astype(float)
    discharge_hours = list(range(peak_window[0], peak_window[1]))

    # Find best charge hours (highest CF) before peak window
    pre_peak_hours = list(range(peak_window[0]))
    pre_peak_cfs = sorted(pre_peak_hours, key=lambda h: -cf[h])
    charge_hours = pre_peak_cfs[:4]  # top 4 hours

    # Charge battery up to battery_energy MWh, limited by available CF per hour
    battery_state = 0.0
    charge_arr = np.zeros(24)
    for h in sorted(charge_hours):
        avail = min(battery_power, cf[h])  # can't charge more than VRE generates
        room = battery_energy - battery_state
        actual_charge = min(avail, room)
        if actual_charge > 0:
            battery_state += actual_charge * eff   # energy stored after losses
            charge_arr[h] = actual_charge          # charged from VRE (reduces CF in this hour)

    # Discharge during peak window
    discharge_arr = np.zeros(24)
    for h in sorted(discharge_hours):
        actual_discharge = min(battery_power, battery_state)
        if actual_discharge > 0:
            battery_state -= actual_discharge
            discharge_arr[h] = actual_discharge

    # Hybrid output = base CF - charging + discharging (all in MW per MW VRE)
    hybrid = cf - charge_arr + discharge_arr
    return hybrid


def compute_hybrid_elccafr(year: int = 2024):
    print(f"Reading Cambium {year} national files...")
    caps = read_cambium_annual_capacities(year)
    print(f"  upv cap: {caps['upv_MWh']:,.0f} MW")
    print(f"  wind-ons cap: {caps['wind-ons_MWh']:,.0f} MW")
    print(f"  wind-ofs cap: {caps['wind-ofs_MWh']:,.0f} MW")

    timestamps, data = read_cambium_hourly(year)
    print(f"  Read {len(timestamps)} hourly rows")

    sp_days, wp_days = identify_pinned_peak_days(
        timestamps, data['busbar_load'],
        data['upv_MWh'], data['distpv_MWh'],
        data['wind-ons_MWh'], data['wind-ofs_MWh'],
        N_SUMMER_PEAK, N_WINTER_PEAK,
    )
    print(f"  Pinned SP days (top {N_SUMMER_PEAK}): {len(sp_days)} identified")
    print(f"  Pinned WP days (top {N_WINTER_PEAK}): {len(wp_days)} identified")

    results = {}
    diagnostics = {}
    for tech_label, gen_col in HYBRID_TECHS.items():
        cap = caps[gen_col]
        if cap <= 0:
            results[tech_label] = None
            continue

        # Per-day hourly CF
        cfs = data[gen_col].reshape(365, 24) / cap

        # For each day, simulate battery dispatch
        # Winter peak typically peaks earlier (16-19), summer peak later (17-20)
        # For simplicity, use the same window for both — battery dispatches over evening hours
        hybrid_cfs = np.zeros_like(cfs)
        for day_idx in range(365):
            hybrid_cfs[day_idx] = dispatch_battery_day(cfs[day_idx])

        # Compute ELCCAfR per (slice, hour)
        # Initialize all slices at 1.0; only Summer Peak and Winter Peak get computed values
        grid = {sl: [1.0]*24 for sl in SLICE_ROWS}
        diag = {}

        for slice_name, days in [('Summer Peak', sp_days), ('Winter Peak', wp_days)]:
            if not days:
                continue
            sub = hybrid_cfs[days]   # (n_days, 24)
            for hr in range(24):
                vals = sub[:, hr]
                mean_v = float(vals.mean())
                worst_v = float(vals.min())
                if mean_v < 1e-3:
                    ratio = 1.0
                else:
                    ratio = worst_v / mean_v
                ratio = min(max(ratio, 0.0), 1.0)
                grid[slice_name][hr] = round(ratio, 4)

            # Diagnostics: focus on hour 18-20
            for hr in [17, 18, 19, 20]:
                vals = sub[:, hr]
                diag[f"{slice_name} hr{hr}"] = {
                    "mean_hybrid_cf": vals.mean(),
                    "min_hybrid_cf": vals.min(),
                    "ratio": grid[slice_name][hr],
                }

        results[tech_label] = grid
        diagnostics[tech_label] = diag

    return results, diagnostics, caps


def write_elccafr_csv(tech_label: str, grid: dict, output_path: Path):
    """Write 6x24 hybrid ELCCAfR CSV in same format as standalone files."""
    with open(output_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([tech_label] + HOUR_COLS)
        for sl in SLICE_ROWS:
            row = [sl] + [f"{v:.4f}" for v in grid[sl]]
            w.writerow(row)


def main():
    results, diagnostics, caps = compute_hybrid_elccafr(year=2024)

    print()
    print("=" * 90)
    print("Hybrid ELCCAfR — diagnostic values at evening peak hours")
    print("=" * 90)
    print(f"{'Tech':<20}{'Slice':<14}{'Hour':>6}{'Mean CF':>12}{'Min CF':>12}{'Ratio':>10}")
    print("-" * 90)
    for tech, diag in diagnostics.items():
        for key, d in diag.items():
            slice_part = key.rsplit(' hr', 1)[0]
            hr = key.rsplit(' hr', 1)[1]
            print(f"{tech:<20}{slice_part:<14}{hr:>6}{d['mean_hybrid_cf']:>12.4f}"
                  f"{d['min_hybrid_cf']:>12.4f}{d['ratio']:>10.4f}")
        print()

    # Write CSV outputs (Downloads for now; can move later)
    slug_map = {
        'solar pv':      'solar-pv',
        'onshore wind':  'onshore-wind',
        'offshore wind': 'offshore-wind',
    }
    print("Writing hybrid ELCCAfR CSVs:")
    for tech, grid in results.items():
        if grid is None:
            continue
        slug = slug_map[tech]
        path = OUTPUT_DIR / f"ELCCAfR-hybrid-{slug}.csv"
        write_elccafr_csv(tech, grid, path)
        print(f"  {path}")


if __name__ == "__main__":
    main()
