"""Which ResStock / ComStock release the home and business load shapes are built from, and on which clock.

Two sources (`--buildings`):
  typical  NREL typical-year weather on a 2018 calendar (ResStock 2024 Release 2, ComStock 2021 Release 1).
           The default; reproduces the files on eps-us `develop`.
  amy2012  NREL runs with the actual weather of 2012 (ResStock 2025 Release 1 `resstock_amy2012_release_1`,
           ComStock 2025 Release 2 `comstock_amy2012_release_2`), the weather year of the Cambium file that sets
           the timeslices. The files run 2012-01-01 00:15 to 2012-12-31 00:00 (15-minute intervals, stamped at the
           end of the interval): 1 January to 30 December, 29 February kept, 8,760 hours, so day number n is day
           number n of the Cambium file and no weekday alignment is needed.

Two clocks (`--building-clock`):
  pipeline  each state is moved later by its distance from Eastern time (STATE_TZ_OFFSET_TO_ET) before the states
            are added. The default; what the pipeline has always done.
  eastern   no shift. NREL stamps every state file in Eastern Standard Time already (no daylight saving), so the
            states are added as they are.

Television (`--television`, ResStock 2025 R1 only): counted in `residential-other` by default for amy2012.

Delay (`--building-delay-hours`, default 0): after the states are added, every residential and commercial hourly
series is delayed by a fractional number of hours (delay_hourly). A calibration to measured demand: NREL's modelled
day runs about half an hour early.

The saved national series (data/national_aggregated/) has one file per source, clock and television setting, so that
a series built one way is never read as another. The delay is applied after the series is read, so it has no file.
"""
from __future__ import annotations

SOURCES = ('typical', 'amy2012')
CLOCKS = ('pipeline', 'eastern')
# ResStock 2025 R1 lists television as its own end use (earlier releases counted it in plug loads, which the
# `residential-other` category takes). 'omit' leaves it out (the default); 'other' adds it to residential-other.
TELEVISION = ('omit', 'other')

# key in shelf_v5/paths.py for the folder of raw state files, and base name of the saved national series
_ROOT_KEY = {('resstock', 'typical'): 'resstock_root', ('comstock', 'typical'): 'comstock_root',
             ('resstock', 'amy2012'): 'resstock_amy2012_root', ('comstock', 'amy2012'): 'comstock_amy2012_root'}
_CACHE_BASE = {('resstock', 'typical'): 'resstock_national_hourly', ('comstock', 'typical'): 'comstock_national_hourly',
               ('resstock', 'amy2012'): 'resstock_amy2012_national_hourly',
               ('comstock', 'amy2012'): 'comstock_amy2012_national_hourly'}


def root_key(kind: str, source: str) -> str:
    return _ROOT_KEY[(kind, source)]


def cache_name(kind: str, source: str, clock: str, television: str = 'omit') -> str:
    """File name of the saved national series. The default source and clock keep their original names."""
    assert source in SOURCES and clock in CLOCKS and television in TELEVISION, (source, clock, television)
    tv = '_television' if (kind == 'resstock' and television == 'other') else ''
    return _CACHE_BASE[(kind, source)] + ('' if clock == 'pipeline' else '_eastern_clock') + tv + '.csv'


def television_end_uses(television: str) -> dict[str, list[str]]:
    """Extra residential end uses to add to a category (see `--television`)."""
    return {'residential-other': ['television']} if television == 'other' else {}


def resolve_television(source: str, television: str | None) -> str:
    """The television setting actually used. With the actual-2012-weather source television is counted in
    residential-other unless `--television omit` is given; the typical-year source has no television column."""
    if television is None:
        return 'other' if source == 'amy2012' else 'omit'
    if television == 'other' and source != 'amy2012':
        raise ValueError('--television other applies to --buildings amy2012 only (typical-year ResStock has no '
                         'separate television column)')
    return television


def delay_hourly(df, hours: float):
    """Move every column of an hourly frame later by `hours` (fractional allowed) and keep its energy.

    For a delay of k whole hours plus a fraction f, each hour becomes (1 - f) x the load k hours earlier plus
    f x the load k + 1 hours earlier. The weights add to 1 and the year wraps round (Dec 30 -> Jan 1, as the
    time-zone shift does), so the annual total is unchanged exactly; a single day's total changes slightly,
    because load near midnight moves into the next day. A calibration to measured demand, not a clock
    correction (see the About tab note 'Buildings delay')."""
    import numpy as np
    if not hours:
        return df
    k = int(np.floor(hours))
    f = float(hours) - k
    out = df.copy()
    for c in out.columns:
        x = out[c].values
        out[c] = (1 - f) * np.roll(x, k) + f * np.roll(x, k + 1)
    return out
