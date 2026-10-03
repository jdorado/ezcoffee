"""Offline simulator boundaries; synthetic records only, no Mongo or provider calls."""
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('coach_benchmark', Path(__file__).resolve().parents[1] / 'scripts/benchmark_coach.py')
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class ReplayBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = {'system': 'Synthetic coach', 'turns': [{'id': str(i), 'text': f'Turn {i}'} for i in range(5)],
                        'context': {'selected_coffee_id': 'synthetic', 'intent': 'chat',
                                    'current_records': {'planned_next_shot': {'id': 'plan', 'revision': 3, 'grind': '8.5'}}}}

    def response(self, **changes):
        return {'reply': 'Keep the plan.', 'actions': [{'kind': 'shot', 'id': 'plan',
                    'data_json': json.dumps({'revision': 3, **changes})}]}

    def test_revision_updates_only_the_simulated_copy(self):
        row = bench.record_turn(self.fixture, [], 'full', self.response(grind='9.0'), {})
        context, _ = bench.turn_messages(self.fixture, [row], 'full')
        self.assertEqual(context['current_records']['planned_next_shot']['revision'], 4)
        self.assertEqual(context['current_records']['planned_next_shot']['grind'], '9.0')
        self.assertEqual(self.fixture['context']['current_records']['planned_next_shot']['grind'], '8.5')

    def test_stale_action_cannot_change_the_simulated_plan(self):
        row = bench.record_turn(self.fixture, [], 'full', self.response(revision=2, grind='9.0'), {})
        self.assertIsNone(row['simulated_patch'])
        self.assertIn('stale_or_missing_revision', row['checks'])

    def test_logged_or_measured_results_are_rejected(self):
        for fields in ({'status': 'logged'}, {'yield_g': 24}, {'rating': 4}):
            with self.subTest(fields=fields):
                row = bench.record_turn(self.fixture, [], 'full', self.response(**fields), {})
                self.assertIsNone(row['simulated_patch'])
                self.assertIn('invented_measured_or_tasting_result', row['checks'])

    def test_history_modes_have_identical_current_request_without_future_turns(self):
        rows = [{'user': f'User {i}', 'reply': f'Reply {i}'} for i in range(3)]
        production_context, production = bench.turn_messages(self.fixture, rows, 'production')
        full_context, full = bench.turn_messages(self.fixture, rows, 'full')
        self.assertEqual(production_context, full_context)
        self.assertEqual(production[1:3], full[-3:-1])
        self.assertEqual(len(production), 4)
        self.assertEqual(len(full), 8)
        self.assertEqual(production_context['request'], 'Turn 3')

    def test_non_owner_step_is_flagged_after_calibration_without_hiding_app_behavior(self):
        self.fixture['turns'][0]['text'] = 'Use 0.5 steps.'
        row = bench.record_turn(self.fixture, [], 'full', self.response(grind='8.4'), {})
        self.assertIn('owner_grind_increment', row['checks'])
        self.assertEqual(row['simulated_patch']['grind'], '8.4')


if __name__ == '__main__':
    unittest.main()
