# Integration plan — bring develop's non-US capability onto `master`

*Generated 2026-06-03. **For staff review.** Every git-state fact below was verified against
`origin/develop` and `master` during a Phase 0 audit on 2026-06-03, but branches move — re-confirm
on the live branches before executing. Any pipeline outputs produced after integration must be
validated against primary sources (Cambium, EIA, Ember, DemandCast, Renewables.ninja) before use in
any work product. Treat this as a starting point, open to refinement.*

Companion document: [`CLUSTERING_BRANCH_COMPARISON.md`](CLUSTERING_BRANCH_COMPARISON.md) (the earlier
master→develop framing). **This document supersedes it for the develop→master direction.**

---

## 0. TL;DR

- **Goal:** make `master` the single trunk carrying *both* the US/state pipeline (already on master)
  and develop's international capability (China, South Korea, + 10 more country presets, Zapata/Mendeley
  end-use shapes, NNLS/ridge calibration to EPS priors, Renewables.ninja weather, DemandCast sync).
- **Phase 0 verdict:** a real `git merge origin/develop` produces a **textually clean tree (zero
  conflicts)** that *preserves* master's clustering wrapper, `state_pipeline/`, and the methodology docs,
  while importing develop's new functions and files. **No function bodies merge into "Frankenstein"
  hybrids.** The heavy-conflict scenario feared in the comparison doc did **not** materialise.
- **The merge is not complete on its own.** It leaves exactly one verified functional gap: develop's
  `run_pipeline()` does not forward `country` into the clustering call, so Brazil/Australia would still
  get Northern-Hemisphere seasons. Fix = **one line.**
- **Decision locked (this round):** the large data files (CN/KR MERRA-2 weather CSVs, literature PDFs)
  **will be committed into `master`'s history** (see §6).
- **Recommended path:** **Path B — assisted merge + targeted fixups + verification.** Lower effort than a
  hand-port, now that Phase 0 has shown the merge is clean. **Path A (curated port)** is retained as a
  fallback in §8.
- **Control surface:** `run_pipeline.py` (from develop) is the single user-facing runner — usable by any
  team member, it selects the country and all key settings, keeps the cluster-vs-actual diagnostic plots
  behind a boolean, and (per staff direction) must also surface the US-specific choices. Full requirements
  in **§13**.

---

## 1. Verified branch topology

| Fact | Value |
|---|---|
| Merge base | `d4ef526` ("correcting downloaded hourly data for Korea") |
| `master` ahead of base | 1 commit (`a62879b` "Updated clustering + US/state and carryover clustering to international work") |
| `develop` ahead of base | 5 commits (Mendeley/DemandCast/Ember/Renewables.ninja calibration; `run_pipeline.py` control/processing split) |
| At the merge base | `cluster_timeslices` existed as an **inline** implementation (no wrapper helpers) |
| What `master` did | Refactored inline `cluster_timeslices` → hemisphere-aware **wrapper** delegating to `state_pipeline.builders.clustering_repday.cluster_days_repday`; added `_cluster_timeslices_via_repday`, `_hemisphere_season_months`, `_cluster_timeslices_legacy_impl`; added `state_pipeline/`, `CLAUDE.md`, `CLUSTERING_METHODOLOGY.md`, `DECISIONS.md`, US state Cambium data, workbook/verify scripts |
| What `develop` did | Kept editing the **inline** `cluster_timeslices`; added the non-US layer (functions + `run_pipeline.py` + `requirements.txt` + `data/eps_priors/` + CN/KR weather + literature) |

**Neither branch is a superset of the other.** Master is the stronger trunk (it has the consolidation,
the docs, and the full US/state pipeline). Develop's value-add is a self-contained international layer.

---

## 2. Phase 0 audit results (the evidence)

### 2.1 Compatibility — all green
| Check | Result |
|---|---|
| `cluster_timeslices` signature, master vs develop | **Identical**; master only *adds* a trailing `country: Optional[str] = None` |
| Return shape | **Identical** 4-tuple `(pd.Series labels, KMeans, Dict[int,int] mapping, Dict[int,pd.Timestamp] representative_dates)` |
| All 11 run-path helpers present on master (`_extract_timestamps`, `compute_net_load`, `compute_capacity_factors`, `compute_load_factors`, `build_timeslice_metadata`, `compute_hourly_capacity_profiles`, `compute_hourly_load_profiles`, `resolve_output_path`, `export_to_excel`, `list_country_presets`, `generate_full_pipeline_for_preset`) | ✓ |
| `KMeans` model / `mapping` introspected downstream? | **No** — develop's only use of `.fit_predict`/`.cluster_centers_` is *inside* its inline `cluster_timeslices` body (the code we discard). Both call sites unpack the tuple and use only `labels` + `representative_dates`; `run_pipeline()` passes `model`/`mapping` through to its `return_details` dict but never reads them. Master's placeholder model is safe. |

