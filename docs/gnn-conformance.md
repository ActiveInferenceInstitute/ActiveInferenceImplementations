# GNN conformance gate

The mean-field VMP Normal model in
[`../specs/normal_vmp.gnn.md`](../specs/normal_vmp.gnn.md) is declared in
[Generalized Notation Notation](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation)
(GNN). It is the single source of truth for the notebook, the Julia test suite,
and the validation gate. This page explains how the gate proves that the
document and its readers agree.

## The pin

[`../specs/gnn-pin.json`](../specs/gnn-pin.json) records the upstream revision:
repository, tag `v5.0.3`, commit `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`,
GNN language version, recording date, and the SHA-256 digests of five parser
files. The validator reads these exact filenames; it does not enumerate the
directory. Bumping the pin is a deliberate paired change: update the commit and
the parser digests together, then re-run the gate.

## Three independent readers

The gate compares the same declared scalars read three ways:

1. the **pinned upstream parser**, run in a subprocess through
   [`../scripts/gnn_parser_probe.py`](../scripts/gnn_parser_probe.py), the only
   module that imports the upstream `gnn` package;
2. the **regular-expression reader** inside
   [`../scripts/validate_gnn_spec.py`](../scripts/validate_gnn_spec.py);
3. the **dependency-free Julia reader** in
   [`../src/spec_reader.jl`](../src/spec_reader.jl), also included by the notebook
   and the test suite.

Agreement across three readers is the point: the document cannot drift from what
the notebook and the tests actually consume.

## Verified source and digest checks

The validator accepts either a GNN git checkout or an installed pinned runtime:

- `--gnn-root` or `GNN_ROOT` — materializes the pinned commit with
  `git archive` and verifies every recorded parser digest. The live working tree
  is never imported.
- `--gnn-runtime` or `GNN_RUNTIME_PYTHON` — an interpreter whose `gnn` package is
  installed at the pinned revision; the distribution version and installed parser
  file digests are verified.

The Julia reader is selected with `--julia` or `JULIA_BIN`. When a source is
missing or the requested Julia binary is unavailable, the validator exits `2`.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Pass: the document conforms and the readers agree. |
| `1` | Conformance failure. |
| `2` | The pinned runtime, pinned checkout, or requested Julia reader is unavailable. The check was **not run**, never a pass. |

## Run it locally

From the repository root:

```sh
# Installed pinned runtime (the CI form)
python3 scripts/validate_gnn_spec.py \
  --gnn-runtime /path/to/venv/bin/python --julia julia --json

# Local GNN checkout (archives the pinned commit and verifies digests)
GNN_ROOT=/path/to/Generalized_Notation_Notation \
GNN_PYTHON=/path/to/parser-runtime/bin/python \
  python3 scripts/validate_gnn_spec.py --julia julia --json
```

## How CI runs it

The `gnn conformance (pinned)` job in
[`../.github/workflows/ci.yml`](../.github/workflows/ci.yml) installs `uv`
0.13.7 (pinned by [`../uv.toml`](../uv.toml)), provisions a Python 3.12 runtime
from the pin, runs the validator, and then asserts that the installed `gnn`
version equals the pin's tag without the leading `v`.

## Scope

The gate covers the declared model name, variables and dimensions, connection
graph, declared scalars, mean-field equations, ontology annotations, and the
pinned semantic validator and consistency checker. It also checks that the
notebooks keep pointing at their canonical GNN documents. The Beta–Bernoulli
coin model used by `00_intro.ipynb` is not declared here; its canonical document
is `specs/coin_flip.gnn.md` in [ActInf_RxInfer](https://github.com/ActiveInferenceInstitute/ActInf_RxInfer).
