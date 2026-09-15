// Adapted from AIFit aifit_ai/server.mjs.
export function buildCodexArgs(selection = {}, sessionId = null) {
  const limit = Number(process.env.CODEX_AUTO_COMPACT_TOKEN_LIMIT || 32000);
  const args = [
    "--ask-for-approval",
    "never",
    "exec",
    "--skip-git-repo-check",
    "--sandbox",
    "danger-full-access",
    "--color",
    "never",
    "--json",
    "-c",
    `model_auto_compact_token_limit=${Number.isSafeInteger(limit) && limit > 0 ? limit : 32000}`,
  ];

  const model = selection.model || process.env.CODEX_MODEL?.trim();
  const reasoningEffort = (
    selection.reasoningEffort
    || process.env.CODEX_REASONING_EFFORT?.trim().toLowerCase()
  );
  if (model) {
    args.push("--model", model);
  }
  if (reasoningEffort) {
    args.push("-c", `model_reasoning_effort="${reasoningEffort}"`);
  }

  if (sessionId) {
    args.push("resume", sessionId, "-");
  } else {
    args.push("-");
  }
  return args;
}

export function parseCodexJsonl(stdout, expectedSessionId = null) {
  let sessionId = expectedSessionId;
  let answer = "";

  for (const rawLine of stdout.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) continue;
    let event;
    try {
      event = JSON.parse(line);
    } catch {
      throw new Error("Codex returned invalid JSONL output");
    }
    if (event.type === "thread.started" && typeof event.thread_id === "string") {
      sessionId = event.thread_id.trim() || sessionId;
    }
    if (
      event.type === "item.completed"
      && event.item?.type === "agent_message"
      && typeof event.item.text === "string"
    ) {
      answer = event.item.text.trim();
    }
  }

  if (!sessionId) throw new Error("Codex returned no session id");
  if (!answer) throw new Error("Codex returned an empty response");
  return { answer, sessionId };
}
