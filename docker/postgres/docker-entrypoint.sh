#!/usr/bin/env bash
set -euo pipefail

readonly PG_BIN_DIR="/usr/lib/postgresql/15/bin"

: "${PGDATA:=/var/lib/postgresql/data}"
: "${POSTGRES_DB:=echodaily}"
: "${POSTGRES_USER:=echodaily}"
: "${POSTGRES_PASSWORD:=echodaily}"

mkdir -p "${PGDATA}" /run/postgresql
chown -R postgres:postgres "${PGDATA}" /run/postgresql
chmod 700 "${PGDATA}"

if [[ ! -s "${PGDATA}/PG_VERSION" ]]; then
  runuser -u postgres -- "${PG_BIN_DIR}/initdb" -D "${PGDATA}"

  {
    echo "listen_addresses = '*'"
    echo "port = 5432"
  } >> "${PGDATA}/postgresql.conf"

  cat > "${PGDATA}/pg_hba.conf" <<'EOF'
local   all             all                                     trust
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256
host    all             all             0.0.0.0/0               scram-sha-256
host    all             all             ::/0                    scram-sha-256
EOF

  runuser -u postgres -- "${PG_BIN_DIR}/pg_ctl" -D "${PGDATA}" -w start

  runuser -u postgres -- psql --username postgres --dbname postgres -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${POSTGRES_USER}') THEN
        CREATE ROLE ${POSTGRES_USER} LOGIN PASSWORD '${POSTGRES_PASSWORD}';
    ELSE
        ALTER ROLE ${POSTGRES_USER} WITH LOGIN PASSWORD '${POSTGRES_PASSWORD}';
    END IF;
END
\$\$;

SELECT 'CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER}'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '${POSTGRES_DB}')\gexec

GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};
SQL

  runuser -u postgres -- "${PG_BIN_DIR}/pg_ctl" -D "${PGDATA}" -m fast -w stop
fi

exec runuser -u postgres -- "${PG_BIN_DIR}/postgres" -D "${PGDATA}"
