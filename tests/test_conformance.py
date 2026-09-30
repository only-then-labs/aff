import subprocess
import sys
import unittest
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "fixtures/manifest.json").read_text())


class ConformanceRunnerTests(unittest.TestCase):
    def test_reference_cli_passes_public_corpus(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/conformance.py"), "--",
             sys.executable, "-m", "oaff.cli", "verify", "{file}", "--json"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        count = len(MANIFEST["valid"]) + len(MANIFEST["invalid"])
        self.assertIn(f"{count}/{count} conformance cases passed", completed.stdout)

    def test_missing_placeholder_is_usage_error(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/conformance.py"), "--", "true"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("{file}", completed.stderr)


if __name__ == "__main__":
    unittest.main()
