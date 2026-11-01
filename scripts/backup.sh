#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

DB_CONTAINER="$(docker ps -q -f name=pytende_db | head -n1)"
[ -n "$DB_CONTAINER" ] || { echo "ERRO: container pytende_db não encontrado."; exit 1; }

echo "[$(date)] Backup do PostgreSQL..."
docker exec "$DB_CONTAINER" sh -c 'pg_dump --clean --if-exists --no-owner -U "$POSTGRES_USER" "$POSTGRES_DB"' \
    | gzip > "${BACKUP_DIR}/db_${DATE}.sql.gz"

echo "[$(date)] Rotação: removendo backups com mais de ${RETENTION_DAYS} dias..."
find "$BACKUP_DIR" -name 'db_*.sql.gz' -mtime +"$RETENTION_DAYS" -delete

echo "[$(date)] Backup concluído: db_${DATE}.sql.gz"
