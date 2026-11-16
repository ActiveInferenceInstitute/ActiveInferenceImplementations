"""Actual pinned-runtime acceptance, never provisioned by these tests.

Enable with GNN_RUNTIME_PYTHON pointing at the already-qualified installed pin.
JULIA_BIN selects existing Julia, otherwise the existing PATH Julia is used.
Without explicit parser-runtime admission these cases report a skip, not proof.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_validate_gnn_spec import FixtureCase, PIN, ROOT, git_fixture, vgs

RUNTIME = os.environ.get("GNN_RUNTIME_PYTHON")
JULIA = os.environ.get("JULIA_BIN") or shutil.which("julia")


def manifest(root: Path):
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


@unittest.skipUnless(RUNTIME, "set GNN_RUNTIME_PYTHON to admit existing pinned-runtime acceptance")
class PinnedRuntimeTests(FixtureCase):
    @classmethod
    def setUpClass(cls):
        if not JULIA:
            raise RuntimeError("actual-reader acceptance requires existing Julia or JULIA_BIN")
        temporary = tempfile.TemporaryDirectory(prefix="aii-parser-fixture-")
        cls.addClassCleanup(temporary.cleanup)
        cls.source_tree = Path(temporary.name) / "caller-tree"
        completed = subprocess.run(
            [RUNTIME, "-B", "-c",
             "import importlib.util; print(importlib.util.find_spec('gnn').origin)"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30,
        )
        if completed.returncode:
            raise RuntimeError(f"existing GNN runtime cannot locate its package: {completed.stderr}")
        package = Path(completed.stdout.strip()).parent
        destination = cls.source_tree / "src" / "gnn"
        destination.parent.mkdir(parents=True)
        shutil.copytree(
            package, destination,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"),
        )
        (cls.source_tree / "sentinel.txt").write_text("caller-owned\n", encoding="utf-8")
        cls.caller_manifest = manifest(cls.source_tree)

    def setUp(self):
        super().setUp()
        self.scratch = self.directory / "scratch"
        self.scratch.mkdir()
        self.sequence = 0

    def cli(self, *arguments, environment=None, json_mode=True):
        self.sequence += 1
        receipt = self.directory / f"runtime-receipt-{self.sequence}.json"
        argv = [sys.executable, "-B", str(ROOT / "scripts" / "validate_gnn_spec.py"),
                "--pin", str(self.pin), "--spec", str(self.spec), "--receipt", str(receipt)]
        if json_mode:
            argv.append("--json")
        argv.extend(arguments)
        selected = dict(os.environ)
        selected.update({"PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(self.scratch)})
        selected.update(environment or {})
        completed = subprocess.run(
            argv, cwd=ROOT, env=selected, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(
            [path.name for path in self.scratch.iterdir() if path.name.startswith("aii-gnn")],
            [], "validator-owned archive/workspace survived process completion",
        )
        return completed, receipt

    def success(self, result):
        completed, receipt = result
        self.assertEqual(completed.returncode, 0, completed.stderr)
        saved = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(completed.stdout), saved)
        self.assertTrue(saved["ok"])
        self.assertEqual(saved["failures"], [])
        self.assertEqual(saved["pin"], json.loads(self.pin.read_text(encoding="utf-8")))
        self.assertEqual(saved["gnn_version"], PIN["tag"].lstrip("v"))
        self.assertNotIn("Traceback", completed.stderr)
        return saved

    def input_failure(self, result, field):
        completed, receipt = result
        return self.assert_input_failure(
            (completed.returncode, completed.stdout, completed.stderr), field, receipt,
        )

    def unavailable(self, result, field):
        completed, receipt = result
        self.assert_unavailable(
            (completed.returncode, completed.stdout, completed.stderr), field, receipt,
        )

    def test_explicit_runtime_beats_inherited_root_and_has_single_json_receipt(self):
        saved = self.success(self.cli(
            "--gnn-runtime", RUNTIME, "--julia", JULIA,
            environment={"GNN_ROOT": "/nonexistent/inherited-checkout"},
        ))
        self.assertTrue(saved["pin_source"].startswith("installed runtime "))
        self.assertEqual(saved["julia_reader"]["seed"], "1234")

    def test_explicit_root_beats_inherited_runtime(self):
        saved = self.success(self.cli(
            "--gnn-root", str(self.source_tree), "--python", RUNTIME, "--julia", JULIA,
            environment={"GNN_RUNTIME_PYTHON": "/nonexistent/inherited-parser"},
        ))
        self.assertIn(str(self.source_tree), saved["pin_source"])
        self.assertTrue(Path(saved["gnn_module"]).is_relative_to(self.source_tree))

    def test_environment_only_runtime_precedes_root_and_root_only_works(self):
        saved = self.success(self.cli("--julia", JULIA, environment={
            "GNN_RUNTIME_PYTHON": RUNTIME, "GNN_ROOT": str(self.source_tree),
        }))
        self.assertTrue(saved["pin_source"].startswith("installed runtime "))
        saved = self.success(self.cli("--julia", JULIA, environment={
            "GNN_ROOT": str(self.source_tree), "GNN_PYTHON": RUNTIME,
        }))
        self.assertTrue(Path(saved["gnn_module"]).is_relative_to(self.source_tree))

    def test_invalid_explicit_source_does_not_use_valid_inherited_alternative(self):
        self.unavailable(self.cli(
            "--gnn-runtime", "/nonexistent/explicit-parser",
            environment={"GNN_ROOT": str(self.source_tree), "GNN_PYTHON": RUNTIME},
        ), "/nonexistent/explicit-parser")
        self.unavailable(self.cli(
            "--gnn-root", "/nonexistent/explicit-root",
            environment={"GNN_RUNTIME_PYTHON": RUNTIME},
        ), "/nonexistent/explicit-root")

    def test_two_explicit_sources_are_usage_error_before_receipt(self):
        completed, receipt = self.cli(
            "--gnn-runtime", RUNTIME, "--gnn-root", str(self.source_tree),
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("--gnn-root", completed.stderr)
        self.assertIn("--gnn-runtime", completed.stderr)
        self.assertFalse(receipt.exists())

    def test_conformance_failure_stdout_is_one_document_equal_to_receipt(self):
        self.spec.write_text(
            self.spec.read_text(encoding="utf-8").replace(
                "m_prior_mean={(0.0)}", "m_prior_mean={(1.0)}",
            ), encoding="utf-8",
        )
        self.input_failure(self.cli("--gnn-runtime", RUNTIME, "--julia", JULIA), "m_prior_mean")

    def test_non_json_success_keeps_readable_output_and_valid_receipt(self):
        completed, receipt = self.cli("--gnn-runtime", RUNTIME, json_mode=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(str(self.spec), completed.stdout)
        self.assertIn(str(receipt), completed.stdout)
        self.assertIn(PIN["tag"].lstrip("v"), completed.stdout)
        self.assertTrue(json.loads(receipt.read_text(encoding="utf-8"))["ok"])

    def test_caller_owned_tree_survives_success_and_conformance_failure(self):
        self.success(self.cli("--gnn-root", str(self.source_tree), "--python", RUNTIME))
        self.spec.write_text(
            self.spec.read_text(encoding="utf-8").replace(
                "m_prior_mean={(0.0)}", "m_prior_mean={(1.0)}",
            ), encoding="utf-8",
        )
        self.input_failure(self.cli(
            "--gnn-root", str(self.source_tree), "--python", RUNTIME,
        ), "m_prior_mean")
        self.assertEqual(manifest(self.source_tree), self.caller_manifest)
        self.assertEqual((self.source_tree / "sentinel.txt").read_text(), "caller-owned\n")

    def test_actual_reader_rejection_is_conformance_failure_not_not_run(self):
        self.spec.write_text(
            self.spec.read_text(encoding="utf-8").replace("seed={(1234)}", "seed={(1234.4)}"),
            encoding="utf-8",
        )
        with self.assertRaises(vgs.InvalidInput) as failure:
            vgs.run_julia_reader(JULIA, self.spec)
        self.assertIn("seed", str(failure.exception))
        self.assertIn("1234.4", str(failure.exception))
        self.assertIn(str(self.spec), str(failure.exception))
        self.input_failure(self.cli("--gnn-runtime", RUNTIME, "--julia", JULIA), "seed")

    def test_missing_requested_julia_is_unavailable_and_has_no_false_receipt(self):
        self.unavailable(self.cli(
            "--gnn-runtime", RUNTIME, "--julia", str(self.directory / "missing-julia"),
        ), "missing-julia")

    def test_nonnumeric_authored_value_is_controlled_with_real_runtime_selected(self):
        self.spec.write_text(
            self.spec.read_text(encoding="utf-8").replace(
                "data_mean={(-4.0)}", "data_mean={(banana)}",
            ), encoding="utf-8",
        )
        self.input_failure(self.cli("--gnn-runtime", RUNTIME, "--julia", JULIA), "data_mean")

    @unittest.skipUnless(shutil.which("git"), "actual archive acceptance requires existing Git")
    def test_real_git_archive_lifetime_on_success_digest_reader_and_conformance_failures(self):
        repository, pin = git_fixture(self.directory, self.source_tree)
        self.assertEqual(pin["parser_files"], PIN["parser_files"])
        self.pin.write_text(json.dumps(pin), encoding="utf-8")
        # A live-tree tripwire establishes that only the committed package runs.
        (repository / "src" / "gnn" / "__init__.py").write_text(
            "raise RuntimeError('live working tree must not be imported')\n", encoding="utf-8",
        )
        caller_manifest = manifest(repository)
        source_arguments = ("--gnn-root", str(repository), "--python", RUNTIME, "--julia", JULIA)
        canonical = self.spec.read_text(encoding="utf-8")

        saved = self.success(self.cli(*source_arguments))
        self.assertIn(pin["commit"], saved["pin_source"])
        self.assertFalse(Path(saved["gnn_module"]).exists())
        self.assertEqual(manifest(repository), caller_manifest)

        self.spec.write_text(
            canonical.replace("seed={(1234)}", "seed={(1234.4)}"), encoding="utf-8",
        )
        self.input_failure(self.cli(*source_arguments), "seed")
        self.assertEqual(manifest(repository), caller_manifest)

        self.spec.write_text(
            canonical.replace("m_prior_mean={(0.0)}", "m_prior_mean={(1.0)}"), encoding="utf-8",
        )
        self.input_failure(self.cli(*source_arguments), "m_prior_mean")
        self.assertEqual(manifest(repository), caller_manifest)

        self.spec.write_text(canonical, encoding="utf-8")
        self.unavailable(self.cli(
            "--gnn-root", str(repository), "--python", "/nonexistent/parser-after-extraction",
        ), "/nonexistent/parser-after-extraction")
        self.assertEqual(manifest(repository), caller_manifest)

        bad_pin = dict(pin, parser_files=dict(pin["parser_files"]))
        bad_pin["parser_files"][next(iter(bad_pin["parser_files"]))] = "0" * 64
        self.pin.write_text(json.dumps(bad_pin), encoding="utf-8")
        self.unavailable(self.cli(*source_arguments), "digest mismatch")
        self.assertEqual(manifest(repository), caller_manifest)

        self.pin.write_text(json.dumps(dict(pin, commit="f" * 40)), encoding="utf-8")
        self.unavailable(self.cli(*source_arguments), "not present")
        self.assertEqual(manifest(repository), caller_manifest)

    def test_missing_or_mismatched_pinned_package_files_remain_unavailable(self):
        owned_tree = self.directory / "damaged-tree"
        shutil.copytree(self.source_tree, owned_tree)
        parser_file = owned_tree / next(iter(PIN["parser_files"]))
        parser_file.unlink()
        self.unavailable(self.cli(
            "--gnn-root", str(owned_tree), "--python", RUNTIME,
        ), "missing")
        original = self.source_tree / next(iter(PIN["parser_files"]))
        parser_file.write_bytes(original.read_bytes() + b"\n# digest drift\n")
        self.unavailable(self.cli(
            "--gnn-root", str(owned_tree), "--python", RUNTIME,
        ), "digest mismatch")
        self.assertEqual(manifest(self.source_tree), self.caller_manifest)


if __name__ == "__main__":
    unittest.main()
