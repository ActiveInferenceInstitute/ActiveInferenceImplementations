# GNN conformance

`gnn conformance (pinned)` is defined in `.github/workflows/ci.yml` and reads
`specs/gnn-pin.json`, which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.0.3`
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`).

The job installs that commit into its own runtime, verifies the recorded parser
digests, then runs `scripts/validate_gnn_spec.py` with
`--gnn-runtime "$RUNNER_TEMP/gnn-runtime/bin/python" --julia julia --json`. The
script parses `specs/normal_vmp.gnn.md` with the pinned parser, checks the
model name, variable dimensions, connections, scalars, equations, ontology
annotations, required sections, and static time specification, requires the
pinned semantic validator and consistency checker to accept the document,
compares the pinned parser, a regular-expression reader, and the
`src/spec_reader.jl` summary on the same declarations, and confirms both
notebooks still name the document they use. It does not scan the rest of the
repository for `*.gnn.md`.
