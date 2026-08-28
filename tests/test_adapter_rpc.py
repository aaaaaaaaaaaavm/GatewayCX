import unittest
from pathlib import Path

from gatewaycx.adapter_rpc import AdapterRPCServer, RPC_VERSION
from gatewaycx.adapter_transport_probe import build_transport_probe
from gatewaycx.bearer_adapter import ProfileBackedAdapter


class AdapterRPCDispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = AdapterRPCServer(
            ProfileBackedAdapter.from_file(Path("profiles/bearers/reference-rf.json")),
        )

    def test_request_requires_identifier(self) -> None:
        response = self.server.dispatch({"operation": "snapshot"})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"], "invalid_request_id")

    def test_unknown_operation_is_rejected(self) -> None:
        response = self.server.dispatch(
            {"request_id": "r1", "operation": "vendor_private", "arguments": {}}
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"], "unknown_operation")

    def test_arguments_must_be_object(self) -> None:
        response = self.server.dispatch(
            {"request_id": "r1", "operation": "snapshot", "arguments": []}
        )
        self.assertEqual(response["error"], "arguments_must_be_object")

    def test_capability_response_preserves_rpc_and_adapter_versions(self) -> None:
        response = self.server.dispatch(
            {"request_id": "r1", "operation": "capabilities", "arguments": {}}
        )
        self.assertEqual(response["rpc_version"], RPC_VERSION)
        self.assertEqual(response["result"]["api_version"], "GX-A1/0.1")

    def test_s018_crosses_and_restarts_process_boundary(self) -> None:
        result = build_transport_probe()
        positive_checks = {
            key: value
            for key, value in result["checks"].items()
            if key != "payload_content_crossed_rpc"
        }
        self.assertTrue(all(positive_checks.values()))
        self.assertFalse(result["checks"]["payload_content_crossed_rpc"])


if __name__ == "__main__":
    unittest.main()
