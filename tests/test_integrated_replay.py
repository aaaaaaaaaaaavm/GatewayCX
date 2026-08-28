from __future__ import annotations

import unittest

from gatewaycx.diagnostics import validate_trace
from gatewaycx.integrated_replay import build_integrated_replay


class IntegratedReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = build_integrated_replay()

    def test_every_composition_check_passes(self) -> None:
        checks = self.record["composition_checks"]
        self.assertTrue(all(value is True or value is False for value in checks.values()))
        self.assertTrue(
            all(
                value is True
                for key, value in checks.items()
                if key != "application_plaintext_recorded"
            )
        )
        self.assertFalse(checks["application_plaintext_recorded"])

    def test_warm_rf_limits_interruption_to_one_step(self) -> None:
        continuity = self.record["continuity"]
        self.assertEqual(continuity["maximum_interruption_s"], 0.5)
        self.assertEqual(continuity["rejected_bytes"]["control"], 31_250)
        self.assertEqual(continuity["rejected_bytes"]["interactive"], 125_000)

    def test_object_is_conserved_and_uses_both_bearers(self) -> None:
        durable = self.record["durable_object"]
        self.assertEqual(durable["accepted_bytes"], 1_000_000_000)
        self.assertEqual(durable["delivered_bytes"], 1_000_000_000)
        self.assertEqual(durable["queued_at_end_bytes"], 0)
        self.assertEqual(durable["retransmitted_bytes"], 0)
        self.assertGreater(durable["bytes_by_bearer"]["gx-reference-optical"], 0)
        self.assertGreater(durable["bytes_by_bearer"]["gx-reference-rf"], 0)

    def test_acknowledgements_follow_physical_recovery(self) -> None:
        events = self.record["gx_o1_trace"]["events"]
        by_code = {item["fault_code"]: item["observed_offset_ms"] for item in events}
        self.assertLess(
            by_code["GX.BEARER.PREFERRED_RESTORED"],
            by_code["GX.DELIVERY.ADAPTER_DELIVERED"],
        )
        self.assertLess(
            by_code["GX.DELIVERY.ADAPTER_DELIVERED"],
            by_code["GX.DELIVERY.REMOTE_COMPLETED"],
        )

    def test_integrated_trace_conforms_to_gx_o1(self) -> None:
        self.assertEqual(validate_trace(self.record["gx_o1_trace"]), [])


if __name__ == "__main__":
    unittest.main()
