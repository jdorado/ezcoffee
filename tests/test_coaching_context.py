import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'coffee_api'))
from src.services.coaching_context import bounded_history, family_coffee_ids, owner_grind_adjustment, preferred_shot


class CoachingEvidence(unittest.TestCase):
    def test_enjoyment_is_not_overridden_by_balance(self):
        newer = {'id': 'enjoyed', 'rating': 3, 'grind': '8.5', 'seconds': 45}
        balanced = {'id': 'less-enjoyed', 'rating': 2, 'outcome': 'good', 'taste_balance': 'balanced', 'seconds': 49}
        self.assertEqual(preferred_shot([newer, balanced])[0]['id'], 'enjoyed')
        balanced['reference'] = True
        self.assertEqual(preferred_shot([newer, balanced])[0]['id'], 'less-enjoyed')

    def test_correction_is_sourced_from_owner_not_assistant_or_decimal_format(self):
        messages = [{'role': 'user', 'id': 'correction', 'text': "0.1 is not the right step impossible, it's 0.5 steps"},
                    {'role': 'assistant', 'text': 'Use 0.1 steps.'},
                    {'role': 'user', 'text': 'Should we try 0.1 steps?'}]
        self.assertEqual(owner_grind_adjustment(messages)['increment'], .5)
        self.assertEqual(owner_grind_adjustment(messages)['message_id'], 'correction')
        self.assertIsNone(owner_grind_adjustment([{'role': 'user', 'text': 'Grind was 8.5.'}]))
        self.assertIsNone(owner_grind_adjustment([{'role': 'user', 'text': '0.1 steps are impossible.'}]))

    def test_same_bean_family_does_not_include_unrelated_coffees(self):
        rows = [{'id': 'bag', 'bean_id': 'bean'}, {'id': 'old', 'bean_id': 'bean', 'source_coffee_id': 'bag', 'archived': True},
                {'id': 'new', 'bean_id': 'bean', 'source_coffee_id': 'bag'}, {'id': 'other', 'bean_id': 'other'}]
        self.assertEqual(family_coffee_ids(rows, rows[2]), ['bag', 'old', 'new'])

    def test_bounded_history_keeps_whole_recent_messages_in_order(self):
        messages = [{'role': 'user', 'text': f'{i}: ' + 'x' * 3900} for i in range(40)]
        history = bounded_history(messages)
        self.assertLessEqual(sum(len(row['text']) for row in history), 32000)
        self.assertEqual(history[-1], messages[-1])
        self.assertLessEqual(len(history), 24)


if __name__ == '__main__':
    unittest.main()
