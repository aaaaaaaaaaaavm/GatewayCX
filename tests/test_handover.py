from __future__ import annotations

import unittest

from gatewaycx.handover import build_handover_study


class HandoverStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        record = build_handover_study()
        cls.policies = {item["policy"]: item for item in record["policies"]}

    def test_warm_standby_reduces_interruption(self) -> None:
        cold = self.policies["cold_failover"]
        warm = self.policies["warm_standby"]
        self.assertEqual(cold["maximum_continuous_interruption_s"]["interactive"], 20.0)
        self.assertEqual(warm["maximum_continuous_interruption_s"]["interactive"], 0.5)
        self.assertLess(
            warm["rejected_bytes"]["interactive"], cold["rejected_bytes"]["interactive"]
        )

    def test_split_continuity_avoids_interactive_rejection(self) -> None:
        split = self.policies["split_continuity"]
        self.assertEqual(split["rejected_bytes"]["control"], 0)
        self.assertEqual(split["rejected_bytes"]["interactive"], 0)
        self.assertEqual(split["maximum_continuous_interruption_s"]["interactive"], 0)

    def test_warm_standby_has_visible_keepalive_cost(self) -> None:
        self.assertGreater(self.policies["warm_standby"]["rf_keepalive_bytes"], 0)
        self.assertEqual(self.policies["cold_failover"]["rf_keepalive_bytes"], 0)

    def test_bulk_is_never_silently_rejected(self) -> None:
        for policy in self.policies.values():
            self.assertEqual(policy["rejected_bytes"]["bulk"], 0)
            self.assertEqual(
                policy["offered_bytes"]["bulk"],
                policy["delivered_bytes"]["bulk"] + policy["queued_at_end_bytes"]["bulk"],
            )


if __name__ == "__main__":
    unittest.main()
