"""L1 verification of recoverable-failure logging (ACCEPTANCE: command failures append JSONL)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import paperwiki


class ErrorLoggingTests(unittest.TestCase):
    def test_command_failure_exits_1_and_appends_errors_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            proc = subprocess.run(
                [sys.executable, str(Path(paperwiki.__file__)), "read", "not a paper", "--root", str(root)],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            errs = root / ".paperwiki" / "errors.jsonl"
            self.assertTrue(errs.exists(), "expected .paperwiki/errors.jsonl to be written")
            event = json.loads(errs.read_text(encoding="utf-8").splitlines()[-1])
            self.assertIn("error", event)
            self.assertTrue(event.get("recoverable"))


if __name__ == "__main__":
    unittest.main()
