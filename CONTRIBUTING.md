# Contributing to Active Inference Implementations

Thanks for your interest in contributing! This repository is part of the
Active Inference Institute's open learning materials, and we welcome
improvements to the notebooks, documentation, and repository hygiene.

## What this repository contains

Educational Jupyter notebooks that demonstrate computational implementations
of probabilistic and active inference methods. Today the repo holds
[RxInfer.jl](https://docs.rxinfer.com/stable/) tutorials; the intent is to
collect working implementations of active inference models over time.

## Ways to contribute

- **Fix a bug in a notebook** — a wrong formula, a broken link, code that no
  longer runs on a current Julia/RxInfer release.
- **Improve the teaching material** — clearer markdown explanations, better
  figures, additional worked examples that extend an existing notebook.
- **Add a new notebook** — a new implementation, ideally one that builds on
  the existing series. Add it to the repository contents table in
  `README.md`.
- **Improve the docs** — this includes `README.md`, `CONTRIBUTING.md`, and
  any future documentation.

## Notebook guidelines

- Use Jupyter **nbformat 4** with the Julia kernel (see the existing
  notebooks under `RxInfer.jl/`).
- Notebooks must run **top to bottom** on a fresh kernel.
- Use a **fixed random seed** (e.g. `MersenneTwister(42)`) so results are
  reproducible.
- Write prose cells that explain **what** each step does and **why**; a
  notebook that only contains code is not finished teaching material.
- Keep embedded outputs modest. Large base64-encoded plot outputs bloat the
  repository and create noisy diffs; prefer small figures or cleared outputs
  where reasonable.
- **Never commit Jupyter autosave artifacts** (`.ipynb_checkpoints/`,
  `*_checkpoint.ipynb`) — they are gitignored.
- Update the contents table in `README.md` when you add, rename, or
  substantially retitle a notebook.

## Link and accuracy rules

- Every link you add must resolve. External documentation moves; when you
  notice a dead link (e.g. to RxInfer docs), update it to the current
  canonical URL.
- Never invent statistics, citations, file paths, or claims. Documentation
  must match what the code actually does.

## Style

- Follow the style of the surrounding notebook/code. For Julia, keep to
  standard Julia formatting conventions.
- Do not introduce heavyweight toolchains for documentation work.

## Pull request process

1. Fork the repository and create a branch (`git checkout -b my-change`).
2. Make focused, well-scoped changes.
3. Use clear conventional commit messages: `docs:`, `chore:`, `fix:`.
4. Open a pull request against `main` and describe what you changed and why.

## License

By contributing, you agree that your contributions are licensed under the
repository's license, [CC BY 4.0](LICENSE).
