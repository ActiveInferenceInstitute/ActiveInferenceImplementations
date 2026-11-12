# Agent guide — ActiveInferenceImplementations

Educational Jupyter notebooks exploring probabilistic inference and active inference with RxInfer.jl, from Beta-Bernoulli coin inference to variational message passing.

## Working notes

- Repository: `ActiveInferenceInstitute/ActiveInferenceImplementations` (default branch `main`).
- InstituteOS classification: category `education`, maturity `wip`, status `active`.
- License: `CC-BY-4.0`.
- Keep private content in private repositories; never commit credentials,
  personal data, or unverified claims.
- Read [`README.md`](README.md) first, then the nearest nested `AGENTS.md`.
- Documentation lives in [`docs/`](docs/README.md) (index, repository layout,
  notebook guide, GNN conformance) with folder guides next to each material
  folder: `RxInfer.jl/`, `specs/`, `src/`, `scripts/`, and `test/`.
- Prefer small, verified changes; run the declared tasks before handing work back.

## Tasks

`./run.sh` is the single gate entry point; `./run.sh --list` prints the arms.
CI calls the same arms.

| Task | Command | Working directory |
| --- | --- | --- |
| `inventory` | `git ls-files` | `.` |
| `setup` | `./run.sh setup` | `.` |
| `lint` | `./run.sh lint` | `.` |
| `test-fast` | `./run.sh test-fast` | `.` |
| `test` | `./run.sh test` (full suite; includes `test-fast`) | `.` |
| `docs` | `./run.sh docs` | `.` |
| `gnn` | `./run.sh gnn` | `.` |
| `notebooks` | `./run.sh notebooks` | `.` |
| `gate` | `./run.sh gate` | `.` |

## InstituteOS sidecar

This repository carries a committed [`.aii/`](.aii/README.md) sidecar with curated
InstituteOS metadata (`aii-sidecar/v1`): category, maturity, ecosystem relations,
key artifacts, provenance, and portable tasks. It is read by
[InstituteOS](https://github.com/ActiveInferenceInstitute/InstituteOS) tooling and
does not affect the project's build or runtime. Regenerating the sidecar docs
rewrites only `.aii/README.md`, `.aii/AGENTS.md`, `.aii/docs/README.md`,
`.aii/docs/AGENTS.md`, and `.aii/docs/INTEGRATION.md`.
