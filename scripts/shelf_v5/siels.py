"""National hourly load for seven industries from the Oak Ridge / Berkeley Lab SIELS dataset.

Source: Simulation of Industrial Electrical Load Shapes, Mendeley Data, doi:10.17632/jhghzm9yk5
(https://data.mendeley.com/datasets/jhghzm9yk5). The download is one zip holding seven CSVs, one per industry,
8,760 rows for 2018, one column per state, each state in its own local time.

Each state's column is moved later by its whole-hour offset from Eastern time, wrapping around the end of the
year, and the states are added together. The offsets are the same table the ResStock and ComStock aggregation
uses (STATE_TZ_OFFSET_TO_ET in scripts/build_shelf_workbook.py), passed in by the caller.

The result is saved to data/national_aggregated/siels_national_hourly.csv and reused on later runs, the same
way the ResStock and ComStock national series are.
"""
from __future__ import annotations
import csv
import io
import zipfile
from pathlib import Path

# column name in the workbook, file name inside the zip
FILES = [('food and beverage', 'food_and_beverage.csv'), ('pulp and paper', 'pulp_and_paper.csv'),
         ('petroleum and coal products', 'petroleum_and_coal_products.csv'), ('chemicals', 'chemical.csv'),
         ('ammonia', 'ammonia.csv'), ('cement', 'cement.csv'), ('iron and steel', 'ferroalloys.csv')]
NAMES = [n for n, _ in FILES]
ALIAS = {'Il': 'IL', 'IO': 'IA'}          # state labels as spelled in cement.csv
CACHE_NAME = 'siels_national_hourly.csv'


def _national(rows: list[list[str]], offsets: dict[str, int], label: str) -> tuple[list[str], list[float]]:
    hdr, data = rows[0], rows[1:]
    if len(data) != 8760:
        raise ValueError(f'{label}: expected 8760 hourly rows, found {len(data)}')
    out = [0.0] * 8760
    for j, h in enumerate(hdr):
        if j == 0:
            continue
        st = ALIAS.get(h, h)
        if st not in offsets:
            raise KeyError(f'{label}: no time-zone offset for state column {h!r}')
        off = offsets[st]
        for i, r in enumerate(data):
            v = r[j]
            if v not in ('', 'nan', 'NaN'):
                out[(i + off) % 8760] += float(v)
    return [r[0][:16] for r in data], out


def national_from_zip(zip_path: Path, offsets: dict[str, int]) -> tuple[list[str], dict[str, list[float]]]:
    """Return (timestamps, {industry: 8760 national values in Eastern time}) straight from the download."""
    cols: dict[str, list[float]] = {}
    stamps: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        members = {Path(n).name: n for n in zf.namelist() if not n.startswith('__MACOSX')}
        for name, fn in FILES:
            if fn not in members:
                raise FileNotFoundError(f'{fn} is not in {zip_path}')
            with zf.open(members[fn]) as raw:
                rows = list(csv.reader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline='')))
            stamps, cols[name] = _national(rows, offsets, fn)
    return stamps, cols


def write_cache(path: Path, stamps: list[str], cols: dict[str, list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['timestamp_eastern'] + NAMES)
        for i in range(8760):
            w.writerow([stamps[i]] + [repr(cols[n][i]) for n in NAMES])


def read_cache(path: Path) -> tuple[list[str], dict[str, list[float]]]:
    rows = list(csv.reader(open(path, newline='')))
    if rows[0][1:] != NAMES or len(rows) != 8761:
        raise ValueError(f'{path} is not a SIELS national series (columns {rows[0][1:]}, {len(rows) - 1} rows)')
    return [r[0] for r in rows[1:]], {n: [float(r[j + 1]) for r in rows[1:]] for j, n in enumerate(NAMES)}


def load_national(cache_dir: Path, zip_path: Path, offsets: dict[str, int], refresh: bool = False,
                  cache_name: str = CACHE_NAME):
    """Saved national series if present (and not refreshing), else build it from the zip and save it.

    Returns (timestamps, columns, where) with where = 'saved series' or 'raw zip'.
    cache_name lets a series built with a different time-zone table be saved beside the default one
    instead of over it.
    """
    cache = cache_dir / cache_name
    if cache.exists() and not refresh:
        print(f'  [siels] using saved series {cache}')
        return (*read_cache(cache), 'saved series')
    if not Path(zip_path).exists():
        raise FileNotFoundError(
            f'No saved series at {cache} and no SIELS zip at {zip_path}. Download it from '
            'https://data.mendeley.com/datasets/jhghzm9yk5 and point siels_zip at it (see local_paths.example.yml).')
    print(f'  [siels] aggregating {zip_path} to a national series (each state moved to Eastern time)...')
    stamps, cols = national_from_zip(Path(zip_path), offsets)
    write_cache(cache, stamps, cols)
    print(f'  [siels] saved -> {cache}')
    return stamps, cols, 'raw zip'
