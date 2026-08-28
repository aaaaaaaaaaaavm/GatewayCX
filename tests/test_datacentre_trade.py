import unittest

from gatewaycx.datacentre_trade import build_datacentre_trade


class DatacentreTradeTests(unittest.TestCase):
    def test_s026_checks_pass(self) -> None:
        self.assertTrue(all(build_datacentre_trade()["checks"].values()))


if __name__ == "__main__": unittest.main()
