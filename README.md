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
| [RxInfer.jl/00_intro.ipynb](RxInfer.jl/00_intro.ipynb) | Getting started with RxInfer.jl: inferring the bias of a coin with a Beta–Bernoulli model, including manual inference with `create_model`/`update!` and scaling up the dataset |
| [RxInfer.jl/01_message_passing.ipynb](RxInfer.jl/01_message_passing.ipynb) | Exploring message-passing schemes: variational message passing (VMP) for estimating the mean and precision of a Normal distribution |

## Prerequisites

- [Julia](https://julialang.org/downloads/) — the notebooks were authored
  against Julia 1.8; any modern 1.x release should work.
- [Jupyter](https://jupyter.org/install) with the
  [IJulia](https://github.com/JuliaLang/IJulia.jl) kernel.
- The Julia packages used by the notebooks:
  [RxInfer.jl](https://docs.rxinfer.com/stable/), `Distributions`, `Random`,
  and `Plots`.

## Getting started

```sh
git clone https://github.com/ActiveInferenceInstitute/ActiveInferenceImplementations.git
cd ActiveInferenceImplementations
```

Start Julia and install the required packages (this only needs to be done
once):

```julia
using Pkg
Pkg.add("RxInfer")
Pkg.add("Distributions")
Pkg.add("Random")
Pkg.add("Plots")
Pkg.add("IJulia")
```

Then launch Jupyter from the repository root and open the notebooks under
`RxInfer.jl/`:

```sh
julia -e 'using IJulia; jupyterlab()'
```

Each notebook is designed to run top to bottom with a fresh kernel. No
environment variables or configuration are required.

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
