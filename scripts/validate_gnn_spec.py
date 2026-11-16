"""Validate the committed GNN specification with the pinned upstream parser.

The canonical GNN pin is recorded in ``specs/gnn-pin.json`` (repository, tag,
commit, and SHA-256 digests of the parser files). This script supports two
verified sources for that pin:

* a GNN git checkout (``--gnn-root`` or ``GNN_ROOT``): the pinned commit is
  materialized with ``git archive`` and every recorded digest is verified, so
  the live working tree is never imported;
* an installed pinned runtime (``--gnn-runtime`` or ``GNN_RUNTIME_PYTHON``):
  an interpreter whose ``gnn`` package is installed at the pinned revision; the
  distribution version and the installed parser file digests are verified.

Either way the document is parsed by ``scripts/gnn_parser_probe.py`` in a
subprocess and checked for conformance. ``specs/normal_vmp.gnn.md`` is the
single source of truth for the mean-field VMP model, so the checks cover the
declared model name, the declared variables and their dimensions, the
connection graph, the declared scalars, the mean-field equations, and the
ontology annotations, plus the pinned semantic validator and consistency
checker. The notebooks must keep pointing at the model's canonical GNN document
(``specs/normal_vmp.gnn.md`` here, ``specs/coin_flip.gnn.md`` in
ActInf_RxInfer for the Beta-Bernoulli coin model), so their signposts are
checked too.

The declared scalars are compared against three independent readers of the same
document: the pinned parser, the regular-expression reader in this script, and
the dependency-free Julia reader in ``src/spec_reader.jl``
(``--julia`` or ``JULIA_BIN``, used by the Julia test suite as well).

The pin's ``language_version`` (for example ``GNN v1.1``) must equal the version
the pinned parser reports for the document (``language-version-mismatch``).

Exit codes: ``0`` pass; ``1`` recognized authored/configuration or conformance
failure; ``2`` genuine pinned-runtime/checkout/Julia unavailability (*not run*,
never a pass). Ordinary argparse usage errors are invocation failures, not
validation receipts. Use fresh receipt destinations: unavailability writes no
new receipt. JSON stdout is one object matching the saved validation receipt.

Usage:

    # Local checkout (strongest: archive of the pinned commit)
    GNN_ROOT=/path/to/Generalized_Notation_Notation \\
    GNN_PYTHON=/path/to/parser-runtime/bin/python \\
    python3 scripts/validate_gnn_spec.py --julia julia --json

    # Pinned installed runtime (used by CI)
    python3 scripts/validate_gnn_spec.py --gnn-runtime /path/to/venv/bin/python
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "gnn_parser_probe.py"
GNN_SPEC_PATH = ROOT / "specs" / "normal_vmp.gnn.md"
GNN_PIN_PATH = ROOT / "specs" / "gnn-pin.json"
DEFAULT_RECEIPT = ROOT / "_build" / "gnn" / "validation-receipt.json"
PACKAGE_PREFIX = "src/gnn/"

# Expectations of the pinned document. These are the declarations the notebook,
# the Julia reader, and the test suite rely on; changing the model means
# changing the document and this block together.
MODEL_NAME = "ActiveInferenceImplementations Mean-Field VMP Normal Estimation"
VARIABLES = {"m": [1], "w": [1], "y": [100, 1]}
CONNECTIONS = [
    (["m"], ["y"]),
    (["w"], ["y"]),
]
SCALARS = {
    "m_prior_mean": 0.0,
    "m_prior_variance": 10.0,
    "w_prior_shape": 0.1,
    "w_prior_rate": 10.0,
    "data_mean": -4.0,
    "data_precision": 0.2,
    "n_observations": 100,
    "vmp_iterations": 10,
    "seed": 1234,
}
ONTOLOGY = {
    "m": "HiddenState",
    "w": "Precision",
    "y": "Observation",
}
EQUATIONS = (
    "m ~ NormalMeanVariance(m_prior_mean, m_prior_variance)",
    "w ~ Gamma(shape = w_prior_shape, rate = w_prior_rate)",
    "y_i | m, w ~ NormalMeanPrecision(m, w)",
    "q(m, w) = q(m) q(w)",
)
REQUIRED_SECTIONS = (
    "GNNSection",
    "GNNVersionAndFlags",
    "ModelName",
    "ModelAnnotation",
    "StateSpaceBlock",
    "Connections",
    "InitialParameterization",
    "Equations",
    "Time",
    "ActInfOntologyAnnotation",
    "ModelParameters",
    "Footer",
    "Signature",
)
# Notebook signposts: each notebook must name the canonical GNN document of the
# model it implements, and the VMP notebook must read its declarations.
NOTEBOOKS = {
    "RxInfer.jl/00_intro.ipynb": ("specs/coin_flip.gnn.md", "ActInf_RxInfer"),
    "RxInfer.jl/01_message_passing.ipynb": ("specs/normal_vmp.gnn.md", "spec_parameters()"),
}
SCALAR_PATTERN = re.compile(r"(?m)^[ \t]*([A-Za-z_]\w*)[ \t]*=[ \t]*\{[ \t]*\(([^)]*)\)[ \t]*\}")
READER_INPUT_PREFIX = "gnn-reader-input-error:"
READER_EXPRESSION = (
    'include(joinpath(pwd(), "src", "spec_reader.jl")); '
    'try print(spec_summary(ARGS[1])); catch err; '
    'if err isa ArgumentError || err isa SystemError; '
    f'println(stderr, "{READER_INPUT_PREFIX}", sprint(showerror, err)); exit(1); '
    'else rethrow(); end; end'
)


class Unavailable(RuntimeError):
    """Raised when the pinned parser runtime or checkout is not available."""


class InvalidInput(ValueError):
    """Raised for a recognized authored-document or supplied-pin failure."""


def _run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
            check=False, **kwargs,
        )
    except OSError as exc:
        raise Unavailable(f"cannot start {argv[0]!r}: {exc}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_pin(path: Path) -> dict[str, Any]:
    """Read the consumed pin fields, distinguishing bad input from unavailable code."""

    try:
        pin = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InvalidInput(f"cannot read pin record {path}: {exc}") from exc
    if not isinstance(pin, dict):
        raise InvalidInput(f"pin record {path} must be a JSON object")
    for key in ("repository", "tag", "commit", "language_version"):
        if not isinstance(pin.get(key), str) or not pin[key].strip():
            raise InvalidInput(f"pin record {path} requires a nonempty string '{key}'")
    if re.fullmatch(r"[0-9a-f]{40}", pin["commit"]) is None:
        raise InvalidInput(f"pin record {path} requires a full hexadecimal commit")
    files = pin.get("parser_files")
    if not isinstance(files, dict) or not files:
        raise InvalidInput(f"pin record {path} requires a nonempty 'parser_files' object")
    for relative, digest in files.items():
        if (
            not isinstance(relative, str)
            or not relative.startswith(PACKAGE_PREFIX)
            or relative == PACKAGE_PREFIX
            or ".." in Path(relative).parts
        ):
            raise InvalidInput(f"pin record {path} has an invalid parser path: {relative!r}")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise InvalidInput(f"pin record {path} has an invalid SHA-256 for {relative!r}")
    return pin


def _verify_digests(package_dir: Path, pin: dict[str, Any], *, origin: str) -> dict[str, str]:
    """Verify every recorded parser digest under an installed ``gnn`` package."""

    observed: dict[str, str] = {}
    for relative, expected in sorted(pin["parser_files"].items()):
        suffix = relative[len(PACKAGE_PREFIX) :] if relative.startswith(PACKAGE_PREFIX) else relative
        path = package_dir / suffix
        if not path.is_file():
            raise Unavailable(f"pinned parser file is missing from {origin}: {suffix}")
        try:
            observed[relative] = _sha256(path)
        except OSError as exc:
            raise Unavailable(f"cannot read pinned parser file {path}: {exc}") from exc
        if observed[relative] != expected:
            raise Unavailable(
                f"pinned parser file digest mismatch for {suffix} in {origin}: "
                f"expected {expected}, observed {observed[relative]}"
            )
    return observed


def materialize_pin(
    gnn_root: Path, pin: dict[str, Any], *, workspace: Path
) -> tuple[Path, str]:
    """Return pinned sources; only materialization inside ``workspace`` is owned."""

    if not gnn_root.is_dir():
        raise Unavailable(f"GNN checkout is not a directory: {gnn_root}")
    if not (gnn_root / ".git").exists():
        _verify_digests(gnn_root / "src" / "gnn", pin, origin=str(gnn_root))
        return gnn_root, f"digest-verified source tree {gnn_root} (no git metadata)"

    commit = pin["commit"]
    resolved = _run(["git", "-C", str(gnn_root), "rev-parse", f"{commit}^{{commit}}"])
    if resolved.returncode != 0:
        raise Unavailable(f"pinned commit {commit} is not present in {gnn_root}")
    if resolved.stdout.strip() != commit:
        raise Unavailable(
            f"resolved commit {resolved.stdout.strip()} differs from the pin {commit}"
        )

    target = workspace / "pinned-source"
    target.mkdir()
    archive = workspace / "pinned.tar"
    completed = _run(
        ["git", "-C", str(gnn_root), "archive", "--format=tar", f"--output={archive}", commit]
    )
    if completed.returncode != 0:
        raise Unavailable(f"git archive failed for {commit}: {completed.stderr.strip()}")
    try:
        with tarfile.open(archive) as handle:
            try:
                handle.extractall(target, filter="data")
            except TypeError:  # Python < 3.12, as supported by the original reader
                handle.extractall(target)
    except (OSError, tarfile.TarError) as exc:
        raise Unavailable(f"cannot extract pinned archive of {commit}: {exc}") from exc
    archive.unlink()
    _verify_digests(target / "src" / "gnn", pin, origin=f"archive of {commit}")
    return target, f"git archive of {commit}"


def run_probe(python: str, spec: Path, output: Path, *, source: Path | None) -> dict[str, Any]:
    """Run the probe, honoring only its explicit expected-error envelope."""

    environment = dict(os.environ)
    if source is not None:
        existing = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = str(source / "src") + (
            os.pathsep + existing if existing else ""
        )
    completed = _run(
        [python, str(PROBE), "--spec", str(spec), "--output", str(output)],
        env=environment,
    )
    detail = (completed.stderr or completed.stdout).strip().splitlines()
    tail = " | ".join(detail[-3:]) if detail else "no output"
    try:
        payload = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"pinned parser probe produced no valid payload: {tail}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("pinned parser probe payload must be an object")
    if "probe_error" in payload:
        error = payload["probe_error"]
        if not isinstance(error, dict) or not isinstance(error.get("message"), str):
            raise RuntimeError("pinned parser probe returned an invalid error envelope")
        if error.get("kind") == "input" and completed.returncode == 1:
            raise InvalidInput(error["message"])
        if error.get("kind") == "unavailable" and completed.returncode == 2:
            raise Unavailable(error["message"])
        raise RuntimeError(f"pinned parser probe returned an unexpected error: {error}")
    if completed.returncode != 0:
        raise RuntimeError(f"pinned parser probe failed with {python}: {tail}")
    return payload


def run_julia_reader(julia: str, spec: Path) -> dict[str, str]:
    """Distinguish explicit reader input rejection from startup/programming failures."""

    if shutil.which(julia) is None and not Path(julia).is_file():
        raise Unavailable(f"julia reader interpreter not found: {julia}")
    completed = _run(
        [julia, "--startup-file=no", "--history-file=no", "-e", READER_EXPRESSION, str(spec)],
        cwd=ROOT,
    )
    if completed.returncode != 0:
        for line in completed.stderr.splitlines():
            if completed.returncode == 1 and line.startswith(READER_INPUT_PREFIX):
                raise InvalidInput(line[len(READER_INPUT_PREFIX):].strip())
        detail = (completed.stderr or completed.stdout).strip().splitlines()
        tail = " | ".join(detail[-3:]) if detail else "no output"
        raise RuntimeError(f"julia reader failed with {julia}: {tail}")
    summary = {}
    for line in completed.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            summary[key.strip()] = value.strip()
    if not summary:
        raise RuntimeError("the julia reader produced no summary lines")
    return summary


def _scalar_number(value: object, *, name: str, reader: str) -> float:
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise InvalidInput(f"{reader} value for {name!r} is not a finite number: {value!r}") from exc
    if not math.isfinite(number):
        raise InvalidInput(f"{reader} value for {name!r} is not finite: {value!r}")
    return number


def declared_scalars(spec_text: str) -> dict[str, float]:
    """Read ``name={(value)}`` declarations from the InitialParameterization section."""

    match = re.search(r"(?ms)^##[ \t]+InitialParameterization[ \t]*$(.*?)(?=^##[ \t]|\Z)", spec_text)
    if match is None:
        return {}
    return {
        name: _scalar_number(value.strip(), name=name, reader="authored")
        for name, value in SCALAR_PATTERN.findall(match.group(1))
    }


def parsed_scalars(parser: dict[str, Any]) -> dict[str, float]:
    """Flatten the pinned parser's own view of the declared scalars."""

    observed: dict[str, float] = {}
    for name, value in parser["parameters"].items():
        while isinstance(value, list) and len(value) == 1:
            value = value[0]
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            observed[name] = float(value)
    return observed


