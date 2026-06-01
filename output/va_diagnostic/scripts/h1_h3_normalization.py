"""H1 & H3 diagnostic: Compare VA vs USA SHELF normalization and shapes.

For each SHELF category, compute:
- Sum of LF * days[slice] across all hours and slices.  Should be ~1.0.
- Max LF in peak slices and in main slices, and the ratio.
"""
import os
import sys
import pandas as pd
import numpy as np

VA_DIR = r"C:\Users\RobbieOrvis\Models\state-eps-data-repository\VA\elec\SHELF"
USA_DIR = r"C:\Users\RobbieOrvis\Models\state-eps-data-repository\USA\InputData\elec\SHELF"
OUT_DIR = r"C:\Users\RobbieOrvis\Models\Global Electricity File Creator\output\va_diagnostic\tables"

HOUR_COLS = [f"Hour{i}" for i in range(24)]
SLICES = ["Winter", "Spring", "Summer", "Fall", "Summer Peak", "Winter Peak"]
PEAK_SLICES = ["Summer Peak", "Winter Peak"]
MAIN_SLICES = ["Winter", "Spring", "Summer", "Fall"]


def load_days(d):
    p = os.path.join(d, "SHELF-days-per-timeslice.csv")
    df = pd.read_csv(p, header=0)
    df.columns = ["slice", "days"]
    return dict(zip(df["slice"], df["days"].astype(float)))


def load_lf(path):
    df = pd.read_csv(path)
    # First col is slice label
    df.columns = ["slice"] + HOUR_COLS
    df = df.set_index("slice")
    return df.astype(float)


def shelf_files(d):
    out = {}
    for f in sorted(os.listdir(d)):
        if f.startswith("SHELF-") and f.endswith(".csv") and "days-per-timeslice" not in f:
            cat = f.replace("SHELF-", "").replace(".csv", "")
            out[cat] = os.path.join(d, f)
    return out


def diagnose(label, src_dir):
    days = load_days(src_dir)
    files = shelf_files(src_dir)
    rows = []
    peak_rows = []
    for cat, path in files.items():
        try:
            df = load_lf(path)
        except Exception as e:
            print(f"  skip {cat}: {e}")
            continue

        # ---- H1: sum of LF * days[slice] across all hours ----
        # Two interpretations:
        # (a) Σ_slice Σ_hour LF[s,h] * days[s] — scaled by total days (what user asked)
        # (b) Σ_slice Σ_hour LF[s,h] * days[s] / 365 — should be ~1 if LFs are fractions of annual demand spread per hour
        # SHELF unit says "ratio of electricity demand in this hour to annual demand"
        # If LF[s,h] is the share of annual demand in that hour, then summing over all hours of the year
        # = Σ_s days[s] * Σ_h LF[s,h] should = 1.0
        weighted = 0.0
        per_slice = {}
        for s in SLICES:
            if s in df.index:
                row_sum = df.loc[s, HOUR_COLS].sum()
                w = row_sum * days.get(s, 0.0)
                per_slice[s] = (row_sum, days.get(s, 0.0), w)
                weighted += w

        # Also assume each hour-LF is per-day fraction, sum to 1 PER DAY (alternative interpretation)
        # Then total_year = Σ_s days[s] * Σ_h LF[s,h] / N_per_day where N_per_day = 1 if rows already share
        # Stick to (a)

        # ---- H2: peak vs main ratios ----
        max_main = -np.inf
        max_peak = -np.inf
        for s in MAIN_SLICES:
            if s in df.index:
                m = df.loc[s, HOUR_COLS].max()
                max_main = max(max_main, m)
        for s in PEAK_SLICES:
            if s in df.index:
                m = df.loc[s, HOUR_COLS].max()
                max_peak = max(max_peak, m)
        ratio = (max_peak / max_main) if max_main > 0 else np.nan

        rows.append({
            "category": cat,
            "sum_LF_x_days": weighted,
            "deviation_from_1.0": weighted - 1.0,
            "pct_deviation": (weighted - 1.0) * 100.0,
            "winter_row_sum": per_slice.get("Winter", (np.nan,))[0] if "Winter" in per_slice else np.nan,
            "summer_row_sum": per_slice.get("Summer", (np.nan,))[0] if "Summer" in per_slice else np.nan,
            "summer_peak_row_sum": per_slice.get("Summer Peak", (np.nan,))[0] if "Summer Peak" in per_slice else np.nan,
            "winter_peak_row_sum": per_slice.get("Winter Peak", (np.nan,))[0] if "Winter Peak" in per_slice else np.nan,
        })
        peak_rows.append({
            "category": cat,
            "max_main_LF": max_main if np.isfinite(max_main) else np.nan,
            "max_peak_LF": max_peak if np.isfinite(max_peak) else np.nan,
            "peak_to_main_ratio": ratio,
        })

    norm_df = pd.DataFrame(rows).sort_values("category")
    peak_df = pd.DataFrame(peak_rows).sort_values("category")
    return norm_df, peak_df


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    va_n, va_p = diagnose("VA", VA_DIR)
    usa_n, usa_p = diagnose("USA", USA_DIR)

    va_n.to_csv(os.path.join(OUT_DIR, "h1_normalization_VA.csv"), index=False)
    usa_n.to_csv(os.path.join(OUT_DIR, "h1_normalization_USA.csv"), index=False)
    va_p.to_csv(os.path.join(OUT_DIR, "h2_peak_ratios_VA.csv"), index=False)
    usa_p.to_csv(os.path.join(OUT_DIR, "h2_peak_ratios_USA.csv"), index=False)

    # Side-by-side compare
    merged_n = va_n[["category", "sum_LF_x_days", "pct_deviation"]].merge(
        usa_n[["category", "sum_LF_x_days", "pct_deviation"]], on="category", suffixes=("_VA", "_USA"))
    merged_n.to_csv(os.path.join(OUT_DIR, "h1_normalization_compare.csv"), index=False)

    merged_p = va_p[["category", "max_main_LF", "max_peak_LF", "peak_to_main_ratio"]].merge(
        usa_p[["category", "max_main_LF", "max_peak_LF", "peak_to_main_ratio"]], on="category", suffixes=("_VA", "_USA"))
    merged_p["VA_minus_USA_peak_ratio"] = merged_p["peak_to_main_ratio_VA"] - merged_p["peak_to_main_ratio_USA"]
    merged_p.to_csv(os.path.join(OUT_DIR, "h2_peak_ratios_compare.csv"), index=False)

    print("=== H1 normalization (VA) ===")
    print(va_n.to_string(index=False))
    print("\n=== H1 normalization (USA) ===")
    print(usa_n.to_string(index=False))
    print("\n=== H1 compare ===")
    print(merged_n.to_string(index=False))
    print("\n=== H2 peak ratios compare ===")
    print(merged_p.to_string(index=False))


if __name__ == "__main__":
    main()
