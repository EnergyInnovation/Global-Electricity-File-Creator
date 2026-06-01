"""Compute hybrid ELCCAfR using multi-year renewables.ninja data.

For each tech:
1. Read cached CSVs for all (site, year) combinations
2. Aggregate site CFs to national fleet (capacity-weighted; simple equal weights for now)
3. Apply stylized battery dispatch per day
4. Identify pinned peak days from a load proxy (top-N net-load days per year)
5. Compute worst-day/mean ratio across all (year, day) pairs for each (slice, hour)
"""
import csv
from pathlib import Path
from collections import defaultdict
import numpy as np

CACHE_DIR = Path(r"C:\Users\RobbieOrvis\Downloads\ninja_cache")  # external cache, accumulated cross-session
OUTPUT_DIR = Path(__file__).parent / "data_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Match EPS model parameters
BATTERY_MW_PER_VRE = 0.5
DURATION_HR = 4
ROUND_TRIP_EFF = 0.85

# Half-year peak pools (consistent with State EPS conventions)
WINTER_MONTHS = {10, 11, 12, 1, 2, 3}
SUMMER_MONTHS = {4, 5, 6, 7, 8, 9}

# Days per slice (K6 canonical)
N_SUMMER_PEAK = 27
N_WINTER_PEAK = 20

# Sites (must match fetch script)
WIND_SITES = [
    ("IA_Iowa",         42.0,  -93.5),
    ("TX_Panhandle",    35.5, -101.5),
    ("KS_Kansas",       38.5, -100.0),
    ("OK_Oklahoma",     35.5,  -98.0),
    ("ND_NorthDakota",  47.0, -100.0),
]
SOLAR_SITES = [
    ("CA_CentralValley", 36.0, -120.0),
    ("TX_West",          31.5, -103.0),
    ("AZ_Arizona",       33.0, -111.5),
    ("FL_Florida",       28.0,  -82.0),
    ("NC_NorthCarolina", 35.5,  -78.0),
]
OFFSHORE_SITES = [
    ("NE_Massachusetts", 41.0,  -70.5),
    ("MA_RhodeIsland",   41.3,  -71.0),
    ("NY_NewYorkBight",  40.0,  -73.0),
]

YEARS = [2019, 2020, 2021, 2022, 2023]

SLICE_ROWS = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']
HOUR_COLS = [f'Hour{h}' for h in range(24)]


