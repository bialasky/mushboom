"""TimesFM-3.0 wrapper.

The model forecasts the next 14 days of precipitation, humidity, and nights
as one multivariate series. The fruiting kernel then reads that forecast.

If the checkpoint is missing or the machine cannot load 330M weights, the
pipeline keeps the Open-Meteo + kernel path and says so.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

CONTEXT = 64
HORIZON = 14


@dataclass
class TimesFMStatus:
    available: bool
    device: str
    error: str | None = None
    license: str = "TimesFM 3.0 weights: non-commercial, non-production"


class TimesFMEngine:
    def __init__(self) -> None:
        self.status = TimesFMStatus(available=False, device="none", error="not loaded")
        self._forecaster: Any = None

    def load(self) -> TimesFMStatus:
        try:
            import torch
            from timesfm3 import ModelConfig, TimesFM3Evaluator
        except Exception as exc:
            self.status = TimesFMStatus(available=False, device="none", error=str(exc))
            return self.status

        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

        try:
            self._forecaster = TimesFM3Evaluator(
                ModelConfig(
                    checkpoint_path="google/timesfm-3.0-pytorch",
                    per_core_batch_size=8,
                    device=device,
                )
            )
            self.status = TimesFMStatus(available=True, device=device)
        except Exception as exc:
            self.status = TimesFMStatus(available=False, device=device, error=str(exc))
        return self.status

    def forecast_weather(
        self,
        precip: np.ndarray,
        humidity: np.ndarray,
        tmin: np.ndarray,
    ) -> dict[str, np.ndarray] | None:
        if not self.status.available or self._forecaster is None:
            return None
        n = int(min(len(precip), len(humidity), len(tmin)))
        if n < 16:
            return None
        ctx = min(CONTEXT, n)
        target = np.stack(
            [
                precip[n - ctx : n],
                humidity[n - ctx : n],
                tmin[n - ctx : n],
            ]
        ).astype(np.float32)
        try:
            outputs = list(
                self._forecaster.predict_batch(
                    contexts=[target],
                    horizon=HORIZON,
                    return_quantiles=True,
                    use_symmetric_averaging=False,
                )
            )
        except TypeError:
            outputs = list(
                self._forecaster.predict_batch(
                    contexts=[target],
                    horizon=HORIZON,
                    return_quantiles=True,
                )
            )
        except Exception:
            return None
        if not outputs:
            return None
        point = np.asarray(outputs[0].forecast, dtype=np.float64)
        quantiles = getattr(outputs[0], "quantiles", None)
        q10 = q90 = None
        if quantiles is not None:
            q = np.asarray(quantiles, dtype=np.float64)
            if q.ndim == 3 and q.shape[-1] >= 9:
                q10, q90 = q[:, :, 0], q[:, :, 8]
        return {
            "precip": point[0],
            "humidity": point[1],
            "tmin": point[2],
            "precip_q10": None if q10 is None else q10[0],
            "precip_q90": None if q90 is None else q90[0],
        }


def aggregate_series(rows: list[dict[str, Any]], indexes: list[int]) -> dict[str, np.ndarray]:
    precip = np.mean(np.stack([rows[i]["precip"] for i in indexes]), axis=0)
    humidity = np.mean(np.stack([rows[i]["humidity"] for i in indexes]), axis=0)
    tmin = np.mean(np.stack([rows[i]["tmin"] for i in indexes]), axis=0)
    return {"precip": precip, "humidity": humidity, "tmin": tmin}
