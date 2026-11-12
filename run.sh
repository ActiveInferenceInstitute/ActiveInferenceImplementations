#!/usr/bin/env bash
#
# Single entry point for every gate of this repository. Each arm is separately
# runnable, and `.github/workflows/ci.yml` calls the same arms, so a local run
# and CI never diverge.
#
#   ./run.sh                # default arm: test-fast
#   ./run.sh setup          # Julia environment, notebook runtime, IJulia kernel
#   ./run.sh lint           # syntax checks (Julia, Python, JSON, shell)
#   ./run.sh test-fast      # static gates: no RxInfer, no inference
#   ./run.sh test           # full suite (includes the static gates)
#   ./run.sh docs           # relative links + generated gate table freshness
#   ./run.sh gnn            # GNN conformance against specs/gnn-pin.json
#   ./run.sh notebooks      # execute both notebooks into _build/executed
#   ./run.sh gate           # every gate arm above, failures aggregated
#   ./run.sh --list         # print the arm names, one per line
#
# The GNN arm uses, in order of precedence: $GNN_RUNTIME_PYTHON, a
# $GNN_ROOT checkout run with ${GNN_PYTHON:-python3}, or a runtime it provisions
# from the pin into `_build/gnn-runtime` with `uv`.
#
# The notebooks arm uses `_build/notebook-runtime/bin/python` when present,
# otherwise $AII_NOTEBOOK_PYTHON, otherwise `python3`.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
ROOT=$(pwd)
BUILD="$ROOT/_build"
GNN_PIN="specs/gnn-pin.json"

JULIA_BIN=${JULIA_BIN:-julia}
PYTHON_BIN=${PYTHON_BIN:-python3}

ARMS=(setup lint test-fast test docs gnn notebooks gate)
MEASURED_ARMS=(lint test-fast test docs gnn notebooks)
NOTEBOOKS=(RxInfer.jl/00_intro.ipynb RxInfer.jl/01_message_passing.ipynb)

usage() {
    sed -n '3,30p' "$0" | sed 's/^# \{0,1\}//'
}

pin_field() {
    "$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' \
        "$GNN_PIN" "$1"
}

gnn_runtime() {
    local runtime="$BUILD/gnn-runtime"
    local commit
    commit=$(pin_field commit)
    if [ -x "$runtime/bin/python" ] && [ "$(cat "$runtime/.pin-commit" 2>/dev/null || true)" = "$commit" ]; then
        printf '%s\n' "$runtime/bin/python"
        return 0
    fi
    command -v uv >/dev/null 2>&1 || {
        echo "gnn arm: uv is required to provision the pinned runtime (or set GNN_RUNTIME_PYTHON / GNN_ROOT+GNN_PYTHON)" >&2
        return 2
    }
    local repository
    repository=$(pin_field repository)
    mkdir -p "$BUILD"
    # The pin is the only source of the revision: a bump re-points the install.
    uv python install 3.12 >/dev/null
    uv venv --clear --python 3.12 "$runtime" >/dev/null
    uv pip install --python "$runtime/bin/python" \
        "generalized-notation-notation @ git+${repository}@${commit}" >/dev/null
    printf '%s\n' "$commit" > "$runtime/.pin-commit"
    printf '%s\n' "$runtime/bin/python"
}

notebook_python() {
    if [ -x "$BUILD/notebook-runtime/bin/python" ]; then
        printf '%s\n' "$BUILD/notebook-runtime/bin/python"
    else
        printf '%s\n' "${AII_NOTEBOOK_PYTHON:-$PYTHON_BIN}"
    fi
}

