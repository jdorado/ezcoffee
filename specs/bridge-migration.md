# Hosted inference migration

Objective: Ezcoffee chat uses the private Ezenciel bridge, defaulting to
GPT-6.1 Sol at medium, with optional request-level model and effort selection
and native public web lookup for coffee links and roaster comparisons.

Constraints: credentials stay server-only; self-host profile needs no bridge;
preserve account scoping, record revisions and structured action validation;
reuse the existing private VM network; preserve selections on chat retries.

Owner: Ezcoffee owns its request adapter and chat records. The bridge owns its
supported model/effort catalogue and CLI execution.

Simplest path: replace the OpenRouter adapter with the existing bridge contract
and keep the current chat UI and canonical record writes.
Enable the bridge's opt-in native web capability in Coffee's request adapter;
retain Markdown source links and treat public pages as untrusted reference data.

Proof: focused adapter checks, isolated API contract checks, exact deployment
readback, then a real chat completion through the deployed adapter.

Stop: only unavailable owner authentication for the signed-in UI verification.
