#!/bin/bash
set -euo pipefail
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE checkin_service_db OWNER $POSTGRES_USER;
    CREATE DATABASE notification_worker_db OWNER $POSTGRES_USER;
EOSQL
