from __future__ import annotations

import unittest

from gatewaycx.capacity import build_capacity_envelope


class CapacityEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = build_capacity_envelope()
        cls.paths = {item["distance_case"]: item for item in cls.record["paths"]}

    def test_distance_changes_light_time(self) -> None:
        self.assertLess(
            self.paths["closest_cited"]["round_trip_light_time_s"],
            self.paths["farthest_cited"]["round_trip_light_time_s"],
        )

    def test_622_mbps_requires_about_200_mb_at_mean_distance(self) -> None:
        rate = next(
            item for item in self.paths["mean"]["rates"] if item["capacity_mbps"] == 622
        )
        self.assertGreater(rate["minimum_full_rate_window_bytes"], 199_000_000)
        self.assertLess(rate["minimum_full_rate_window_bytes"], 200_000_000)

    def test_small_window_caps_throughput(self) -> None:
        rate = next(
            item for item in self.paths["mean"]["rates"] if item["capacity_mbps"] == 1_000
        )
        one_mib = rate["window_limited_throughput_mbps"][str(2**20)]
        two_fifty_six_mib = rate["window_limited_throughput_mbps"][str(256 * 2**20)]
        self.assertLess(one_mib, 4)
        self.assertGreater(two_fifty_six_mib, 800)

    def test_one_day_buffer_at_100_mbps_is_1_08_tb(self) -> None:
        row = next(item for item in self.record["outage_buffers"] if item["admitted_rate_mbps"] == 100)
        self.assertEqual(row["required_bytes"]["86400"], 1_080_000_000_000)


if __name__ == "__main__":
    unittest.main()
