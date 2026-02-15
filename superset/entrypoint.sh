#!/bin/bash
set -e

superset db upgrade

superset fab create-admin \
  --username admin \
  --firstname admin \
  --lastname admin \
  --email admin@admin.com \
  --password admin || true

superset init

superset import-datasources -p /app/import/datasources.zip -u admin || echo "error"
superset import_dashboards -p /app/import/dashboards.zip -u admin || echo "error"

exec superset run -h 0.0.0.0 -p 8088
