from __future__ import annotations

import shutil
import unittest

from gatewaycx.emulation import EmulationConfig, run_https_experiment


@unittest.skipUnless(shutil.which("curl") and shutil.which("openssl"), "curl and openssl required")
class HttpsEmulationTests(unittest.TestCase):
    def test_unmodified_https_client_and_connection_reuse(self) -> None:
        # Ten milliseconds one way keeps CI fast while exercising the same code as the full study.
        config = EmulationConfig(distance_km=2_997.92458, capacity_mbps=100, object_bytes=1_024)
        record = run_https_experiment(config)
        self.assertTrue(record["checks"]["experiment_passed"])
        cold = record["measurements"]["cold_connection"]
        reused = record["measurements"]["reuse_sequence_second"]
        self.assertEqual(cold["http_code"], 200)
        self.assertEqual(cold["size_download"], 1_024)
        self.assertGreater(cold["time_appconnect"], 0.01)
        self.assertEqual(reused["num_connects"], 0)
        self.assertEqual(reused["time_appconnect"], 0)

    def test_invalid_configuration_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_https_experiment(EmulationConfig(capacity_mbps=0))


if __name__ == "__main__":
    unittest.main()
