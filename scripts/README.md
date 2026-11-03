# Validation scripts

## `validate_gnn_spec.py`

The documented conformance gate for `specs/normal_vmp.gnn.md`. It verifies the
pinned GNN parser and its recorded digests, parses the document in a subprocess,
and compares three independent readers of the declarations: the pinned parser,
the regular-expression reader in this script, and the dependency-free Julia
reader in `src/spec_reader.jl`.

Exit codes: `0` pass, `1` conformance failure, `2` pinned runtime, pinned
checkout, or requested Julia reader unavailable. Exit `2` means the check was
**not run**, never a pass.

Usage (from the repository root):

```bash
# Installed pinned runtime (used by CI)
python3 scripts/validate_gnn_spec.py \
  --gnn-runtime /path/to/venv/bin/python --julia julia --json

# Local GNN checkout (archives the pinned commit and verifies its digests)
GNN_ROOT=/path/to/Generalized_Notation_Notation \
GNN_PYTHON=/path/to/parser-runtime/bin/python \
  python3 scripts/validate_gnn_spec.py --julia julia --json
```

The pin is `specs/gnn-pin.json`; bumping it is a deliberate paired change.

## `gnn_parser_probe.py`

The only module that imports the upstream `gnn` package. `validate_gnn_spec.py`
runs it in a subprocess with the pinned source first on `PYTHONPATH`, so the
parser that runs is always the revision recorded in the pin, never a live
checkout. It is normally invoked by the validator, not by hand.
