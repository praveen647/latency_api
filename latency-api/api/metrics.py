from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import json
import os

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry data once
with open(os.path.join(os.path.dirname(__file__), "../telemetry/sample_data.json")) as f:
    data = json.load(f)

df = pd.DataFrame(data)
@app.post("/api/metrics")
async def metrics(request: Request):
    try:
        body = await request.json()
        regions = body.get("regions", [])
        threshold = body.get("threshold_ms", 180)

        result = {}
        for region in regions:
            region_df = df[df["region"] == region]
            if region_df.empty:
                continue

            result[region] = {
                "avg_latency": round(region_df["latency_ms"].mean(), 2),
                "p95_latency": round(np.percentile(region_df["latency_ms"], 95), 2),
                "avg_uptime": round(region_df["uptime"].mean(), 4),
                "breaches": int((region_df["latency_ms"] > threshold).sum())
            }

        return result or {"message": "No data for given regions"}

    except Exception as e:
        return {"error": str(e)}

