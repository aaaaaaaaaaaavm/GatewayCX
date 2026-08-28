import tempfile
import unittest
from pathlib import Path

from gatewaycx.bpv7_interop_lab import FaultInjectedGateway


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


if __name__ == "__main__": unittest.main()
