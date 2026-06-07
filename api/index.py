from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from pathlib import Path
import json
import numpy as np

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Access-Control-Allow-Origin"],
)

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS,HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"

    return response


# Load telemetry data
DATA_FILE = Path(__file__).parent.parent / "telemetry.json"

with open(DATA_FILE, "r") as f:
    telemetry = json.load(f)


class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float


@app.get("/")
async def root():
    return {"status": "ok"}


@app.head("/")
async def head_root():
    return JSONResponse(content={})


@app.options("/")
async def options_root():
    return {"status": "ok"}


@app.post("/")
async def analyze_latency(payload: RequestBody):

    regions_output = []

    for region in payload.regions:

        region_rows = [
            row
            for row in telemetry
            if row.get("region", "").lower() == region.lower()
        ]

        if not region_rows:
            regions_output.append(
                {
                    "region": region,
                    "avg_latency": 0.0,
                    "p95_latency": 0.0,
                    "avg_uptime": 0.0,
                    "breaches": 0,
                }
            )
            continue

        latencies = [row["latency_ms"] for row in region_rows]
        uptimes = [row["uptime_pct"] for row in region_rows]

        regions_output.append(
            {
                "region": region,
                "avg_latency": float(np.mean(latencies)),
                "p95_latency": float(np.percentile(latencies, 95)),
                "avg_uptime": float(np.mean(uptimes)),
                "breaches": int(
                    sum(
                        1
                        for latency in latencies
                        if latency > payload.threshold_ms
                    )
                ),
            }
        )

    return {
        "regions": regions_output
    }