"""K6 cluster Cambium 2024 MidCase national 2025 hourly load.

Methodology mirrors EPS State convention:
- Half-year peak pools (winter = Oct-Mar, summer = Apr-Sep)
- Summer Peak slice = top 27 summer days by NET peak load
- Winter Peak slice = top 20 winter days by NET peak load
- Remaining 318 days assigned to seasonal slices (Winter / Spring / Summer / Fall)
- Days per slice: Winter 65, Spring 82, Summer 119, Fall 52, Summer Peak 27, Winter Peak 20

Outputs the average 24-hour profile for each slice on gross load, net load,
and VRE generation. Compares to current model values (gross 621, net 532).
"""
import csv
import datetime as dt
from collections import defaultdict
from pathlib import Path

INPUT = Path(r"C:\Users\RobbieOrvis\AppData\Local\Temp\Cambium24_MidCase_hourly_usa_2025.csv")

SUMMER_MONTHS = {4, 5, 6, 7, 8, 9}
WINTER_MONTHS = {10, 11, 12, 1, 2, 3}

# Standard seasonal definitions (3-month meteorological seasons)
SEASON_OF_MONTH = {
    12: 'Winter', 1: 'Winter', 2: 'Winter',
    3: 'Spring', 4: 'Spring', 5: 'Spring',
    6: 'Summer', 7: 'Summer', 8: 'Summer',
    9: 'Fall', 10: 'Fall', 11: 'Fall',
}

K6_DAYS = {'Winter': 65, 'Spring': 82, 'Summer': 119, 'Fall': 52,
           'Summer Peak': 27, 'Winter Peak': 20}

SLICES = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']


def parse_file(path):
    # Skip 6 header lines, parse data
    with open(path) as f:
        lines = f.readlines()
    # Header row 6 (index 5) has machine column names
    headers = lines[5].strip().split(',')
    idx = {name: i for i, name in enumerate(headers)}

    busbar_load_i = idx['busbar_load']
    enduse_load_i = idx['enduse_load']
    net_load_i    = idx['net_load_busbar']
    upv_i         = idx['upv_MWh']
    distpv_i      = idx['distpv_MWh']
    wind_ons_i    = idx['wind-ons_MWh']
    wind_ofs_i    = idx['wind-ofs_MWh']
    var_gen_i     = idx['variable_generation']

    rows = []
    for line in lines[6:]:
        parts = line.strip().split(',')
        if len(parts) < 5: continue
        try:
            ts = dt.datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
        gross = float(parts[busbar_load_i]) / 1000.0   # MWh -> GW (hourly)
        enduse = float(parts[enduse_load_i]) / 1000.0
        net = float(parts[net_load_i]) / 1000.0
        upv = float(parts[upv_i]) / 1000.0
        distpv = float(parts[distpv_i]) / 1000.0
        wind_ons = float(parts[wind_ons_i]) / 1000.0
        wind_ofs = float(parts[wind_ofs_i]) / 1000.0
        var_gen = float(parts[var_gen_i]) / 1000.0
        rows.append({
            'ts': ts, 'gross': gross, 'enduse': enduse, 'net': net,
            'upv': upv, 'distpv': distpv, 'wind_ons': wind_ons, 'wind_ofs': wind_ofs,
            'var_gen': var_gen,
        })
    return rows


def cluster_k6(rows):
    """Assign each day (1-365) to a slice."""
    # Group rows by day-of-year
    by_day = defaultdict(list)
    for r in rows:
        doy = r['ts'].timetuple().tm_yday
        by_day[doy].append(r)

    # Compute per-day metrics
    day_info = []
    for doy, day_rows in sorted(by_day.items()):
        if len(day_rows) < 23:  # skip partial days
            continue
        month = day_rows[0]['ts'].month
        net_peak = max(r['net'] for r in day_rows)
        gross_peak = max(r['gross'] for r in day_rows)
        day_info.append({
            'doy': doy, 'month': month, 'rows': day_rows,
            'net_peak': net_peak, 'gross_peak': gross_peak,
            'pool': 'summer' if month in SUMMER_MONTHS else 'winter',
        })

    # Sort summer pool by net_peak descending, take top 27 as Summer Peak
    summer_pool = sorted([d for d in day_info if d['pool'] == 'summer'],
                          key=lambda d: -d['net_peak'])
    winter_pool = sorted([d for d in day_info if d['pool'] == 'winter'],
                          key=lambda d: -d['net_peak'])

    sp_doys = set(d['doy'] for d in summer_pool[:27])
    wp_doys = set(d['doy'] for d in winter_pool[:20])

    # Remaining days assigned by meteorological season
    for d in day_info:
        if d['doy'] in sp_doys:
            d['slice'] = 'Summer Peak'
        elif d['doy'] in wp_doys:
            d['slice'] = 'Winter Peak'
        else:
            d['slice'] = SEASON_OF_MONTH[d['month']]

    return day_info


