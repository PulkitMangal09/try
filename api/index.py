from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import numpy as np
import json
import os

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data once at startup
with open(os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")) as f:
    telemetry_data = json.load(f)

class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

@app.post("/latency")
async def check_latency(payload: LatencyRequest):
    results: Dict[str, Any] = {}

    for region in payload.regions:
        # Filter records for this region
        region_data = [rec for rec in telemetry_data if rec["region"] == region]

        if not region_data:
            results[region] = {"error": "region not found"}
            continue

        latencies = [rec["latency_ms"] for rec in region_data]
        uptimes = [rec["uptime_pct"] for rec in region_data]

        # Metrics
        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = sum(1 for l in latencies if l > payload.threshold_ms)

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return results
