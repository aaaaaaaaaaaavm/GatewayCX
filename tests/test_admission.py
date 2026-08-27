from __future__ import annotations

import unittest

from gatewaycx.admission import build_admission_study


class AdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = build_admission_study()
        cls.fallback = cls.record["cases"]["rf_fallback_only"]

    def test_allocations_never_exceed_contact_capacity(self) -> None:
        for case in self.record["cases"].values():
            for policy in ("strict_priority", "bounded_priority"):
                result = case[policy]
                self.assertLessEqual(result["delivered_bytes"], result["capacity_bytes"])
                self.assertGreaterEqual(result["unused_bytes"], 0)

    def test_safety_and_command_demands_complete_on_rf_fallback(self) -> None:
        rows = {
            item["traffic_class"]: item
            for item in self.fallback["bounded_priority"]["classes"]
        }
        self.assertEqual(rows["GX-T0"]["status"], "delivered")
        self.assertEqual(rows["GX-T1"]["status"], "delivered")

    def test_strict_priority_starves_lower_classes(self) -> None:
        rows = {
            item["traffic_class"]: item
            for item in self.fallback["strict_priority"]["classes"]
        }
        self.assertEqual(rows["GX-T4"]["delivered_bytes"], 0)
        self.assertEqual(rows["GX-T5"]["delivered_bytes"], 0)

    def test_bounded_policy_preserves_lower_class_progress(self) -> None:
        rows = {
            item["traffic_class"]: item
            for item in self.fallback["bounded_priority"]["classes"]
        }
        self.assertGreater(rows["GX-T4"]["delivered_bytes"], 0)
        self.assertGreater(rows["GX-T5"]["delivered_bytes"], 0)
        self.assertGreater(self.fallback["bounded_priority"]["queued_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
