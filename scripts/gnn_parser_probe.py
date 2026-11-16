"""Extract one GNN document with the pinned upstream parser and print JSON.

This module is the only place that imports the upstream ``gnn`` package. It is
executed as a subprocess by ``scripts/validate_gnn_spec.py`` with the pinned
source tree first on ``PYTHONPATH``, so the parser that runs is always the
revision recorded in ``specs/gnn-pin.json`` and never a live checkout.

Usage (normally invoked by the validator, not by hand):

    PYTHONPATH=<pinned>/src python3 scripts/gnn_parser_probe.py --spec <file>

The probe mirrors the probe of the same name in ActInf_RxInfer, the fleet
reference implementation for pinned GNN validation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class DocumentError(ValueError):
    """An explicit document-read or parser-declared rejection."""


class RuntimeUnavailable(RuntimeError):
    """The GNN parser or an import dependency is unavailable."""


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def probe(spec: Path) -> dict[str, Any]:
    """Parse and validate ``spec`` with the imported (pinned) parser."""

    try:
        text = spec.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise DocumentError(f"cannot read specification {spec}: {exc}") from exc
    try:
        from gnn import __version__ as gnn_version
        from gnn.parsers.markdown_parser import MarkdownGNNParser
        from gnn.validation.consistency_checker import check_consistency
        from gnn.validation.orientation import check_b_orientation
        from gnn.validation.semantic_validator import SemanticValidator
    except ImportError as exc:
        raise RuntimeUnavailable(f"cannot import the GNN parser dependencies: {exc}") from exc

    parser = MarkdownGNNParser()
    result = parser.parse_file(str(spec))
    if not result.success:
        errors = "; ".join(str(error) for error in result.errors) or "no parser diagnostic"
        raise DocumentError(f"pinned parser rejected {spec}: {errors}")
    model = result.model
    semantic = SemanticValidator().validate(text)
    orientation = check_b_orientation(spec)
    consistency = check_consistency(spec)
    return {
        "gnn_version": gnn_version,
        "gnn_module": __import__("gnn").__file__,
        "parser": {
            "success": bool(result.success),
            "errors": list(result.errors),
            "warnings": list(result.warnings),
            "model_name": model.model_name,
            "version": model.version,
            "variables": [
                {
                    "name": variable.name,
                    "dimensions": list(variable.dimensions),
                    "data_type": str(variable.data_type),
                }
                for variable in model.variables
            ],
            "connections": [
                {
                    "sources": list(connection.source_variables),
                    "targets": list(connection.target_variables),
                    "type": str(connection.connection_type),
                }
                for connection in model.connections
            ],
            "ontology_mappings": [
                {"variable": mapping.variable_name, "term": mapping.ontology_term}
                for mapping in model.ontology_mappings
            ],
            "parameters": {
                parameter.name: _jsonable(parameter.value) for parameter in model.parameters
            },
            "sections": sorted(model.raw_sections),
            "time_specification": _jsonable(model.time_specification),
        },
        "semantic": _jsonable(semantic),
        "orientation": _jsonable(orientation),
        "consistency": _jsonable(consistency),
    }


def main(argv: list[str] | None = None) -> int:
    """Parse one specification and print the JSON payload."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    status = 0
    try:
        payload = probe(args.spec)
    except DocumentError as exc:
        payload = {"probe_error": {"kind": "input", "message": str(exc)}}
        status = 1
    except RuntimeUnavailable as exc:
        payload = {"probe_error": {"kind": "unavailable", "message": str(exc)}}
        status = 2
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
