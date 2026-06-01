"""H4: EFS state-level vs national peakiness, plus coincident-peak check.

Loads EFS hourly state data, filters VA + 2024, summarizes peak/mean ratios
by sector, and identifies the LocalHourID where each sector peaks.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, r"C:\Users\RobbieOrvis\Models\Global Electricity File Creator\.venv\Lib\site-packages")
import zipfile_deflate64 as zd

EFS_ZIP = r"C:\Users\RobbieOrvis\Models\Global Electricity File Creator\data\efs\EFSLoadProfile_Reference_Moderate.zip"
OUT_DIR = r"C:\Users\RobbieOrvis\Models\Global Electricity File Creator\output\va_diagnostic\tables"

YEAR = 2024


def load_efs():
    with zd.ZipFile(EFS_ZIP) as z:
        names = z.namelist()
        print("ZIP contents:", names)
        # find a CSV
        target = None
        for n in names:
            if n.lower().endswith(".csv"):
                target = n
                break
        if target is None:
            raise RuntimeError("no CSV in zip")
        print(f"Reading {target}")
        with z.open(target) as f:
            df = pd.read_csv(f)
    return df


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df = load_efs()
    print(f"Loaded {len(df):,} rows")
    print("Columns:", list(df.columns))
    print("Years:", sorted(df["Year"].unique()))

    # Filter to YEAR; pick Reference / Moderate if present
    if "Electrification" in df.columns:
        ref = df[(df["Electrification"] == "Reference") &
                 (df["TechnologyAdvancement"] == "Moderate") &
                 (df["Year"] == YEAR)].copy()
    else:
        ref = df[df["Year"] == YEAR].copy()
    print(f"After filter: {len(ref):,}")

    # Aggregate to (State, Sector, Subsector, LocalHourID) -> sum LoadMW
    grp_cols = ["State", "Sector", "Subsector", "LocalHourID"]
    agg = ref.groupby(grp_cols, as_index=False)["LoadMW"].sum()

    # Subset for VA & national-aggregate (sum across states) for residential cooling, residential heating, total
    va = agg[agg["State"] == "VA"].copy()
    print(f"VA rows: {len(va):,}; sectors: {sorted(va['Sector'].unique())}; subsectors: {sorted(va['Subsector'].unique())}")

    # National aggregate by summing across states
    nat = agg.groupby(["Sector", "Subsector", "LocalHourID"], as_index=False)["LoadMW"].sum()

    # ---- Peak/mean ratios per sector(+subsector) for VA and USA-aggregate ----
    rows = []
    for label, dfx, group_keys in [("VA", va, ["Sector", "Subsector"]),
                                    ("USA_aggregate", nat, ["Sector", "Subsector"])]:
        for keys, g in dfx.groupby(group_keys):
            mean = g["LoadMW"].mean()
            mx = g["LoadMW"].max()
            mn = g["LoadMW"].min()
            peak_hour = int(g.loc[g["LoadMW"].idxmax(), "LocalHourID"])
            rows.append({
                "scope": label,
                "Sector": keys[0] if isinstance(keys, tuple) else keys,
                "Subsector": keys[1] if isinstance(keys, tuple) else "",
                "mean_MW": mean,
                "max_MW": mx,
                "min_MW": mn,
                "peak_to_mean": mx / mean if mean > 0 else np.nan,
                "peak_LocalHourID": peak_hour,
            })

    # Also total system
    for label, dfx in [("VA", va), ("USA_aggregate", nat)]:
        sys_tot = dfx.groupby("LocalHourID", as_index=False)["LoadMW"].sum()
        mean = sys_tot["LoadMW"].mean()
        mx = sys_tot["LoadMW"].max()
        peak_hour = int(sys_tot.loc[sys_tot["LoadMW"].idxmax(), "LocalHourID"])
        rows.append({
            "scope": label, "Sector": "TOTAL", "Subsector": "",
            "mean_MW": mean, "max_MW": mx, "min_MW": sys_tot["LoadMW"].min(),
            "peak_to_mean": mx / mean, "peak_LocalHourID": peak_hour,
        })

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT_DIR, "h4_efs_peakiness.csv"), index=False)
    print("\n=== H4 EFS peak/mean ratios ===")
    print(out.to_string(index=False))

    # ---- H2/coincident-peak: list which LocalHourID each VA sector/subsector peaks on ----
    va_peaks = []
    for keys, g in va.groupby(["Sector", "Subsector"]):
        idx = g["LoadMW"].idxmax()
        h = int(g.loc[idx, "LocalHourID"])
        # Convert to day of year and hour of day; LocalHourID is 1..8760 typically by hour
        day = (h - 1) // 24 + 1
        hod = (h - 1) % 24
        va_peaks.append({
            "Sector": keys[0], "Subsector": keys[1],
            "peak_LocalHourID": h, "day_of_year": day, "hour_of_day": hod,
            "peak_MW": float(g.loc[idx, "LoadMW"]),
            "mean_MW": float(g["LoadMW"].mean()),
        })
    pk = pd.DataFrame(va_peaks).sort_values("peak_LocalHourID")
    pk.to_csv(os.path.join(OUT_DIR, "h2b_va_sector_peaks.csv"), index=False)
    print("\n=== VA sector peak hours (coincident-peak check) ===")
    print(pk.to_string(index=False))

    # System total peak hour for VA
    va_tot = va.groupby("LocalHourID", as_index=False)["LoadMW"].sum()
    sys_peak_hour = int(va_tot.loc[va_tot["LoadMW"].idxmax(), "LocalHourID"])
    sys_peak_mw = float(va_tot["LoadMW"].max())
    sys_mean_mw = float(va_tot["LoadMW"].mean())
    print(f"\nVA system total peak: hour={sys_peak_hour} (day {(sys_peak_hour-1)//24+1}, hod {(sys_peak_hour-1)%24}), peak={sys_peak_mw:.0f} MW, mean={sys_mean_mw:.0f} MW, ratio={sys_peak_mw/sys_mean_mw:.3f}")

    # Sum-of-individual-sector-peaks (the "phantom" max) vs system coincident peak
    sum_indiv_peaks = pk["peak_MW"].sum()
    print(f"Sum of individual sector peaks (phantom): {sum_indiv_peaks:.0f} MW")
    print(f"Phantom over coincident: {sum_indiv_peaks/sys_peak_mw:.3f}x")

    # Also compute: at the system peak hour, what is each sector's load?
    at_sys_peak = va[va["LocalHourID"] == sys_peak_hour].copy()
    at_sys_peak.to_csv(os.path.join(OUT_DIR, "h2c_va_loads_at_system_peak.csv"), index=False)


if __name__ == "__main__":
    main()
