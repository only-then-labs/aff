import hashlib
import json
import unittest
from pathlib import Path

import rfc8785

from oaff.interop import okf_view

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class OKFViewTests(unittest.TestCase):
    def test_success_and_failure_use_the_same_limited_view(self):
        for outcome in ("successful", "failed"):
            with self.subTest(outcome=outcome):
                source = FIXTURES / f"valid/{outcome}-run-finding-valid.aff"
                markdown, loss = okf_view(source.read_bytes())
                frontmatter = json.loads(markdown.split("---\n", 2)[1])
                self.assertEqual(frontmatter["type"], "Finding")
                self.assertEqual(frontmatter["status"], "draft")
                self.assertEqual(len(frontmatter["sources"]), 1)
                self.assertNotIn("verified", frontmatter)
                self.assertNotIn("generated", frontmatter)
                self.assertFalse(loss["round_trip"])
                self.assertEqual(loss["local_authority"], "none")
                self.assertIn(json.loads(source.read_bytes())["finding"]["statement"], markdown)

    def test_foreign_admission_and_withdrawal_never_turn_into_okf_verification(self):
        for name in ("admitted-valid", "withdrawn-valid"):
            with self.subTest(name=name):
                markdown, loss = okf_view(
                    (FIXTURES / f"valid/{name}.aff").read_bytes()
                )
                frontmatter = json.loads(markdown.split("---\n", 2)[1])
                self.assertEqual(frontmatter["status"], "draft")
                self.assertNotIn("verified", frontmatter)
                self.assertIn("AFF receipts cannot become OKF verified", loss["losses"][4])

    def test_invalid_package_cannot_be_rendered(self):
        with self.assertRaises(ValueError):
            okf_view((FIXTURES / "invalid/tampered-statement.aff").read_bytes())

    def test_non_web_source_uri_is_reported_as_omitted(self):
        package = json.loads((FIXTURES / "valid/candidate-valid.aff").read_bytes())
        package["finding"]["evidence"][0]["source_uri"] = "urn:example:local-run"
        unsigned = {key: value for key, value in package.items() if key != "integrity"}
        package["integrity"]["digest"] = hashlib.sha256(rfc8785.dumps(unsigned)).hexdigest()
        markdown, loss = okf_view(json.dumps(package).encode())
        frontmatter = json.loads(markdown.split("---\n", 2)[1])
        self.assertNotIn("sources", frontmatter)
        self.assertTrue(any("omitted" in entry for entry in loss["losses"]))


if __name__ == "__main__":
    unittest.main()
