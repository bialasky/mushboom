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

Open [http://localhost:3000](http://localhost:3000). First forecast takes a bit — 380 counties through Open-Meteo. Results cache for 3 hours in `forecast/data/cache/`.
