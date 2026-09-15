# Same VM CLI system as AIFit; carries the installed, tested Codex binary.
ARG CODEX_BASE_IMAGE=node:22-bookworm-slim
FROM ${CODEX_BASE_IMAGE}
WORKDIR /coffee
COPY coffee_api/coffee_ai/package.json coffee_api/coffee_ai/server.mjs coffee_api/coffee_ai/codex.mjs ./
COPY coffee_api/coffee_ai/workspace/AGENTS.md /opt/coffee/AGENTS.md
COPY coffee_api/coffee_ai/runtime/bin/coffee.mjs /opt/coffee/coffee.mjs
COPY ops/start-ai.sh /opt/coffee/start-ai.sh
ENV HOME=/srv/coffee/home CODEX_HOME=/srv/coffee/codex-home WORKSPACE_DIR=/srv/coffee/workspace AI_HOST=0.0.0.0 AI_PORT=8102 COFFEE_API_URL=http://api:8080
ENTRYPOINT ["sh", "/opt/coffee/start-ai.sh"]
