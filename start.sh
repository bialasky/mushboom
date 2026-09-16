#!/bin/sh
set -eu

mkdir -p /app/forecast/data/cache

# Next.js rewrites /api/* to this process. Bind loopback only.
cd /app/forecast
uvicorn mushboom.api:app --host 127.0.0.1 --port 8000 &

# Coolify hits this port from outside the container.
cd /app/web
exec ./node_modules/.bin/next start --hostname 0.0.0.0 --port 3000
