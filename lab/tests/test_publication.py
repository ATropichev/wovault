"""Regression checks use disposable directories, with no Docker or cloud access."""
import copy
import importlib.util
import json
import io
import contextlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

LAB = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lab_runner", LAB / "tools/run_checks.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wovault-publication-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.publish = self.root / "lab/evidence/runs"
        self.publish.parent.mkdir(parents=True)
        self.outside = Path(self.temp.name) / "unrelated"
        self.outside.mkdir()
        self.sentinel = self.outside / "preserve.txt"
        self.sentinel.write_text("synthetic unrelated data")
        for key, value in (("REPO_ROOT", self.root), ("PUBLISH_DIR", self.publish)):
            p = patch.object(runner, key, value)
            p.start()
            self.addCleanup(p.stop)

    def test_publication_root_symlink_is_refused_before_writing(self):
        self.publish.symlink_to(self.outside, target_is_directory=True)
        with self.assertRaises(runner.labctl.Refused):
            runner.Artifacts(self.publish / "new-run")
        self.assertEqual(self.sentinel.read_text(), "synthetic unrelated data")
        self.assertFalse((self.outside / "new-run").exists())

    def test_publication_ancestor_symlink_is_refused(self):
        self.publish.parent.rmdir()
        self.publish.parent.symlink_to(self.outside, target_is_directory=True)
        with self.assertRaises(runner.labctl.Refused):
            runner.resolve_publish(self.publish / "new-run")

    def test_artifact_leaf_symlink_and_traversal_are_refused(self):
        artifacts = runner.Artifacts(self.publish / "new-run")
        (artifacts.dest_dir / "redirect").symlink_to(self.sentinel)
        for name in ("redirect", "../../../outside.txt", str(self.sentinel)):
            with self.subTest(name=name), self.assertRaises(runner.labctl.Refused):
                artifacts.save(name, "must not overwrite")
        self.assertEqual(self.sentinel.read_text(), "synthetic unrelated data")

    def test_owned_artifact_can_be_published(self):
        artifacts = runner.Artifacts(self.publish / "new-run")
        saved = artifacts.save("nested/log.txt", "synthetic log")
        self.assertEqual((self.root / saved["path"]).read_text(), "synthetic log")

    def test_reused_workspace_with_redirected_group_is_preserved_and_refused(self):
        workspace = self.root / "lab-output/reused"
        workspace.mkdir(parents=True)
        (workspace / "targets").symlink_to(self.outside, target_is_directory=True)
        resources = self.root / "lab/resources.json"
        resources.write_text(json.dumps({"filesystem": {
            "owned_path_prefixes": ["lab-output/"]}}))
        with patch.object(runner.labctl, "REPO_ROOT", self.root), \
                patch.object(runner.labctl, "RESOURCES_PATH", resources), \
                patch.dict(runner.GROUPS, {"targets": unittest.mock.Mock()}), \
                contextlib.redirect_stderr(io.StringIO()):
            result = runner.main(["targets", "--workdir", str(workspace)])
            runner.GROUPS["targets"].assert_not_called()
        self.assertEqual(result, 3)
        self.assertTrue((workspace / "targets").is_symlink())
        self.assertEqual(self.sentinel.read_text(), "synthetic unrelated data")

    def test_error_report_json_scrubs_nested_paths_before_serialization(self):
        report = {"report_id": "synthetic-error", "scenarios": [{
            "blocker": f'OSError: {self.root}/a"quoted/path',
            "actual": {"summary": f"home={Path.home()}/private"}}],
            "notes": [str(self.root)]}
        artifacts = runner.Artifacts(self.publish / report["report_id"])
        # This unit test covers serialization. Full report validation is
        # exercised separately by the retained examples and protocol runner.
        with patch.object(runner.evidence_validate, "validate",
                          return_value=SimpleNamespace(errors=[])), \
                patch.object(runner.evidence_validate, "load_json", return_value={}):
            path, valid = runner.finalize(report, artifacts, self.publish)
        self.assertTrue(valid)
        serialized = path.read_text()
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn(str(Path.home()), serialized)
        parsed = json.loads(serialized)
        self.assertIn('<repo>/a"quoted/path', parsed["scenarios"][0]["blocker"])
        self.assertIn("<home>/private", parsed["scenarios"][0]["actual"]["summary"])


class MalformedReportTests(unittest.TestCase):
    def test_schema_and_validator_reject_empty_inline_evidence(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("optional jsonschema cross-check is unavailable")
        schema = json.loads((LAB / "evidence/report.schema.json").read_text())
        original = json.loads((LAB / "evidence/examples/valid-report.json").read_text())
        targets = json.loads((LAB / "targets.json").read_text())
        for evidence in ({"kind": "stdout"}, {"kind": "stdout", "note": "  "},
                         {"kind": "command", "note": "  "}):
            report = copy.deepcopy(original)
            report["scenarios"][0]["evidence"] = [evidence]
            with self.subTest(evidence=evidence):
                self.assertTrue(list(Draft202012Validator(schema).iter_errors(report)))
                self.assertTrue(runner.evidence_validate.validate(report, targets).errors)

    def test_field_type_mutations_return_errors_without_exceptions(self):
        validator = runner.evidence_validate
        original = json.loads((LAB / "evidence/examples/valid-report.json").read_text())
        targets = json.loads((LAB / "targets.json").read_text())
        paths = []

        def visit(value, path):
            if path:
                paths.append(path)
            if isinstance(value, dict):
                for key, child in value.items():
                    visit(child, path + (key,))
            elif isinstance(value, list):
                for i, child in enumerate(value):
                    visit(child, path + (i,))

        visit(original, ())
        count = 0
        for path in paths:
            for value in (None, True, 0, 1.5, "", {}, [], ["unexpected"], {"x": 1}):
                mutated = copy.deepcopy(original)
                parent = mutated
                for part in path[:-1]:
                    parent = parent[part]
                parent[path[-1]] = copy.deepcopy(value)
                with self.subTest(path=path, value=value):
                    result = validator.validate(mutated, targets)
                    self.assertIsInstance(result.errors, list)
                count += 1
        self.assertGreater(count, 500)


if __name__ == "__main__":
    unittest.main()