def _variable_dimensions(parser: dict[str, Any]) -> dict[str, list[int]]:
    return {variable["name"]: list(variable["dimensions"]) for variable in parser["variables"]}


def _notebook_failures() -> list[str]:
    """Check that each notebook still names the canonical GNN document it uses."""

    failures: list[str] = []
    for relative, fragments in sorted(NOTEBOOKS.items()):
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"notebook {relative} is missing")
            continue
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            if fragment not in text:
                failures.append(f"notebook {relative} does not reference {fragment!r}")
    return failures


_LANGUAGE_VERSION = re.compile(r"(?i)^\s*(?:GNN\s*)?v?(\d+(?:\.\d+)*)")


def _normalize_language_version(text: object) -> str | None:
    """Return ``1.1`` for ``GNN v1.1``, ``v1.1`` or ``1.1``; ``None`` when unparseable."""

    match = _LANGUAGE_VERSION.match(str(text))
    return match.group(1) if match else None


def language_version_failures(pin: dict[str, Any], declared: object) -> list[str]:
    """Return failures when the parser's declared language version is not the pin's."""

    expected = _normalize_language_version(pin["language_version"])
    if expected is None:
        return [f"the pin's language_version {pin['language_version']!r} is not parseable"]
    if _normalize_language_version(declared) != expected:
        return [
            f"language-version-mismatch: the pinned parser reports {declared!r}, "
            f"the pin records {pin['language_version']!r}"
        ]
    return []


