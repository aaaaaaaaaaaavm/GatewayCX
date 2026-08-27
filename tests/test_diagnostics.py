from __future__ import annotations

import copy
import unittest

from gatewaycx.diagnostics import build_reference_trace, validate_trace


class DiagnosticProfileTests(unittest.TestCase):
    def test_reference_trace_passes(self) -> None:
        self.assertEqual(validate_trace(build_reference_trace()), [])

    def test_event_offsets_are_strictly_monotonic(self) -> None:
        trace = build_reference_trace()
        offsets = [event["observed_offset_ms"] for event in trace["events"]]
        self.assertEqual(offsets, sorted(set(offsets)))

    def test_contact_loss_captures_freeze_frame(self) -> None:
        trace = build_reference_trace()
        event = next(
            item for item in trace["events"]
            if item["fault_code"] == "GX.BEARER.CONTACT_LOST"
        )
        self.assertEqual(event["freeze_frame"]["link_state"], "unavailable")
        self.assertEqual(event["freeze_frame"]["queue_bytes"], 6_000_000)
        self.assertEqual(event["freeze_frame"]["tx_rate_mbps"], 0.0)

    def test_payload_and_user_identity_are_excluded(self) -> None:
        trace = build_reference_trace()
        self.assertFalse(trace["traffic_unit"]["payload_content_recorded"])
        for event in trace["events"]:
            self.assertFalse(event["privacy"]["payload_plaintext_included"])
            self.assertFalse(event["privacy"]["user_identifier_included"])

    def test_unknown_fault_code_is_rejected(self) -> None:
        trace = copy.deepcopy(build_reference_trace())
        trace["events"][1]["fault_code"] = "VENDOR.SECRET.FAILURE"
        self.assertTrue(any("not in the GX-O1 registry" in item for item in validate_trace(trace)))

    def test_delivery_state_cannot_skip_adapter_delivery(self) -> None:
        trace = copy.deepcopy(build_reference_trace())
        trace["events"] = [trace["events"][0], trace["events"][-1]]
        self.assertTrue(any("collapses or reorders" in item for item in validate_trace(trace)))

    def test_duplicate_event_id_is_rejected(self) -> None:
        trace = copy.deepcopy(build_reference_trace())
        trace["events"][1]["event_id"] = trace["events"][0]["event_id"]
        self.assertTrue(any("duplicated" in item for item in validate_trace(trace)))


if __name__ == "__main__":
    unittest.main()
