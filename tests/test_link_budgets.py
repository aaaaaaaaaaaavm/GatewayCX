import unittest

from gatewaycx.link_budgets import RF_CLASSES, build_link_budget_study, rf_budget


class LinkBudgetTests(unittest.TestCase):
    def test_extra_loss_is_preserved_in_margin(self) -> None:
        clear = rf_budget(RF_CLASSES[0])
        degraded = rf_budget(RF_CLASSES[0], 6.0)
        self.assertAlmostEqual(clear["margin_db"] - degraded["margin_db"], 6.0)

    def test_s025_checks_pass(self) -> None:
        self.assertTrue(all(build_link_budget_study()["checks"].values()))


if __name__ == "__main__": unittest.main()
