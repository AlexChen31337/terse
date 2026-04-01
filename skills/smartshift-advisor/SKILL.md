---
name: smartshift-advisor
description: Solar battery strategy advisor for ha-smartshift. Analyzes Amber Electric prices, weather forecasts, Solplanet inverter state, and historical patterns to recommend optimal battery charge/discharge thresholds. Use when running the SmartShift advisory cycle (cron every 15 min), when asked about battery/solar/energy strategy, or when tuning export thresholds and discharge floors. Writes advice JSON consumed by the deterministic inverter_control.py script.
---

# SmartShift Advisor

Advisory agent for the ha-smartshift battery automation system at 29 Jack Peel Cct, Kellyville NSW 2155.

## Architecture

```
[This Skill]  →  /tmp/smartshift-advice.json  →  [inverter_control.py]  →  [Inverter]
  (advisory)       (threshold recommendations)      (deterministic guard)     (hardware)
```

The advisor **recommends** parameters. The deterministic script **enforces** safety. The LLM never directly controls the inverter.

## System Context

- **Solar**: 20kW panels, ~100kWh/day on sunny day
- **Battery**: 46kWh capacity (AISWEI ASW12kH-T3)
- **Inverter**: Solplanet at https://10.0.0.2 (self-signed cert)
- **Location**: -33.7114, 150.9457 (Kellyville NSW)
- **Grid**: Amber Electric (spot pricing, 5-min intervals)
- **No grid buy strategy**: sell price never below 4c, no arbitrage value

## Data Sources

### 1. Amber Electric API
```bash
# Current + forecast prices (next 12 hours)
uv run python scripts/amber_prices.py
```
Returns: buy price, feed-in earn, spike status, forecast array.

### 2. Weather / Solar Forecast
```bash
# Tomorrow's solar production estimate
uv run python scripts/solar_forecast.py
```
Returns: estimated kWh, cloud %, peak hours, confidence (sunny/partly_cloudy/cloudy).

### 3. Inverter State
```bash
# Current battery SoC, power, mode
uv run python scripts/inverter_state.py
```
Returns: SoC %, charge/discharge power W, current mod_r.

### 4. Historical Performance
```bash
# Last 7 days of decisions and outcomes
cat /home/bowen/ha-smartshift/.smartshift_history.jsonl | tail -100
```

## Advisory Workflow

Run every 15 minutes via OpenClaw cron. Produce advice JSON:

1. **Gather data**: Call all 3 scripts above
2. **Analyze**: Consider price trends, weather, battery state, time of day, day of week
3. **Recommend**: Write `/tmp/smartshift-advice.json` with:

```json
{
  "timestamp": "2026-04-01T11:30:00+11:00",
  "export_threshold": 8.5,
  "discharge_floor": 15,
  "hold_until": "17:30",
  "strategy": "aggressive_export",
  "reasoning": "Tonight's 6pm peak forecast at 18c, tomorrow sunny (95kWh est). Safe to drain to 15%.",
  "confidence": 0.85,
  "alerts": []
}
```

4. **Log**: Append decision to history JSONL for pattern learning

## Decision Framework

### Strategy Types

| Strategy | When | export_threshold | discharge_floor |
|----------|------|-----------------|----------------|
| `aggressive_export` | Sunny tomorrow + high peak tonight | 6-8c | 5-10% |
| `moderate_export` | Partly cloudy tomorrow | 10-12c | 15-25% |
| `conservative_hold` | Cloudy/rain tomorrow | 15c+ | 30-40% |
| `grid_charge` | Negative spot price | N/A (force charge) | N/A |
| `emergency_hold` | Price spike / grid event | 25c+ | 50%+ |

### Key Signals

- **Price shape**: Is tonight's peak higher or lower than last 7 days average?
- **Weather trajectory**: Getting sunnier or cloudier over next 3 days?
- **Battery cycle depth**: How deep did we discharge last night? Did solar recover fully?
- **Day of week**: Weekday peaks tend to be higher than weekends
- **Season**: Winter has shorter solar windows, need higher reserves

### Safety Bounds (non-negotiable)

The deterministic script clamps all recommendations:
- `export_threshold`: min 3c, max 30c
- `discharge_floor`: min 5% (SOC_MIN), max 60%
- `hold_until`: must be valid HH:MM in next 24h
- Any value outside bounds → script uses defaults

## Advice JSON Schema

See `references/advice-schema.md` for full field definitions and validation rules.

## Pattern Learning

After each night's export cycle, check outcomes:
- Did we hit the peak price window?
- How much did we actually export?
- Did solar refill the battery next day?
- What was the profit vs holding?

Log observations to history. Adjust future recommendations based on patterns.
Over time, reference `references/pattern-guide.md` for learned heuristics.