def read_ninja_csv(path: Path):
    """Parse renewables.ninja CSV. Returns (timestamps, hourly_cf array).

    First 4 lines are metadata. Then 'time,electricity' header. Then data.
    Electricity is in kW with capacity=1000kW, so CF = electricity/1000.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    # Find header line
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("time,"):
            header_idx = i
            break
    if header_idx is None:
        return None, None
    data_lines = lines[header_idx + 1:]
    import datetime as dt
    ts = []
    cfs = []
    for line in data_lines:
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) < 2:
            continue
        try:
            t = dt.datetime.strptime(parts[0], "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        try:
            cf = float(parts[1]) / 1000.0  # kW -> dimensionless CF
        except ValueError:
            continue
        ts.append(t)
        cfs.append(cf)
    return ts, np.array(cfs)


def aggregate_national(tech: str, sites: list, years: list):
    """Aggregate site CFs to national fleet (equal-weighted).

    Returns dict: year -> 365x24 array of national CF.
    """
    by_year = {}
    for year in years:
        site_arrays = []
        for site_name, _, _ in sites:
            path = CACHE_DIR / f"{tech}_{site_name}_{year}.csv"
            if not path.exists():
                continue
            ts, cf = read_ninja_csv(path)
            if cf is None or len(cf) < 8760:
                continue
            site_arrays.append(cf[:8760])  # trim leap-year days
        if not site_arrays:
            continue
        national = np.mean(site_arrays, axis=0)  # equal weights
        # Reshape to 365x24
        if len(national) >= 8760:
            by_year[year] = national[:8760].reshape(365, 24)
    return by_year


def dispatch_battery_day(cf_profile: np.ndarray,
                          peak_window=(17, 21),
                          battery_power: float = BATTERY_MW_PER_VRE,
                          battery_energy: float = BATTERY_MW_PER_VRE * DURATION_HR,
                          eff: float = ROUND_TRIP_EFF) -> np.ndarray:
    """Same as the single-year script."""
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


def synthetic_load_proxy():
    """Construct a stylized US-national hourly load shape (24 values per day-type).

    Used to identify pinned peak days from net-load metric. Profile based on
    typical US summer/winter load patterns: evening peak in summer (5pm),
    morning + evening peak in winter (8am, 6pm).
    """
    # Summer day shape: minimum at 4am, peak at 6pm
    summer = np.array([0.72, 0.69, 0.67, 0.66, 0.66, 0.69, 0.74, 0.80, 0.84, 0.88,
                       0.91, 0.93, 0.94, 0.95, 0.97, 0.99, 1.00, 1.00, 0.98, 0.95,
                       0.91, 0.85, 0.79, 0.74])
    winter = np.array([0.78, 0.76, 0.75, 0.74, 0.75, 0.79, 0.86, 0.93, 0.97, 0.97,
                       0.95, 0.94, 0.92, 0.90, 0.89, 0.90, 0.94, 0.99, 1.00, 0.98,
                       0.95, 0.91, 0.86, 0.81])
    return summer, winter


def identify_peak_days(cf_by_year: dict, n_sp: int, n_wp: int):
    """Identify top-N peak days per year using stylized net-load.

    Returns dict: year -> (sp_day_indices, wp_day_indices) 0-indexed.
    """
    import datetime as dt
    summer_load, winter_load = synthetic_load_proxy()

    result = {}
    for year, cfs in cf_by_year.items():
        # Determine month per day
        day_months = []
        for d in range(365):
            day_date = dt.date(year, 1, 1) + dt.timedelta(days=d)
            day_months.append(day_date.month)
        day_months = np.array(day_months)

        # Compute peak net-load per day (max of load - cf over 24 hours)
        # Use winter_load profile for winter months, summer_load for summer months
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


def compute_hybrid_elccafr_multi_year(cf_by_year: dict, peak_days_by_year: dict):
    """Compute hybrid ELCCAfR using worst-day-across-all-years / mean methodology.

    Returns 6x24 grid.
    """
    # Collect hybrid CFs across all years on pinned peak days
    sp_collected = {hr: [] for hr in range(24)}
    wp_collected = {hr: [] for hr in range(24)}

    for year, cfs in cf_by_year.items():
        sp_days, wp_days = peak_days_by_year[year]
        for d in sp_days:
            hybrid_day = dispatch_battery_day(cfs[d])
            for hr in range(24):
                sp_collected[hr].append(hybrid_day[hr])
        for d in wp_days:
            hybrid_day = dispatch_battery_day(cfs[d])
            for hr in range(24):
                wp_collected[hr].append(hybrid_day[hr])

    grid = {sl: [1.0]*24 for sl in SLICE_ROWS}
    diagnostics = {}

    for slice_name, collected in [('Summer Peak', sp_collected), ('Winter Peak', wp_collected)]:
        for hr in range(24):
            vals = np.array(collected[hr])
            if len(vals) == 0:
                continue
            mean_v = float(vals.mean())
            worst_v = float(vals.min())
            ratio = worst_v / mean_v if mean_v > 1e-3 else 1.0
            ratio = min(max(ratio, 0.0), 1.0)
            grid[slice_name][hr] = round(ratio, 4)
            if hr in [17, 18, 19, 20]:
                diagnostics[f"{slice_name} hr{hr}"] = {
                    "n_samples": len(vals),
                    "mean": mean_v,
                    "worst": worst_v,
                    "ratio": grid[slice_name][hr],
                }

    return grid, diagnostics


def write_elccafr_csv(tech_label: str, grid: dict, output_path: Path):
    with open(output_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([tech_label] + HOUR_COLS)
        for sl in SLICE_ROWS:
            row = [sl] + [f"{v:.4f}" for v in grid[sl]]
            w.writerow(row)


def main():
    techs = [
        ('wind', WIND_SITES, 'onshore wind', 'onshore-wind'),
        ('solar', SOLAR_SITES, 'solar pv', 'solar-pv'),
        ('offshore', OFFSHORE_SITES, 'offshore wind', 'offshore-wind'),
    ]

    print(f"{'Tech':<18}{'Slice':<14}{'Hour':>6}{'N samples':>12}{'Mean':>10}{'Worst':>10}{'Ratio':>10}")
    print("-"*80)

    for tech_short, sites, tech_label, slug in techs:
        cf_by_year = aggregate_national(tech_short, sites, YEARS)
        if not cf_by_year:
            print(f"  {tech_short}: no cached data found, skipping")
            continue
        print(f"\n{tech_short}: aggregated {len(cf_by_year)} years across {len(sites)} sites")

        peak_days = identify_peak_days(cf_by_year, N_SUMMER_PEAK, N_WINTER_PEAK)
        grid, diagnostics = compute_hybrid_elccafr_multi_year(cf_by_year, peak_days)

        for key, d in diagnostics.items():
            slice_part = key.rsplit(' hr', 1)[0]
            hr = key.rsplit(' hr', 1)[1]
            print(f"{tech_short:<18}{slice_part:<14}{hr:>6}{d['n_samples']:>12}{d['mean']:>10.4f}"
                  f"{d['worst']:>10.4f}{d['ratio']:>10.4f}")

        out_path = OUTPUT_DIR / f"ELCCAfR-hybrid-{slug}-multiyear.csv"
        write_elccafr_csv(tech_label, grid, out_path)
        print(f"  written to: {out_path}")


if __name__ == "__main__":
    main()
