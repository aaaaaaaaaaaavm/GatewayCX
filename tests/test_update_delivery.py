from __future__ import annotations

import unittest

from gatewaycx.update_delivery import build_update_study


class UpdateDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = build_update_study()

    def test_unchanged_chunks_are_reused(self) -> None:
        transfer = self.record["content_addressed_transfer"]
        self.assertEqual(transfer["reused_chunks"], 60)
        self.assertEqual(transfer["missing_chunks"], 43)
        self.assertEqual(transfer["wire_bytes"], 430_000_000)

    def test_interruption_does_not_force_chunk_retransmission(self) -> None:
        transfer = self.record["content_addressed_transfer"]
        self.assertEqual(transfer["first_contact_delivered_bytes"], 250_000_000)
        self.assertEqual(transfer["second_contact_resumed_bytes"], 180_000_000)
        self.assertEqual(transfer["bytes_retransmitted_after_interruption"], 0)

    def test_content_addressing_beats_both_monolithic_cases(self) -> None:
        comparison = self.record["comparisons"]
        self.assertLess(
            comparison["content_addressed_wire_bytes"],
            comparison["monolithic_range_resume_wire_bytes"],
        )
        self.assertLess(
            comparison["content_addressed_wire_bytes"],
            comparison["monolithic_restart_wire_bytes"],
        )

    def test_active_slot_survives_download_interruption(self) -> None:
        events = self.record["activation"]["successful_update"]
        interrupted = next(item for item in events if item["event"] == "first_contact_interrupted")
        self.assertEqual(interrupted["active_slot"], "A")
        self.assertEqual(interrupted["active_version"], "v1")

    def test_failed_health_check_rolls_back(self) -> None:
        events = self.record["activation"]["failed_health_check"]
        self.assertEqual(events[-1]["event"], "automatic_rollback")
        self.assertEqual(events[-1]["active_slot"], "A")
        self.assertEqual(events[-1]["active_version"], "v1")


if __name__ == "__main__":
    unittest.main()
