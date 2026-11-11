# Repository layout

This repository is a small, self-contained teaching project: two Jupyter
notebooks, one Generalized Notation Notation (GNN) specification, and the code
and tests that keep the notebook's model declarations honest. There is no Julia
package to install; `Project.toml` is the notebook environment.

## Top level

| Path | Kind | Purpose |
| --- | --- | --- |
| [`README.md`](../README.md) | source | Overview, prerequisites, getting started, verification. |
| [`Project.toml`](../Project.toml) | environment | Julia notebook environment (RxInfer 6, Distributions, Plots, Random; Julia 1.10+ compat, exercised on 1.13). |
| [`uv.toml`](../uv.toml) | tooling | Pins `uv` 0.13.7 for the GNN conformance job's Python runtime. |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | source | Contribution guidelines. |
| [`CITATION.cff`](../CITATION.cff) | metadata | Citation File Format record. |
| [`LICENSE`](../LICENSE) | legal | CC BY 4.0. |
| [`AGENTS.md`](../AGENTS.md) | source | Agent guidance and declared task commands. |
| [`TO-DO.md`](../TO-DO.md) | source | Review log and open items. |
| [`REVIEW_LOG_2026-08-02.md`](../REVIEW_LOG_2026-08-02.md) | source | Record of the 2026-08-02 documentation review. |
| [`docs/`](README.md) | source | This documentation tree. |

## Folders

| Path | Purpose |
| --- | --- |
| [`RxInfer.jl/`](../RxInfer.jl/README.md) | The two teaching notebooks and their folder guide. |
| [`specs/`](../specs/README.md) | `normal_vmp.gnn.md`, the single source of truth for the mean-field VMP model, and `gnn-pin.json`, the pinned upstream revision and parser digests. |
| [`src/`](../src/README.md) | `spec_reader.jl`, the dependency-free Julia reader of the GNN document. |
| [`scripts/`](../scripts/README.md) | `validate_gnn_spec.py` (the conformance gate) and `gnn_parser_probe.py` (the only module that imports the upstream parser). |
| [`test/`](../test/README.md) | `runtests.jl`, the Julia test suite. |
| [`.github/`](../.github/workflows/ci.yml) | CI workflow and Dependabot configuration. |
| `.aii/` | InstituteOS sidecar: curated institutional metadata (`aii-sidecar/v1`). See [`.aii/README.md`](../.aii/README.md). |

## How the pieces fit

1. [`specs/normal_vmp.gnn.md`](../specs/normal_vmp.gnn.md) declares the model's
   priors, data statistics, observation count, iteration count, seed, equations,
   and ontology annotations. It is the source of truth; the notebook does not
   hard-code those numbers.
2. [`src/spec_reader.jl`](../src/spec_reader.jl) reads the declarations without
   any Julia package dependency. The notebook and the test suite include it.
3. [`scripts/validate_gnn_spec.py`](../scripts/validate_gnn_spec.py) compares the
   Julia reader, its own regular-expression reader, and the pinned upstream GNN
   parser. See [`gnn-conformance.md`](gnn-conformance.md).
4. [`test/runtests.jl`](../test/runtests.jl) checks the declarations and the
   recovered posterior, and guards against the retired RxInfer API.
5. [`RxInfer.jl/01_message_passing.ipynb`](../RxInfer.jl/01_message_passing.ipynb)
   runs the model; [`RxInfer.jl/00_intro.ipynb`](../RxInfer.jl/00_intro.ipynb)
   teaches the Beta-Bernoulli foundation and points at its canonical GNN document
   in `ActInf_RxInfer` instead of declaring a second copy.

## Source versus generated

Everything tracked is hand-maintained except the notebook outputs: the two
`.ipynb` files keep their rendered cell outputs in git, so executing a notebook
rewrites committed content. There is no build directory and no generated code.
