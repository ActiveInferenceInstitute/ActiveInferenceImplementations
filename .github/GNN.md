# GNN conformance

The job key is `gnn-conformance`, its display name is
`gnn conformance (pinned)`, and both are defined in
[`.github/workflows/ci.yml`](workflows/ci.yml). The job calls `./run.sh gnn`.

It reads [`../specs/gnn-pin.json`](../specs/gnn-pin.json), the canonical pin
record with schema `gnn-importer-pin/v1`, which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.0.3`
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`).

The arm installs that commit into its own runtime (or uses
`$GNN_RUNTIME_PYTHON`, or a `$GNN_ROOT` checkout), verifies the recorded parser
digests, then runs
`python3 scripts/validate_gnn_spec.py --gnn-runtime <runtime> --julia julia --json`
against `specs/normal_vmp.gnn.md`. The
script parses `specs/normal_vmp.gnn.md` with the pinned parser, checks the model
name, variable dimensions, connections, scalars, equations, ontology
annotations, required sections, and static time specification, requires the
pinned semantic validator and consistency checker to accept the document,
compares the pinned parser, a regular-expression reader, and the
`src/spec_reader.jl` summary on the same declarations, confirms both notebooks
still name the document they use, and asserts the installed `gnn` version equals
the pin's tag without the leading `v`. It does not scan the rest of the
repository for `*.gnn.md`.

The workflow pins `astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2`
with `uv` 0.13.7, which [`../uv.toml`](../uv.toml) also requires. It does not use
the `ActiveInferenceInstitute/.github` composite action. Measured wall time is in
[`../docs/gate-timings.md`](../docs/gate-timings.md).
