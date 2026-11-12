# TO-DO — ActiveInferenceImplementations

Last reviewed: 2026-11-12 (truth pass; every open item names its blocker and owner)

Evidence rule: a gate counts as passed only on a local `./run.sh <arm>` run.
Hosted GitHub Actions is billing-locked org-wide, so a green hosted run is not
evidence that a gate passed.

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
- [x] M7 — Notebooks used the retired reactive RxInfer API (`inference(...)`, `create_model`/`update!`); refresh them against RxInfer 6 (`infer`, `MeanField`, `@initialization`, `@call_message_update_rule`, `free_energy`) on Julia 1.13, re-execute end to end, and guard the retired tokens in the static gates (`test/static_tests.jl`). (RxInfer.jl/00_intro.ipynb, RxInfer.jl/01_message_passing.ipynb) — ✓ 285288e
- [x] M8 — Adopt a pinned GNN specification for the mean-field VMP model: `specs/normal_vmp.gnn.md` is the single source of truth, read by `src/spec_reader.jl`, validated against the parser revision in `specs/gnn-pin.json`, and enforced by `scripts/validate_gnn_spec.py` in CI. The Beta-Bernoulli coin model is signposted to its canonical document in ActInf_RxInfer instead of being declared a second time. (specs/, src/spec_reader.jl, scripts/, test/runtests.jl, Project.toml, .github/workflows/ci.yml, README.md) — ✓ 285288e

### 2026-11-11 — modular `docs/` tree

- [x] ✓ Add `docs/README.md` as the documentation index plus
      `docs/repository-layout.md`, `docs/notebooks.md`, and
      `docs/gnn-conformance.md`; link the index from `README.md` and name the docs
      locations in `AGENTS.md`. No notebook or Julia execution was involved.
- [ ] Keep `docs/repository-layout.md` and `docs/gnn-conformance.md` in step when the
      notebook set, the GNN document, or the pin changes. It has already slipped:
      `docs/gnn-conformance.md` (§ *How CI runs it*) and `.github/GNN.md:3` still
      name a job key `gnn-conformance` with display name `gnn conformance
      (pinned)`, while `.github/workflows/ci.yml` has declared a single job,
      `gate`, since #11 (d2497d4) merged the two CI jobs. Owner: repository
      maintainer; no external blocker.

### 2026-11-12 — one gate entry point, measured arms

- [x] ✓ Added `run.sh` as the single gate entry point with separately runnable
      arms (`setup`, `lint`, `test-fast`, `test`, `docs`, `gnn`, `contract`,
      `notebooks`, `gate`) and rewrote `.github/workflows/ci.yml` to call those
      arms instead of inlining commands. The two CI jobs became one, sharing one
      Julia/uv/GNN/notebook environment.
- [x] ✓ Split `test/runtests.jl` into `test/static_tests.jl` (no RxInfer, the
      default arm) and the full suite, which includes it, so no test runs twice.
- [x] ✓ Added `scripts/check_docs_links.py` (relative links, heading anchors,
      documentation-index completeness) and `scripts/measure_gates.py`, which
      generates `docs/gate-timings.md`; `./run.sh docs` fails when an arm is
      missing from that page.
- [x] ✓ Added `docs/documentation-index.md` and linked it from the hub.
- [ ] Regenerate `docs/gate-timings.md`. The page records `Commit 4c7c708`, which
      is not an ancestor of `origin/main` (`git merge-base --is-ancestor 4c7c708
      origin/main` fails; that commit exists only on `origin/workflows/migration`),
      and `scripts/measure_gates.py --check` asserts only that every
      `./run.sh --list` arm has a row, so the stale environment block still passes
      the docs arm. Refresh with `python3 scripts/measure_gates.py` on a clean main
      checkout. Owner: repository maintainer; needs a host with Julia 1.13, `uv`,
      and network access for the GNN runtime.

### 2026-11-12 — to-do truth pass

- [x] ✓ Re-verified the done items above against the repository: commits `968e5c7`,
      `f98a027`, `8ed3496` and `285288e` exist with the content they are credited
      with; no `.ipynb_checkpoints` file is tracked and `.gitignore:1-3` covers it;
      `./run.sh --list` reports the nine documented arms; `test/runtests.jl:51`
      includes `static_tests.jl` once, so no test runs twice.
- [x] ✓ Education contract passes locally: `./run.sh contract` prints
      `specs/education/implementations.json: OK -- 2 unit(s), 0 edge(s), 0 term(s)`
      against the canonical `courses` checker (`software/scripts/check_education_contract.py`).
- [x] ✓ `.aii` sidecar validates:
      `python -m aii_platform.aii_sidecar validate .` → `OK: .`.
- [x] ✓ Checked for a `pymdp` / `inferactively-pymdp` dependency: there is none.
      The Python surface is `scripts/*.py` on the standard library, and the
      notebooks are Julia, so no 1.0.5 pin applies here.
- [ ] Raise the GNN pin from `v5.0.3` to the importer release `v5.1.0`.
      `specs/gnn-pin.json` records `v5.0.3` at
      `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`; `v5.1.0` is
      `75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf` ("Release GNN 5.1.0 with the
      downstream importer registry", GNN #385) and is already pinned by
      ActInf_RxInfer, ActiveBlockference, active_inference_power and pymdp. Four of
      the five recorded parser digests change at that commit (`src/gnn/__init__.py`,
      `src/gnn/parsers/__init__.py`, `common.py`, `markdown_parser.py`;
      `markdown_parser_parameter.py` is unchanged), so tag, commit and digests move
      as one change; the `v5.0.3` / `8f293d9b` strings at `.github/GNN.md:9`,
      `docs/README.md:58`, `docs/gnn-conformance.md:14`, `docs/gate-timings.md:40`
      and in `RxInfer.jl/01_message_passing.ipynb` follow, then `./run.sh gnn` is
      re-run. Owner: repository maintainer; no external blocker — the release
      exists. Upstream's `docs/downstream/importers.json` (observed 2026-11-12)
      still records this repository at `v5.0.3` and needs re-observation after the
      bump.

---

## Open / deferred

- [x] m4 — `.aii/config.yaml` `artifacts:` now lists the repository entry points,
      including `RxInfer.jl`, `specs`, `src`, and `test`, so the earlier
      "README.md only" note no longer applies. Verified 2026-11-11. (.aii/config.yaml)
- [ ] (deferred) — Notebook files embed base64 plot outputs: 8 image outputs
      totalling 975,946 base64 characters (~0.93 MiB) inside 1.18 MB of committed
      notebook JSON; optionally strip outputs and add an `nbstripout` pre-commit
      hook. Reason deferred: maintainer preference on keeping rendered outputs
      in-repo. (RxInfer.jl/*.ipynb)
