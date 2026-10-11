import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))
from market_discovery import within_research_scope


class RecallTests(unittest.TestCase):
    def test_evidenced_exact_catalogue_tail_is_not_truncated(self):
        rows = [(str(i), True, 1) for i in range(35)]
        selected = []
        for identity, canonical, evidence in rows:
            if within_research_scope(len(selected), 30, canonical, evidence):
                selected.append(identity)
        self.assertEqual(len(selected), 35)
        self.assertEqual(selected[-1], "34")

    def test_unverified_tail_remains_bounded(self):
        for canonical, evidence in ((False, 0), (True, 0), (False, 1)):
            self.assertFalse(within_research_scope(30, 30, canonical, evidence))
            self.assertTrue(within_research_scope(29, 30, canonical, evidence))


if __name__ == "__main__":
    unittest.main()
