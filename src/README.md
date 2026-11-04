# `spec_reader.jl`

A dependency-free reader for the committed GNN document
`specs/normal_vmp.gnn.md`. It is included (not imported as a package) by:

- `RxInfer.jl/01_message_passing.ipynb`;
- `test/runtests.jl`;
- `scripts/validate_gnn_spec.py`, which runs it with a bare `julia` binary and
  compares its declarations with the pinned GNN parser.

It defines `GNNSpecParameters`, `SPEC_PATH`, `SPEC_SCALAR_KEYS`, and
`spec_parameters()`. The file intentionally has no `using` statements; keep it
dependency-free so the cross-reader comparison remains independent of the GNN
runtime.
