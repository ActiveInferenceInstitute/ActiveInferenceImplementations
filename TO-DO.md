# TO-DO — ActiveInferenceImplementations

Last reviewed: 2026-08-02 (mega-deep docs pass; see REVIEW_LOG_2026-08-02.md)

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

---

## Open / deferred

- [ ] M7 (deferred) — Notebooks use legacy RxInfer API (`inference(...)`); current RxInfer exports `infer(...)`. Refresh notebook code against current RxInfer and re-execute end-to-end. Reason deferred: code-only change that must be verified by running a Julia environment (heavy install; out of scope for a docs pass). (RxInfer.jl/00_intro.ipynb, RxInfer.jl/01_message_passing.ipynb)
- [ ] m4 (deferred) — `.aii/config.yaml` `artifacts:` lists only README.md; add the two notebooks. Reason deferred: machine-consumed InstituteOS sidecar, schema-controlled; leave to an InstituteOS-side update. (.aii/config.yaml)
- [ ] (deferred) — Notebook files embed large base64 plot outputs (~1.4 MB total); optionally strip outputs and add an `nbstripout` pre-commit hook. Reason deferred: maintainer preference on keeping rendered outputs in-repo. (RxInfer.jl/*.ipynb)
