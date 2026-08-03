# Review Log — 2026-08-02

Mega-deep documentation review of `ActiveInferenceImplementations` (docs-deep pass).

## Phase 0 — Preflight

- Default branch: `main` (origin/HEAD -> origin/main).
- HEAD at start: `9caff52` — "add .aii sidecar (100% complete) + CC-BY-4.0 LICENSE (InstituteOS metadata)".
- `git fetch origin` + `git pull --ff-only` → already up to date, clean tree.
- Repo inventory (all tracked files):
  - `README.md` (2 lines)
  - `LICENSE` (CC-BY-4.0, SPDX header present)
  - `.aii/config.yaml` (InstituteOS sidecar metadata)
  - `RxInfer.jl/00_intro.ipynb` (23 cells, Julia 1.8.2 kernel, ~950 KB with embedded plot outputs)
  - `RxInfer.jl/01_message_passing.ipynb` (10 cells, Julia 1.8.2 kernel)
  - `RxInfer.jl/.ipynb_checkpoints/00_intro-checkpoint.ipynb` — **tracked Jupyter autosave artifact** (7 cells, stale)
- No docs/ folder, no AGENTS.md/CLAUDE.md, no CI config, no .github/, no .gitignore, no TODO/ROADMAP files, no CONTRIBUTING.md, no CITATION.cff.

## Phase 1 — Findings

### Major
- **M1** README.md is a 2-line stub: no repo contents index, no prerequisites (Julia), no install/usage instructions, no license/citation section, no contributing pointer. Not useful to a new visitor.
- **M2** A Jupyter checkpoint file (`.ipynb_checkpoints/00_intro-checkpoint.ipynb`) is committed to git, and there is no `.gitignore` at all. Autosave artifacts must not live in a public repo.
- **M3** No contributor-facing docs: no `CONTRIBUTING.md` and no `CITATION.cff` for a public research/learning repo.

### Medium
- **M4** All three RxInfer.jl documentation links in the notebooks are dead. `biaslab.github.io/RxInfer.jl/stable/...` returns 404 (docs moved to the ReactiveBayes org). Verified replacements (HTTP 200 + anchors):
  - getting-started → `https://docs.rxinfer.com/stable/manuals/getting-started/`
  - `inference` function → `https://docs.rxinfer.com/stable/manuals/inference/overview/` (anchor `#user-guide-inference-execution`)
  - VMP / manual inference → `https://docs.rxinfer.com/stable/concepts/variational-inference/`
- **M5** `01_message_passing.ipynb` has almost no prose: title + one link only. No explanation of the model, the mean-field constraint, or what the plots show.
- **M6** `00_intro.ipynb` ends with an empty code cell (cell 22) — dead weight.
- **M7** API drift: notebooks use the legacy `inference(...)` entry point; current RxInfer exports `infer(...)`. Not rewritten in this pass (code change would need a full Julia execution to verify; heavy toolchain per pass constraints) — tracked as deferred in TO-DO.md.

### Minor
- **m1** `00_intro.ipynb` markdown cell 0 repeats the getting-started URL as plain text with no link formatting.
- **m2** `01_message_passing.ipynb` uses iteration indices `[1, 2, 10]` for the mean and `[2, 3, 10]` for the precision with no explanation.
- **m3** Code comment in `00_intro.ipynb` ("GraphPPL.jl export `@model` macro") — grammar fix while editing.
- **m4** `.aii/config.yaml` `artifacts:` lists only `README.md` although the notebooks are the substantive content. Left untouched: machine-consumed InstituteOS metadata (schema-controlled).

### Checks performed
- External links checked with `curl -L` (all Wikipedia + creativecommons.org links live; all three biaslab links 404).
- Saved notebook outputs inspected programmatically: no error outputs; printed statistics consistent with the code (mean ≈ 0.47 for n=10, ≈ 0.75 for n=10,000 with p=0.75).
- Julia 1.12.6 present locally, but notebooks were NOT executed: per pass constraints, heavy Julia installs/execution are out of scope. Notebook execution against current RxInfer is noted as a deferred verification item.

## Phase 3 — Implementation summary
- chore: removed tracked `.ipynb_checkpoints/` artifact; added `.gitignore`.
- docs: rewrote `README.md` (about, contents, prerequisites, getting started, license, citation, contributing).
- docs: added `CONTRIBUTING.md` and `CITATION.cff`.
- docs: updated dead RxInfer links in both notebooks; added explanatory markdown to `01_message_passing.ipynb`; removed trailing empty cell in `00_intro.ipynb`; minor copy fixes.
- Validation: re-checked all URLs touched, re-validated notebook JSON, confirmed `git status` contains only intended changes.

## Phase 4 — Verification
- Push to `origin/main` succeeded; `git status` clean and up to date with `origin/main`.

## Deferred / open items (see TO-DO.md)
- Notebook API refresh to current RxInfer (`inference` → `infer`) + re-execution against Julia ≥ 1.9 (needs heavy Julia environment; code-only change outside docs scope).
- Add notebooks to `.aii/config.yaml` artifacts list (machine-consumed metadata; schema-controlled).
- Optionally strip embedded plot outputs / add `nbstripout` pre-commit hook to keep notebook diffs lean (maintainer preference).
