"""First-run initialization keeps an existing project's instructions intact."""

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from oaff.collection import check_index
from oaff.onboarding import InitError, init_project


class OnboardingTest(unittest.TestCase):
    def test_new_project_has_usable_agent_policy_and_collection(self):
        with TemporaryDirectory() as directory:
            project = Path(directory)
            result = subprocess.run(
                [sys.executable, "-m", "oaff.cli", "init", "--project", str(project)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("created:", result.stdout)
            self.assertIn("aff/policy.md", (project / "AGENTS.md").read_text())
            self.assertIn("When to capture", (project / "aff/policy.md").read_text())
            check_index(project / "aff")

    def test_existing_agent_file_is_preserved_and_stale_index_rejected(self):
        with TemporaryDirectory() as directory:
            project = Path(directory)
            agents = project / "AGENTS.md"
            agents.write_text("# Existing team rules\n")
            first = init_project(project)
            self.assertIn("kept existing: " + str(agents), first)
            self.assertEqual(agents.read_text(), "# Existing team rules\n")
            policy = project / "aff/policy.md"
            policy.write_text("# Customized policy\n")
            second = init_project(project)
            self.assertIn("kept existing: " + str(policy), second)
            self.assertEqual(policy.read_text(), "# Customized policy\n")
            index = project / "aff/index.md"
            index.write_text("stale\n")
            with self.assertRaisesRegex(InitError, "index is stale"):
                init_project(project)
            self.assertEqual(index.read_text(), "stale\n")
            self.assertEqual(agents.read_text(), "# Existing team rules\n")


if __name__ == "__main__":
    unittest.main()
