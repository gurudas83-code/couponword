import json
import subprocess
import sys
import unittest
from pathlib import Path


class OfflineCertificationHarnessTests(unittest.TestCase):
    def test_harness_runs_without_network_and_reports_fixture_gaps(self):
        root = Path(__file__).resolve().parent
        output = root / "outputs" / "phase_e_offline_test.json"
        result = subprocess.run(
            [sys.executable, "phase_e_offline_certification.py", "--output", str(output)],
            cwd=root, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["total"], 1000)
        self.assertFalse(payload["freeze"]["external_network"])
        self.assertIn("fixture_gap", payload["counts"])
        self.assertEqual(payload["quality_review_status"], "PROPOSED_NOT_INDEPENDENTLY_APPROVED")


if __name__ == "__main__":
    unittest.main()