### 2.2 The comparison doc's "one correctness pitfall" is **overstated**
- `assign_seasonal_labels` — **byte-identical** on both branches. It derives season from the **timestamp's
  calendar month**, not from label rank; labels are used only for a cosmetic `labels >= half`
  peak/off-peak suffix.
- `build_timeslice_metadata` — **byte-identical** on both branches, and **data-driven**: it identifies the
  pinned summer/winter slice by locating the max-net-load row *within calendar summer/winter months* and
  reading off whichever integer ID sits there. Slice naming therefore works correctly **regardless** of
  whether the integers are master's DOY order (Winter=0…Winter Peak=5) or develop's p95-rank order.
- **Consequence:** no downstream-consumer rewrite is required for label semantics. The only label-order
  effect is the cosmetic peak/off-peak suffix in `assign_seasonal_labels`, which annotates the
  international Excel export — not the SHELF/SYSHECF slice identities.

### 2.3 Merge simulation (`git merge-tree --write-tree master origin/develop`)
- **Clean: zero conflicts, exit 0.** Written tree OID `a1a8a28…` (a dangling object from the simulation;
  no working-tree changes were made).
- Merged tree **preserves** master's `_cluster_timeslices_via_repday`, `_hemisphere_season_months`,
  `state_pipeline/`, and `CLAUDE.md`; **imports** `run_pipeline.py`, `requirements.txt`,
  `data/eps_priors/`, and all of develop's new functions (`build_zapata_hybrid_basis`,
  `calibrate_via_monthly_nnls`, `calibrate_via_monthly_ridge_nnls`, `load_eps_magnitude_prior`,
  `_load_weather_data_uncached`, `set_verbosity`, `make_calibration_overview_plot`, …).
- **Body resolution** (md5 of each shared function vs master vs develop):
  | Function | Resolved to | Assessment |
  |---|---|---|
  | `cluster_timeslices` | **master's wrapper** | ✅ intended — keeps the consolidated rep-day clustering |
  | `generate_full_pipeline_for_preset` | **develop's** | ✅ keeps the international orchestrator |
  | `calibrate_seasonal_enduse_load` | identical (both) | ✅ no-op |
  | `compare_pinned_unpinned_clustering` | identical (both) | ✅ no-op |
  | `assign_seasonal_labels` | identical (both) | ✅ no-op |
  | — any function — | **HYBRID (matches neither)** | **None.** No Frankenstein bodies. |
- The Zapata / `latitude_deg` / `calibration_method` wiring lives in `generate_full_pipeline_for_country`
  (develop:3123), which the merge takes from develop. Develop's new helper functions are therefore
  **wired in, not orphaned.**

> **Correction recorded for transparency:** during the live audit an intermediate step mis-attributed the
> Zapata wiring to `calibrate_seasonal_enduse_load` and reported a false "smoking gun" that the merge
> orphaned develop's helpers. The byte-level body comparison disproved this. The helpers are wired via
> `generate_full_pipeline_for_country`, which the merge keeps from develop.

### 2.4 The one verified functional gap
- Develop's `run_pipeline()` function (call site `energy_timeslice_pipeline.py:6822`) calls
  `cluster_timeslices(net, timestamps=…, n_clusters=…, feature_weight_mode=…, search_seeds=…)` — **without**
  `country`, `winter_months`, or `summer_months`.
- Result after a plain merge: master's wrapper runs but defaults to Northern-Hemisphere season months, so
  **Brazil/Australia silently get boreal-winter peaks** — the exact bug the consolidation was meant to fix.
- **`run_pipeline()` already receives a `country: Optional[str] = None` parameter**, so the fix is a
  one-line forward (see §7).
- Master's `SOUTHERN_HEMISPHERE_COUNTRIES` set already includes **Brazil** and **Australia** (the only two
  SH presets among develop's 12: south korea, china, united states, canada, japan, india, germany, france,
  united kingdom, australia, brazil, mexico).

