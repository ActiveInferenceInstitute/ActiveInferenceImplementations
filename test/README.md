# Test suite

Run from the repository root:

```bash
julia --project=. -e 'using Pkg; Pkg.instantiate()'
julia --project=. test/runtests.jl
```

CI runs the same command on Julia 1.13 in
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

`runtests.jl` reads the declarations from `specs/normal_vmp.gnn.md` through
`src/spec_reader.jl` and checks:

- the declared model name, priors, data statistics, observation count, VMP
  iteration count, and seed;
- that the seeded data is reproducible and matches the declared mean and
  precision within the stated tolerances;
- that mean-field VMP recovers the declared data statistics and reduces free
  energy;
- that the notebooks use the current RxInfer API and do not fall back to the
  retired reactive interface;
- that the notebooks point at their canonical GNN documents.
