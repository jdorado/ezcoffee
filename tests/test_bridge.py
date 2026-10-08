import os
import json
import httpx
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "coffee_api"))

from src.services.bridge import (
    SYSTEM_PROMPT,
    BridgeConfigError,
    BridgeError,
    BridgeSettings,
    PlanSyncError,
    build_payload,
    response_result,
    bridge_reply,
    validate_plan_sync,
)


class BridgeContract(unittest.TestCase):
    def test_concrete_next_recipe_updates_the_existing_plan(self):
        self.assertIn('same planned record', SYSTEM_PROMPT)
        self.assertIn('Never create a second planned shot', SYSTEM_PROMPT)
        self.assertIn('even when the user asked only for advice', SYSTEM_PROMPT)
        self.assertIn('you MUST return one update action', SYSTEM_PROMPT)

    def test_reply_contract_uses_markdown_emphasis(self):
        self.assertIn('concise Markdown', SYSTEM_PROMPT)
        self.assertIn('Bold only brew values', SYSTEM_PROMPT)
        self.assertIn('never labels', SYSTEM_PROMPT)
        self.assertIn('Grind: **5.0**', SYSTEM_PROMPT)

    def test_structured_bean_details_guide_dial_in(self):
        self.assertIn('process', SYSTEM_PROMPT)
        self.assertIn('roast_level', SYSTEM_PROMPT)
        self.assertIn('single_origin', SYSTEM_PROMPT)
        self.assertIn('decaf', SYSTEM_PROMPT)
        self.assertIn('Never invent a bean detail', SYSTEM_PROMPT)
        self.assertIn('similar roast age, process, and roast level', SYSTEM_PROMPT)

    def test_cross_coffee_questions_use_the_bounded_overview(self):
        self.assertIn('current_records.coffee_overview', SYSTEM_PROMPT)
        self.assertIn('current_records.coffee_catalog', SYSTEM_PROMPT)
        self.assertIn('current_records.reference_shots', SYSTEM_PROMPT)
        self.assertIn("what's-working reference", SYSTEM_PROMPT)
        self.assertIn('current_records.equipment_context', SYSTEM_PROMPT)
        self.assertIn('authoritative cross-coffee and equipment context', SYSTEM_PROMPT)

    def settings(self):
        return BridgeSettings(
            api_key="unit-test-value",
            model="provider/small-model",
            base_url="https://example.invalid/api/v1",
        )

    def test_payload_is_bounded_and_never_contains_the_key(self):
        history = [
            {"role": "user" if index % 2 == 0 else "assistant", "text": f"message {index}"}
            for index in range(10)
        ]
        payload = build_payload('{"request":"help"}', history, self.settings())
        self.assertEqual(payload["model"], "provider/small-model")
        self.assertNotIn("provider", payload)
        self.assertEqual(payload["reasoning_effort"], "medium")
        self.assertNotIn("max_tokens", payload)
        self.assertTrue(payload["response_format"]["json_schema"]["strict"])
        self.assertEqual(len(payload["messages"]), 12)
        self.assertEqual(payload["messages"][1]["content"], "message 0")
        self.assertNotIn("unit-test-value", str(payload))

    def test_response_requires_assistant_text(self):
        result = response_result({"choices": [{"message": {"content": '{"reply":"Try a finer grind.","actions":[]}'}}]})
        self.assertEqual(result.text, "Try a finer grind.")
        self.assertEqual(result.actions, [])
        with self.assertRaises(BridgeError):
            response_result({"choices": []})

    def test_structured_action_data_is_parsed_before_validation(self):
        result = response_result({"choices": [{"message": {"content": '{"reply":"Logged.","actions":[{"kind":"shot","id":null,"data_json":"{\\"coffee_id\\":\\"coffee-1\\",\\"dose\\":14}"}]}'}}]})
        self.assertEqual(result.actions, [{"kind": "shot", "id": None, "data": {"coffee_id": "coffee-1", "dose": 14}}])

    def test_next_recipe_cannot_leave_the_planned_shot_stale(self):
        prompt = '{"current_records":{"planned_next_shot":{"id":"plan-1","revision":4}}}'
        stale = response_result({"choices": [{"message": {"content": '{"reply":"Next test: grind finer. Change only the grind.","actions":[]}'}}]})
        with self.assertRaises(PlanSyncError):
            validate_plan_sync(prompt, stale)
        with self.assertRaises(BridgeError):
            validate_plan_sync(prompt, stale)
        synced = response_result({"choices": [{"message": {"content": '{"reply":"Next test: grind finer.","actions":[{"kind":"shot","id":"plan-1","data_json":"{\\"revision\\":4,\\"grind\\":\\"8.5\\",\\"status\\":\\"planned\\"}"}]}'}}]})
        validate_plan_sync(prompt, synced)

    def test_invented_plan_id_still_counts_as_a_sync_attempt(self):
        prompt = '{"current_records":{"planned_next_shot":{"id":"plan-1","revision":4}}}'
        invented = response_result({"choices": [{"message": {"content": '{"reply":"Next test: grind finer.","actions":[{"kind":"shot","id":"shot-1","data_json":"{\\"revision\\":0,\\"grind\\":\\"8.5\\",\\"status\\":\\"planned\\"}"}]}'}}]})
        validate_plan_sync(prompt, invented)

    def test_record_ids_must_come_from_supplied_records(self):
        self.assertIn('never invent, guess, or reuse a placeholder id', SYSTEM_PROMPT)
        schema = build_payload('{"request":"help"}', [], self.settings())["response_format"]["json_schema"]["schema"]
        description = schema["properties"]["actions"]["items"]["properties"]["id"]["description"]
        self.assertIn("copied verbatim", description)
        self.assertIn("Never a guessed or placeholder id", description)

    def test_explicit_plan_request_creates_the_planned_shot(self):
        prompt = '{"request":"Plan my next shot for this coffee and save it as the planned shot.","current_records":{}}'
        missing = response_result({"choices": [{"message": {"content": '{"reply":"Use a finer grind.","actions":[]}'}}]})
        with self.assertRaises(PlanSyncError):
            validate_plan_sync(prompt, missing)
        created = response_result({"choices": [{"message": {"content": '{"reply":"Planned.","actions":[{"kind":"shot","id":null,"data_json":"{\\"coffee_id\\":\\"coffee-1\\",\\"status\\":\\"planned\\"}"}]}'}}]})
        validate_plan_sync(prompt, created)

    def test_plan_sync_is_required_even_when_the_recipe_matches(self):
        self.assertIn('even when the recipe matches the plan', SYSTEM_PROMPT)

    def test_tool_guidance_names_revision_example_and_read_only_fields(self):
        self.assertIn('{"revision": 3', SYSTEM_PROMPT)
        self.assertIn('never write ratio', SYSTEM_PROMPT.lower())
        self.assertIn('never put the record id inside data_json', SYSTEM_PROMPT.lower())
        schema = build_payload('{"request":"help"}', [], self.settings())["response_format"]["json_schema"]["schema"]
        description = schema["properties"]["actions"]["items"]["properties"]["data_json"]["description"]
        self.assertIn('revision', description)
        self.assertIn('ratio', description)

    def test_enabled_configuration_requires_a_server_key(self):
        with patch.dict(os.environ, {"BRIDGE_API_KEY": ""}, clear=False):
            with self.assertRaises(BridgeConfigError):
                BridgeSettings.from_env()

    def test_truncated_completion_is_rejected(self):
        with self.assertRaises(BridgeError) as raised:
            response_result({"provider": "Parasail", "choices": [{"finish_reason": "length", "message": {"content": '{"reply":"Channeling here is likely the'}}]})
        self.assertEqual(raised.exception.code, "output_truncated")
        self.assertEqual(raised.exception.provider, "Parasail")
        self.assertEqual(raised.exception.finish_reason, "length")

    def test_invalid_structured_output_reports_provider_and_stage(self):
        with self.assertRaises(BridgeError) as raised:
            response_result({"provider": "Parasail", "choices": [{"finish_reason": "stop", "message": {"content": "not json"}}]})
        self.assertEqual(raised.exception.code, "invalid_structured_output")
        self.assertEqual(raised.exception.provider, "Parasail")
        self.assertEqual(raised.exception.finish_reason, "stop")
        self.assertEqual(raised.exception.stage, "parse")

    def test_bridge_model_and_effort_are_configurable(self):
        with patch.dict(os.environ, {"BRIDGE_API_KEY": "test", "BRIDGE_BASE_URL": "http://bridge/v1", "BRIDGE_MODEL": "claude-sonnet-5-5", "BRIDGE_REASONING_EFFORT": "high"}, clear=False):
            self.assertEqual(BridgeSettings.from_env().model, "claude-sonnet-5-5")
            self.assertEqual(BridgeSettings.from_env().reasoning_effort, "high")


