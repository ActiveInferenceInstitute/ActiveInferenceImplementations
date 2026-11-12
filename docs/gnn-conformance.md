# GNN conformance gate

The mean-field VMP Normal model in
[`../specs/normal_vmp.gnn.md`](../specs/normal_vmp.gnn.md) is declared in
[Generalized Notation Notation](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation)
(GNN). It is the single source of truth for the notebook, the Julia test suite,
and the validation gate. This page explains how the gate proves that the
document and its readers agree.

## The pin

[`../specs/gnn-pin.json`](../specs/gnn-pin.json) is the canonical pin record,
schema `gnn-importer-pin/v1`. It records the
repository, tag `v5.0.3`, commit `8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`,
GNN language version, recording date, and the SHA-256 digests of five parser
files. The validator reads these exact filenames; it does not enumerate the
directory. Bumping the pin is a deliberate paired change: update the commit and
the parser digests together, then re-run the gate.

[`../.github/GNN.md`](../.github/GNN.md) is the short pointer: it names the pin
file, the revision, the job, and what the job parses. This page is the long form.

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

`./run.sh gnn` is the arm CI calls. It uses, in order of precedence:

1. `$GNN_RUNTIME_PYTHON` — an interpreter whose `gnn` package is installed at the
   pinned revision;
2. `$GNN_ROOT` with `${GNN_PYTHON:-python3}` — a GNN checkout, archived at the
   pinned commit and digest-verified;
3. no override — a runtime provisioned from the pin into
   `_build/gnn-runtime` with `uv` (network access on the first run, cached
   afterwards under the pin's commit).

```sh
./run.sh gnn

# Equivalently, with an existing pinned runtime:
GNN_RUNTIME_PYTHON=/path/to/venv/bin/python ./run.sh gnn

# Or with a local GNN checkout:
GNN_ROOT=/path/to/Generalized_Notation_Notation \
GNN_PYTHON=/path/to/parser-runtime/bin/python \
  ./run.sh gnn
```

The underlying validator invocation is
`python3 scripts/validate_gnn_spec.py --gnn-runtime <python> --julia julia --json`
(or `--gnn-root <dir> --python <python>`).

## How CI runs it

The job key is `gnn-conformance`; its display name is
`gnn conformance (pinned)`, and both live in
[`../.github/workflows/ci.yml`](../.github/workflows/ci.yml). The workflow does
not use the `ActiveInferenceInstitute/.github` composite action; it pins
`astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2` and relies on
[`../uv.toml`](../uv.toml) (`required-version = "==0.13.7"`). It then calls
`./run.sh gnn`, which provisions a Python 3.12 runtime from the pin, runs the
validator, and asserts the installed `gnn` version equals the pin's tag without
the leading `v`. The validator already enforces that version equality, so the
workspace does not repeat the check in a second step. The measured arm wall time
is in [`gate-timings.md`](gate-timings.md).

## Scope

The gate covers the declared model name, variables and dimensions, connection
graph, declared scalars, mean-field equations, ontology annotations, and the
pinned semantic validator and consistency checker. It also checks that the
notebooks keep pointing at their canonical GNN documents. The Beta–Bernoulli
coin model used by `00_intro.ipynb` is not declared here; its canonical document
is `specs/coin_flip.gnn.md` in [ActInf_RxInfer](https://github.com/ActiveInferenceInstitute/ActInf_RxInfer).
