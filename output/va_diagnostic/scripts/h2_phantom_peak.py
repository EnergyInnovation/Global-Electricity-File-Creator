"""H2: Test whether SHELF Summer Peak rows encode each sector's *own* worst-day shape.

If yes, summing categories at hour-of-Summer-Peak gives the phantom peak.
We compare:
  (a) Sum across categories of LF[Summer Peak, h] at the worst hour of that row -> phantom max
  (b) Sum across categories of LF[Summer, h] at the same hour
  (c) For comparison: peak-hour LF derived from EFS coincident system load.
"""
import os
import pandas as pd
import numpy as np

VA_DIR = r"C:\Users\RobbieOrvis\Models\state-eps-data-repository\VA\elec\SHELF"
USA_DIR = r"C:\Users\RobbieOrvis\Models\state-eps-data-repository\USA\InputData\elec\SHELF"
OUT_DIR = r"C:\Users\RobbieOrvis\Models\Global Electricity File Creator\output\va_diagnostic\tables"

HOUR_COLS = [f"Hour{i}" for i in range(24)]


def shelf_files(d):
    out = {}
    for f in sorted(os.listdir(d)):
        if f.startswith("SHELF-") and f.endswith(".csv") and "days-per-timeslice" not in f:
            cat = f.replace("SHELF-", "").replace(".csv", "")
            out[cat] = os.path.join(d, f)
    return out


def load_lf(path):
    df = pd.read_csv(path)
    df.columns = ["slice"] + HOUR_COLS
    df = df.set_index("slice")
    return df.astype(float)


