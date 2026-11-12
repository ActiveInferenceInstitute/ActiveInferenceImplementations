# Documentation index

Flat index of the long-lived documentation in this repository. The hub is
[`README.md`](README.md); this page is the complete list, so a new page is
added here in the same change that adds it.

## `docs/`

- [README.md](README.md) — documentation hub: what exists and where to start.
- [documentation-index.md](documentation-index.md) — this flat index.
- [repository-layout.md](repository-layout.md) — every tracked file and folder,
  and how the notebook environment is assembled.
- [notebooks.md](notebooks.md) — teaching order, how to run the notebooks, and
  what executing them changes in git.
- [gnn-conformance.md](gnn-conformance.md) — the GNN pin record, the three
  readers, the digest checks, and the conformance gate.
- [gate-timings.md](gate-timings.md) — generated: per-arm wall times and test
  counts for `./run.sh`.
- [gate-baseline.md](gate-baseline.md) — the measured pre-change baseline those
  arms replaced.

## Repository root

- [`../README.md`](../README.md) — overview, prerequisites, getting started.
- [`../run.sh`](../run.sh) — the single gate entry point; run
  `./run.sh --list` for the arms.
- [`../AGENTS.md`](../AGENTS.md) — agent guidance and declared tasks.
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — contribution guidelines.
- [`../TO-DO.md`](../TO-DO.md) — review log and open items.
- [`../REVIEW_LOG_2026-08-02.md`](../REVIEW_LOG_2026-08-02.md) — documentation
  review record.
- [`../CITATION.cff`](../CITATION.cff) — machine-readable citation metadata.
- [`../LICENSE`](../LICENSE) — CC BY 4.0.

## `.github/`

- [`../.github/GNN.md`](../.github/GNN.md) — what the GNN conformance job
  parses and where the pin lives.
- [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) — the CI
  workflow, which calls the arms of `run.sh`.

## Folder guides

- [`../RxInfer.jl/README.md`](../RxInfer.jl/README.md) — the two notebooks.
- [`../specs/README.md`](../specs/README.md) — the GNN document and the pin.
- [`../src/README.md`](../src/README.md) — the dependency-free Julia spec reader.
- [`../scripts/README.md`](../scripts/README.md) — validation, documentation and
  measurement scripts.
- [`../test/README.md`](../test/README.md) — the fast static gates and the full
  suite.

## InstituteOS sidecar

- [`../.aii/README.md`](../.aii/README.md) — curated institutional metadata
  (`aii-sidecar/v1`).
- [`../.aii/docs/README.md`](../.aii/docs/README.md) — sidecar documentation hub.
- [`../.aii/docs/INTEGRATION.md`](../.aii/docs/INTEGRATION.md) — how the sidecar
  is read by InstituteOS tooling.