def conformance_failures(
    payload: dict[str, Any],
    *,
    pin: dict[str, Any],
    source: Path | None,
    spec_text: str,
    julia_summary: dict[str, str] | None,
) -> list[str]:
    """Return every conformance failure between the document and the model."""

    failures: list[str] = []
    parser = payload["parser"]
    expected_version = pin["tag"].lstrip("v")

    if payload["gnn_version"] != expected_version:
        failures.append(
            f"parser version {payload['gnn_version']} differs from the pinned {expected_version}"
        )
    failures.extend(language_version_failures(pin, parser["version"]))
    if source is not None:
        module = Path(str(payload["gnn_module"])).resolve()
        if not module.is_relative_to((source / "src").resolve()):
            failures.append(f"parser was imported from {module}, outside the pinned tree {source}")
    if not parser["success"]:
        failures.append("pinned parser reported failure")
    for message in parser["errors"]:
        failures.append(f"parser error: {message}")
    for message in parser["warnings"]:
        failures.append(f"parser warning: {message}")

    if parser["model_name"] != MODEL_NAME:
        failures.append(
            f"declared model name {parser['model_name']!r} differs from {MODEL_NAME!r}"
        )

    dimensions = _variable_dimensions(parser)
    if dimensions != VARIABLES:
        failures.append(f"declared variables {dimensions} differ from {VARIABLES}")
    if dimensions.get("y") != [SCALARS["n_observations"], 1]:
        failures.append(
            f"StateSpaceBlock y dimensions {dimensions.get('y')} do not match the declared "
            f"n_observations {SCALARS['n_observations']}"
        )

    connections = [
        (list(connection["sources"]), list(connection["targets"]))
        for connection in parser["connections"]
    ]
    if connections != CONNECTIONS:
        failures.append(f"declared connections {connections} differ from {CONNECTIONS}")

    readers = (("regex", declared_scalars(spec_text)), ("parser", parsed_scalars(parser)))
    for name, expected in SCALARS.items():
        for label, observed in readers:
            if observed.get(name) != expected:
                failures.append(
                    f"{label} reader sees {name}={observed.get(name)} instead of {expected}"
                )
    if julia_summary is not None:
        if julia_summary.get("model_name") != MODEL_NAME:
            failures.append(
                f"julia reader sees model_name={julia_summary.get('model_name')!r} "
                f"instead of {MODEL_NAME!r}"
            )
        for name, expected in SCALARS.items():
            observed = julia_summary.get(name)
            if observed is None or _scalar_number(observed, name=name, reader="julia") != expected:
                failures.append(
                    f"julia reader sees {name}={observed} instead of {expected} "
                    "(src/spec_reader.jl must read the committed declarations)"
                )

    for fragment in EQUATIONS:
        if fragment not in spec_text:
            failures.append(f"equations do not state the model fragment {fragment!r}")

    ontology = {mapping["variable"]: mapping["term"] for mapping in parser["ontology_mappings"]}
    if ontology != ONTOLOGY:
        failures.append(f"ontology annotations {ontology} differ from {ONTOLOGY}")

    sections = set(parser["sections"])
    missing = [section for section in REQUIRED_SECTIONS if section not in sections]
    if missing:
        failures.append(f"document is missing the sections {missing}")
    if "Static" not in str(parser["time_specification"]):
        failures.append(f"declared time specification {parser['time_specification']!r} is not Static")

    semantic = payload["semantic"]
    if not semantic.get("is_valid"):
        failures.append(
            f"pinned semantic validator rejected the document: {semantic.get('errors')}"
        )
    for message in semantic.get("warnings", []):
        failures.append(f"semantic warning: {message}")

    consistency = payload["consistency"]
    if not consistency.get("consistent"):
        failures.append(f"pinned consistency checker reported: {consistency.get('warnings')}")

    failures.extend(_notebook_failures())

    return failures


