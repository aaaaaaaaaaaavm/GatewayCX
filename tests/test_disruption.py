from __future__ import annotations

import unittest

from gatewaycx.disruption import build_disruption_study


class DisruptionStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = build_disruption_study()
        cls.modes = cls.record["modes"]

    def test_native_retry_retransmits_partial_object(self) -> None:
        native = self.modes["native_https_retry"]
        self.assertEqual(native["traffic"]["wire_bytes"], 14_000_000)
        self.assertEqual(native["traffic"]["retransmitted_bytes"], 4_000_000)

    def test_durable_modes_resume_without_retransmitting_verified_chunks(self) -> None:
        for name in ("terminating_deferred_proxy", "opaque_deferred_object"):
            mode = self.modes[name]
            self.assertEqual(mode["traffic"]["wire_bytes"], 10_000_000)
            self.assertEqual(mode["traffic"]["retransmitted_bytes"], 0)

    def test_acknowledgement_levels_are_not_collapsed(self) -> None:
        opaque = self.modes["opaque_deferred_object"]
        acknowledgement = opaque["acknowledgement"]
        self.assertTrue(acknowledgement["local_durable_acceptance"])
        self.assertFalse(acknowledgement["local_acceptance_means_remote_completion"])
        self.assertFalse(acknowledgement["bp_delivery_report_means_remote_application_processed"])
        self.assertTrue(acknowledgement["application_receipt_required_for_remote_completion"])

    def test_security_boundaries_are_distinct(self) -> None:
        native = self.modes["native_https_retry"]["security"]
        proxy = self.modes["terminating_deferred_proxy"]["security"]
        opaque = self.modes["opaque_deferred_object"]["security"]
        self.assertFalse(native["gateway_can_read_application_plaintext"])
        self.assertTrue(proxy["gateway_can_read_application_plaintext"])
        self.assertFalse(opaque["gateway_can_read_application_plaintext"])
        self.assertTrue(opaque["payload_object_encryption_required"])

    def test_idempotency_does_not_become_exactly_once_claim(self) -> None:
        for mode in self.modes.values():
            self.assertFalse(mode["mutation_retry"]["exactly_once_claimed"])

    def test_transparent_partition_survival_is_rejected(self) -> None:
        rejected = " ".join(self.record["rejected_claims"])
        self.assertIn("indefinite partition transparently", rejected)
        self.assertIn("BPv7 provides native", rejected)


if __name__ == "__main__":
    unittest.main()