---

## 3. Scope of the integration

**Code (single file):** `energy_timeslice_pipeline.py` — reconciled by the merge as in §2.3, plus the §7 fixup.

**New files imported from develop (additive):**
- `run_pipeline.py` (control/processing entry point; only imports `energy_timeslice_pipeline`)
- `requirements.txt`, `zipfile_deflate64.py`
- `data/eps_priors/` (`eps_prior_CN.csv`, `eps_prior_KR.csv`, `eps_prior_US.csv`, `parse_eps_extract.py`)
- `data/output_demand_ninja/china_*` (province split, heating/cooling hourly, summary)
- `data/weather/ninja-weather-country-CN-…merra2.csv` and the KR weather file
- `literature/` (Staffell et al. 2023 + supplement, Zapata et al. 2022 + supplement, reading notes)

**Preserved from master (the merge keeps these — confirmed in §2.3):**
- `state_pipeline/` package (all readers/builders/presets/run.py)
- `CLAUDE.md`, `CLUSTERING_METHODOLOGY.md`, `DECISIONS.md`
- US state Cambium 2022 data, EIA state profiles, workbook + verify scripts, validation reports

---

## 4. Recommended approach — Path B: assisted merge + fixups + verification

Effort estimate: **~half a day**, dominated by verification.

### Phase B1 — Branch & merge (~20 min)
1. `git checkout -b feature/international-onto-master master` *(already created during Phase 0; reuse it).*
2. `git merge --no-ff --no-commit origin/develop`
   — Expect a clean merge (Phase 0 simulation showed zero conflicts). `--no-commit` lets you inspect before
   committing.
3. Sanity-inspect the staged tree **before** committing:
   - `python -c "import ast,sys; ast.parse(open('energy_timeslice_pipeline.py').read())"` — syntax OK.
   - `grep -c "^def cluster_timeslices" energy_timeslice_pipeline.py` → expect **1**.
   - Confirm `state_pipeline/`, `CLAUDE.md`, `CLUSTERING_METHODOLOGY.md`, `DECISIONS.md` still present.
   - Confirm `run_pipeline.py`, `requirements.txt`, `data/eps_priors/` now present.

### Phase B2 — The one required code fixup (~10 min)
In `run_pipeline()` (`energy_timeslice_pipeline.py:~6822`), forward the hemisphere context that the
function already has into the clustering call (see §7 for the exact diff).

### Phase B3 — Commit (~5 min)
`git commit` the merge with the fixup folded in. Use a message documenting the consolidation and the
hemisphere fix; reference this plan and `DECISIONS.md`.

### Phase B4 — Verify (~2–4 hrs) — see §9.

### Phase B5 — Docs & cleanup (~30 min)
- Add a `DECISIONS.md` entry: the develop→master consolidation, the data-driven-naming finding (which
  retired the "label-semantics pitfall"), and the `country=` hemisphere fix.
- Update `README.md` / `CLAUDE.md` to document the international entry point (`run_pipeline.py`,
  `generate_full_pipeline_for_preset`) and the 12-country preset list.
- Open the PR against `master`. After merge, decide with the team whether `develop` is retired (it becomes
  redundant under a single-trunk model — see §10).

---

## 5. (Not chosen) — open the PR strategy with the team
Single-trunk vs. keep-develop-as-fork is a team decision (§10). The plan assumes single-trunk because the
request is "incorporate develop's non-US changes onto master," but Path B works either way.

---

## 6. Large data files — DECISION: commit into `master`

Per staff direction (2026-06-03), the large binary/CSV inputs from develop are to be **committed into
`master`'s permanent history**:
- CN/KR MERRA-2 weather CSVs (`data/weather/ninja-weather-country-CN-…merra2.csv`, KR file) — hundreds of
  thousands of rows each.
- Literature PDFs (`literature/Staffell et al 2023 Supplement.pdf` ≈ 46 MB, `Staffell et al 2023.pdf`
  ≈ 30 MB, Zapata PDFs/docx).

A plain `git merge` (Path B) brings these in automatically — **no `.gitignore` surgery needed.**

