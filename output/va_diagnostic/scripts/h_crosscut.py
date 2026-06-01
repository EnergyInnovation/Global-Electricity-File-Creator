"""Cross-cutting check: build implied total demand peak/mean from SHELF assuming
weights for each category proportional to annual demand share. Without those weights
we'll use raw equal-sum-across-cats and equal-sum-with-no-weighting (since LFs are already
normalized so their per-cat ratio across hours).
"""
import os
import pandas as pd
import numpy as np

VA_DIR = r"C:\Users\RobbieOrvis\Models\state-eps-data-repository\VA\elec\SHELF"
USA_DIR = r"C:\Users\RobbieOrvis\Models\state-eps-data-repository\USA\InputData\elec\SHELF"
OUT_DIR = r"C:\Users\RobbieOrvis\Models\Global Electricity File Creator\output\va_diagnostic\tables"

HOUR_COLS = [f"Hour{i}" for i in range(24)]

def load_days(d):
    df = pd.read_csv(os.path.join(d, "SHELF-days-per-timeslice.csv"), header=0)
    df.columns = ["slice", "days"]
    return dict(zip(df["slice"], df["days"].astype(float)))

def shelf_files(d):
    out = {}
    for f in sorted(os.listdir(d)):
        if f.startswith("SHELF-") and f.endswith(".csv") and "days-per-timeslice" not in f:
            cat = f.replace("SHELF-", "").replace(".csv", "")
            out[cat] = os.path.join(d, f)
    return out

def load_lf(p):
    df = pd.read_csv(p)
    df.columns = ["slice"] + HOUR_COLS
    return df.set_index("slice").astype(float)

def build_8760(d):
    """Reconstruct an implied 8760-hour load series assuming each category
    contributes equally to total annual energy. Then compute peak/mean.

    Note: this is approximate since true category weights aren't here. But it tests
    whether the *shape* of the SHELF data, when expanded across the year, has a peak
    at hour-of-Summer-Peak that exceeds main-slice peaks by N%.
    """
    days = load_days(d)
    files = shelf_files(d)
    # Total per-hour LF summed over all categories
    sum_lf = pd.DataFrame(index=["Winter","Spring","Summer","Fall","Summer Peak","Winter Peak"], columns=HOUR_COLS, dtype=float).fillna(0.0)
    for cat, p in files.items():
        df = load_lf(p)
        for s in sum_lf.index:
            if s in df.index:
                sum_lf.loc[s] = sum_lf.loc[s].values + df.loc[s, HOUR_COLS].values
    # Normalize to per-hour share of one category's annual total — but each row sums
    # to ~1/sum_of_cats not great. Just compare hour values.
    return sum_lf, days

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for label, d in [("VA", VA_DIR), ("USA", USA_DIR)]:
        sum_lf, days = build_8760(d)
        print(f"\n=== {label} sum-of-cat LF by slice/hour ===")
        # Drop envelope rows (all zeros) - already summed in
        # Show max each row
        print("Max LF per slice:")
        for s in sum_lf.index:
            mx = sum_lf.loc[s].max()
            mn = sum_lf.loc[s].mean()
            print(f"  {s}: max={mx:.6f}, mean={mn:.6f}, peak/mean={mx/mn if mn>0 else float('nan'):.3f}")

        sum_lf.to_csv(os.path.join(OUT_DIR, f"crosscut_{label}_sum_of_cat_LF.csv"))

        # Reconstructed annual peak: max across all slice/hour combinations
        all_max = sum_lf.values.max()
        # Peak is taken from Summer Peak slice in EPS (with days=0)
        sp_max = sum_lf.loc["Summer Peak"].max()
        wp_max = sum_lf.loc["Winter Peak"].max()
        sm_max = max(sum_lf.loc["Summer"].max(), sum_lf.loc["Winter"].max(),
                     sum_lf.loc["Spring"].max(), sum_lf.loc["Fall"].max())
        print(f"  Summer Peak slice max / max of main slices: {sp_max/sm_max:.3f}")
        print(f"  Winter Peak slice max / max of main slices: {wp_max/sm_max:.3f}")

        # Annual mean using days weights
        total_days = sum(days.values())
        # Compute weighted-mean LF across the year
        weighted_sum = 0.0
        weighted_hours = 0
        for s, n_days in days.items():
            if s in sum_lf.index and n_days > 0:
                row = sum_lf.loc[s].values  # 24 values
                weighted_sum += row.sum() * n_days
                weighted_hours += 24 * n_days
        annual_mean = weighted_sum / weighted_hours
        print(f"  Annual mean LF (across all main slices): {annual_mean:.6f}")
        # Peak slice value over annual mean
        print(f"  Peak slice (Summer Peak) max / annual mean: {sp_max/annual_mean:.3f}")
        print(f"  Main slice max / annual mean: {sm_max/annual_mean:.3f}")

if __name__ == "__main__":
    main()
