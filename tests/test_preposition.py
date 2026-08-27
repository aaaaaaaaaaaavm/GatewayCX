from __future__ import annotations

import unittest

from gatewaycx.preposition import CACHE_BUDGET_BYTES, build_preposition_study


class PrepositionStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = build_preposition_study()
        cls.policies = cls.record["policies"]

    def test_every_policy_preserves_essential_reservation(self) -> None:
        for result in self.policies.values():
            self.assertIn("emergency_maps", result["selected_ids"])
            self.assertIn("medical_reference", result["selected_ids"])
            self.assertEqual(result["essential_reserved_bytes"], 300_000_000)

    def test_no_policy_exceeds_cache_budget(self) -> None:
        for result in self.policies.values():
            self.assertLessEqual(result["prefetched_bytes"], CACHE_BUDGET_BYTES)

    def test_overconfidence_has_visible_opportunity_cost(self) -> None:
        comparison = self.record["comparison"]
        self.assertEqual(comparison["overconfident_minus_popularity_wasted_bytes"], 450_000_000)
        self.assertGreater(
            self.policies["overconfident_forecast"]["forecast_brier_score"],
            self.policies["popularity_only"]["forecast_brier_score"],
        )

    def test_calibrated_input_does_not_yet_beat_simple_baseline(self) -> None:
        comparison = self.record["comparison"]
        self.assertEqual(comparison["calibrated_minus_popularity_useful_bytes"], 0)
        self.assertEqual(comparison["learned_policy_admission_result"], "not established")

    def test_oracle_is_declared_as_comparator_not_policy(self) -> None:
        self.assertTrue(self.record["comparison"]["calibrated_matches_oracle_selection"])
        boundary = " ".join(self.record["interpretation_boundary"])
        self.assertIn("unavailable at decision time", boundary)


if __name__ == "__main__":
    unittest.main()
