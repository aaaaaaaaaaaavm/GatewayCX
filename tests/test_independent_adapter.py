import json
import unittest

from gatewaycx.independent_adapter_probe import build_independent_adapter_probe


class IndependentAdapterTests(unittest.TestCase):
    def test_s021_crosses_independent_code_path(self) -> None:
        result = build_independent_adapter_probe()
        positive = {
            key: value
            for key, value in result["checks"].items()
            if key != "payload_content_crossed_binding"
        }
        self.assertTrue(all(positive.values()), json.dumps(result, indent=2))
        self.assertFalse(result["checks"]["payload_content_crossed_binding"])


if __name__ == "__main__":
    unittest.main()
