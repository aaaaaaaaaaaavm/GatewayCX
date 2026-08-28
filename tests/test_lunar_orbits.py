import unittest

from gatewaycx.lunar_orbits import (
    MOON_RADIUS_KM,
    approximate_hill_radius_km,
    build_lunar_orbit_envelope,
    circular_period_s,
    synchronous_radius_km,
)


class LunarOrbitEnvelopeTests(unittest.TestCase):
    def test_synchronous_radius_is_outside_approximate_hill_radius(self) -> None:
        self.assertGreater(synchronous_radius_km(), approximate_hill_radius_km())

    def test_period_rejects_surface_or_lower_radius(self) -> None:
        with self.assertRaises(ValueError):
            circular_period_s(MOON_RADIUS_KM)

    def test_s022_checks_pass(self) -> None:
        result = build_lunar_orbit_envelope()
        self.assertTrue(all(result["checks"].values()))
        self.assertFalse(result["synchronous_case"]["inside_approximate_hill_sphere"])


if __name__ == "__main__":
    unittest.main()
