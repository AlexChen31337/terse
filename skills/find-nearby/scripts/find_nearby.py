#!/usr/bin/env python3
"""
find_nearby.py — Find nearby amenities using OpenStreetMap (Nominatim + Overpass).
No API keys required.

Usage:
    uv run python scripts/find_nearby.py --lat -33.8688 --lon 151.2093 --type restaurant
    uv run python scripts/find_nearby.py --address "Sydney CBD" --type cafe --radius 500
"""

import argparse
import math
import sys
import time

try:
    import requests
except ImportError:
    print("Installing requests...", file=sys.stderr)
    import subprocess
    subprocess.run(["uv", "pip", "install", "requests"], check=True)
    import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "OpenClaw-find-nearby/1.0 (openclaw-agent)"


def geocode_address(address: str) -> tuple[float, float]:
    """Geocode an address to (lat, lon) via Nominatim."""
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
    }
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError(f"Could not geocode address: {address!r}")
    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    display = results[0].get("display_name", "")
    print(f"Geocoded: {display}", file=sys.stderr)
    print(f"Coordinates: {lat}, {lon}", file=sys.stderr)
    # Respect Nominatim rate limit
    time.sleep(1)
    return lat, lon


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in metres between two lat/lon points."""
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def query_overpass(lat: float, lon: float, amenity_type: str, radius: int) -> list[dict]:
    """Query Overpass API for amenity nodes within radius metres."""
    query = (
        f'[out:json][timeout:25];'
        f'node["amenity"="{amenity_type}"](around:{radius},{lat},{lon});'
        f'out body;'
    )
    resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("elements", [])


def extract_address(tags: dict) -> str:
    """Build a human-readable address from OSM tags."""
    parts = []
    for key in ("addr:housenumber", "addr:street", "addr:suburb", "addr:city"):
        val = tags.get(key, "")
        if val:
            parts.append(val)
    return ", ".join(parts) if parts else ""


def format_distance(metres: float) -> str:
    if metres < 1000:
        return f"{metres:.0f} m"
    return f"{metres / 1000:.2f} km"


def build_table(results: list[dict]) -> str:
    """Render results as a markdown table."""
    if not results:
        return "_No results found._"

    header = "| Name | Type | Distance | Address |"
    sep    = "|------|------|----------|---------|"
    rows = [header, sep]
    for r in results:
        name = r.get("name", "(unnamed)")
        atype = r.get("amenity", "")
        dist = format_distance(r["distance"])
        addr = r.get("address", "")
        rows.append(f"| {name} | {atype} | {dist} | {addr} |")
    return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description="Find nearby amenities via OpenStreetMap")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--address", help="Address to geocode (alternative to --lat/--lon)")
    group.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lon", type=float, help="Longitude (required with --lat)")
    parser.add_argument("--type", dest="amenity_type", default="restaurant",
                        help="OSM amenity type (default: restaurant)")
    parser.add_argument("--radius", type=int, default=1000,
                        help="Search radius in metres (default: 1000)")
    args = parser.parse_args()

    # Resolve coordinates
    if args.address:
        lat, lon = geocode_address(args.address)
    else:
        if args.lon is None:
            parser.error("--lon is required when using --lat")
        lat, lon = args.lat, args.lon

    print(f"Searching for {args.amenity_type!r} within {args.radius}m of ({lat}, {lon})...",
          file=sys.stderr)

    elements = query_overpass(lat, lon, args.amenity_type, args.radius)
    print(f"Found {len(elements)} raw results.", file=sys.stderr)

    # Enrich with distance and address
    enriched = []
    for el in elements:
        tags = el.get("tags", {})
        el_lat = el.get("lat", 0)
        el_lon = el.get("lon", 0)
        dist = haversine(lat, lon, el_lat, el_lon)
        enriched.append({
            "name": tags.get("name", "(unnamed)"),
            "amenity": tags.get("amenity", args.amenity_type),
            "distance": dist,
            "address": extract_address(tags),
        })

    enriched.sort(key=lambda x: x["distance"])

    table = build_table(enriched)
    print(f"\n## Nearby {args.amenity_type.capitalize()}s\n")
    print(table)


if __name__ == "__main__":
    main()
