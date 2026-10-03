# Coffee coach replay benchmark

Run from the repository root with `coffee_api/.venv/bin/python`.

```sh
coffee_api/.venv/bin/python scripts/benchmark_coach.py prepare --coffee-id COFFEE_ID --start-message-id MESSAGE_ID
coffee_api/.venv/bin/python scripts/benchmark_coach.py run
coffee_api/.venv/bin/python scripts/benchmark_coach.py summarize
```

`prepare` uses the ignored `data/chat-review-2026-10-03.json` export to select
the specified conversation, then reads the current production context without
starting the API or chat jobs. It saves the original snippets, eight user
turns, frozen system prompt, schema, current records, and qualitative rubric
in `data/coach-benchmark/fixture.json`. This is a replay against current frozen
records, **not an exact reconstruction of every historical prompt**.

`run` requests Muse Spark 1.3 Contributor at medium and high reasoning from
OpenRouter. Each runs the same eight turns twice: the production history limit
(one prior exchange) and full history. Each candidate generates its own answers;
the original assistant answers are never fed into the replay. Temperature,
schema and instructions stay the same. Suggested plan changes are applied to
an in-memory copy; no Mongo writes, deployment or production model changes occur.
The original candidate generator's 0.1-step suggestions remain in the fixture.

Results retain visible responses, supplied messages, model/provider/request IDs,
usage/cost if supplied, latency, fixture/request hashes and mechanical action
checks. They do not store credentials or private reasoning. There is no silent
retry or fallback to another model. An unsuccessful run records its stopping
turn. A single run per configuration is exploratory, not a statistical ranking.

To compare xhigh with enriched context, preserve the original frozen fixture:

```sh
coffee_api/.venv/bin/python scripts/benchmark_coach.py run --effort xhigh
coffee_api/.venv/bin/python scripts/benchmark_coach.py enrich
coffee_api/.venv/bin/python scripts/benchmark_coach.py run --directory data/coach-benchmark-enriched --effort high xhigh --history enriched
coffee_api/.venv/bin/python scripts/benchmark_coach.py summarize --directory data/coach-benchmark-enriched
```

Enrichment reuses the live context helpers: bounded same-bean conversation,
owner step declarations with their original quotation, earlier bag/batch results,
enjoyment-aware recipe selection, and evidence-aware coaching guidance. It uses
the same frozen brew records. Only original messages before the first replay
turn seed history, with each candidate's own messages added as the replay runs.
Future turns and original assistant answers from the replay are excluded. This
tests the context-and-guidance bundle, not an isolated history-length change.

To compare MiMo with the same enriched fixture without overwriting Muse results:

```sh
coffee_api/.venv/bin/python scripts/benchmark_coach.py run --directory data/coach-benchmark-enriched --model xiaomi/mimo-v2.6-pro --effort high xhigh --history enriched --max-tokens 8192
```

The explicit output budget includes reasoning tokens and avoids a provider's
large default output reservation. Requested effort labels do not establish equal
reasoning budgets across model families. Record truncation and provider receipts
alongside advice quality; the existing Muse runs used their default output budget.
Use `--resume` to continue a matching saved run without repeating successful
turns; preserve the stopped attempt separately first. A resumed run verifies the
model, transport, effort, history mode and frozen fixture hash. Each new turn
records its requested output budget. Switching transport creates a separate run.

For a native GPT-6.1 Sol low subagent, use `export-turn`, have the candidate
read `sol-next-turn.json` and save its schema-conforming answer, then ingest it:

```sh
coffee_api/.venv/bin/python scripts/benchmark_coach.py export-turn
coffee_api/.venv/bin/python scripts/benchmark_coach.py ingest --response data/coach-benchmark/sol-response-1.json
```

Repeat for each turn, without revealing future turns or the scoring rubric to
the candidate. Native Sol uses full history; compare it directly with Muse full
history, and use Muse production versus full to examine context loss. The native
agent transport does not expose the same temperature, provider token usage or
API latency controls; treat transport as a comparison limitation.

An optional OpenCode Go route uses Responses for Muse and Chat Completions for
MiMo, the same structured-output schema, and `--transport opencode-go`.
MiMo Chat Completions sends `reasoning_effort`; acceptance does not prove the
upstream applied that effort. Go rejected MiMo xhigh in the October comparison.
Credentials come from
`OPENCODE_GO_API_KEY` or the existing local OpenCode auth file; they are never
printed or copied into artifacts. The client identifies itself honestly and
sends a stable conversation session ID. Its results are labeled separately
from OpenRouter, so changing transport does not silently replace a comparison.

Review the qualitative rubric alongside mechanical checks. Mentioning 8.4 to
reject it is different from recommending 8.4. Changing advice after new taste
evidence is different from agreeing with a false claim. Do not grade purely by
keywords or by whether the coach chose one predetermined grind.

All real snippets, fixtures, answers and reports stay under ignored `data/`.
To preserve a run, choose a fresh `--directory` for preparation and execution.
Do not commit these private files.
