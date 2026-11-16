"""Offline regressions for ``scripts/validate_gnn_spec.py``.

Standard library only; no network and no GNN runtime. Run with
``python3 -m unittest discover -s test -p 'test_*.py'`` (``./run.sh gnn`` does).
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

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


def git_fixture(directory: Path, source_tree: Path | None = None):
    """Create a task-owned Git archive fixture, never a repository under test."""
    repository = directory / "checkout"
    repository.mkdir()
    if source_tree is None:
        for relative in PIN["parser_files"]:
            path = repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# isolated archive fixture: {relative}\n", encoding="utf-8")
    else:
        shutil.copytree(source_tree / "src", repository / "src")
    (repository / "sentinel.txt").write_text("caller-owned\n", encoding="utf-8")
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_AUTHOR_NAME": "Archive fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "Archive fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_TERMINAL_PROMPT": "0",
    })

    def git(*arguments):
        completed = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-c", "commit.gpgsign=false",
             "-C", str(repository), *arguments],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, env=environment,
        )
        if completed.returncode:
            raise RuntimeError(f"fixture git {arguments!r} failed: {completed.stderr}")
        return completed.stdout.strip()

    git("init", "--quiet")
    git("config", "core.fsmonitor", "false")
    git("add", ".")
    git("commit", "--quiet", "-m", "task-owned archive fixture")
    pin = dict(PIN, commit=git("rev-parse", "HEAD"))
    pin["parser_files"] = {
        relative: hashlib.sha256((repository / relative).read_bytes()).hexdigest()
        for relative in PIN["parser_files"]
    }
    return repository, pin


class FixtureCase(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="aii-validator-test-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.spec = self.directory / "normal.gnn.md"
        self.spec.write_bytes(vgs.GNN_SPEC_PATH.read_bytes())
        self.pin = self.directory / "pin.json"
        self.pin.write_text(json.dumps(PIN), encoding="utf-8")
        self.receipt = self.directory / "receipt.json"
        environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        environment.update({
            "GNN_ROOT": "", "GNN_RUNTIME_PYTHON": "", "GNN_PYTHON": "", "JULIA_BIN": "",
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        })
        selection = patch.dict(os.environ, environment, clear=True)
        selection.start()
        self.addCleanup(selection.stop)

    def invoke(self, *arguments, environment=None, receipt=None, json_mode=True):
        destination = receipt or self.receipt
        argv = ["--spec", str(self.spec), "--pin", str(self.pin), "--receipt", str(destination)]
        if json_mode:
            argv.append("--json")
        argv.extend(arguments)
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, environment or {}), redirect_stdout(stdout), redirect_stderr(stderr):
            status = vgs.main(argv)
        return status, stdout.getvalue(), stderr.getvalue()

    def assert_input_failure(self, result, fragment, receipt=None):
        status, stdout, stderr = result
        self.assertEqual(status, 1)
        saved = json.loads((receipt or self.receipt).read_text(encoding="utf-8"))
        self.assertEqual(json.loads(stdout), saved)
        self.assertFalse(saved["ok"])
        self.assertTrue(any(fragment in failure for failure in saved["failures"]), saved)
        self.assertNotIn("Traceback", stderr)
        self.assertNotIn("not run", stderr)
        return saved

    def assert_unavailable(self, result, fragment, receipt=None):
        status, stdout, stderr = result
        self.assertEqual(status, 2)
        self.assertEqual(stdout, "")
        self.assertIn(fragment, stderr)
        self.assertIn("not run", stderr)
        self.assertNotIn("Traceback", stderr)
        self.assertFalse((receipt or self.receipt).exists())


class ProbeProcessTests(FixtureCase):
    def test_actual_probe_distinguishes_missing_document_from_missing_dependencies(self):
        for name, spec, expected_status, expected_kind in (
            ("document", self.directory / "missing.gnn.md", 1, "input"),
            ("dependencies", self.spec, 2, "unavailable"),
        ):
            with self.subTest(name=name):
                output = self.directory / f"{name}-probe.json"
                completed = subprocess.run(
                    [sys.executable, "-I", "-S", str(vgs.PROBE), "--spec", str(spec),
                     "--output", str(output)],
                    stdin=subprocess.DEVNULL, capture_output=True, text=True,
                )
                self.assertEqual(completed.returncode, expected_status, completed.stderr)
                payload = json.loads(completed.stdout)
                self.assertEqual(payload, json.loads(output.read_text(encoding="utf-8")))
                self.assertEqual(payload["probe_error"]["kind"], expected_kind)
                self.assertNotIn("Traceback", completed.stderr)
                if name == "document":
                    self.assertIn(str(spec), payload["probe_error"]["message"])
                else:
                    self.assertIn("gnn", payload["probe_error"]["message"])

    def test_unexpected_probe_programming_errors_escape_without_false_input_receipt(self):
        spec = importlib.util.spec_from_file_location("gnn_probe_under_test", vgs.PROBE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        output = self.directory / "unexpected-probe.json"
        stdout = io.StringIO()
        with patch.object(module, "probe", side_effect=KeyError("programming defect")):
            with redirect_stdout(stdout), self.assertRaises(KeyError):
                module.main(["--spec", str(self.spec), "--output", str(output)])
        self.assertEqual(stdout.getvalue(), "")
        self.assertFalse(output.exists())


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


class InputAndSelectionTests(FixtureCase):
    def test_invalid_pin_files_are_controlled_json_failures(self):
        cases = [
            ("missing", None), ("json", "{"), ("empty", "{}"), ("array", "[]"),
            ("files-array", json.dumps(dict(PIN, parser_files=[]))),
            ("files-empty", json.dumps(dict(PIN, parser_files={}))),
            ("commit-type", json.dumps(dict(PIN, commit=123))),
            ("commit-format", json.dumps(dict(PIN, commit="not-a-commit"))),
            ("digest-type", json.dumps(dict(PIN, parser_files={"src/gnn/a.py": []}))),
            ("digest-format", json.dumps(dict(PIN, parser_files={"src/gnn/a.py": "x"}))),
            ("path", json.dumps(dict(PIN, parser_files={"src/gnn/../a.py": "0" * 64}))),
        ]
        for key in ("repository", "tag", "commit", "language_version", "parser_files"):
            incomplete = dict(PIN)
            del incomplete[key]
            cases.append((f"missing-{key}", json.dumps(incomplete)))
        for name, text in cases:
            with self.subTest(name=name):
                bad_pin = self.directory / f"{name}.json"
                receipt = self.directory / f"{name}-receipt.json"
                if text is not None:
                    bad_pin.write_text(text, encoding="utf-8")
                saved = self.assert_input_failure(
                    self.invoke("--pin", str(bad_pin), "--gnn-runtime", "/missing/parser",
                                receipt=receipt),
                    str(bad_pin), receipt,
                )
                self.assertIsNone(saved["gnn_version"])

    def test_bad_authored_scalars_fail_before_runtime_startup(self):
        canonical = self.spec.read_text(encoding="utf-8")
        for index, token in enumerate(("banana", "NaN", "Inf", "-Inf")):
            with self.subTest(token=token):
                self.spec.write_text(
                    canonical.replace("data_mean={(-4.0)}", f"data_mean={{({token})}}"),
                    encoding="utf-8",
                )
                self.assert_input_failure(
                    self.invoke("--gnn-runtime", "/missing/parser",
                                receipt=self.directory / f"scalar-{index}.json"),
                    "data_mean", self.directory / f"scalar-{index}.json",
                )

    def test_missing_spec_is_input_failure(self):
        missing = self.directory / "missing.gnn.md"
        self.assert_input_failure(
            self.invoke("--spec", str(missing), "--gnn-runtime", "/missing/parser"),
            str(missing),
        )

    def test_explicit_bad_runtime_never_falls_back_to_environment_root(self):
        self.assert_unavailable(
            self.invoke("--gnn-runtime", "/missing/explicit-parser",
                        environment={"GNN_ROOT": "/missing/environment-root"}),
            "/missing/explicit-parser",
        )

    def test_explicit_bad_root_never_falls_back_to_environment_runtime(self):
        self.assert_unavailable(
            self.invoke("--gnn-root", "/missing/explicit-root",
                        environment={"GNN_RUNTIME_PYTHON": "/missing/environment-parser"}),
            "/missing/explicit-root",
        )

    def test_environment_runtime_precedes_environment_root(self):
        self.assert_unavailable(
            self.invoke(environment={
                "GNN_RUNTIME_PYTHON": "/missing/environment-parser",
                "GNN_ROOT": "/missing/environment-root",
            }),
            "/missing/environment-parser",
        )

    def test_root_only_environment_selects_root(self):
        self.assert_unavailable(
            self.invoke(environment={"GNN_ROOT": "/missing/environment-root"}),
            "/missing/environment-root",
        )

    def test_missing_source_is_not_run_and_writes_no_receipt(self):
        self.assert_unavailable(self.invoke(), "supply")

    def test_two_explicit_sources_are_usage_error_without_receipt(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as failure:
                vgs.main(["--gnn-root", "/missing/root", "--gnn-runtime", "/missing/parser"])
        self.assertEqual(failure.exception.code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("--gnn-root", stderr.getvalue())
        self.assertIn("--gnn-runtime", stderr.getvalue())
        self.assertFalse(self.receipt.exists())


class SubprocessDiagnosticsTests(FixtureCase):
    def test_startup_errors_are_unavailable(self):
        for failure in (FileNotFoundError("missing"), PermissionError("denied")):
            with self.subTest(failure=type(failure).__name__):
                with patch.object(vgs.subprocess, "run", side_effect=failure):
                    with self.assertRaises(vgs.Unavailable) as raised:
                        vgs._run(["/explicit/parser"])
                self.assertIn("/explicit/parser", str(raised.exception))

    def test_probe_expected_errors_keep_their_domains(self):
        output = self.directory / "probe.json"
        for kind, status, exception in (
            ("input", 1, vgs.InvalidInput), ("unavailable", 2, vgs.Unavailable),
        ):
            with self.subTest(kind=kind):
                output.write_text(json.dumps({
                    "probe_error": {"kind": kind, "message": "seed in authored.gnn.md"},
                }), encoding="utf-8")
                with patch.object(vgs, "_run", return_value=subprocess.CompletedProcess([], status, "", "")):
                    with self.assertRaises(exception) as failure:
                        vgs.run_probe("python", self.spec, output, source=None)
                self.assertIn("seed in authored.gnn.md", str(failure.exception))

    def test_unexpected_probe_errors_are_not_disguised_as_bad_input_or_missing_runtime(self):
        output = self.directory / "probe.json"
        cases = [
            ("{", 0),
            ("[]", 0),
            (json.dumps({"probe_error": {"kind": "input", "message": "wrong status"}}), 2),
            (json.dumps({"probe_error": {"kind": "unknown", "message": "bug"}}), 1),
            (json.dumps({"probe_error": {"kind": "input", "message": []}}), 1),
            ("{}", 1),
        ]
        for text, status in cases:
            with self.subTest(text=text, status=status):
                output.write_text(text, encoding="utf-8")
                with patch.object(vgs, "_run", return_value=subprocess.CompletedProcess(
                    [], status, "", "unexpected programming failure",
                )):
                    with self.assertRaises(RuntimeError) as failure:
                        vgs.run_probe("python", self.spec, output, source=None)
                self.assertNotIsInstance(failure.exception, vgs.Unavailable)

    def test_missing_probe_payload_is_programming_failure(self):
        with patch.object(vgs, "_run", return_value=subprocess.CompletedProcess([], 1, "", "bug")):
            with self.assertRaises(RuntimeError) as failure:
                vgs.run_probe("python", self.spec, self.directory / "absent.json", source=None)
        self.assertNotIsInstance(failure.exception, vgs.Unavailable)

    def test_julia_input_marker_is_distinct_from_unexpected_failure(self):
        rejection = subprocess.CompletedProcess(
            [], 1, "", vgs.READER_INPUT_PREFIX + "seed in authored.gnn.md: 1234.4\n",
        )
        with patch.object(vgs.shutil, "which", return_value="/existing/julia"):
            with patch.object(vgs, "_run", return_value=rejection):
                with self.assertRaises(vgs.InvalidInput) as failure:
                    vgs.run_julia_reader("julia", self.spec)
            self.assertIn("seed", str(failure.exception))
            for completed in (
                subprocess.CompletedProcess([], 1, "", "unexpected Julia bug"),
                subprocess.CompletedProcess([], 0, "", ""),
            ):
                with patch.object(vgs, "_run", return_value=completed):
                    with self.assertRaises(RuntimeError) as failure:
                        vgs.run_julia_reader("julia", self.spec)
                self.assertNotIsInstance(failure.exception, vgs.Unavailable)

    def test_missing_julia_executable_is_unavailable(self):
        with self.assertRaises(vgs.Unavailable) as failure:
            vgs.run_julia_reader(str(self.directory / "missing-julia"), self.spec)
        self.assertIn("missing-julia", str(failure.exception))


@unittest.skipUnless(shutil.which("git"), "archive regressions require existing Git")
class ArchiveLifetimeTests(FixtureCase):
    def test_main_cleans_owned_archive_on_each_failure_and_preserves_checkout(self):
        repository, pin = git_fixture(self.directory)
        self.pin.write_text(json.dumps(pin), encoding="utf-8")
        caller_bytes = {
            path.relative_to(repository): path.read_bytes()
            for path in repository.rglob("*") if path.is_file() and ".git" not in path.parts
        }
        owned = self.directory / "owned"
        owned.mkdir()
        real_temporary_directory = tempfile.TemporaryDirectory
        real_run = vgs._run

        def workspace(*args, **kwargs):
            return real_temporary_directory(*args, dir=owned, **kwargs)

        def archive_failure(argv, **kwargs):
            if "archive" in argv:
                return subprocess.CompletedProcess(argv, 1, "", "injected archive failure")
            return real_run(argv, **kwargs)

        faults = (
            ("archive", patch.object(vgs, "_run", side_effect=archive_failure), 2),
            ("extract", patch.object(vgs.tarfile, "open", side_effect=tarfile.ReadError("bad tar")), 2),
            ("probe-input", patch.object(vgs, "run_probe", side_effect=vgs.InvalidInput("authored seed")), 1),
            ("probe-unavailable", patch.object(vgs, "run_probe", side_effect=vgs.Unavailable("dependency")), 2),
            ("probe-bug", patch.object(vgs, "run_probe", side_effect=KeyError("programming bug")), None),
        )
        for name, fault, expected_status in faults:
            with self.subTest(fault=name):
                receipt = self.directory / f"{name}.json"
                with patch.object(vgs.tempfile, "TemporaryDirectory", side_effect=workspace), fault:
                    if expected_status is None:
                        with self.assertRaises(KeyError):
                            self.invoke("--gnn-root", str(repository), receipt=receipt)
                        self.assertFalse(receipt.exists())
                    else:
                        result = self.invoke("--gnn-root", str(repository), receipt=receipt)
                        if expected_status == 1:
                            self.assert_input_failure(result, "authored seed", receipt)
                        else:
                            self.assert_unavailable(result, "not run", receipt)
                self.assertEqual(list(owned.iterdir()), [])
                self.assertEqual({
                    relative: (repository / relative).read_bytes() for relative in caller_bytes
                }, caller_bytes)

    def test_post_extraction_digest_failure_cleans_owned_workspace(self):
        repository, pin = git_fixture(self.directory)
        pin["parser_files"][next(iter(pin["parser_files"]))] = "0" * 64
        self.pin.write_text(json.dumps(pin), encoding="utf-8")
        owned = self.directory / "owned"
        owned.mkdir()
        real_temporary_directory = tempfile.TemporaryDirectory
        with patch.object(vgs.tempfile, "TemporaryDirectory", side_effect=lambda *a, **k:
                          real_temporary_directory(*a, dir=owned, **k)):
            self.assert_unavailable(
                self.invoke("--gnn-root", str(repository)), "digest mismatch",
            )
        self.assertEqual(list(owned.iterdir()), [])
        self.assertEqual((repository / "sentinel.txt").read_text(), "caller-owned\n")


if __name__ == "__main__":
    unittest.main()
