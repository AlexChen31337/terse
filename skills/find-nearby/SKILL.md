---
metadata.openclaw:
  always: true
  reason: "Auto-classified as always-load (no specific rule for 'find-nearby')"
---


# find-nearby

Find nearby restaurants, cafes, shops, and other amenities using OpenStreetMap data. No API keys required.

## When to Use

- User asks "find nearby restaurants", "coffee shops near me", "pharmacies nearby", etc.
- User shares a location (coordinates or address) and wants to discover places around it
- User wants a list of amenities within a certain radius

## Procedure

1. **Get coordinates** — If the user provides an address, geocode it via Nominatim. If they provide lat/lon directly, use those.
2. **Query Overpass API** — Send the amenity query with the given radius.
3. **Parse results** — Extract name, type, distance, and address from each node.
4. **Calculate distance** — Use haversine formula to compute distance from user's location.
5. **Format as markdown table** — Sort by distance ascending, output: Name | Type | Distance | Address.

```bash
# Basic usage (coordinates)
uv run python skills/find-nearby/scripts/find_nearby.py --lat -33.8688 --lon 151.2093 --type restaurant --radius 500

# Using address
uv run python skills/find-nearby/scripts/find_nearby.py --address "Sydney Opera House" --type cafe --radius 800
```

## Pitfalls

- **Nominatim rate limit:** Max 1 request/second. Add delay if geocoding multiple addresses.
- **Missing names:** Many OSM nodes lack a `name` tag — script shows "(unnamed)" for these.
- **Overpass timeout:** Large radius + dense area can time out. Reduce radius or increase `[timeout:25]`.
- **Address geocoding ambiguity:** Nominatim picks the top result. Be specific with addresses.
- **Result cap:** Overpass returns up to ~10,000 nodes. Very common amenity types in large radii may be truncated.

## Verification

After running, confirm:
- Table has at least some results (unless area is genuinely empty)
- Distances are in ascending order
- Distance values are plausible (nearby = meters, not km for small radius)
- If address was used, geocoded coordinates are printed and look correct
