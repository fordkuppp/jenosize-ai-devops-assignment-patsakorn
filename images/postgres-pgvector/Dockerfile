# CloudNativePG's operand images do not ship pgvector, and the extension is a
# compiled module rather than something an init script can create. Building it
# onto the stock operand keeps CNPG's expectations about users, paths and
# entrypoint intact — which a generic postgres image would not.
ARG PG_MAJOR=17
FROM ghcr.io/cloudnative-pg/postgresql:${PG_MAJOR}-bookworm

ARG PG_MAJOR
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends "postgresql-${PG_MAJOR}-pgvector" \
 && rm -rf /var/lib/apt/lists/*
USER 26
