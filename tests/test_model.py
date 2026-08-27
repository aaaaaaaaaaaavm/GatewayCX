from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from gatewaycx.audit import audit
from gatewaycx.io import load_scenario, run_directory, write_json
from gatewaycx.model import Path as NetworkPath
from gatewaycx.model import Scenario, ScenarioError, SPEED_OF_LIGHT_KM_S, simulate


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "scenarios"


class PhysicsTests(unittest.TestCase):
    def test_mean_distance_light_time(self) -> None:
        path = NetworkPath("earth_moon", "cislunar", 384400, 0, 100, True)
        self.assertAlmostEqual(path.propagation_one_way_s, 384400 / SPEED_OF_LIGHT_KM_S, places=12)
        self.assertAlmostEqual(path.propagation_one_way_s, 1.282220382, places=9)
        self.assertAlmostEqual(path.round_trip_s, 2.564440764, places=9)

    def test_processing_is_not_hidden_inside_propagation(self) -> None:
        path = NetworkPath("earth_moon", "cislunar", 384400, 20, 100, True)
        self.assertAlmostEqual(path.round_trip_s, 2.604440764, places=9)

    def test_capacity_changes_serialization_not_light_time(self) -> None:
        slow = NetworkPath("slow", "cislunar", 384400, 0, 10, True)
        fast = NetworkPath("fast", "cislunar", 384400, 0, 1000, True)
        self.assertEqual(slow.round_trip_s, fast.round_trip_s)
        self.assertGreater(slow.serialization_s(1_000_000), fast.serialization_s(1_000_000))


class ScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = run_directory(SCENARIOS)
        cls.results = {item["scenario_id"]: item for item in cls.record["results"]}

    def test_all_baselines_run(self) -> None:
        self.assertEqual(set(self.results), {"S001", "S002", "S003"})

    def test_native_direct_is_compatible_but_slow(self) -> None:
        direct = self.results["S001"]
        self.assertTrue(direct["user_transaction_complete"])
        self.assertGreater(direct["elapsed_s"], 15.0)
        self.assertEqual(direct["status_counts"], {"completed": 3, "queued": 0, "failed": 0})

    def test_lunar_edge_removes_remote_work(self) -> None:
        direct = self.results["S001"]
        edge = self.results["S002"]
        self.assertTrue(edge["user_transaction_complete"])
        self.assertLess(edge["elapsed_s"], direct["elapsed_s"])
        self.assertLess(edge["completed_backbone_bytes"], direct["completed_backbone_bytes"])

    def test_lunar_region_survives_partition(self) -> None:
        partitioned = self.results["S003"]
        self.assertTrue(partitioned["user_transaction_complete"])
        self.assertEqual(partitioned["status_counts"], {"completed": 2, "queued": 1, "failed": 1})
        self.assertEqual(partitioned["completed_backbone_bytes"], 0)
        self.assertEqual(partitioned["queued_backbone_bytes"], 10_000_000)

    def test_generated_record_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            write_json(first, run_directory(SCENARIOS))
            write_json(second, run_directory(SCENARIOS))
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_unknown_path_is_rejected(self) -> None:
        data = json.loads((SCENARIOS / "S001_native_direct.json").read_text(encoding="utf-8"))
        data["operations"][0]["path"] = "imaginary"
        with self.assertRaises(ScenarioError):
            Scenario.from_dict(data)

    def test_local_only_cannot_use_cislunar_path(self) -> None:
        data = json.loads((SCENARIOS / "S002_lunar_edge.json").read_text(encoding="utf-8"))
        data["operations"][0]["path"] = "earth_moon"
        with self.assertRaises(ScenarioError):
            Scenario.from_dict(data)

    def test_model_rejects_zero_capacity(self) -> None:
        data = json.loads((SCENARIOS / "S001_native_direct.json").read_text(encoding="utf-8"))
        data["paths"]["earth_moon"]["capacity_mbps"] = 0
        with self.assertRaises(ScenarioError):
            Scenario.from_dict(data)

    def test_scenario_requires_user_completion_operation(self) -> None:
        data = json.loads((SCENARIOS / "S001_native_direct.json").read_text(encoding="utf-8"))
        for operation in data["operations"]:
            operation["required_for_user_completion"] = False
        with self.assertRaises(ScenarioError):
            Scenario.from_dict(data)

    def test_record_audit_passes(self) -> None:
        self.assertEqual(audit(ROOT), [])


if __name__ == "__main__":
    unittest.main()
