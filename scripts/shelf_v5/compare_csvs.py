"""Compare exported SHELF CSVs (and ICwIwLF.csv) with a reference copy, file by file.

Reports how many files are identical as text (line endings aside) and, for the rest, how many numbers differ
as printed and by how much. The reference can be an eps-us InputData folder, or files pulled from a commit
with `git show <commit>:<path>`.

Usage:
    python scripts/shelf_v5/compare_csvs.py <built out folder> <reference InputData folder>
Both folders hold elec/SHELF/*.csv and, for 5.0, ctrl-settings/ICwIwLF/ICwIwLF.csv.
Exit code 0 when every file present on either side matches as printed.
"""
from __future__ import annotations
import sys
from pathlib import Path

SUBS = [Path('elec') / 'SHELF', Path('ctrl-settings') / 'ICwIwLF']


def read(p: Path) -> str:
    return p.read_bytes().decode('utf-8-sig').replace('\r\n', '\n')


def main() -> int:
    built, ref = Path(sys.argv[1]), Path(sys.argv[2])
    files = sorted({(s, f.name) for root in (built, ref) for s in SUBS for f in (root / s).glob('*.csv')})
    identical = cells = diff_cells = 0
    worst = 0.0
    problems = []
    for sub, name in files:
        a, b = built / sub / name, ref / sub / name
        if not a.exists() or not b.exists():
            problems.append(f'{name}: only in {"reference" if b.exists() else "built"}')
            continue
        ta, tb = read(a), read(b)
        ra = [line.split(',') for line in ta.strip().split('\n')]
        rb = [line.split(',') for line in tb.strip().split('\n')]
        cells += sum(len(r) - 1 for r in rb[1:])
        if ta == tb:
            identical += 1
            continue
        if len(ra) != len(rb) or [r[0] for r in ra] != [r[0] for r in rb] or ra[0] != rb[0]:
            problems.append(f'{name}: row labels, header or row count differ')
            continue
        n, mx = 0, 0.0
        for x, y in zip(ra[1:], rb[1:]):
            for u, v in zip(x[1:], y[1:]):
                if u == v:
                    continue
                try:
                    fu, fv = float(u), float(v)
                except ValueError:
                    n += 1
                    mx = float('inf')
                    continue
                if fu != fv:
                    n += 1
                    mx = max(mx, abs(fu - fv) / max(abs(fu), abs(fv)))
        if n:
            diff_cells += n
            worst = max(worst, mx)
            problems.append(f'{name}: {n} numbers differ as printed, largest relative difference {mx:.1e}')
        else:
            problems.append(f'{name}: same numbers, written differently')
    print(f'files compared: {len(files)}; identical as text: {identical}; numbers compared: {cells}; '
          f'numbers that differ as printed: {diff_cells}; largest relative difference: {worst:.1e}')
    for p in problems:
        print('  ', p)
    return 0 if not problems else 1


if __name__ == '__main__':
    sys.exit(main())
