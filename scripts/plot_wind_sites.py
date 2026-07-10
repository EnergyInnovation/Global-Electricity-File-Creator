"""Plot Renewables.ninja wind sites for a selected country on a map (GeoPandas).

Country-generic: set COUNTRY to the ISO2 code and the script does the rest —
it pulls that country's sites from the canonical list in
scripts/fetch_ninja_sites.py (single source of truth, so the map always matches
what was fetched), draws the country's boundary from Natural Earth, and writes
output/<country>_wind_sites_map.png. Onshore vs offshore are colored separately.

To add a country: add its sites to SITES in scripts/fetch_ninja_sites.py, then
set COUNTRY here to its ISO2 code. Nothing else to edit.

Run:
    python scripts/plot_wind_sites.py
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
from fetch_ninja_sites import SITES as NINJA_SITES  # canonical site list  # noqa: E402

# ---------------------------------------------------------------------------
# Country selector — ISO2 code. Must match the 'country' field used in
# scripts/fetch_ninja_sites.py SITES (e.g. "CN", "KR").
# ---------------------------------------------------------------------------
COUNTRY = "KR"

CACHE = Path(
    r"C:\Users\CLAIRE~1\AppData\Local\Temp\claude"
    r"\C--Users-Claire-Trevisan-GitHub-Global-Electricity-File-Creator"
    r"\a342d72e-41b1-4ba8-b9d3-8ba11cc8cc65\scratchpad"
)
NE_URL = "https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_countries.zip"
COLORS = {"onshore": "#1f77b4", "offshore": "#d62728"}


def load_countries() -> gpd.GeoDataFrame:
    """Load Natural Earth admin-0, downloading + caching the zip if needed."""
    CACHE.mkdir(parents=True, exist_ok=True)
    zpath = CACHE / "ne_50m_admin_0_countries.zip"
    if not zpath.exists():
        print(f"Downloading Natural Earth boundaries -> {zpath}")
        req = urllib.request.Request(NE_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            zpath.write_bytes(r.read())
    return gpd.read_file(f"zip://{zpath}")


def select_country(world: gpd.GeoDataFrame, iso2: str) -> tuple[gpd.GeoDataFrame, str]:
    """Return (country_geometry, display_name) for an ISO2 code.

    Tries ISO_A2, then ISO_A2_EH (Natural Earth stores '-99' in ISO_A2 for a few
    disputed/small territories but fills ISO_A2_EH).
    """
    name_col = "ADMIN" if "ADMIN" in world.columns else "NAME"
    for col in ("ISO_A2", "ISO_A2_EH"):
        if col in world.columns:
            sel = world[world[col] == iso2]
            if not sel.empty:
                return sel, str(sel.iloc[0][name_col])
    raise SystemExit(
        f"Country ISO2 {iso2!r} not found in Natural Earth admin-0. "
        f"Check the COUNTRY selector."
    )


def main():
    world = load_countries()
    country, display_name = select_country(world, COUNTRY)

    country_sites = [s for s in NINJA_SITES if s.get("country") == COUNTRY]
    if not country_sites:
        raise SystemExit(
            f"No sites for {COUNTRY!r} in fetch_ninja_sites.SITES. "
            f"Add them there first."
        )

    sites = gpd.GeoDataFrame(
        country_sites,
        geometry=[Point(s["lon"], s["lat"]) for s in country_sites],
        crs="EPSG:4326",
    )

    fig, ax = plt.subplots(figsize=(11, 9))
    country.plot(ax=ax, color="#f2f2ee", edgecolor="#555555", linewidth=0.8)
    world.boundary.plot(ax=ax, color="#cccccc", linewidth=0.4, zorder=0)  # neighbor context

    for typ, grp in sites.groupby("type"):
        grp.plot(ax=ax, color=COLORS.get(typ, "#666666"), markersize=90,
                 edgecolor="white", linewidth=0.8, label=f"{typ} ({len(grp)})", zorder=5)

    for _, row in sites.iterrows():
        ax.annotate(
            row["name"].replace("_", " "),
            xy=(row.geometry.x, row.geometry.y),
            xytext=(5, 5), textcoords="offset points",
            fontsize=8, color="#222222",
        )

    # Frame to the country with a small margin.
    minx, miny, maxx, maxy = country.total_bounds
    ax.set_xlim(minx - 2, maxx + 2)
    ax.set_ylim(miny - 2, maxy + 2)
    ax.set_title(
        f"Renewables.ninja wind sites — {display_name}\n",
       # f"(placeholder coordinates, verify before use)",
        fontsize=13,
    )
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.legend(title="Site type", loc="lower left")
    ax.set_aspect("equal")
    fig.tight_layout()

    slug = display_name.lower().replace(" ", "_")
    out_png = PROJECT_ROOT / "output" / f"{slug}_wind_sites_map.png"
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=150)
    print(f"Saved: {out_png}  ({len(country_sites)} sites)")


if __name__ == "__main__":
    main()