arm_setup() {
    "$JULIA_BIN" --project=. -e 'using Pkg; Pkg.instantiate()'
    mkdir -p "$BUILD"
    if [ ! -x "$BUILD/notebook-runtime/bin/python" ]; then
        command -v uv >/dev/null 2>&1 || {
            echo "setup: uv is required to provision the notebook runtime" >&2
            return 2
        }
        uv venv --clear --python 3.12 "$BUILD/notebook-runtime" >/dev/null
        uv pip install --python "$BUILD/notebook-runtime/bin/python" nbconvert >/dev/null
    fi
    if ! "$JULIA_BIN" --startup-file=no -e 'using IJulia' >/dev/null 2>&1; then
        "$JULIA_BIN" -e 'using Pkg; Pkg.add("IJulia")'
    fi
    # `specname` keeps the kernelspec exactly `julia-1.13`, which is what the
    # notebooks request; `--project=@.` keeps this repository's Project.toml.
    "$JULIA_BIN" --startup-file=no -e \
        'using IJulia; IJulia.installkernel("julia-1.13", "--project=@.", specname="julia-1.13")'
}

arm_lint() {
    "$JULIA_BIN" --startup-file=no --history-file=no -e \
        'for f in ARGS; Meta.parseall(read(f, String)); end' \
        src/spec_reader.jl test/static_tests.jl test/runtests.jl
    local script
    for script in scripts/*.py; do
        "$PYTHON_BIN" -c 'import sys; compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec")' \
            "$script"
    done
    "$PYTHON_BIN" -c 'import json,sys; [json.load(open(p, encoding="utf-8")) for p in sys.argv[1:]]' \
        "$GNN_PIN" "${NOTEBOOKS[@]}"
    bash -n run.sh
}

arm_test_fast() {
    "$JULIA_BIN" --project=. test/static_tests.jl
}

arm_test() {
    "$JULIA_BIN" --project=. test/runtests.jl
}

arm_docs() {
    "$PYTHON_BIN" scripts/check_docs_links.py
    "$PYTHON_BIN" scripts/measure_gates.py --check
}

arm_gnn() {
    if [ -n "${GNN_RUNTIME_PYTHON:-}" ]; then
        "$PYTHON_BIN" scripts/validate_gnn_spec.py \
            --gnn-runtime "$GNN_RUNTIME_PYTHON" --julia "$JULIA_BIN" --json
    elif [ -n "${GNN_ROOT:-}" ]; then
        "$PYTHON_BIN" scripts/validate_gnn_spec.py \
            --gnn-root "$GNN_ROOT" --python "${GNN_PYTHON:-$PYTHON_BIN}" \
            --julia "$JULIA_BIN" --json
    else
        local runtime
        runtime=$(gnn_runtime)
        "$PYTHON_BIN" scripts/validate_gnn_spec.py \
            --gnn-runtime "$runtime" --julia "$JULIA_BIN" --json
    fi
}

arm_notebooks() {
    mkdir -p "$BUILD/executed"
    "$(notebook_python)" -m nbconvert --to notebook --execute \
        --ExecutePreprocessor.timeout=1800 \
        --output-dir "$BUILD/executed" "${NOTEBOOKS[@]}"
}

run_arm() {
    case "$1" in
        setup) arm_setup ;;
        lint) arm_lint ;;
        test-fast) arm_test_fast ;;
        test) arm_test ;;
        docs) arm_docs ;;
        gnn) arm_gnn ;;
        notebooks) arm_notebooks ;;
        *) echo "unknown arm: $1" >&2; usage >&2; return 64 ;;
    esac
}

if [ $# -eq 0 ]; then
    set -- test-fast
fi

case "$1" in
    -h|--help)
        usage
        exit 0
        ;;
    --list)
        printf '%s\n' "${ARMS[@]}"
        exit 0
        ;;
    gate)
        failed=""
        for arm in "${MEASURED_ARMS[@]}"; do
            printf '\n=== %s ===\n' "$arm"
            if ! run_arm "$arm"; then
                failed="${failed}${failed:+ }${arm}"
            fi
        done
        if [ -n "$failed" ]; then
            printf '\nfailed arms: %s\n' "$failed" >&2
            exit 1
        fi
        printf '\nall arms passed\n'
        ;;
    *)
        run_arm "$1"
        ;;
esac
