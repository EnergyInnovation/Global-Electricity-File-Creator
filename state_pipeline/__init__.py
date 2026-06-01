"""State-level SHELF + SYSHECF + clustering pipeline.

Architecture:
- Pulls per-end-use annual electricity demand from EPS input files (state-specific BCEU,
  BIFUbC, transportation calculator inputs, plus data center / district-heat / geoeng /
  hydrogen / CCS as those become populated).
- Applies hourly shapes from ResStock (TMY3), ComStock (TMY3), and EFS (2012 weather)
  to produce 8760 hourly demand by end-use category.
- Pulls hourly capacity factors from Cambium 2022 (Mid-case, 2024 anchor year, 2012
  weather basis) and computes hourly renewable generation per state using Cambium
  annual capacity by tech.
- Clusters days into 6 representative timeslices (Winter / Spring / Summer / Fall +
  Summer Peak + Winter Peak) on net load = demand - renewable generation.
- Exports per-state SHELF/SYSHECF CSVs and an annotated Excel workbook for user review.

Design principles:
- Pure-Python, no Vensim runtime dependency. Reads EPS *input* files, not EPS outputs.
- Bottom-up assembly with full categorical breakdown matching EPS BCEU AEO conventions.
- Methodologically transparent: every assumption documented in the per-state Excel
  About / Sources tabs.
- Replicable: any user with the same source data on disk can re-run the pipeline.
"""
__version__ = "0.1.0-sprint1"
