"""Extract onshore/offshore wind capacity shares from EPS models' start-year capacities.

Reads `InputData/elec/BHRaSYC/BHRaSYC-StartYearCapacities.csv` from one or more
regional EPS model checkouts, sums the `onshore wind` and `offshore wind` rows
across ALL vintage columns (the sum over vintages IS that technology's start-year
capacity), and writes the resulting capacity shares to a lookup CSV.

Output: `data/eps_wind_capacity_split.csv`
Columns: iso2, onshore_mw, offshore_mw, onshore_share, offshore_share,
         source_model, source_file, retrieved

`source_model` is the model folder's name and `source_file` its repo-relative
path — machine-independent provenance, since each person's checkout lives
somewhere different.

Those shares are what `energy_timeslice_pipeline.load_eps_wind_capacity_split`
feeds to the wind-CF loader as `wind_capacity_split`, so the blended `wind_cf`
(net load, clustering, and the Ember calibration anchor) is weighted by installed
capacity rather than by how many Renewables.ninja site files happen to be on
disk. Only presets on the `ninja_sites` wind path use it. See CLAUDE.md →
"Onshore vs offshore wind are separate SYSHECF series" and DECISIONS.md.

Model checkouts live outside this repo and their paths differ per machine, so
they are passed in rather than hardcoded:

    python scripts/fetch_eps_wind_capacity_split.py \
        --model CN="C:/Users/<you>/GitHub/eps-china-igdp/eps-china-igdp" \
        --model KR="C:/Users/<you>/GitHub/eps-southkorea"

    # or point straight at a BHRaSYC-StartYearCapacities.csv
    python scripts/fetch_eps_wind_capacity_split.py --model CN=".../BHRaSYC-StartYearCapacities.csv"

    python scripts/fetch_eps_wind_capacity_split.py --model CN=... --dry-run

Re-run whenever a model's start-year capacities are updated. Existing rows for
an ISO2 are replaced; rows for other regions are left alone, so you can refresh
one country at a time. Verify the extracted capacities against the model's own
documentation before relying on them in a work product.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
OUTPUT_CSV = ROOT / "data" / "eps_wind_capacity_split.csv"

# Row labels in BHRaSYC-StartYearCapacities.csv (first column).
ONSHORE_ROW = "onshore wind"
OFFSHORE_ROW = "offshore wind"

REL_PATH = Path("InputData") / "elec" / "BHRaSYC" / "BHRaSYC-StartYearCapacities.csv"

FIELDS = ["iso2", "onshore_mw", "offshore_mw", "onshore_share", "offshore_share",
          "source_model", "source_file", "retrieved"]


def source_provenance(capacities_csv: Path) -> tuple[str, str]:
    """Machine-independent provenance: (model folder name, model-relative path).

    Absolute paths would bake one person's home directory into a checked-in data
    file, so record where the file sits *inside* the model instead.
    """
    parts = capacities_csv.resolve().parts
    try:
        # .../<model>/InputData/elec/BHRaSYC/BHRaSYC-StartYearCapacities.csv
        input_data_idx = len(parts) - 1 - parts[::-1].index('InputData')
        model = parts[input_data_idx - 1]
        rel = '/'.join(parts[input_data_idx:])
    except ValueError:
        # Non-standard layout (e.g. a CSV passed from somewhere else entirely).
        model = capacities_csv.parent.name
        rel = capacities_csv.name
    return model, rel


def resolve_capacities_csv(model_path: Path) -> Path:
    """Accept either a model root or the capacities CSV itself."""
    if model_path.is_file():
        return model_path
    candidate = model_path / REL_PATH
    if candidate.is_file():
        return candidate
    raise SystemExit(
        f"ERROR: no start-year capacities file for {model_path}\n"
        f"  expected {candidate}\n"
        "  Pass either the model root (containing InputData/elec/BHRaSYC/) or the "
        "BHRaSYC-StartYearCapacities.csv path directly."
    )


def wind_capacities(capacities_csv: Path) -> tuple[float, float]:
    """Return (onshore_MW, offshore_MW) summed over every vintage column."""
    df = pd.read_csv(capacities_csv, index_col=0)
    df.index = df.index.astype(str).str.strip()
    missing = [r for r in (ONSHORE_ROW, OFFSHORE_ROW) if r not in df.index]
    if missing:
        raise SystemExit(
            f"ERROR: {capacities_csv} has no {missing} row(s). "
            f"Found wind-like rows: {[r for r in df.index if 'wind' in r.lower()]}"
        )
    totals = df.apply(pd.to_numeric, errors='coerce').fillna(0.0).sum(axis=1)
    return float(totals.loc[ONSHORE_ROW]), float(totals.loc[OFFSHORE_ROW])


def vintage_span(capacities_csv: Path, row: str) -> str:
    """First..last vintage column with a non-zero entry — provenance for the log."""
    df = pd.read_csv(capacities_csv, index_col=0)
    df.index = df.index.astype(str).str.strip()
    series = pd.to_numeric(df.loc[row], errors='coerce').fillna(0.0)
    nonzero = series[series != 0]
    if nonzero.empty:
        return "none"
    return f"{nonzero.index[0]}..{nonzero.index[-1]}"


def read_existing() -> dict[str, dict]:
    if not OUTPUT_CSV.exists():
        return {}
    with open(OUTPUT_CSV, newline='', encoding='utf-8') as fh:
        return {row['iso2']: row for row in csv.DictReader(fh)}


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--model', action='append', default=[], metavar='ISO2=PATH',
                    required=True,
                    help='Region and its EPS model checkout (repeatable), e.g. '
                         '--model CN="C:/.../eps-china-igdp". PATH may be the model '
                         'root or the BHRaSYC-StartYearCapacities.csv itself.')
    ap.add_argument('--dry-run', action='store_true',
                    help='Report the capacities and shares without writing the CSV.')
    args = ap.parse_args()

    rows = read_existing()
    retrieved = dt.date.today().isoformat()

    for spec in args.model:
        if '=' not in spec:
            raise SystemExit(f"ERROR: --model expects ISO2=PATH, got {spec!r}")
        iso2, _, path_txt = spec.partition('=')
        iso2 = iso2.strip().upper()
        capacities_csv = resolve_capacities_csv(Path(path_txt.strip().strip('"\'')))
        onshore, offshore = wind_capacities(capacities_csv)
        total = onshore + offshore
        if total <= 0:
            print(f"[{iso2}] SKIP: start-year wind capacity is zero in {capacities_csv}")
            continue
        print(f"[{iso2}] {capacities_csv}")
        print(f"       onshore  {onshore:>12,.0f} MW  (vintages "
              f"{vintage_span(capacities_csv, ONSHORE_ROW)})")
        print(f"       offshore {offshore:>12,.0f} MW  (vintages "
              f"{vintage_span(capacities_csv, OFFSHORE_ROW)})")
        print(f"       shares   onshore={onshore / total:.6f}  "
              f"offshore={offshore / total:.6f}")
        source_model, source_file = source_provenance(capacities_csv)
        rows[iso2] = {
            'iso2': iso2,
            'onshore_mw': f'{onshore:.6g}',
            'offshore_mw': f'{offshore:.6g}',
            'onshore_share': f'{onshore / total:.6f}',
            'offshore_share': f'{offshore / total:.6f}',
            'source_model': source_model,
            'source_file': source_file,
            'retrieved': retrieved,
        }

    if args.dry_run:
        print('\n--dry-run: nothing written.')
        return

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for iso2 in sorted(rows):
            writer.writerow({k: rows[iso2].get(k, '') for k in FIELDS})
    print(f"\nWrote {OUTPUT_CSV}  ({len(rows)} region(s): {', '.join(sorted(rows))})")


if __name__ == '__main__':
    main()
