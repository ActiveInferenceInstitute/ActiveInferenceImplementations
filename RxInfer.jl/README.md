# RxInfer.jl notebooks

Two self-contained, seeded notebooks that run top to bottom against the
repository's `Project.toml`:

- `00_intro.ipynb` — the Beta-Bernoulli coin model: infer the bias of a coin
  with RxInfer, rebuild the posterior by hand from the individual messages, and
  scale the dataset. The canonical GNN document for this model is
  `specs/coin_flip.gnn.md` in
  [ActInf_RxInfer](https://github.com/ActiveInferenceInstitute/ActInf_RxInfer);
  this notebook links to it and does not declare a second copy.
- `01_message_passing.ipynb` — mean-field variational message passing for the
  mean and precision of a Normal model. The priors, data statistics,
  observation count, iteration count, and seed are read from
  `specs/normal_vmp.gnn.md` through `src/spec_reader.jl`.

## Run

From the repository root:

```bash
julia --project=. -e 'using Pkg; Pkg.instantiate()'
```

Install the IJulia kernel the notebooks declare (once per machine):

```julia
using Pkg
Pkg.add("IJulia")
using IJulia
IJulia.installkernel("julia-1.13", "--project=@.", specname="julia-1.13")
```

Then launch Jupyter from the repository root and open the notebooks. No
environment variables are required. CI executes both notebooks with
`nbconvert --execute` on Julia 1.13.

The notebooks keep their rendered outputs in git, so executing them rewrites
the committed outputs.
