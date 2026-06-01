"""Calibrate VRE SYSHECF files to EIA observed annual CFs.

For each VRE tech:
1. Read existing SYSHECF CSV from eps-us InputData
2. Compute implied annual CF using days_per_slice
3. Apply a multiplicative scale so annual CF matches EIA target
4. Write new SYSHECF CSV (same format) back to eps-us InputData
"""
import csv
from pathlib import Path

SYSHECF_DIR = Path(r"C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SYSHECF")

# EIA 2024 observed annual fleet CFs (Table 4.8.B)
EIA_TARGET_CF = {
    'onshore-wind':    0.343,
    'offshore-wind':   0.42,    # approximate; small US fleet
    'solar-pv':        0.232,
    'solar-pv-dist':   0.17,
    'solar-thermal':   0.250,
}

# K6 canonical days per slice (must sum to 365)
DAYS_PER_SLICE = {
    'Winter': 65, 'Spring': 82, 'Summer': 119, 'Fall': 52,
    'Summer Peak': 27, 'Winter Peak': 20,
}
assert sum(DAYS_PER_SLICE.values()) == 365

SLICE_ORDER = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']
MAX_CF_CLIP = 1.0


def read_syshecf(path: Path):
    """Return (first_cell_label, {slice: [24 floats]})."""
    with open(path, newline='') as f:
        rows = list(csv.reader(f))
    first_cell = rows[0][0]
    grid = {}
    for r in rows[1:]:
        if not r or not r[0]:
            continue
        slice_name = r[0].strip()
        try:
            vals = [float(x) for x in r[1:25]]
        except (ValueError, IndexError):
            continue
        if len(vals) == 24:
            grid[slice_name] = vals
    return first_cell, grid


def annual_cf(grid):
    """Weighted average CF using days_per_slice."""
    total_cf_hours = 0.0
    for sl in SLICE_ORDER:
        if sl not in grid:
            continue
        slice_sum = sum(grid[sl])  # 24 hourly CFs
        total_cf_hours += slice_sum * DAYS_PER_SLICE[sl]
    return total_cf_hours / 8760.0


def scale_grid(grid, scale):
    out = {}
    for sl, vals in grid.items():
        out[sl] = [min(MAX_CF_CLIP, v * scale) for v in vals]
    return out


def write_syshecf(path: Path, first_cell: str, grid: dict):
    hour_cols = [f'Hour{h}' for h in range(24)]
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([first_cell] + hour_cols)
        for sl in SLICE_ORDER:
            if sl in grid:
                vals_str = [f"{v:.10g}" for v in grid[sl]]
                w.writerow([sl] + vals_str)


def main():
    print(f"Reading SYSHECF files from: {SYSHECF_DIR}")
    print()
    print(f"{'Tech':<20}{'EIA target':>13}{'Before':>10}{'Scale':>10}{'After':>10}")
    print("-" * 70)

    for tech_slug, target in EIA_TARGET_CF.items():
        fp = SYSHECF_DIR / f"SYSHECF-{tech_slug}.csv"
        if not fp.exists():
            print(f"  ! File not found: {fp.name}")
            continue
        first_cell, grid = read_syshecf(fp)
        before = annual_cf(grid)
        if before <= 1e-6:
            print(f"{tech_slug:<20}{target:>13.4f}{'~0':>10}{'skip':>10}{'-':>10}")
            continue
        scale = target / before
        new_grid = scale_grid(grid, scale)
        after = annual_cf(new_grid)
        write_syshecf(fp, first_cell, new_grid)
        print(f"{tech_slug:<20}{target:>13.4f}{before:>10.4f}{scale:>10.4f}{after:>10.4f}")

    print()
    print("Done. Files written to:", SYSHECF_DIR)


if __name__ == "__main__":
    main()
