# Active Inference Implementations

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-blue)](LICENSE)
[![Made with Julia](https://img.shields.io/badge/Made%20with-Julia-9558B2)](https://julialang.org)

Educational notebooks exploring probabilistic inference and active inference
implementations, maintained by the [Active Inference Institute](https://www.activeinference.org).

This repository collects working computational implementations — currently a
set of [RxInfer.jl](https://docs.rxinfer.com/stable/) tutorials demonstrating
Bayesian inference on factor graphs by message passing. The notebooks are
intended as hands-on learning material: each one is self-contained, seeded for
reproducibility, and builds on the previous one.

## Repository contents

| Notebook | Topic |
| --- | --- |
| [RxInfer.jl/00_intro.ipynb](RxInfer.jl/00_intro.ipynb) | Getting started with RxInfer.jl: inferring the bias of a coin with a Beta–Bernoulli model, building the same posterior by hand from individual messages, and scaling up the dataset |
| [RxInfer.jl/01_message_passing.ipynb](RxInfer.jl/01_message_passing.ipynb) | Exploring message-passing schemes: mean-field variational message passing (VMP) for the mean and the precision of a Normal model, read from its Generalized Notation Notation document |

| Path | Contents |
| --- | --- |
| [specs/normal_vmp.gnn.md](specs/normal_vmp.gnn.md) | Generalized Notation Notation (GNN) document declaring the mean-field VMP model: the single source of truth for the priors, the data statistics, the observation count, the iteration count, and the seed |
| [specs/gnn-pin.json](specs/gnn-pin.json) | The upstream GNN revision the document is validated against (tag, commit, and SHA-256 digests of the parser files) |
| [src/spec_reader.jl](src/spec_reader.jl) | Dependency-free reader of the committed GNN document, used by the notebook, the test suite, and the validation gate |
| [scripts/validate_gnn_spec.py](scripts/validate_gnn_spec.py) | Validation gate: parses the document with the pinned GNN parser and compares the three readers of the declarations |
| [scripts/gnn_parser_probe.py](scripts/gnn_parser_probe.py) | The pinned-parser probe run in a subprocess by the validation gate |
| [test/runtests.jl](test/runtests.jl) | Test suite: declared scalars, data reproducibility, and the recovered posterior statistics |
| [Project.toml](Project.toml) | The notebook environment |

## Canonical models elsewhere in the fleet

`RxInfer.jl/00_intro.ipynb` uses the Beta-Bernoulli coin model. Its canonical
GNN document is
[`specs/coin_flip.gnn.md`](https://github.com/ActiveInferenceInstitute/ActInf_RxInfer/blob/main/specs/coin_flip.gnn.md)
in the [ActInf_RxInfer](https://github.com/ActiveInferenceInstitute/ActInf_RxInfer)
repository, which also implements that model as a Julia package. This repository
keeps the walkthrough and does not declare a second copy of that model; the
notebook links to the canonical document, and the file declaring the model is
validated there.

GNN maintains a [downstream adoption guide](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/integration/downstream_adoption.md) for repositories that consume the notation.

## Prerequisites

- [Julia](https://julialang.org/downloads/) 1.13 — the notebooks were refreshed
  against RxInfer 6 and are executed on Julia 1.13 in CI. The `[compat]` bounds
  in `Project.toml` follow the notebook dependencies (RxInfer 6 supports Julia
  1.10 and newer).
- [Jupyter](https://jupyter.org/install) with the
  [IJulia](https://github.com/JuliaLang/IJulia.jl) kernel.
- The Julia packages in [Project.toml](Project.toml):
  [RxInfer.jl](https://docs.rxinfer.com/stable/), `Distributions`, `Random`,
  and `Plots`.

## Getting started

```sh
git clone https://github.com/ActiveInferenceInstitute/ActiveInferenceImplementations.git
cd ActiveInferenceImplementations
julia --project=. -e 'using Pkg; Pkg.instantiate()'
```

Register the kernel the notebooks declare, once per machine:

```julia
using Pkg
Pkg.add("IJulia")
using IJulia
IJulia.installkernel("julia-1.13", "--project=@.", specname="julia-1.13")
```

The `specname` argument keeps the installed kernelspec named exactly
`julia-1.13`, which is what the notebooks request; without it IJulia appends the
Julia version to the kernel name (`julia-1.13-1.13`). The `--project=@.` option
keeps the repository's `Project.toml` active inside the kernel, so the
notebooks run against the committed environment. Then launch
Jupyter from the repository root and open the notebooks under `RxInfer.jl/`:

```sh
julia -e 'using IJulia; jupyterlab()'
```

Each notebook is designed to run top to bottom with a fresh kernel. No
environment variables or configuration are required.

## Verification

These are the documented gates of the repository; `.github/workflows/ci.yml`
runs all of them on every push and pull request.

```sh
julia --project=. -e 'using Pkg; Pkg.instantiate()'   # notebook environment
julia --project=. test/runtests.jl                    # test suite
python3 scripts/validate_gnn_spec.py --gnn-runtime <python> --julia julia --json
python3 -m nbconvert --to notebook --execute RxInfer.jl/00_intro.ipynb \
    RxInfer.jl/01_message_passing.ipynb --output-dir=/tmp/executed
```

The GNN validation needs a runtime with the pinned GNN distribution
(`--gnn-runtime` or `GNN_RUNTIME_PYTHON`) or a GNN git checkout
(`--gnn-root` or `GNN_ROOT`). Without one it exits `2` and prints that the check
was not run; that is not a pass. The pin is recorded in
[`specs/gnn-pin.json`](specs/gnn-pin.json) and bumping it is a deliberate change
followed by a fresh validation run.

Two environment notes from running the gates on macOS:

- If GR (the default `Plots.jl` backend) cannot load `libssl.3.dylib`, export
  `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/opt/openssl@3/lib:/usr/lib` before
  starting Jupyter.
- The notebooks keep their rendered outputs in git, so executing them rewrites
  the committed outputs.

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for
guidelines on notebook and documentation contributions.

## Citation

If you use or reference this repository in your work, please cite it via the
metadata in [CITATION.cff](CITATION.cff).

## License

This repository is licensed under the
[Creative Commons Attribution 4.0 International License (CC BY 4.0)](LICENSE).
See the [human-readable summary](https://creativecommons.org/licenses/by/4.0/)
and the [full legal code](https://creativecommons.org/licenses/by/4.0/legalcode).

## InstituteOS sidecar

This repository carries a committed [`.aii/`](.aii/README.md) sidecar with curated
InstituteOS metadata (`aii-sidecar/v1`): category, maturity, ecosystem relations,
key artifacts, provenance, and portable tasks. It is read by
[InstituteOS](https://github.com/ActiveInferenceInstitute/InstituteOS) tooling and
does not affect the project's build or runtime.
