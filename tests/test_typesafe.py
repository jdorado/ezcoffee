import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "coffee_api"))

from src.services.typesafe import TypeSafeConfigError, TypeSafeSettings, build_payload


class TypeSafeContract(unittest.TestCase):
    def settings(self):
        return TypeSafeSettings("unit-test-value", "jev-latest", "https://example.invalid/v1", 10)

    def test_payload_contains_full_state_and_closed_candidates(self):
        state = {"coffee": {"roast_age_days": 12}, "owner_guidance": "Make it sweeter", "shots": [{"id": str(index), "taste": "sour"} for index in range(10)]}
        candidates = {
            "finer": {"label": "Grind one step finer", "plan": {"grind": "4.9"}},
            "repeat": {"label": "Repeat", "plan": {"grind": "5"}},
        }
        payload = build_payload(state, candidates, self.settings())
        self.assertEqual(len(payload["state"]["shots"]), 10)
        self.assertEqual(set(payload["questions"]["next_shot"]["criteria"]), set(candidates))
        self.assertEqual(payload["state"]["coffee"]["roast_age_days"], 12)
        self.assertEqual(payload["state"]["owner_guidance"], "Make it sweeter")
        self.assertNotIn("unit-test-value", str(payload))

    def test_configuration_requires_server_key(self):
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": ""}, clear=False):
            with self.assertRaises(TypeSafeConfigError):
                TypeSafeSettings.from_env()


if __name__ == "__main__":
    unittest.main()
