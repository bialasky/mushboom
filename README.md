# mushboom

Can you predict a mushroom boom with mathematics? Yes — the **conditions**, not the basket.

Each of Poland’s 380 powiaty gets a 0–100 flush score from a 14-day lagged kernel:

- **Rain** from 14–5 days ago (not yesterday)
- **Nights** around 10–15 °C
- **Humidity** above ~70%
- A September peak, with a weaker spring morel bump

TimesFM-3.0 then forecasts the next 14 days of those three series per voivodeship and nudges the county scores. [grzyby.pl](https://www.grzyby.pl/foto/wystepowanie-0.htm) is an extra comparison layer: forager reports, not mushroom counts.

TimesFM 3.0 weights are **non-commercial**. Weather is Open-Meteo. Powiat outlines are from [ppatrzyk/polska-geojson](https://github.com/ppatrzyk/polska-geojson).

## Run

```bash
cd forecast
uv venv --python 3.12
source .venv/bin/activate
uv pip install fastapi uvicorn httpx numpy pydantic timesfm torch
uvicorn mushboom.api:app --reload --port 8000
```

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The API rebuilds the forecast once a day at **06:00 Europe/Warsaw** and serves that saved file when you open the page. If the process starts after 06:00 and today's snapshot is missing, it builds once in the background, then waits for the next morning. The file is `forecast/data/cache/snapshot.json`.

## Production / Coolify

One Docker image: Next.js on port **3000**, FastAPI on `127.0.0.1:8000` (the Next rewrite talks to localhost). TimesFM and torch are **not** in this image — scores use the kernel + Open-Meteo path.

```bash
docker build -t mushboom .
docker run --rm -p 3000:3000 mushboom
```

In Coolify, build from the repo `Dockerfile` and expose **3000**. Mount `forecast/data/cache` if the morning snapshot should survive a redeploy; otherwise the new container builds once on startup.
