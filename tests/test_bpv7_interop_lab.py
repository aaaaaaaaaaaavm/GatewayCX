import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gatewaycx.bpv7_interop_lab import FaultInjectedGateway, main


class BPv7GatewayUnitTests(unittest.TestCase):
    def test_fault_then_retry_preserves_ledger_and_authentication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            gateway = FaultInjectedGateway(Path(temporary) / "gateway.db")
            try:
                payload = b"synthetic-wire-image-for-gateway-unit-test"
                delivered, record = gateway.transfer(payload, "unit-1", 1)
                self.assertEqual(delivered, payload)
                self.assertTrue(record["authenticated"])
                self.assertTrue(record["tampered_metadata_rejected"])
                self.assertTrue(record["same_sequence_rejected"])
                self.assertLess(record["faulted_wire_bytes"], record["retry_wire_bytes"])
                self.assertEqual(record["gx_a1_transmitted_bytes"], len(payload))
            finally:
                gateway.close()

    def test_cli_passes_both_external_binary_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result.json"
            with patch("gatewaycx.bpv7_interop_lab.build_bpv7_interop_lab", return_value={"checks": {}}) as build:
                self.assertEqual(main(["--go-bridge", "/go", "--rust-bp7", "/rust", "--output", str(output)]), 0)
            build.assert_called_once_with(Path("/go"), Path("/rust"))
            self.assertTrue(output.exists())


if __name__ == "__main__": unittest.main()
