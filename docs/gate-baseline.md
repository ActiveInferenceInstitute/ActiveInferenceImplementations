# Gate baseline (pre-change)

The numbers below were measured on one host, one run per command, against the
pre-change tree (`a1e09ea`, the commit before `run.sh` existed). They are
historical evidence and are not refreshed by any script; the current numbers
are generated in [`gate-timings.md`](gate-timings.md).

Baseline checkout:

```sh
git archive a1e09ea | tar -x -C /tmp/aii-baseline
cd /tmp/aii-baseline
julia --project=. -e 'using Pkg; Pkg.instantiate()'   # 49.6 s, untimed setup
```

| Arm before the change | Command | Wall time | Result |
| --- | --- | --- | --- |
| full tests, cold tree | `julia --project=. test/runtests.jl` | 60.9 s | 47 pass |
| full tests, warm tree | `julia --project=. test/runtests.jl` | 20.7 s | 47 pass |
| lint | none existed | — | — |
| fast tests | none existed; the only suite loaded RxInfer | — | — |
| docs/links | none existed; no link checker or index | — | — |
| GNN conformance | `GNN_ROOT=… GNN_PYTHON=… python3 scripts/validate_gnn_spec.py --julia julia --json` | 10.0 s | pass, gnn 5.0.3 |
| notebooks | `python3 -m nbconvert --to notebook --execute --output-dir=… RxInfer.jl/*.ipynb` | 81.2 s | **fail** |

The cold and warm full-suite rows differ only by Julia precompilation and JIT
warm-up; they are not a speed comparison. The arm split does not make the full
suite faster, and this page claims no such speedup: the change is that the
static gates became a separate ~5 s arm and that CI stopped provisioning the
same environments twice.

The notebook command failed because `nbconvert`'s default per-cell timeout is
30 s and the cold `using Plots` cell (precompiling GR and its JLLs) exceeded it;
the observed trace unwound through `Plots.jl`'s module include. A cold
`julia --project=. -e 'using Plots'` on the same host took 117 s. The
`notebooks` arm therefore sets `--ExecutePreprocessor.timeout=1800`.

CI before the change ran two jobs, each setting up Julia independently, and
inlined the commands: the `notebooks` job ran the test suite, installed
`nbconvert` with `pip`, and installed the IJulia kernel; the
`gnn-conformance` job installed `uv`, Python, and Julia again, provisioned the
parser runtime inline, and repeated the pin-version assertion that the validator
already performs. The GNN job also had no Julia cache.
