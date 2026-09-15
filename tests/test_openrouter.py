import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "coffee_api"))

from src.services.openrouter import (
    OpenRouterConfigError,
    OpenRouterError,
    OpenRouterSettings,
    build_payload,
    response_result,
)


class OpenRouterContract(unittest.TestCase):
    def settings(self):
        return OpenRouterSettings(
            api_key="unit-test-value",
            model="provider/small-model",
            base_url="https://example.invalid/api/v1",
            max_output_tokens=400,
            timeout_seconds=10,
        )

    def test_payload_is_bounded_and_never_contains_the_key(self):
        history = [
            {"role": "user" if index % 2 == 0 else "assistant", "text": f"message {index}"}
            for index in range(10)
        ]
        payload = build_payload('{"request":"help"}', history, self.settings())
        self.assertEqual(payload["model"], "provider/small-model")
        self.assertEqual(payload["provider"], {"data_collection": "deny", "require_parameters": True})
        self.assertTrue(payload["response_format"]["json_schema"]["strict"])
        self.assertEqual(len(payload["messages"]), 8)
        self.assertEqual(payload["messages"][1]["content"], "message 4")
        self.assertNotIn("unit-test-value", str(payload))

    def test_response_requires_assistant_text(self):
        result = response_result({"choices": [{"message": {"content": '{"reply":"Try a finer grind.","actions":[]}'}}]})
        self.assertEqual(result.text, "Try a finer grind.")
        self.assertEqual(result.actions, [])
        with self.assertRaises(OpenRouterError):
            response_result({"choices": []})

    def test_structured_action_data_is_parsed_before_validation(self):
        result = response_result({"choices": [{"message": {"content": '{"reply":"Logged.","actions":[{"kind":"shot","id":null,"data_json":"{\\"coffee_id\\":\\"coffee-1\\",\\"dose\\":14}"}]}'}}]})
        self.assertEqual(result.actions, [{"kind": "shot", "id": None, "data": {"coffee_id": "coffee-1", "dose": 14}}])

    def test_enabled_configuration_requires_a_server_key(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            with self.assertRaises(OpenRouterConfigError):
                OpenRouterSettings.from_env()


if __name__ == "__main__":
    unittest.main()
