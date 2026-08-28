import unittest

from gatewaycx.ephemeris import Orbit, build_ephemeris_study, elevation_deg, position


class EphemerisTests(unittest.TestCase):
    def test_position_stays_at_orbit_radius(self) -> None:
        orbit = Orbit("test", 100.0, 88.0, 20.0, 30.0)
        for elapsed in (0, 1000, 10000):
            point = position(orbit, elapsed)
            self.assertAlmostEqual(sum(v * v for v in point) ** 0.5, 1837.4, places=6)

    def test_s024_checks_pass(self) -> None:
        self.assertTrue(all(build_ephemeris_study()["checks"].values()))


if __name__ == "__main__": unittest.main()
