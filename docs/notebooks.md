# Notebooks

The teaching material is two self-contained Jupyter notebooks in
[`../RxInfer.jl/`](../RxInfer.jl/README.md), executed top to bottom against the
repository's committed [`../Project.toml`](../Project.toml).

## Teaching order

| Notebook | Topic | Model source |
| --- | --- | --- |
| [`00_intro.ipynb`](../RxInfer.jl/00_intro.ipynb) | Infer the bias of a coin with a Beta–Bernoulli model in RxInfer.jl, rebuild the posterior by hand from individual messages, and scale the dataset. | Links to the canonical `specs/coin_flip.gnn.md` in [ActInf_RxInfer](https://github.com/ActiveInferenceInstitute/ActInf_RxInfer); no second copy is declared here. |
| [`01_message_passing.ipynb`](../RxInfer.jl/01_message_passing.ipynb) | Mean-field variational message passing (VMP) for the mean and precision of a Normal model. | Reads priors, data statistics, observation count, iteration count, and seed from [`../specs/normal_vmp.gnn.md`](../specs/normal_vmp.gnn.md) through [`../src/spec_reader.jl`](../src/spec_reader.jl). |

The notebooks use the current RxInfer 6 API (`infer`, `MeanField`,
`@initialization`, `@call_message_update_rule`, `free_energy`), not the retired
reactive interface. [`../test/runtests.jl`](../test/runtests.jl) guards both the
API use and the notebook signposts.

## Run them

From the repository root:

```sh
julia --project=. -e 'using Pkg; Pkg.instantiate()'
```

Register the IJulia kernel the notebooks declare, once per machine (`./run.sh
setup` does this and instantiates the environment):

```julia
using Pkg
Pkg.add("IJulia")
using IJulia
IJulia.installkernel("julia-1.13", "--project=@.", specname="julia-1.13")
```

The `specname` argument keeps the kernelspec named exactly `julia-1.13`, which is
what the notebooks request; without it IJulia appends the Julia version
(`julia-1.13-1.13`). `--project=@.` keeps the committed `Project.toml` active
inside the kernel. Then launch Jupyter from the repository root and open the
notebooks under `RxInfer.jl/`. No environment variables or configuration are
required for the notebooks themselves.

CI executes both notebooks headlessly with `nbconvert --execute` on Julia 1.13
through `./run.sh notebooks`; see
[`../.github/workflows/ci.yml`](../.github/workflows/ci.yml). That arm writes
into `_build/executed` and never overwrites the committed outputs. Notebook
execution is deliberately not part of the fast arm: `./run.sh test-fast` reads
the notebooks as text and never runs a kernel, so the default local gate stays
in seconds.

## Outputs and git

The notebooks keep their rendered cell outputs in git. Executing a notebook
rewrites the committed outputs, so a notebook run is a content change, not a
side effect to discard. This is a deliberate maintainer choice; there is no
`nbstripout` hook.

## Environment notes

These were observed running the gates on macOS and are recorded in the
[`../README.md`](../README.md) as well:

- If GR (the default `Plots.jl` backend) cannot load `libssl.3.dylib`, export
  `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/opt/openssl@3/lib:/usr/lib` before
  starting Jupyter.
- The `[compat]` bounds allow Julia 1.10+, but the configuration exercised by CI
  and the notebook refresh is Julia 1.13 with RxInfer 6.
