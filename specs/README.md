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
