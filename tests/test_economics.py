import unittest

from gatewaycx.economics import annualised_capex, build_economics_study


class EconomicsTests(unittest.TestCase):
    def test_annualisation_exceeds_straight_line_at_positive_discount(self) -> None:
        self.assertGreater(annualised_capex(100.0, 10, 0.08), 10.0)

    def test_s027_checks_pass(self) -> None:
        self.assertTrue(all(build_economics_study()["checks"].values()))


if __name__ == "__main__": unittest.main()
