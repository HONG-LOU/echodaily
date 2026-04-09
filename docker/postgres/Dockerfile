FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PGDATA=/var/lib/postgresql/data \
    POSTGRES_DB=echodaily \
    POSTGRES_USER=echodaily \
    POSTGRES_PASSWORD=echodaily

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-15 postgresql-client-15 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/lib/postgresql/data /run/postgresql \
    && chown -R postgres:postgres /var/lib/postgresql /run/postgresql

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 5432

ENTRYPOINT ["docker-entrypoint.sh"]
