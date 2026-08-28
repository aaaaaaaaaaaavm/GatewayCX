import tempfile
import unittest
from pathlib import Path

from gatewaycx.bearer_adapter import ProfileBackedAdapter, TrafficUnit
from gatewaycx.durable_restart import build_durable_restart_study
from gatewaycx.traffic_store import (
    InMemoryTrafficStore,
    SQLiteTrafficStore,
    StoredTrafficUnit,
)


def unit(identity: str = "unit-001", size: int = 1_000) -> StoredTrafficUnit:
    return StoredTrafficUnit(identity, size, "GX-T3-operational", True)


class TrafficStoreContractTests(unittest.TestCase):
    def exercise_contract(self, store) -> None:
        self.assertEqual(store.accept(unit(), 2_000)["status"], "accepted_pending")
        self.assertEqual(store.accept(unit(), 2_000)["status"], "duplicate_known")
        self.assertEqual(
            store.accept(unit(size=999), 2_000)["status"], "duplicate_conflict"
        )
        self.assertEqual(store.accept(unit("unit-002", 1_001), 2_000)["reason"], "durable_queue_full")
        fragments = store.transmit(250)
        self.assertEqual(sum(item["bytes"] for item in fragments), 250)
        snapshot = store.snapshot()
        self.assertEqual(snapshot["accepted_bytes"], 1_000)
        self.assertEqual(snapshot["transmitted_bytes"], 250)
        self.assertEqual(snapshot["queue_bytes"], 750)

    def test_memory_store_contract(self) -> None:
        store = InMemoryTrafficStore()
        self.exercise_contract(store)

    def test_store_rejects_invalid_metadata(self) -> None:
        def assert_invalid(store) -> None:
            self.assertEqual(store.accept(unit(size=0), 2_000)["reason"], "invalid_payload_bytes")
            self.assertEqual(
                store.accept(StoredTrafficUnit("", 1, "GX-T3-operational", True), 2_000)["reason"],
                "missing_traffic_unit_id",
            )

        assert_invalid(InMemoryTrafficStore())
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SQLiteTrafficStore(Path(temp_dir) / "ledger.sqlite3")
            assert_invalid(store)
            store.close()

    def test_sqlite_store_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SQLiteTrafficStore(Path(temp_dir) / "ledger.sqlite3")
            self.exercise_contract(store)
            store.close()

    def test_sqlite_reopen_preserves_partial_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ledger.sqlite3"
            first = SQLiteTrafficStore(path)
            first.accept(unit(), 2_000)
            first.transmit(250)
            first.close()
            second = SQLiteTrafficStore(path)
            self.assertEqual(
                second.snapshot(),
                {
                    "accepted_bytes": 1_000,
                    "transmitted_bytes": 250,
                    "queue_bytes": 750,
                    "traffic_units": 1,
                    "pending_units": 1,
                },
            )
            second.close()

    def test_schema_has_no_payload_content_column(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ledger.sqlite3"
            store = SQLiteTrafficStore(path)
            self.assertNotIn("payload", store.schema_columns())
            self.assertEqual(
                store.database_settings(),
                {"journal_mode": "WAL", "synchronous_mode": "FULL"},
            )
            store.close()

    def test_adapter_can_use_sqlite_store(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ledger.sqlite3"
            adapter = ProfileBackedAdapter.from_file(
                Path("profiles/bearers/reference-rf.json"),
                store=SQLiteTrafficStore(path),
            )
            accepted = adapter.submit(TrafficUnit("unit-001", 1_000, "GX-T3-operational"))
            self.assertEqual(accepted["status"], "accepted_pending")
            self.assertEqual(
                adapter.snapshot()["reference_persistence_scope"], "sqlite_file"
            )
            adapter.close()

    def test_s017_restarts_in_a_distinct_process(self) -> None:
        result = build_durable_restart_study()
        self.assertTrue(all(result["checks"].values()))
        self.assertFalse(result["inputs"]["payload_content_supplied"])


if __name__ == "__main__":
    unittest.main()