**Implication to acknowledge with the team (not a blocker):** this permanently adds ~100s of MB to clone
size. *Optional future refinement* (does not change this round): migrate the large binaries to **Git LFS**
to keep working-tree convenience without bloating every clone's pack history. Flag for the IT & Systems
team (itsystems@energyinnovation.org) if repository hosting limits or LFS quotas are a concern.

---

## 7. The required code fixup (exact)

**File:** `energy_timeslice_pipeline.py`, inside `run_pipeline()` (~line 6822 on develop's numbering).

```diff
     labels, model, mapping, representative_dates = cluster_timeslices(
         net,
         timestamps=timestamps,
         n_clusters=n_clusters,
         feature_weight_mode=feature_weight_mode,
         search_seeds=search_seeds,
+        country=country,          # forward hemisphere context (master wrapper handles SH season flip)
     )
```

Notes:
- `run_pipeline()` already declares `country: Optional[str] = None`, so no new parameter threading is
  required — only the forward.
- Master's wrapper resolves `winter_months`/`summer_months` from `_hemisphere_season_months(country)` when
  they are not explicitly passed. Explicit month args still take precedence if a caller supplies them.
- Confirm `compare_pinned_unpinned_clustering` (call site `:2709`) — for non-US diagnostic runs you may
  optionally forward `country=` there too, so the pinned-vs-unpinned diagnostic uses austral seasons for SH
  countries. Lower priority (diagnostic only).

**This is the only fixup needed for correctness.** A second, separate change — surfacing the US-specific
settings on `run_pipeline.py` — is a staff requirement (not a merge blocker) and is specified in **§13**.

---

## 8. Fallback — Path A: curated port (only if Path B verification fails)

If runtime verification (§9) surfaces a semantic problem at the develop-orchestrator ↔ master-wrapper seam
that is awkward to fix in-place, fall back to hand-porting develop's additive layer onto master without a
wholesale merge:
1. `git checkout origin/develop -- run_pipeline.py requirements.txt zipfile_deflate64.py data/eps_priors data/output_demand_ninja data/weather literature`
2. Port develop-only functions into master's `energy_timeslice_pipeline.py`: the `_zapata_*` family,
   `build_zapata_hybrid_basis`, `calibrate_via_monthly_nnls`, `calibrate_via_monthly_ridge_nnls`,
   `align_basis_to_prior`, `load_eps_magnitude_prior`, the weather-cache helpers
   (`_cache_is_stale`, `_read_or_build_cached_parquet`, `_resolve_cache_dir`, `_safe_filename_part`,
   `_load_weather_data_uncached`), `_sync_manual_downloads_to_demandcast`, `_status`, `set_verbosity`,
   `_cap_and_redistribute_cf`, `make_calibration_overview_plot`, `make_cluster_diagnostic_plots`.
3. Port develop's `generate_full_pipeline_for_country`/`_for_preset`, `run_pipeline`, and the expanded
   12-country `COUNTRY_PRESETS` (merge with master's; keep `latitude_deg`/timezone fields).
4. **Keep master's `cluster_timeslices` wrapper** (do not bring develop's inline body — it is already
   preserved on master as `_cluster_timeslices_legacy_impl`).
5. Apply the §7 fixup. Then §9 verification.

Path A is more labour but gives line-by-line control. Given Phase 0, it is **not** expected to be necessary.

---

## 9. Verification plan (applies to both paths)

| # | Test | Pass criterion |
|---|---|---|
| 1 | **US regression (must not change)** — run master's US/state pipeline (`python -m state_pipeline.run --state US-VA`, and/or `rebuild_us_national_v2.py`) | SHELF/SYSHECF CSVs **bit-identical** to pre-merge outputs (US clustering path is untouched) |
| 2 | **Import/syntax** — `import energy_timeslice_pipeline` and `import run_pipeline` | No ImportError; `state_pipeline.builders.clustering_repday` importable so the wrapper uses rep-day (not the legacy fallback) |
| 3 | **Brazil smoke test (SH)** — `generate_full_pipeline_for_preset('Brazil', …)` | (a) no exceptions; (b) Summer Peak representative DOYs in **Dec–Feb**; (c) `days_per_timeslice` sums to **365** |
| 4 | **Korea & China end-to-end** — the two presets with bundled data | Runs against the EPS priors in `data/eps_priors/`; Zapata/NNLS calibration path executes; outputs sane |
| 5 | **Hemisphere diagnostic** — `compare_pinned_unpinned_clustering` for Brazil with `country='Brazil'` | Pinned summer slice lands in austral summer |
| 6 | **Return-dict integrity** — inspect `run_pipeline(..., return_details=True)['model']/['mapping']` | Placeholder model / identity mapping present and harmless; confirm no notebook reads `.cluster_centers_` |

Record results in `output/validation/` (or a new `output/validation/international/`) per the existing
validation-report pattern. **Validate all derived outputs against primary sources before use in any work
product.**

---

## 10. Risks & open questions for the team

1. **Single-trunk vs. fork (governance).** The request implies single-trunk (retire `develop`). Confirm,
   so post-merge branch hygiene is clear.
2. **Runtime seam not yet exercised.** Phase 0 verified signatures and a clean *textual* tree; it did **not**
   run the pipeline. The develop-orchestrator ↔ master-wrapper seam is signature-compatible but
   runtime-unverified until §9 tests 3–4 pass.
3. **Rep-day edge cases for non-US presets.** Master's wrapper delegates to `cluster_days_repday`; confirm
   its season-pool handling is robust for all 12 presets (all are mid-latitude, so empty summer/winter
   pools are unlikely, but verify).
4. **Repo size (acknowledged, accepted this round).** Committing the large weather CSVs + PDFs adds ~100s of
   MB permanently. LFS is an optional future refinement (§6). Flag to IT & Systems if hosting limits bite.
5. **External data dependencies.** The international pipeline relies on DemandCast, Renewables.ninja, and
   Ember. If any are to be wired as **live connectors/integrations** (rather than the current
   manual-download/cached pattern), contact the IT & Systems Team (itsystems@energyinnovation.org) before
   enabling anything.
6. **Cosmetic label suffix.** Under master's DOY ordering, `assign_seasonal_labels`' `labels >= half`
   peak/off-peak split tags a slightly different set of slices than develop's p95-rank ordering did. This
   affects only a human-readable annotation column in the international Excel export, not slice identities.
   Note it so reviewers don't mistake it for a regression.

---

## 11. Rollback

- Path B is a single merge commit on a feature branch → `git reset --hard master` (pre-merge) or revert the
  merge commit. No history rewrite on `master` until the PR is intentionally merged.
- Master's clustering wrapper retains `_cluster_timeslices_legacy_impl` as graceful degradation, so even if
  `state_pipeline` import breaks, clustering still runs.

---

## 12. Reproducibility — Phase 0 commands used

```
git merge-base master origin/develop                      # -> d4ef526
git rev-list --left-right --count master...origin/develop # -> 1   5
git diff --stat master origin/develop
git show origin/develop:energy_timeslice_pipeline.py | grep -nE "^def "   # function inventory
git merge-tree --write-tree --name-only master origin/develop            # -> clean tree, no conflicts
# body resolution: md5sum of each shared function extracted from merged tree vs master vs develop
```

---

## 13. The `run_pipeline.py` control surface (staff requirements)

`run_pipeline.py` (imported from develop, additive — no merge conflict) is the **single user-facing
runner** for the international pipeline and is the interface most team members will touch. All
execution logic stays in `energy_timeslice_pipeline.py`; users edit only the documented CONFIG blocks
at the top of `run_pipeline.py`, then `python run_pipeline.py`. The runner forwards every setting to
`generate_full_pipeline_for_preset(...)` via a single `kwargs` dict.

The following are the agreed requirements for this control surface. Each notes whether it is already
satisfied by develop's `run_pipeline.py` (carried over by the merge) or needs an additional change.

### R1 — Country + key-settings selection, usable by any team member
**Status: already satisfied by develop's runner.** `COUNTRY` (name or alias, e.g. `'China'`, `'KR'`)
and `YEAR` are the top CONFIG block; the runner prints the full preset table on every run and resolves
aliases. All execution code lives in `energy_timeslice_pipeline.py`, so a teammate only edits
documented settings. **Integration action:** none beyond the merge — but confirm the EI review banner
at the top of the file is retained, and that `data_dir`/paths resolve on a fresh clone (Section 5).

### R2 — Cluster-vs-actual diagnostic plots, behind a boolean selector
**Status: already satisfied.** `MAKE_DIAGNOSTIC_PLOTS` (default `True`, Section 8) writes per-timeslice
PNGs under `output/<country>_timeslice_results_plots/`: every assigned day as a thin grey line, a
25–75th-percentile band, the cluster-mean profile, and (on net load) the representative day overlaid in
red — i.e. the visual comparison of each cluster against the actual days in it. Forwarded as
`make_plots=`. **Integration action:** verify the plots still render after the clustering swap (the
representative day shown now comes from master's wrapper; see §2.4 / R5). `matplotlib` is in
`requirements.txt`; if absent the run skips plots with a warning rather than failing.

### R3 — Surface US-specific choices on `run_pipeline.py`, with inline documentation
**Status: needs a small code change (enhancement over develop).** On develop the US-only EFS settings
(`efs_electrification`, `efs_technology_advancement`) and the RECS heating/cooling split are
**preset-locked**: Section 3 of develop's runner documents them but explicitly says the preset ignores
overrides from the runner. Staff direction is that these US-specific choices be **editable from the
runner with inline instructions**, so a US run is configured from the same control surface as any other
country.
- **Action:** add a documented US-only CONFIG block to `run_pipeline.py` (e.g. `EFS_ELECTRIFICATION`,
  `EFS_TECHNOLOGY_ADVANCEMENT`, and a heating/cooling-split toggle), forward them via `kwargs`, and have
  `generate_full_pipeline_for_country` accept them as overrides to the `united states` preset (instead
  of ignoring them). Document valid values inline (`Reference`/`Moderate`/`High`;
  `Slow`/`Moderate`/`Rapid`) and clearly mark the block "United States only — ignored for other
  countries."
- Keep the default values equal to today's preset (`Reference` × `Moderate`) so existing US behavior is
  unchanged unless a user opts in.

### R4 — Non-US calibration-method selector, default `zapata_ridge_nnls`
**Status: already satisfied.** `CALIBRATION_METHOD` (Section 2) defaults to `'zapata_ridge_nnls'` and
accepts `'zapata_nnls'` / `'level_seasonal'`; `LAMBDA_RIDGE` (default 1.0) tunes EPS-prior anchoring.
Forwarded as `calibration_method=` / `lambda_ridge=`. `zapata_ridge_nnls` requires the preset's
`eps_prior_path` (present for US/CN/KR; other presets need one added before that method will run).
**Integration action:** none beyond the merge; confirm `data/eps_priors/` came across (it does — §2.3).

### R5 — Non-US calibration unchanged from develop; only its use in clustering changes
**Status: this is the core integration principle.** The non-US calibration math **and** its data
sources are preserved exactly as on develop:
- Demand shape: Mendeley/Zapata end-use dataset.
- Observed-demand calibration: DemandCast (programmatic per country; KROGD manual files for Korea;
  Wu et al. Zenodo for China).
- VRE: Renewables.ninja MERRA-2 → CF, calibrated to Ember annual CF targets.
- Methods: `level_seasonal` / `zapata_nnls` / `zapata_ridge_nnls` (default), with the EPS-prior
  alignment for the ridge variant.

What changes is **only the downstream use of the calibrated net-load series**: it now flows through
master's consolidated, hemisphere-aware `cluster_days_repday` (via the `cluster_timeslices` wrapper)
instead of develop's inline implementation. Practically this means (a) the SH season flip engages once
`country=` is forwarded (§7), (b) representative-day selection and peak-slice growth follow master's
rep-day methodology, and (c) numerical outputs may shift slightly vs develop's prior runs (expected —
documented in §9). **Integration action:** the §7 one-line fix, plus the §9 verification that
Korea/China still calibrate and cluster sensibly end-to-end.

### Settings → pipeline mapping (for reviewers)
`run_pipeline.py` forwards (develop's current contract): `country`, `year`, `n_clusters`,
`output_path`, `last_n_years`, `seasonal_calibration`, `scenario`, `weight`, `dataset`,
`orientation_factor`, `roughness_length`, `use_cache`, `cache_dir`, `cf_calibration_mode`,
`make_plots`, `compare_pinned_unpinned`, `calibration_only`, `calibration_method`, `lambda_ridge`
(and `data_dir` when set) → `generate_full_pipeline_for_preset(**kwargs)`. The R3 change adds the
US-specific keys to this dict.

---

*Maintained by: Energy Innovation modeling team. This is an input for staff review, not an institutional
position, and is open to refinement. Re-confirm git-state facts on the live branches and validate all
derived outputs against primary sources before any integration is executed or any result is used in a work
product.*
