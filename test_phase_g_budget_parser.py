import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))
from intent_engine import parse_query


# Explicit user budget bands, equivalent spellings, and negative identity examples.
CASES = []
for value in (10000, 12000, 20000, 30000, 40000, 50000, 120000, 150000):
    for query in (
        f"mobile under {value}", f"phone below ₹{value:,}",
        f"best phone up to {value / 1000:g}k", f"mobile {value / 100000:g} lakh",
        f"mobile {value}", f"camera phone budget {value}",
        f"gaming mobile {value / 1000:g} thousand",
        f"battery mobile {value / 1000:g} hazar tak",
        f"Samsung phone under {value} 8GB RAM 256GB storage",
        f"mobile maximum INR {value}", f"phone {value / 1000:g}k ke andar",
        f"mobile under Rs. {value}",
    ):
        CASES.append((query, None, value))
CASES += [
    ("डेढ़ लाख के अंदर सबसे अच्छा मोबाइल", None, 150000),
    ("mobile under 1.5lakh", None, 150000),
    ("mobile between 20k and 30k", 20000, 30000),
    ("phone from ₹1,20,000 to ₹1,50,000", 120000, 150000),
    ("mobile 20-30k", 20000, 30000),
    ("phone above 30k", 30000, None),
    ("mobile 30k se upar", 30000, None),
    ("Samsung Galaxy S24 8GB 256GB", None, None),
    ("mobile 256GB", None, None),
    ("phone 5000mAh", None, None),
    ("mobile 120Hz 50MP 8GB", None, None),
    ("Nokia 3210", None, None),
    ("mobile under 256GB storage", None, None),
    ("mobile 5000 mAh battery", None, None),
    ("mobile Snapdragon 8 Gen 5", None, None),
]


class BudgetParserTests(unittest.TestCase):
    def test_budget_fixtures(self):
        self.assertGreaterEqual(len(CASES), 100)
        for query, lower, upper in CASES:
            with self.subTest(query=query):
                intent = parse_query(query)
                self.assertEqual((intent["budget_min"], intent["budget_max"]), (lower, upper))

    def test_preferences_and_physical_variant_survive(self):
        intent = parse_query("Samsung camera phone under 1.5lakh 8GB RAM 256GB storage")
        self.assertEqual(intent["category"], "smartphone")
        self.assertIn("samsung", [b.lower() for b in intent["brands"]])
        self.assertEqual(intent["budget_max"], 150000)
        self.assertTrue(any("camera" in str(v) for v in intent.values()))


if __name__ == "__main__":
    unittest.main()
