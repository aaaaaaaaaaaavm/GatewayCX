import json
import unittest

from gatewaycx.abrupt_restart import build_abrupt_restart_study


class AbruptRestartTests(unittest.TestCase):
    def test_s020_recovers_both_transaction_boundaries(self) -> None:
        result = build_abrupt_restart_study()
        positive = {
            key: value
            for key, value in result["checks"].items()
            if key != "payload_content_was_supplied"
        }
        self.assertTrue(all(positive.values()), json.dumps(result, indent=2))
        self.assertFalse(result["checks"]["payload_content_was_supplied"])


if __name__ == "__main__":
    unittest.main()
