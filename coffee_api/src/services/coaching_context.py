"""Bounded context from canonical records and original owner messages; no new ledger."""
import re

HISTORY_MESSAGES = 24
HISTORY_CHARS = 32000
COACHING_GUIDANCE = """Separate measured brew facts, the owner's reported taste and enjoyment, and hypotheses. The owner's conversation feedback is evidence even when a shot's taste fields are empty; quote its source and do not invent a persisted measurement. Balanced describes taste balance, not enjoyment: a lower-rated balanced shot is not automatically preferable to a higher-rated slightly sour shot enjoyed in milk. Respect the intended drink and the owner's preferred tradeoff.
Use current-batch results first, same_bean_history for earlier bags or batches second, and other-coffee references as tentative starting points. An earlier batch's locked shot is a benchmark, not proof this batch will reproduce it. preferred_recipe_reason explains the evidence behind the supplied anchor; candidates are optional tests, not commands.
Use only an explicitly supplied grind adjustment increment. Decimal formatting does not establish a step size, and the owner's practical increment is not a universal hardware detent. If no increment is known, ask or describe the direction without inventing a number. Owner assertions about direction still need checking against equipment and measured records.
Do not equate shot time with extraction or taste. A sour fast shot may justify finer grinding, but a slow sour shot needs consideration of ratio, temperature, preparation and uneven extraction before more resistance. A balanced enjoyable slow shot need not be shortened just to meet a time target. Longer yield can increase extraction but dilute strength; shorter yield can improve preference while leaving more acidity. Do not promise a precise time, better taste or extra body from a setting change. Avoid automatic two-step corrections or changing multiple variables. Explain the evidence, tradeoff and what the next test would establish.
Coffee process, roast and frozen storage provide context, not a proven cause of a particular flavor or flow. Do not diagnose damaged or muted beans from a different portion alone. Resist requests to agree with a false fact or provide unwarranted certainty. Keep a consistent recommendation unless new evidence or a changed goal justifies revising it; then acknowledge the revision and name the reason."""


def bounded_history(messages):
    result, remaining = [], HISTORY_CHARS
    for row in reversed(messages[-HISTORY_MESSAGES:]):
        if row.get('role') not in ('user', 'assistant') or not row.get('text', '').strip():
            continue
        value = row['text'][:4000 if row['role'] == 'user' else 2000]
        if len(value) > remaining:
            break  # Keep whole messages; do not cut away the end of a correction.
        result.append({**row, 'text': value})
        remaining -= len(value)
    return list(reversed(result))


def owner_grind_adjustment(messages):
    for row in reversed(messages):
        if row.get('role') != 'user':
            continue
        text = row.get('text', '')
        # Exact owner declarations only. Never take a suggested setting or an
        # assistant's guess as a constraint. Negated statements are skipped.
        matches = list(re.finditer(r'(\d+(?:\.\d+)?)\s*(?:grind\s*)?(?:steps?|increments?)\b', text, re.I))
        for match in reversed(matches):
            trailing = text[match.end():match.end()+45].lower()
            if re.match(r'\s*(?:is|are)?\s*(?:not|wrong|impossible|invalid)', trailing):
                continue
            if re.search(r'(?:try|maybe|should|could|would)\b', text[:match.start()][-35:], re.I):
                continue
            step = float(match.group(1))
            if step > 0:
                return {'increment': step, 'source': 'owner_message', 'message_id': row.get('id'),
                        'coffee_id': row.get('coffee_id'), 'quote': text[:4000],
                        'meaning': 'Owner practical adjustment increment, not a hardware detent.'}
        if re.search(r'steps?\s+are\s+half\s+(?:decimals|steps)', text, re.I):
            return {'increment': .5, 'source': 'owner_message', 'message_id': row.get('id'),
                    'coffee_id': row.get('coffee_id'), 'quote': text[:4000],
                    'meaning': 'Owner practical adjustment increment, not a hardware detent.'}
    return None


def preferred_shot(rows):
    viable = [row for row in rows if row.get('outcome') not in ('bad', 'choked') and not row.get('choked')]
    for field in ('reference', 'locked'):
        marked = next((row for row in viable if row.get(field)), None)
        if marked:
            return marked, f'Owner-marked {field} in this batch.'
    rated = [row for row in viable if row.get('rating') is not None]
    if rated:
        return max(rated, key=lambda row: row['rating']), 'Highest recorded enjoyment rating in this batch; balance is separate.'
    good = next((row for row in viable if row.get('outcome') == 'good'), None)
    if good:
        return good, 'Unrated good outcome; enjoyment has not been established.'
    return (viable[0], 'Most recent viable recipe; no rated or owner-marked success.') if viable else (None, 'No viable anchor.')


def family_coffee_ids(coffees, selected):
    if not selected:
        return []
    bean = selected.get('bean_id')
    bag = selected.get('source_coffee_id') or selected['id']
    return [row['id'] for row in coffees if row['id'] == selected['id'] or
            (bean and row.get('bean_id') == bean) or row['id'] == bag or row.get('source_coffee_id') == bag]


def enrich_records(records, owner_messages, selected_shots, related_shots, candidate_builder, facts):
    """Shared by live context construction and offline replay (never writes records)."""
    equipment = records['equipment_context']
    equipment['grind_adjustment'] = owner_grind_adjustment(owner_messages)
    anchor, reason = preferred_shot(selected_shots)
    records['best_shot_for_coffee'] = {**anchor, 'facts': facts(anchor)} if anchor else None
    records['preferred_recipe_reason'] = reason
    step = (equipment.get('grind_adjustment') or {}).get('increment')
    records['next_shot_candidates'] = candidate_builder(anchor, constraints={'grind_step': step}) if anchor else {}
    records['same_bean_history'] = related_shots[:12]
    reports, remaining = [], 12000
    for row in reversed(owner_messages):
        if row.get('role') != 'user' or len(reports) >= 12:
            continue
        quote = row.get('text', '')[:4000]
        if len(quote) > remaining:
            break
        reports.append({'source': 'owner_message', 'message_id': row.get('id'),
                        'coffee_id': row.get('coffee_id'), 'quote': quote})
        remaining -= len(quote)
    records['owner_reports'] = list(reversed(reports))
    records['evidence_limits'] = ['Owner messages are original reports, not measured shot fields.',
        'Same bean can have different bag/batch freshness and preparation; compare provenance.',
        'Candidates are tests, not predictions; missing values remain unknown.']
