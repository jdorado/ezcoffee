import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "coffee_api"))

from src.services.openrouter import (
    SYSTEM_PROMPT,
    OpenRouterConfigError,
    OpenRouterError,
    OpenRouterSettings,
    build_payload,
    response_result,
    validate_plan_sync,
)


class OpenRouterContract(unittest.TestCase):
    def test_concrete_next_recipe_updates_the_existing_plan(self):
        self.assertIn('same planned record', SYSTEM_PROMPT)
        self.assertIn('Never create a second planned shot', SYSTEM_PROMPT)
        self.assertIn('even when the user asked only for advice', SYSTEM_PROMPT)
        self.assertIn('you MUST return one update action', SYSTEM_PROMPT)

    def test_reply_contract_uses_markdown_emphasis(self):
        self.assertIn('concise Markdown', SYSTEM_PROMPT)
        self.assertIn('Bold the important brew numbers', SYSTEM_PROMPT)

    def test_cross_coffee_questions_use_the_bounded_overview(self):
        self.assertIn('current_records.coffee_overview', SYSTEM_PROMPT)
        self.assertIn('current_records.coffee_catalog', SYSTEM_PROMPT)
        self.assertIn('current_records.equipment_context', SYSTEM_PROMPT)
        self.assertIn('authoritative cross-coffee and equipment context', SYSTEM_PROMPT)

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
        self.assertEqual(payload["provider"], {"only": ["baseten/fp8"], "allow_fallbacks": False})
        self.assertTrue(payload["response_format"]["json_schema"]["strict"])
        self.assertEqual(len(payload["messages"]), 4)
        self.assertEqual(payload["messages"][1]["content"], "message 8")
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

    def test_next_recipe_cannot_leave_the_planned_shot_stale(self):
        prompt = '{"current_records":{"planned_next_shot":{"id":"plan-1","revision":4}}}'
        stale = response_result({"choices": [{"message": {"content": '{"reply":"Next test: grind finer. Change only the grind.","actions":[]}'}}]})
        with self.assertRaises(OpenRouterError):
            validate_plan_sync(prompt, stale)
        synced = response_result({"choices": [{"message": {"content": '{"reply":"Next test: grind finer.","actions":[{"kind":"shot","id":"plan-1","data_json":"{\\"revision\\":4,\\"grind\\":\\"8.5\\",\\"status\\":\\"planned\\"}"}]}'}}]})
        validate_plan_sync(prompt, synced)

    def test_enabled_configuration_requires_a_server_key(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            with self.assertRaises(OpenRouterConfigError):
                OpenRouterSettings.from_env()


if __name__ == "__main__":
    unittest.main()
