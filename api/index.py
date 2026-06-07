from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from pathlib import Path
import json
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS,HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"

    return response


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
    return JSONResponse(content={"status": "ok"})


@app.post("/")
async def analyze_latency(payload: RequestBody):

    result = {}

    for region in payload.regions:

        rows = [
            row
            for row in telemetry
            if row["region"].lower() == region.lower()
        ]

        if not rows:
            result[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0,
            }
            continue

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]

        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 3),
            "breaches": int(
                sum(
                    1
                    for latency in latencies
                    if latency > payload.threshold_ms
                )
            ),
        }

    return result