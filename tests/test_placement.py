from __future__ import annotations

import unittest

from gatewaycx.placement import SERVICES, build_placement_study


class PlacementStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = build_placement_study()

    def test_search_is_exhaustive(self) -> None:
        self.assertEqual(self.record["search"]["candidate_combinations"], 3 ** len(SERVICES))
        self.assertGreater(self.record["search"]["resource_feasible_combinations"], 0)

    def test_selected_plans_keep_essential_services_lunar(self) -> None:
        required = sum(service.essential_during_partition for service in SERVICES)
        for name in ("minimum_backbone_plan", "minimum_latency_plan"):
            plan = self.record[name]
            self.assertEqual(plan["essential_services_available_during_partition"], required)
            for service in SERVICES:
                if service.essential_during_partition:
                    self.assertNotEqual(plan["placements"][service.name], "earth")

    def test_frontier_is_not_collapsed_to_arbitrary_score(self) -> None:
        frontier = self.record["resilient_pareto_frontier"]
        self.assertGreater(len(frontier), 1)
        self.assertEqual(frontier[0], self.record["minimum_backbone_plan"])
        self.assertIn(self.record["minimum_latency_plan"], frontier)

    def test_lunar_plan_reduces_interactive_delay(self) -> None:
        earth = self.record["earth_central_baseline"]
        lunar = self.record["minimum_backbone_plan"]
        self.assertLess(
            lunar["interactive_delay_seconds_per_hour"],
            earth["interactive_delay_seconds_per_hour"],
        )


if __name__ == "__main__":
    unittest.main()
