from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from gatewaycx.conformance import validate_bearer_profile, validate_file


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "profiles" / "bearers"


class BearerConformanceTests(unittest.TestCase):
    def test_published_schema_is_json(self) -> None:
        schema = ROOT / "spec" / "schema" / "gatewaycx-bearer-profile.schema.json"
        self.assertEqual(json.loads(schema.read_text())["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_reference_profiles_pass(self) -> None:
        for path in sorted(PROFILES.glob("*.json")):
            with self.subTest(path=path.name):
                self.assertEqual(validate_file(path), [])

    def test_scheduled_profile_requires_contact_plan(self) -> None:
        profile = json.loads((PROFILES / "reference-optical.json").read_text())
        profile["availability"].pop("contact_plan_uri")
        self.assertIn(
            "scheduled availability requires contact_plan_uri",
            validate_bearer_profile(profile),
        )

    def test_end_to_end_payload_boundary_is_explicit(self) -> None:
        profile = json.loads((PROFILES / "reference-rf.json").read_text())
        profile["security"]["payload_treatment"] = "terminated"
        self.assertIn(
            "non-transparent payload treatment requires termination_disclosure",
            validate_bearer_profile(profile),
        )

    def test_deferred_acceptance_requires_durable_queue(self) -> None:
        profile = json.loads((PROFILES / "reference-rf.json").read_text())
        profile["queue"]["durable_bytes"] = 0
        self.assertIn(
            "deferred delivery requires non-zero durable_bytes",
            validate_bearer_profile(profile),
        )

    def test_qualification_requires_report(self) -> None:
        profile = json.loads((PROFILES / "reference-rf.json").read_text())
        qualified = copy.deepcopy(profile)
        qualified["evidence"]["level"] = "qualified"
        self.assertIn(
            "qualified evidence requires conformance_report_uri",
            validate_bearer_profile(qualified),
        )


if __name__ == "__main__":
    unittest.main()
