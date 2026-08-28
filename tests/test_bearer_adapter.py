import copy
import json
import unittest
from pathlib import Path

from gatewaycx.adapter_probe import build_adapter_probe
from gatewaycx.bearer_adapter import ProfileBackedAdapter, TrafficUnit


PROFILE_PATH = Path("profiles/bearers/reference-rf.json")


class BearerAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = ProfileBackedAdapter.from_file(PROFILE_PATH)

    def unit(self, identity: str = "unit-001", size: int = 1_000) -> TrafficUnit:
        return TrafficUnit(identity, size, "GX-T3-operational")

    def test_invalid_profile_is_rejected(self) -> None:
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        invalid = copy.deepcopy(profile)
        invalid["queue"]["durable_bytes"] = 0
        with self.assertRaisesRegex(ValueError, "invalid GX-B1 profile"):
            ProfileBackedAdapter(invalid)

    def test_offline_deferred_unit_is_accepted(self) -> None:
        response = self.adapter.submit(self.unit())
        self.assertEqual(response["status"], "accepted_pending")
        self.assertEqual(self.adapter.snapshot()["queue_bytes"], 1_000)
        self.assertEqual(
            self.adapter.capabilities()["reference_persistence_scope"], "process_memory"
        )

    def test_offline_non_deferred_unit_is_rejected(self) -> None:
        response = self.adapter.submit(
            TrafficUnit("unit-live", 1_000, "GX-T1-control", deferred=False)
        )
        self.assertEqual(response["reason"], "link_unavailable")
        self.assertEqual(self.adapter.queue_bytes, 0)

    def test_mtu_is_enforced(self) -> None:
        response = self.adapter.submit(self.unit(size=65_537))
        self.assertEqual(response["reason"], "traffic_unit_too_large")

    def test_duplicate_id_does_not_double_accept(self) -> None:
        self.adapter.submit(self.unit())
        duplicate = self.adapter.submit(self.unit())
        self.assertEqual(duplicate["status"], "duplicate_known")
        self.assertEqual(self.adapter.snapshot()["accepted_bytes"], 1_000)

    def test_acquisition_requires_contact(self) -> None:
        response = self.adapter.acquire(1.0)
        self.assertEqual(response["reason"], "contact_unavailable")

    def test_profile_capacity_and_byte_ledger_are_applied(self) -> None:
        self.adapter.submit(self.unit(size=65_536))
        self.adapter.set_contact(True, 1.0)
        acquired = self.adapter.acquire(1.0)
        self.adapter.advance(acquired["ready_at_s"])
        sent = self.adapter.transmit(0.001)
        self.assertEqual(sent["transmitted_bytes"], 12_500)
        snapshot = self.adapter.snapshot()
        self.assertEqual(snapshot["accepted_bytes"], 65_536)
        self.assertEqual(
            snapshot["accepted_bytes"],
            snapshot["transmitted_bytes"] + snapshot["queue_bytes"],
        )

    def test_fault_preserves_queue_and_requires_reacquisition(self) -> None:
        self.adapter.submit(self.unit())
        before = self.adapter.queue_bytes
        self.adapter.inject_fault("GX.BEARER.CONTACT_LOST", 1.0)
        self.assertEqual(self.adapter.transmit(1.0)["status"], "blocked")
        self.assertEqual(self.adapter.queue_bytes, before)
        self.adapter.clear_faults(2.0)
        self.adapter.set_contact(True, 2.0)
        acquired = self.adapter.acquire(2.0)
        self.assertEqual(self.adapter.snapshot()["link_state"], "acquiring")
        self.adapter.advance(acquired["ready_at_s"])
        self.assertEqual(self.adapter.snapshot()["link_state"], "ready")

    def test_fault_requires_portable_bearer_code(self) -> None:
        with self.assertRaisesRegex(ValueError, "GX-O1 bearer code"):
            self.adapter.inject_fault("PROVIDER.INTERNAL.42", 1.0)

    def test_offsets_are_monotonic(self) -> None:
        self.adapter.set_contact(True, 2.0)
        with self.assertRaisesRegex(ValueError, "monotonic"):
            self.adapter.acquire(1.0)

    def test_s016_probe_exercises_one_surface_for_both_media(self) -> None:
        result = build_adapter_probe()
        self.assertTrue(result["cross_adapter_checks"]["same_operation_signatures"])
        self.assertTrue(result["cross_adapter_checks"]["all_adapter_checks_pass"])
        self.assertTrue(result["cross_adapter_checks"]["both_media_families_exercised"])
        self.assertFalse(result["cross_adapter_checks"]["payload_content_recorded"])


if __name__ == "__main__":
    unittest.main()
