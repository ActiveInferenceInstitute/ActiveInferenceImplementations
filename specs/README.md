# GNN specifications and pin

- `normal_vmp.gnn.md` — the single source of truth for the mean-field VMP
  Normal estimation model: priors, data statistics, observation count, VMP
  iteration count, seed, equations, and ontology annotations. The notebook, the
  Julia test suite, and the validation gate all read this file.
- `gnn-pin.json` — the pinned upstream GNN revision: repository, tag, commit,
  language version, recording date, and the SHA-256 digests of the parser files
  the validator verifies.

The validator (`scripts/validate_gnn_spec.py`) reads these exact filenames; it
does not enumerate the directory. Bumping the pin is a deliberate change: update
the commit and parser digests together, then run the validation gate again.

The Beta-Bernoulli coin model used by `00_intro.ipynb` is not declared here; its
canonical GNN document is `specs/coin_flip.gnn.md` in
[ActInf_RxInfer](https://github.com/ActiveInferenceInstitute/ActInf_RxInfer).

## Education contract migration — blocked

[`../education-contract.json`](../education-contract.json) points to
[`education/implementations.json`](education/implementations.json), with one
unit per notebook and titles copied from their first markdown cells.
[`education/schema.json`](education/schema.json) is the unchanged canonical
schema from the
[Education workflow contract](https://github.com/ActiveInferenceInstitute/courses/blob/main/docs/workflows/education.md).

This is an incomplete adoption, not a valid contract bundle. Neither notebook's
first markdown cell states learning objectives: `00_intro.ipynb` describes
RxInfer and the coin model; `01_message_passing.ipynb` describes the GNN model
source and reader. Their `objectives` arrays are deliberately empty rather than
relabeling descriptive prose as learning objectives or copying objectives from
later cells. The canonical checker must reject these arrays until maintainers
author objectives in the required source cells.

The notebooks state no inter-notebook prerequisite requirement.
`01_message_passing.ipynb` mentions the first notebook in “Where to go next,”
but does not require completing it. File/package dependencies are not notebook
units, so no prerequisite edges are inferred from them or from filename order.
No glossary is transcribed by this member's migration step.

Run the lead's checker directly from this repository, without writing into
the lead checkout:

```sh
python3 -B ../courses/software/scripts/check_education_contract.py specs/education/implementations.json
./run.sh docs
./run.sh test-fast
./run.sh test
```
