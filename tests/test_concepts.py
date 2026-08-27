from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "concepts" / "cross-industry-atlas.json"


class ConceptAtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = json.loads(ATLAS.read_text(encoding="utf-8"))
        cls.concepts = cls.record["concepts"]

    def test_identifiers_are_unique_and_ordered(self) -> None:
        identifiers = [item["id"] for item in self.concepts]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(identifiers, [f"X{index:03d}" for index in range(1, 16)])

    def test_every_transfer_is_falsifiable_and_bounded(self) -> None:
        for item in self.concepts:
            with self.subTest(concept=item["id"]):
                self.assertTrue(item["source_industries"])
                self.assertTrue(item["mechanism"])
                self.assertTrue(item["gatewaycx_transfer"])
                self.assertTrue(item["falsifiable_hypothesis"])
                self.assertTrue(item["first_experiment"])
                self.assertTrue(item["failure_mode"])

    def test_priority_scores_recompute(self) -> None:
        for item in self.concepts:
            scores = item["scores"]
            benefit = sum(value for key, value in scores.items() if key != "speculation_risk")
            expected = benefit - scores["speculation_risk"]
            self.assertEqual(item["priority_score"], expected)
            self.assertTrue(all(0 <= value <= 5 for value in scores.values()))

    def test_selected_concepts_have_named_studies(self) -> None:
        selected = [item for item in self.concepts if item["status"] == "selected"]
        self.assertEqual({item["id"] for item in selected}, {"X001", "X002", "X003", "X004"})
        self.assertTrue(all(item["first_experiment"].startswith("S0") for item in selected))


if __name__ == "__main__":
    unittest.main()
