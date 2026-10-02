FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@10.30.3 --activate
COPY coffee_app/package.json coffee_app/pnpm-lock.yaml coffee_app/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile --no-optional
COPY coffee_app/ ./
ARG APP_MODE=selfhost
ARG CHAT_ENABLED=false
ARG ESPRESSO_MACHINE_LABEL
ARG GRINDER_LABEL
ARG DEFAULT_DOSE_G
ARG DEFAULT_GRIND
ARG DEFAULT_BASKET
ARG DEFAULT_PAPER=unknown
ARG DEFAULT_TEMP
ARG DEFAULT_PUCK_SCREEN=unknown
ENV APP_MODE=$APP_MODE CHAT_ENABLED=$CHAT_ENABLED API_BASE_URL=/api \
    ESPRESSO_MACHINE_LABEL=$ESPRESSO_MACHINE_LABEL GRINDER_LABEL=$GRINDER_LABEL \
    DEFAULT_DOSE_G=$DEFAULT_DOSE_G DEFAULT_GRIND=$DEFAULT_GRIND DEFAULT_BASKET=$DEFAULT_BASKET \
    DEFAULT_PAPER=$DEFAULT_PAPER DEFAULT_TEMP=$DEFAULT_TEMP DEFAULT_PUCK_SCREEN=$DEFAULT_PUCK_SCREEN
RUN pnpm run build:selfhost

FROM nginx:1.27-alpine
COPY coffee_app/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
