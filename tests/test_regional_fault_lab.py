import unittest

from gatewaycx.regional_fault_lab import build_regional_fault_lab, issue_token, validate_token


class RegionalFaultLabTests(unittest.TestCase):
    def test_token_rejects_expiry_and_revocation(self) -> None:
        token = issue_token("test", 1, 0, 10)
        self.assertEqual(validate_token(token, 5, set()), (True, "accepted"))
        self.assertEqual(validate_token(token, 10, set()), (False, "expired"))
        self.assertEqual(validate_token(token, 5, {1}), (False, "revoked"))

    def test_s028_checks_pass(self) -> None:
        self.assertTrue(all(build_regional_fault_lab()["checks"].values()))


if __name__ == "__main__": unittest.main()
