#!/usr/bin/env python3
"""Fetch current + forecast Amber Electric prices for SmartShift advisor."""
import json
import os
import sys
import urllib.request

API_KEY = os.environ.get("AMBER_API_KEY", "")
SITE_ID = os.environ.get("AMBER_SITE_ID", "")

def main():
    if not API_KEY:
        # Try loading from ha-smartshift .env
        env_file = "/home/bowen/ha-smartshift/.env"
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("AMBER_API_KEY="):
                        globals()["API_KEY"] = line.split("=", 1)[1].strip().strip('"')
                    elif line.startswith("AMBER_SITE_ID="):
                        globals()["SITE_ID"] = line.split("=", 1)[1].strip().strip('"')

    api_key = API_KEY or globals().get("API_KEY", "")
    site_id = SITE_ID or globals().get("SITE_ID", "")

    if not api_key or not site_id:
        print(json.dumps({"error": "AMBER_API_KEY or AMBER_SITE_ID not set"}))
        sys.exit(1)

    # Fetch current + next 144 intervals (12 hours of 5-min intervals)
    url = f"https://api.amber.com.au/v1/sites/{site_id}/prices/current?next=144&previous=0"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    result = {"current": {}, "forecast_buy": [], "forecast_earn": []}

    for item in data:
        ch = item.get("channelType", "")
        typ = item.get("type", "")
        entry = {
            "time": item.get("nemTime", ""),
            "perKwh": item.get("perKwh"),
            "spotPerKwh": item.get("spotPerKwh"),
            "descriptor": item.get("descriptor", ""),
            "spikeStatus": item.get("spikeStatus", ""),
        }

        if typ == "CurrentInterval":
            if ch == "general":
                result["current"]["buy"] = entry
            elif ch == "feedIn":
                result["current"]["earn"] = {**entry, "earn_ckwh": round(-entry["perKwh"], 2)}
        elif typ == "ForecastInterval":
            if ch == "general":
                result["forecast_buy"].append(entry)
            elif ch == "feedIn":
                result["forecast_earn"].append({**entry, "earn_ckwh": round(-entry["perKwh"], 2)})

    # Summary stats
    earns = [e["earn_ckwh"] for e in result["forecast_earn"]]
    if earns:
        result["summary"] = {
            "max_earn_ckwh": max(earns),
            "min_earn_ckwh": min(earns),
            "avg_earn_ckwh": round(sum(earns) / len(earns), 2),
            "intervals_above_10c": sum(1 for e in earns if e >= 10),
            "intervals_above_15c": sum(1 for e in earns if e >= 15),
            "forecast_hours": round(len(earns) * 5 / 60, 1),
        }

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
