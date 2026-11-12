# Validation, documentation, and measurement scripts

All four scripts are invoked through [`../run.sh`](../run.sh), so CI and a local
run use the same command.

## `validate_gnn_spec.py`

The documented conformance gate for `specs/normal_vmp.gnn.md`; the `gnn` arm.
It verifies the pinned GNN parser and its recorded digests, parses the document
in a subprocess, and compares three independent readers of the declarations: the
pinned parser, the regular-expression reader in this script, and the
dependency-free Julia reader in `src/spec_reader.jl`.

Exit codes: `0` pass, `1` conformance failure, `2` pinned runtime, pinned
checkout, or requested Julia reader unavailable. Exit `2` means the check was
**not run**, never a pass.

Usage (from the repository root):

```bash
./run.sh gnn

# The same arm with an existing pinned runtime:
GNN_RUNTIME_PYTHON=/path/to/venv/bin/python ./run.sh gnn

# Or a local GNN checkout (archives the pinned commit and verifies its digests):
GNN_ROOT=/path/to/Generalized_Notation_Notation \
GNN_PYTHON=/path/to/parser-runtime/bin/python \
  ./run.sh gnn
```

The pin is `specs/gnn-pin.json` (schema `gnn-importer-pin/v1`); bumping it is a
deliberate paired change.

## `gnn_parser_probe.py`

The only module that imports the upstream `gnn` package. `validate_gnn_spec.py`
runs it in a subprocess with the pinned source first on `PYTHONPATH`, so the
parser that runs is always the revision recorded in the pin, never a live
checkout. It is normally invoked by the validator, not by hand.

## `check_docs_links.py`

The `docs` arm, together with `measure_gates.py --check`. It scans every tracked
Markdown file for relative links, requires each target and Markdown heading
anchor to exist, and keeps `docs/documentation-index.md` complete: every page
under `docs/` must be listed there, and `docs/README.md` must link the index.

External URLs are not fetched. Exit `1` lists each failure as
`path:line: reason`.

## `measure_gates.py`

Runs every measured arm of `run.sh`, times it, and writes
`docs/gate-timings.md` with the wall times, Julia test counts, and the host
environment. `--check` (used by the `docs` arm) only verifies that every arm
`./run.sh --list` reports has a row; it never runs an arm. No number in that page
is hand-typed.
