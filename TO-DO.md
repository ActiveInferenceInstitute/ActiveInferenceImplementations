# TO-DO — ActiveInferenceImplementations

Last reviewed: 2026-11-11 (documentation completeness pass; see docs/)

Sections:
- **Minor** = typo, broken link, formatting, dead anchor.
- **Medium** = stale section rewrite, doc restructure, added missing guide.
- **Major** = large doc system overhaul, cross-cutting refactors, repo-hygiene fixes.

---

## Minor

- [x] m1 — `00_intro.ipynb`: getting-started URL in first markdown cell is plain text; render as a link. (RxInfer.jl/00_intro.ipynb) — ✓ 968e5c7
- [x] m2 — `00_intro.ipynb`: grammar fix in code comment ("GraphPPL.jl export `@model` macro" → "exports"). (RxInfer.jl/00_intro.ipynb) — ✓ 968e5c7

## Medium

- [x] M4 — Notebook RxInfer doc links are dead (biaslab.github.io → 404); update to docs.rxinfer.com (getting-started, inference overview, variational-inference). (RxInfer.jl/00_intro.ipynb, RxInfer.jl/01_message_passing.ipynb) — ✓ 968e5c7
- [x] M5 — `01_message_passing.ipynb` lacks explanatory prose (model, mean-field constraint, iteration indices `[1,2,10]` vs `[2,3,10]`); add markdown cells. (RxInfer.jl/01_message_passing.ipynb) — ✓ 968e5c7
- [x] M6 — Trailing empty code cells in both notebooks; remove. (RxInfer.jl/00_intro.ipynb, RxInfer.jl/01_message_passing.ipynb) — ✓ 968e5c7

## Major

- [x] M1 — README.md is a 2-line stub; rewrite with about, contents index, prerequisites, getting-started, license, citation, contributing. (README.md) — ✓ f98a027
- [x] M2 — Tracked Jupyter checkpoint artifact in git and no .gitignore; remove artifact and add .gitignore. (RxInfer.jl/.ipynb_checkpoints/00_intro-checkpoint.ipynb, .gitignore) — ✓ 8ed3496
- [x] M3 — Missing contributor-facing docs; add CONTRIBUTING.md and CITATION.cff. (CONTRIBUTING.md, CITATION.cff) — ✓ f98a027
- [x] M7 — Notebooks used the retired reactive RxInfer API (`inference(...)`, `create_model`/`update!`); refresh them against RxInfer 6 (`infer`, `MeanField`, `@initialization`, `@call_message_update_rule`, `free_energy`) on Julia 1.13, re-execute end to end, and guard the retired tokens in `test/runtests.jl`. (RxInfer.jl/00_intro.ipynb, RxInfer.jl/01_message_passing.ipynb) — ✓ 285288e
- [x] M8 — Adopt a pinned GNN specification for the mean-field VMP model: `specs/normal_vmp.gnn.md` is the single source of truth, read by `src/spec_reader.jl`, validated against the parser revision in `specs/gnn-pin.json`, and enforced by `scripts/validate_gnn_spec.py` in CI. The Beta-Bernoulli coin model is signposted to its canonical document in ActInf_RxInfer instead of being declared a second time. (specs/, src/spec_reader.jl, scripts/, test/runtests.jl, Project.toml, .github/workflows/ci.yml, README.md) — ✓ 285288e

### 2026-11-11 — modular `docs/` tree

- [x] ✓ Add `docs/README.md` as the documentation index plus
      `docs/repository-layout.md`, `docs/notebooks.md`, and
      `docs/gnn-conformance.md`; link the index from `README.md` and name the docs
      locations in `AGENTS.md`. No notebook or Julia execution was involved.
- [ ] Keep `docs/repository-layout.md` and `docs/gnn-conformance.md` in step when the
      notebook set, the GNN document, or the pin changes.

### 2026-11-12 — one gate entry point, measured arms

- [x] ✓ Added `run.sh` as the single gate entry point with separately runnable
      arms (`setup`, `lint`, `test-fast`, `test`, `docs`, `gnn`, `notebooks`,
      `gate`) and rewrote `.github/workflows/ci.yml` to call those arms instead
      of inlining commands. The two CI jobs became one, sharing one Julia/uv/
      GNN/notebook environment.
- [x] ✓ Split `test/runtests.jl` into `test/static_tests.jl` (no RxInfer, the
      default arm) and the full suite, which includes it, so no test runs twice.
- [x] ✓ Added `scripts/check_docs_links.py` (relative links, heading anchors,
      documentation-index completeness) and `scripts/measure_gates.py`, which
      generates `docs/gate-timings.md`; `./run.sh docs` fails when an arm is
      missing from that page.
- [x] ✓ Added `docs/documentation-index.md` and linked it from the hub.
- [ ] Keep `docs/gate-timings.md` refreshed with `python3 scripts/measure_gates.py`
      when an arm's command or dependency set changes.

---

## Open / deferred

- [x] m4 — `.aii/config.yaml` `artifacts:` now lists the repository entry points,
      including `RxInfer.jl`, `specs`, `src`, and `test`, so the earlier
      "README.md only" note no longer applies. Verified 2026-11-11. (.aii/config.yaml)
- [ ] (deferred) — Notebook files embed large base64 plot outputs (~1.4 MB total); optionally strip outputs and add an `nbstripout` pre-commit hook. Reason deferred: maintainer preference on keeping rendered outputs in-repo. (RxInfer.jl/*.ipynb)
