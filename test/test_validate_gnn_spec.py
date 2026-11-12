"""Offline tests for the language-version check in ``scripts/validate_gnn_spec.py``.

Standard library only; no network and no GNN runtime. Run with
``python3 -m unittest discover -s test -p 'test_*.py'`` (``./run.sh gnn`` does).
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "validate_gnn_spec_under_test", ROOT / "scripts" / "validate_gnn_spec.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


vgs = _load()
PIN = json.loads((ROOT / "specs" / "gnn-pin.json").read_text(encoding="utf-8"))


class LanguageVersionTests(unittest.TestCase):
    def test_normalization(self):
        for text in ("GNN v1.1", "v1.1", "1.1", "gnn V1.1 flags"):
            self.assertEqual(vgs._normalize_language_version(text), "1.1")
        self.assertIsNone(vgs._normalize_language_version("latest"))

    def test_the_parser_version_matching_the_pin_passes(self):
        for declared in ("1.1", "GNN v1.1", "v1.1"):
            self.assertEqual(vgs.language_version_failures(PIN, declared), [])

    def test_a_different_parser_version_fails_by_name(self):
        failures = vgs.language_version_failures(PIN, "1.0")
        self.assertEqual(len(failures), 1)
        self.assertTrue(failures[0].startswith("language-version-mismatch"))
        self.assertEqual(len(vgs.language_version_failures(PIN, None)), 1)

    def test_an_unparseable_pin_value_fails(self):
        pin = dict(PIN, language_version="latest")
        self.assertIn("not parseable", vgs.language_version_failures(pin, "1.1")[0])

    def test_conformance_failures_reports_the_mismatch(self):
        payload = {
            "gnn_version": PIN["tag"].lstrip("v"),
            "gnn_module": "/nowhere/gnn/__init__.py",
            "parser": {
                "success": True,
                "errors": [],
                "warnings": [],
                "version": "2.0",
                "model_name": "x",
                "variables": [],
                "connections": [],
                "parameters": {},
                "ontology_mappings": [],
                "sections": [],
                "time_specification": "Static",
            },
            "semantic": {"is_valid": True},
            "consistency": {"consistent": True},
        }
        failures = vgs.conformance_failures(
            payload, pin=PIN, source=None, spec_text="", julia_summary=None
        )
        self.assertTrue(any(f.startswith("language-version-mismatch") for f in failures))
        payload["parser"]["version"] = "1.1"
        failures = vgs.conformance_failures(
            payload, pin=PIN, source=None, spec_text="", julia_summary=None
        )
        self.assertFalse(any(f.startswith("language-version-mismatch") for f in failures))


if __name__ == "__main__":
    unittest.main()