class ReplyRecovery(unittest.IsolatedAsyncioTestCase):
    async def test_request_selection_is_forwarded_to_bridge(self):
        calls = []
        def respond(request):
            calls.append(json.loads(request.content))
            self.assertEqual(request.headers['Authorization'], 'Bearer unit-bridge-secret')
            return httpx.Response(200, json={'provider':'claude','choices':[{'message':{'content':'{"reply":"Use a 1:2 ratio.","actions":[]}'}}]})
        original_client = httpx.AsyncClient
        with patch('src.services.bridge.BridgeSettings.from_env', return_value=BridgeSettings('unit-bridge-secret','gpt-6.1-sol','http://bridge/v1')), patch('src.services.bridge.httpx.AsyncClient', side_effect=lambda **kwargs: original_client(transport=httpx.MockTransport(respond), **kwargs)):
            result = await bridge_reply('{}', [], model='claude-sonnet-5-5', reasoning_effort='high')
        self.assertEqual(calls[0]['model'], 'claude-sonnet-5-5')
        self.assertEqual(calls[0]['reasoning_effort'], 'high')
        self.assertNotIn('unit-bridge-secret', json.dumps(calls[0]))
        self.assertEqual(result.text, 'Use a 1:2 ratio.')

    async def test_punctuation_retries_once_before_returning_action(self):
        calls = []
        action = {"kind": "shot", "id": None, "data_json": json.dumps({"coffee_id": "bag", "status": "planned", "grind": "5.5"})}
        def respond(request):
            calls.append(json.loads(request.content))
            text = "..." if len(calls) == 1 else "Keep the grind at **5.5**; the last shot was balanced."
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"reply": text, "actions": [action]})}}]})
        original_client = httpx.AsyncClient
        with patch("src.services.bridge.BridgeSettings.from_env", return_value=BridgeSettings("test", "test", "https://example.invalid")), patch("src.services.bridge.httpx.AsyncClient", side_effect=lambda **kwargs: original_client(transport=httpx.MockTransport(respond), **kwargs)):
            result = await bridge_reply(json.dumps({"intent": "plan", "selected_coffee_id": "bag", "current_records": {}}), [])
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(result.actions), 1)
        self.assertIn("5.5", result.text)
        self.assertIn("empty_reply", calls[1]["messages"][-1]["content"])

    async def test_repeated_empty_replies_fail_after_two_attempts(self):
        calls = []
        def respond(request):
            calls.append(request)
            return httpx.Response(200, json={"choices": [{"message": {"content": '{"reply":"…","actions":[]}'}}]})
        original_client = httpx.AsyncClient
        with patch("src.services.bridge.BridgeSettings.from_env", return_value=BridgeSettings("test", "test", "https://example.invalid")), patch("src.services.bridge.httpx.AsyncClient", side_effect=lambda **kwargs: original_client(transport=httpx.MockTransport(respond), **kwargs)):
            with self.assertRaises(BridgeError) as raised:
                await bridge_reply('{}', [])
        self.assertEqual(raised.exception.code, "empty_reply")
        self.assertEqual(len(calls), 2)

    def test_plan_intent_requires_selected_plan_action(self):
        from src.services.bridge import BridgeReply
        prompt = json.dumps({"intent": "plan", "selected_coffee_id": "bag", "current_records": {"planned_next_shot": {"id": "plan"}}})
        for action in [None, {"kind": "shot", "id": "wrong", "data": {"status": "planned"}}, {"kind": "shot", "id": "plan", "data": {"status": "logged"}}, {"kind": "shot", "id": "plan", "data": {"coffee_id": "other"}}]:
            with self.assertRaises(PlanSyncError):
                validate_plan_sync(prompt, BridgeReply("Recipe ready.", [] if action is None else [action]))
        validate_plan_sync(prompt, BridgeReply("Keep the same recipe.", [{"kind": "shot", "id": "plan", "data": {"grind": "5.5", "revision": 2}}]))

    def test_markdown_only_replies_are_rejected(self):
        for text in ['...', '…', '** **', '---', '#', '   ']:
            with self.assertRaises(BridgeError):
                response_result({"choices": [{"message": {"content": json.dumps({"reply": text, "actions": []})}}]})

if __name__ == "__main__":
    unittest.main()
