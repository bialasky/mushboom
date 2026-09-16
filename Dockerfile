# Single-container Coolify image: Next.js on :3000, FastAPI on 127.0.0.1:8000.
# TimesFM/torch are intentionally omitted — kernel + Open-Meteo is enough.

# --- Next.js build ---
FROM node:22-bookworm-slim AS web-builder

WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
ENV NEXT_TELEMETRY_DISABLED=1
# Keep typescript: `next start` loads next.config.ts and will npm-install it
# at boot if missing (bad for Coolify if the registry is slow or blocked).
RUN npm run build

# --- Runtime: Python 3.12 + Node 22 ---
FROM python:3.12-slim-bookworm

COPY --from=node:22-bookworm-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:22-bookworm-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Keep the repo layout so mushboom imports and data/cache paths resolve
# (geography.py / pipeline.py use Path(__file__).parent.parent / "data").
COPY forecast/pyproject.toml /app/forecast/pyproject.toml
COPY forecast/mushboom /app/forecast/mushboom
COPY forecast/data/powiaty.geojson /app/forecast/data/powiaty.geojson
COPY forecast/data/wojewodztwa.geojson /app/forecast/data/wojewodztwa.geojson

WORKDIR /app/forecast
# Editable install: deps from pyproject (no [timesfm] extra), source stays here.
RUN uv pip install --system --no-cache -e . \
    && mkdir -p /app/forecast/data/cache

COPY --from=web-builder /app/web /app/web

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/forecast \
    NEXT_TELEMETRY_DISABLED=1

EXPOSE 3000

WORKDIR /app
CMD ["./start.sh"]