def analyze(label, src):
    files = shelf_files(src)
    # Build matrix by category x hour for each slice
    summer_peak = pd.DataFrame(index=list(files.keys()), columns=HOUR_COLS, dtype=float)
    summer = pd.DataFrame(index=list(files.keys()), columns=HOUR_COLS, dtype=float)
    winter = pd.DataFrame(index=list(files.keys()), columns=HOUR_COLS, dtype=float)
    winter_peak = pd.DataFrame(index=list(files.keys()), columns=HOUR_COLS, dtype=float)
    own_max_hour_summer = {}
    own_max_hour_summer_peak = {}
    for cat, p in files.items():
        df = load_lf(p)
        if "Summer Peak" in df.index:
            summer_peak.loc[cat] = df.loc["Summer Peak"].values
        if "Summer" in df.index:
            summer.loc[cat] = df.loc["Summer"].values
            own_max_hour_summer[cat] = int(np.argmax(df.loc["Summer"].values))
        if "Winter" in df.index:
            winter.loc[cat] = df.loc["Winter"].values
        if "Winter Peak" in df.index:
            winter_peak.loc[cat] = df.loc["Winter Peak"].values
        if "Summer Peak" in df.index:
            own_max_hour_summer_peak[cat] = int(np.argmax(df.loc["Summer Peak"].values))

    # Per-row max hour: which hour each cat peaks within its own Summer Peak row
    own_peaks = pd.DataFrame({
        "category": list(own_max_hour_summer_peak.keys()),
        f"{label}_summer_peak_max_hour": [own_max_hour_summer_peak[c] for c in own_max_hour_summer_peak],
        f"{label}_summer_max_hour": [own_max_hour_summer.get(c, np.nan) for c in own_max_hour_summer_peak],
    })

    # Sum over categories at each hour (the "system-level" Summer Peak shape)
    sys_sp = summer_peak.sum(axis=0)
    sys_sm = summer.sum(axis=0)
    sys_wp = winter_peak.sum(axis=0)
    sys_w = winter.sum(axis=0)
    summary = pd.DataFrame({
        "hour": HOUR_COLS,
        "sum_LF_Summer_Peak": sys_sp.values,
        "sum_LF_Summer": sys_sm.values,
        "sum_LF_Winter_Peak": sys_wp.values,
        "sum_LF_Winter": sys_w.values,
    })
    return own_peaks, summary, summer_peak, summer


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    va_op, va_sum, va_sp, va_sm = analyze("VA", VA_DIR)
    usa_op, usa_sum, usa_sp, usa_sm = analyze("USA", USA_DIR)

    # Save sums
    va_sum.to_csv(os.path.join(OUT_DIR, "h2_VA_system_LF_by_hour.csv"), index=False)
    usa_sum.to_csv(os.path.join(OUT_DIR, "h2_USA_system_LF_by_hour.csv"), index=False)

    # Phantom peak metric: max of summed Summer Peak vs max of summed Summer
    print("=== VA sums by hour ===")
    print(va_sum.to_string(index=False))
    print("\n=== USA sums by hour ===")
    print(usa_sum.to_string(index=False))

    print("\n--- VA system peak metrics ---")
    sp_max_va = va_sum["sum_LF_Summer_Peak"].max()
    sm_max_va = va_sum["sum_LF_Summer"].max()
    sp_max_usa = usa_sum["sum_LF_Summer_Peak"].max()
    sm_max_usa = usa_sum["sum_LF_Summer"].max()
    print(f"VA: sum-of-cats Summer Peak max = {sp_max_va:.6f}; Summer max = {sm_max_va:.6f}; ratio = {sp_max_va/sm_max_va:.3f}")
    print(f"USA: sum-of-cats Summer Peak max = {sp_max_usa:.6f}; Summer max = {sm_max_usa:.6f}; ratio = {sp_max_usa/sm_max_usa:.3f}")

    # Compare individual-cat peaks: do they all peak at the same hour in Summer Peak?
    print("\n--- Per-cat peak hours within Summer Peak vs Summer ---")
    merged_op = va_op.merge(usa_op, on="category", how="outer", suffixes=("_VA", "_USA"))
    merged_op.to_csv(os.path.join(OUT_DIR, "h2_per_category_peak_hours.csv"), index=False)
    print(merged_op.to_string(index=False))

    # Phantom check: sum of (per-cat max in Summer Peak) versus max of (sum across cats in Summer Peak)
    phantom_va = va_sp.max(axis=1).sum()
    coincident_va = va_sp.sum(axis=0).max()
    phantom_usa = usa_sp.max(axis=1).sum()
    coincident_usa = usa_sp.sum(axis=0).max()
    print(f"\nVA phantom (sum of cat-max) / coincident (max of cat-sum) for Summer Peak: {phantom_va:.6f} / {coincident_va:.6f} = {phantom_va/coincident_va:.3f}")
    print(f"USA phantom / coincident for Summer Peak: {phantom_usa:.6f} / {coincident_usa:.6f} = {phantom_usa/coincident_usa:.3f}")

    # Same for Summer (non-peak)
    phantom_va_s = va_sm.max(axis=1).sum()
    coincident_va_s = va_sm.sum(axis=0).max()
    phantom_usa_s = usa_sm.max(axis=1).sum()
    coincident_usa_s = usa_sm.sum(axis=0).max()
    print(f"VA phantom/coincident for Summer (main): {phantom_va_s/coincident_va_s:.3f}")
    print(f"USA phantom/coincident for Summer (main): {phantom_usa_s/coincident_usa_s:.3f}")

    # Save phantom metrics
    pm = pd.DataFrame([
        {"region": "VA", "slice": "Summer Peak", "phantom_sum": phantom_va, "coincident_max": coincident_va, "ratio": phantom_va/coincident_va},
        {"region": "USA", "slice": "Summer Peak", "phantom_sum": phantom_usa, "coincident_max": coincident_usa, "ratio": phantom_usa/coincident_usa},
        {"region": "VA", "slice": "Summer", "phantom_sum": phantom_va_s, "coincident_max": coincident_va_s, "ratio": phantom_va_s/coincident_va_s},
        {"region": "USA", "slice": "Summer", "phantom_sum": phantom_usa_s, "coincident_max": coincident_usa_s, "ratio": phantom_usa_s/coincident_usa_s},
    ])
    pm.to_csv(os.path.join(OUT_DIR, "h2_phantom_metrics.csv"), index=False)


if __name__ == "__main__":
    main()
