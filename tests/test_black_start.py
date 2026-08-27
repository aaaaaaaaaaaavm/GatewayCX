from __future__ import annotations

import unittest

from gatewaycx.black_start import ESSENTIAL_SERVICES, build_black_start_study


class BlackStartStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = build_black_start_study()
        cls.scenarios = cls.record["scenarios"]

    def test_earth_coupling_blocks_partition_restart(self) -> None:
        result = self.scenarios["earth_coupled_during_partition"]
        self.assertEqual(result["started_essential_count"], 2)
        self.assertIn("earth_dns", result["blocked"]["local_name_root"])

    def test_islandable_graph_restarts_all_essential_services(self) -> None:
        result = self.scenarios["islandable_during_partition"]
        self.assertEqual(result["started_essential_count"], len(ESSENTIAL_SERVICES))
        self.assertEqual(result["blocked"], {})

    def test_earth_recovery_restores_coupled_graph(self) -> None:
        result = self.scenarios["earth_coupled_after_earth_recovery"]
        self.assertEqual(result["started_essential_count"], len(ESSENTIAL_SERVICES))

    def test_holdover_time_is_the_largest_single_dependency(self) -> None:
        ranking = self.record["fault_ranking"]
        self.assertEqual(ranking[0]["failed_service"], "holdover_time")
        self.assertEqual(ranking[0]["remaining_essential_count"], 1)

    def test_fault_does_not_start_failed_service(self) -> None:
        for failed, result in self.record["single_local_faults"].items():
            self.assertNotIn(failed, result["started_essential"])


if __name__ == "__main__":
    unittest.main()
