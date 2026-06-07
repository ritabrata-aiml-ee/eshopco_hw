from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import numpy as np
from pathlib import Path

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data
DATA_FILE = Path(__file__).parent.parent / "telemetry.json"

with open(DATA_FILE, "r") as f:
    telemetry = json.load(f)


class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float


@app.post("/")
async def analyze_latency(payload: RequestBody):

    response = {}

    for region in payload.regions:

        region_rows = [
            row
            for row in telemetry
            if row["region"].lower() == region.lower()
        ]

        if not region_rows:
            response[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0
            }
            continue

        latencies = [r["latency_ms"] for r in region_rows]
        uptimes = [r["uptime_pct"] for r in region_rows]

        response[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 3),
            "breaches": int(
                sum(
                    1
                    for latency in latencies
                    if latency > payload.threshold_ms
                )
            )
        }

    return response