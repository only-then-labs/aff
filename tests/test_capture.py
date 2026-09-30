"""Capture existing notes as proposed Findings, without copying private content."""

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from oaff.capture import CaptureError, capture_source
from oaff.collection import add_package, check_index
from oaff.verify import verify_bytes


class CaptureTest(unittest.TestCase):
    def test_failed_postmortem_to_git_collection(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "postmortem.md"
            raw = (
                b"# Failed training run\nBatch size 64 exhausted accelerator memory.\n"
            )
            source.write_bytes(raw)
            output = root / "oom.aff"
            command = [
                sys.executable,
                "-m",
                "oaff.cli",
                "capture",
                "--source",
                str(source),
                "--source-uri",
                "https://example.org/notes/failed-training-run",
                "--output",
                str(output),
                "--statement",
                "Batch size 64 exhausted memory in the synthetic training run.",
                "--applicability",
                "The same model and accelerator configuration is used.",
                "--condition",
                "Batch size 64",
                "--condition",
                "Synthetic accelerator A",
                "--exclusion",
                "A different accelerator is used.",
                "--producer-id",
                "tag:example.org,2026:human/researcher",
                "--producer-kind",
                "human",
                "--locator",
                "Run summary",
            ]
            result = subprocess.run(
                command, capture_output=True, text=True, check=False
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = output.read_bytes()
            self.assertNotIn(raw, data)
            document = json.loads(data)
            finding = document["finding"]
            self.assertEqual(finding["type"], "observation")
            self.assertEqual(finding["applicability"]["conditions"][0], "Batch size 64")
            self.assertEqual(document["receipts"], [])
            self.assertEqual(
                finding["evidence"][0]["content_digest"]["value"],
                hashlib.sha256(raw).hexdigest(),
            )
            self.assertEqual(verify_bytes(data, {"source-1": raw})["status"], "valid")
            collection = root / "aff"
            add_package(collection, output)
            check_index(collection)
            self.assertEqual(len(list((collection / "findings").glob("*.aff"))), 1)

    def test_invalid_fields_do_not_write_and_existing_output_is_preserved(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("An observation")
            output = root / "finding.aff"
            kwargs = {
                "source": source,
                "source_uri": "https://example.org/source",
                "output": output,
                "statement": "Observed outcome.",
                "applicability": "One synthetic run.",
                "conditions": ["Model A"],
                "producer_id": "tag:example.org,2026:agent/test",
                "producer_kind": "agent",
            }
            with self.assertRaisesRegex(CaptureError, "invalid Finding fields"):
                capture_source(**(kwargs | {"source_uri": "relative/path"}))
            self.assertFalse(output.exists())
            capture_source(**kwargs)
            before = output.read_bytes()
            with self.assertRaisesRegex(CaptureError, "already exists"):
                capture_source(**kwargs)
            self.assertEqual(output.read_bytes(), before)

    def test_symlink_source_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("private source")
            link = root / "link.md"
            link.symlink_to(source)
            with self.assertRaisesRegex(CaptureError, "not a symlink"):
                capture_source(
                    source=link,
                    source_uri="https://example.org/source",
                    output=root / "finding.aff",
                    statement="Observed outcome.",
                    applicability="One synthetic run.",
                    conditions=["Model A"],
                    producer_id="tag:example.org,2026:agent/test",
                    producer_kind="agent",
                )


if __name__ == "__main__":
    unittest.main()