def slice_profiles(day_info):
    """Return dict: slice -> dict of 24-hour average profiles."""
    by_slice = defaultdict(list)
    for d in day_info:
        by_slice[d['slice']].append(d)

    profiles = {}
    for sl, days in by_slice.items():
        # Aggregate hour-by-hour
        gross_hr = [[] for _ in range(24)]
        net_hr = [[] for _ in range(24)]
        vre_hr = [[] for _ in range(24)]
        upv_hr = [[] for _ in range(24)]
        wind_hr = [[] for _ in range(24)]
        for d in days:
            for r in d['rows']:
                h = r['ts'].hour
                gross_hr[h].append(r['gross'])
                net_hr[h].append(r['net'])
                vre_hr[h].append(r['var_gen'])
                upv_hr[h].append(r['upv'] + r['distpv'])
                wind_hr[h].append(r['wind_ons'] + r['wind_ofs'])
        profiles[sl] = {
            'n_days': len(days),
            'gross': [sum(v)/len(v) if v else 0 for v in gross_hr],
            'net':   [sum(v)/len(v) if v else 0 for v in net_hr],
            'vre':   [sum(v)/len(v) if v else 0 for v in vre_hr],
            'upv':   [sum(v)/len(v) if v else 0 for v in upv_hr],
            'wind':  [sum(v)/len(v) if v else 0 for v in wind_hr],
        }
    return profiles


def main():
    rows = parse_file(INPUT)
    print(f"Parsed {len(rows)} hourly rows")
    annual_gross = sum(r['gross'] for r in rows) / 1000.0  # GW-h -> TWh
    annual_enduse = sum(r['enduse'] for r in rows) / 1000.0
    annual_vre = sum(r['var_gen'] for r in rows) / 1000.0
    print(f"Annual gross (busbar) load: {annual_gross:.1f} TWh")
    print(f"Annual end-use load:        {annual_enduse:.1f} TWh")
    print(f"Annual VRE generation:      {annual_vre:.1f} TWh")
    print(f"Implied loss/own-use rate:  {(1-annual_enduse/annual_gross)*100:.2f}%")
    print()
    max_gross = max(r['gross'] for r in rows)
    max_net   = max(r['net'] for r in rows)
    arg_g = max(rows, key=lambda r: r['gross'])['ts']
    arg_n = max(rows, key=lambda r: r['net'])['ts']
    print(f"Annual peak gross: {max_gross:.1f} GW at {arg_g}")
    print(f"Annual peak net:   {max_net:.1f} GW at {arg_n}")
    print()

    day_info = cluster_k6(rows)
    profiles = slice_profiles(day_info)

    print(f"{'Slice':<14}{'Days':>6}{'GrossPk':>10}{'GrossHr':>10}{'NetPk':>10}{'NetHr':>10}{'VRE@NetPk':>12}")
    print("-"*72)
    for sl in SLICES:
        p = profiles[sl]
        gross_pk = max(p['gross'])
        gross_hr = p['gross'].index(gross_pk)
        net_pk = max(p['net'])
        net_hr = p['net'].index(net_pk)
        vre_at_net = p['vre'][net_hr]
        print(f"{sl:<14}{p['n_days']:>6}{gross_pk:>10.1f}{gross_hr:>10d}{net_pk:>10.1f}{net_hr:>10d}{vre_at_net:>12.1f}")

    print()
    print("Summer Peak 24-hour profile (gross / net / VRE / solar / wind, GW):")
    print(f"{'Hr':>4}{'Gross':>10}{'Net':>10}{'VRE':>10}{'Solar':>10}{'Wind':>10}")
    sp = profiles['Summer Peak']
    for h in range(24):
        print(f"{h:>4}{sp['gross'][h]:>10.1f}{sp['net'][h]:>10.1f}{sp['vre'][h]:>10.1f}{sp['upv'][h]:>10.1f}{sp['wind'][h]:>10.1f}")

    print()
    print("Winter Peak 24-hour profile (gross / net / VRE, GW):")
    print(f"{'Hr':>4}{'Gross':>10}{'Net':>10}{'VRE':>10}")
    wp = profiles['Winter Peak']
    for h in range(24):
        print(f"{h:>4}{wp['gross'][h]:>10.1f}{wp['net'][h]:>10.1f}{wp['vre'][h]:>10.1f}")

    # Save full profile to CSV for downstream use
    out = Path(__file__).parent / "data_outputs" / "cambium24_2025_k6_profiles.csv"
    out.parent.mkdir(exist_ok=True)
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['slice', 'series'] + [f'Hour{h}' for h in range(24)])
        for sl in SLICES:
            p = profiles[sl]
            for series in ['gross', 'net', 'vre', 'upv', 'wind']:
                w.writerow([sl, series] + [f"{v:.4f}" for v in p[series]])
    print(f"\nWrote: {out}")


if __name__ == '__main__':
    main()
