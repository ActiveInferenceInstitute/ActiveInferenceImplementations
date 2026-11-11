# Documentation — ActiveInferenceImplementations

Documentation index for **`ActiveInferenceInstitute/ActiveInferenceImplementations`**,
an educational Julia notebook repository maintained by the Active Inference
Institute. Start with [`../README.md`](../README.md) for the overview, then use
this index for the layout and the two gates that protect the notebooks.

## This folder

- [`repository-layout.md`](repository-layout.md) — what every tracked file and
  folder is for, and how the notebook environment is assembled.
- [`notebooks.md`](notebooks.md) — the teaching order of the notebooks, how to
  run them, and what executing them changes in git.
- [`gnn-conformance.md`](gnn-conformance.md) — the Generalized Notation Notation
  specification, the pinned parser, the three readers, and the conformance gate.

## Repository documents

- [`../README.md`](../README.md) — overview, prerequisites, getting started,
  verification commands, citation, and license.
- [`../RxInfer.jl/README.md`](../RxInfer.jl/README.md) — the two notebooks and
  how to run them.
- [`../specs/README.md`](../specs/README.md) — the GNN document and the pin.
- [`../src/README.md`](../src/README.md) — the dependency-free Julia spec reader.
- [`../scripts/README.md`](../scripts/README.md) — the validation scripts and
  their exit codes.
- [`../test/README.md`](../test/README.md) — what the Julia test suite checks.
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — contribution guidelines.
- [`../CITATION.cff`](../CITATION.cff) — machine-readable citation metadata.
- [`../LICENSE`](../LICENSE) — CC BY 4.0.
- [`../AGENTS.md`](../AGENTS.md) — agent guidance and declared task commands.
- [`../TO-DO.md`](../TO-DO.md) — review log and open items.
- [`../.aii/README.md`](../.aii/README.md) — the InstituteOS sidecar.

## Status

The notebooks and the Julia test suite work from a clean checkout after
`Pkg.instantiate()`, and CI runs both on Julia 1.13. The GNN conformance gate
needs network access the first time to install the pinned parser, or a local GNN
checkout plus a matching parser runtime; without either it exits `2`, which
means *not run*, never a pass. No notebook execution or Julia run is required to
read or edit this documentation.
