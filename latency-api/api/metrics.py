from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import json
import os
import pathlib

app = FastAPI()

# Enable CORS for POST requests from any origin

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Allow any origin
    allow_credentials=False,
    allow_methods=["*"],            # Allow all HTTP methods (important!)
    allow_headers=["*"],            # Allow all headers
)

# Correct path resolution for Vercel
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
with open(BASE_DIR / "telemetry" / "sample_data.json") as f:
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

            avg_latency = region_df["latency_ms"].mean()
            p95_latency = np.percentile(region_df["latency_ms"], 95)
            avg_uptime = region_df["uptime_pct"].mean() / 100  # Convert % to decimal
            breaches = (region_df["latency_ms"] > threshold).sum()

            result[region] = {
                "avg_latency": round(avg_latency, 2),
                "p95_latency": round(p95_latency, 2),
                "avg_uptime": round(avg_uptime, 4),
                "breaches": int(breaches)
            }

        return result or {"message": "No data for given regions"}

    except Exception as e:
        return {"error": str(e)}
