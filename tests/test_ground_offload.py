import unittest

from gatewaycx.ground_offload import build_ground_offload_envelope, pipeline


class GroundOffloadEnvelopeTests(unittest.TestCase):
    def test_pipeline_uses_smallest_stage(self) -> None:
        result = pipeline("test", ingress=10.0, isl=20.0, egress=4.0)
        self.assertEqual(result["delivered_units"], 4.0)
        self.assertEqual(result["limiting_stage"], "egress")

    def test_s023_checks_pass(self) -> None:
        result = build_ground_offload_envelope()
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["inputs"]["unit_meaning"].split(";")[0], "synthetic scheduled-service unit")


if __name__ == "__main__":
    unittest.main()
