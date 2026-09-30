import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import rfc8785

from oaff import verify_bytes, verify_files


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text())


def seal(document: dict) -> bytes:
    document["integrity"]["digest"] = hashlib.sha256(
        rfc8785.dumps({key: value for key, value in document.items() if key != "integrity"})
    ).hexdigest()
    return json.dumps(document).encode()


class VerifierTest(unittest.TestCase):
    def test_new_and_legacy_extensions_have_identical_verification(self):
        package = (FIXTURES / "valid/candidate-valid.aff").read_bytes()
        with TemporaryDirectory() as directory:
            preferred = Path(directory) / "finding.aff"
            legacy = Path(directory) / "finding.oaff.json"
            preferred.write_bytes(package)
            legacy.write_bytes(package)
            reports = verify_files([preferred, legacy])
        self.assertEqual(len(reports), 2)
        for report in reports:
            self.assertEqual(report["integrity"], "pass")
            self.assertNotEqual(report["status"], "invalid")
        self.assertEqual(
            [{key: value for key, value in report.items() if key != "path"} for report in reports[:1]],
            [{key: value for key, value in report.items() if key != "path"} for report in reports[1:]],
        )

    def test_all_contract_fixtures(self):
        for relative in MANIFEST["valid"]:
            with self.subTest(relative=relative):
                report = verify_bytes((FIXTURES / relative).read_bytes())
                self.assertNotEqual(report["status"], "invalid")
                self.assertEqual(report["integrity"], "pass")
                self.assertEqual(report["local_authority"], "not_evaluated")
        for relative, expected in MANIFEST["invalid"].items():
            with self.subTest(relative=relative):
                report = verify_bytes((FIXTURES / relative).read_bytes())
                self.assertEqual(report["status"], "invalid")
                self.assertEqual(report["diagnostics"][0]["code"], expected)

    def test_caller_supplied_evidence_bytes(self):
        candidate = (FIXTURES / "valid/candidate-valid.aff").read_bytes()
        source = b"synthetic run 42: retry with the same key"
        passing = verify_bytes(candidate, {"run-42": source})
        self.assertEqual(passing["status"], "valid")
        self.assertEqual(passing["evidence"][0]["check"], "pass")
        failing = verify_bytes(candidate, {"run-42": b"changed"})
        self.assertEqual(failing["diagnostics"][0]["code"], "evidence_mismatch")

    def test_successful_and_failed_run_findings_share_the_same_contract(self):
        for outcome in ("successful", "failed"):
            with self.subTest(outcome=outcome):
                package = (
                    FIXTURES / f"valid/{outcome}-run-finding-valid.aff"
                ).read_bytes()
                source = (FIXTURES / f"sources/{outcome}-run.txt").read_bytes()
                report = verify_bytes(package, {f"run-{outcome}-1": source})
                self.assertEqual(report["status"], "valid")
                self.assertEqual(report["integrity"], "pass")
                self.assertEqual(report["evidence"][0]["check"], "pass")
                self.assertEqual(report["local_authority"], "not_evaluated")

    def test_receipts_do_not_inherit_authority(self):
        admitted = (FIXTURES / "valid/admitted-valid.aff").read_bytes()
        report = verify_bytes(admitted)
        self.assertEqual(report["receipt_counts"]["adoption_decision"], 1)
        self.assertEqual(report["local_authority"], "not_evaluated")
        self.assertEqual(report["status"], "valid_with_limits")

    def test_same_revision_with_new_receipts_is_valid(self):
        paths = [
            FIXTURES / "valid/candidate-valid.aff",
            FIXTURES / "valid/admitted-valid.aff",
            FIXTURES / "valid/withdrawn-valid.aff",
        ]
        reports = verify_files(paths)
        self.assertTrue(all(report["status"] != "invalid" for report in reports))

    def test_conflicting_revision_is_rejected_even_with_matching_digest(self):
        original = json.loads(
            (FIXTURES / "valid/candidate-valid.aff").read_text()
        )
        changed = copy.deepcopy(original)
        changed["finding"]["statement"] = "Different statement under the same revision URI."
        with TemporaryDirectory() as directory:
            path = Path(directory) / "conflict.aff"
            path.write_bytes(seal(changed))
            reports = verify_files(
                [FIXTURES / "valid/candidate-valid.aff", path]
            )
        self.assertTrue(all(report["status"] == "invalid" for report in reports))
        self.assertTrue(
            all(
                any(item["code"] == "invalid_binding" for item in report["diagnostics"])
                for report in reports
            )
        )

    def test_unresolved_link_is_a_limit_and_resolved_revision_is_valid(self):
        revision = FIXTURES / "valid/revision-valid.aff"
        alone = verify_files([revision])[0]
        self.assertEqual(alone["status"], "valid_with_limits")
        self.assertIn(
            "unresolved_link", [item["code"] for item in alone["diagnostics"]]
        )
        together = verify_files(
            [FIXTURES / "valid/candidate-valid.aff", revision]
        )
        self.assertTrue(
            all(
                not any(item["code"] == "unresolved_link" for item in report["diagnostics"])
                for report in together
            )
        )

    def test_cli_exit_codes_and_machine_output(self):
        candidate = FIXTURES / "valid/candidate-valid.aff"
        tampered = FIXTURES / "invalid/tampered-statement.aff"
        good = subprocess.run(
            [sys.executable, "-m", "oaff.cli", "verify", str(candidate), "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(good.returncode, 0)
        self.assertEqual(json.loads(good.stdout)[0]["status"], "valid_with_limits")
        bad = subprocess.run(
            [sys.executable, "-m", "oaff.cli", "verify", str(tampered), "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(
            json.loads(bad.stdout)[0]["diagnostics"][0]["code"], "invalid_binding"
        )
        usage = subprocess.run(
            [sys.executable, "-m", "oaff.cli", "verify"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(usage.returncode, 2)


if __name__ == "__main__":
    unittest.main()