def main(argv: list[str] | None = None) -> int:
    """Validate the committed specification against the pinned parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument(
        "--gnn-root",
        type=Path,
        help="Generalized_Notation_Notation checkout (default: $GNN_ROOT)",
    )
    sources.add_argument(
        "--gnn-runtime",
        help="interpreter with the pinned GNN distribution installed",
    )
    parser.add_argument(
        "--python",
        default=os.environ.get("GNN_PYTHON"),
        help="parser interpreter used with --gnn-root (default: $GNN_PYTHON or this interpreter)",
    )
    parser.add_argument(
        "--julia",
        default=os.environ.get("JULIA_BIN"),
        help="julia interpreter for the dependency-free spec reader (default: $JULIA_BIN)",
    )
    parser.add_argument("--spec", type=Path, default=GNN_SPEC_PATH)
    parser.add_argument("--pin", type=Path, default=GNN_PIN_PATH)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--json", action="store_true", help="print the receipt to stdout")
    args = parser.parse_args(argv)

    if args.gnn_root is None and args.gnn_runtime is None:
        args.gnn_runtime = os.environ.get("GNN_RUNTIME_PYTHON") or None
        if args.gnn_runtime is None and os.environ.get("GNN_ROOT"):
            args.gnn_root = Path(os.environ["GNN_ROOT"])

    pin = None
    payload = None
    origin = None
    julia_summary = None
    try:
        pin = load_pin(args.pin)
        if args.gnn_root is None and args.gnn_runtime is None:
            raise Unavailable(
                "supply --gnn-root/GNN_ROOT or --gnn-runtime/GNN_RUNTIME_PYTHON"
            )
        try:
            spec_text = args.spec.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise InvalidInput(f"cannot read specification {args.spec}: {exc}") from exc
        # Diagnose authored numeric rejection before a parser can turn it into
        # an untyped subprocess failure.
        declared_scalars(spec_text)
        with tempfile.TemporaryDirectory(prefix="aii-gnn-") as directory:
            workspace = Path(directory)
            output = workspace / "probe.json"
            if args.gnn_root is not None:
                source, origin = materialize_pin(args.gnn_root, pin, workspace=workspace)
                payload = run_probe(
                    args.python or sys.executable, args.spec, output, source=source
                )
            else:
                source = None
                payload = run_probe(args.gnn_runtime, args.spec, output, source=None)
                package_dir = Path(str(payload["gnn_module"])).resolve().parent
                _verify_digests(package_dir, pin, origin=args.gnn_runtime)
                origin = f"installed runtime {args.gnn_runtime} ({package_dir})"
            if args.julia:
                julia_summary = run_julia_reader(args.julia, args.spec)
            failures = conformance_failures(
                payload, pin=pin, source=source, spec_text=spec_text,
                julia_summary=julia_summary,
            )
    except InvalidInput as exc:
        failures = [f"input-error: {exc}"]
    except Unavailable as exc:
        print(f"gnn validation not run: {exc}", file=sys.stderr)
        return 2

    parser_result = payload["parser"] if payload is not None else {}
    receipt = {
        "ok": not failures,
        "spec": str(args.spec),
        "pin": pin,
        "pin_source": origin,
        "gnn_version": payload["gnn_version"] if payload is not None else None,
        "gnn_module": payload["gnn_module"] if payload is not None else None,
        "language_version": pin["language_version"] if pin is not None else None,
        "parser_language_version": parser_result.get("version"),
        "parser_success": parser_result.get("success"),
        "semantic_valid": payload["semantic"].get("is_valid") if payload is not None else None,
        "consistency_score": (
            payload["consistency"].get("consistency_score") if payload is not None else None
        ),
        "julia_reader": julia_summary,
        "failures": failures,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(receipt, sort_keys=True))
    if failures:
        print("gnn conformance failures:", file=sys.stderr)
        for message in failures:
            print(f"  {message}", file=sys.stderr)
        return 1
    if not args.json:
        reader = (
            f"and the julia reader ({julia_summary['model_name']})"
            if julia_summary is not None
            else "and no julia reader was requested"
        )
        print(
            f"gnn validation passed: {args.spec} parsed by gnn {payload['gnn_version']} "
            f"({origin}); {reader}; receipt {args.receipt}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
