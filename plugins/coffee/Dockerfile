FROM node:22-alpine AS runtime

WORKDIR /app
COPY --chown=node:node bin/coffee.mjs /app/bin/coffee.mjs
USER node
