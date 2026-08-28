import unittest

from gatewaycx.native_protocol_lab import AAAA_ADDRESS, build_dns_query, build_dns_response, parse_dns_aaaa


class NativeProtocolLabUnitTests(unittest.TestCase):
    def test_dns_aaaa_packet_round_trip(self) -> None:
        query = build_dns_query("service.gatewaycx.test")
        response = build_dns_response(query)
        self.assertEqual(response[:2], query[:2])
        self.assertEqual(parse_dns_aaaa(response), AAAA_ADDRESS)

    def test_truncated_dns_query_is_rejected(self) -> None:
        with self.assertRaises(ValueError): build_dns_response(b"short")


if __name__ == "__main__": unittest.main()
