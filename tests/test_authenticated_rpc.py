import json
import tempfile
import unittest
from pathlib import Path

from gatewaycx.authenticated_rpc import (
    AUTH_RPC_VERSION,
    AuthenticatedAdapterRPCClient,
    AuthenticatedAdapterRPCServer,
    DurableReplayStore,
    read_secret,
)
from gatewaycx.authenticated_transport_probe import build_authenticated_transport_probe
from gatewaycx.bearer_adapter import ProfileBackedAdapter


SECRET = bytes.fromhex("42" * 32)


class AuthenticatedRPCDispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "state.sqlite3"
        self.server = AuthenticatedAdapterRPCServer(
            ProfileBackedAdapter.from_file(Path("profiles/bearers/reference-rf.json")),
            DurableReplayStore(self.database),
            {"test-client": SECRET},
        )
        self.client = AuthenticatedAdapterRPCClient(
            "127.0.0.1", 1, "test-client", SECRET
        )

    def tearDown(self) -> None:
        self.server.replay_store.close()
        self.server.adapter.close()
        self.temp.cleanup()

    def test_signed_request_is_accepted_and_response_is_signed(self) -> None:
        request = self.client.build_request("capabilities")
        response = self.server.dispatch(request)
        self.assertTrue(response["ok"])
        self.assertEqual(response["rpc_version"], AUTH_RPC_VERSION)
        self.assertIsInstance(response["mac"], str)

    def test_tampering_is_rejected_without_consuming_sequence(self) -> None:
        request = self.client.build_request("snapshot")
        request["operation"] = "clear_faults"
        self.assertEqual(self.server.dispatch(request)["error"], "authentication_failed")
        valid = self.client.build_request("snapshot")
        valid["sequence"] = request["sequence"]
        valid["request_id"] = request["request_id"]
        from gatewaycx.authenticated_rpc import _mac

        valid["mac"] = _mac(SECRET, valid)
        self.assertTrue(self.server.dispatch(valid)["ok"])

    def test_sequence_rejection_survives_store_reopen(self) -> None:
        request = self.client.build_request("snapshot")
        self.assertTrue(self.server.dispatch(request)["ok"])
        self.server.replay_store.close()
        self.server.replay_store = DurableReplayStore(self.database)
        self.assertEqual(self.server.dispatch(request)["error"], "replayed_sequence")

    def test_invalid_secret_file_is_rejected(self) -> None:
        path = Path(self.temp.name) / "bad.secret"
        path.write_text("not-a-key\n", encoding="ascii")
        with self.assertRaises(ValueError):
            read_secret(path)

    def test_s019_authenticated_process_probe(self) -> None:
        result = build_authenticated_transport_probe()
        positive = {
            key: value
            for key, value in result["checks"].items()
            if key != "payload_content_crossed_rpc"
        }
        self.assertTrue(all(positive.values()), json.dumps(result, indent=2))
        self.assertFalse(result["checks"]["payload_content_crossed_rpc"])


if __name__ == "__main__":
    unittest.main()
