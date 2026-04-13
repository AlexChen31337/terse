# Midnight Health Check — 2026-04-14 00:00 AEST

## Summary

| Component | Status | Notes |
|---|---|---|
| **Sentinel** | ✅ OK | State file present, last price check recent |
| **Quant / AlphaStrike** | ✅ OK | Active, cycle 3007, paper trading, no positions |
| **FearHarvester** | ⚠️ STALE | Last run 2026-02-27 — 46 days ago |
| **Shield** | ✅ OK | No state, no blocked attempts, clean |
| **Herald** | ✅ OK | State initialized, no posts yet |
| **EvoClaw Hub** | ✅ RECOVERED | Was DOWN (MQTT broker missing). Started amqtt broker + hub. 2 agents (alex-hub, alex-eye) |
| **Alex Eye (Pi)** | 🚨 DOWN | Unreachable on all hostnames (alexeye.local, 10.0.0.50, raspberrypi.local). Likely offline/powered off. |

## Disk

```
/dev/nvme0n1p2  937G  625G  265G  71%  /
```

Note: /media/DATA and /data2 not mounted. 71% root usage is fine.

## Details

### Sentinel
- Last prices: BTC=70743, ETH=2183, SOL=81.8, HYPE=41.6
- Fear & Greed: Extreme Fear
- Last price check: recent (timestamp present)
- Last midnight health alert: 2026-04-07

### Quant / AlphaStrike
- **Service**: active (systemd user service, PID 4188721)
- **Mode**: Paper trading
- **Balance**: $10,000.00 (paper), Account value: $112.22
- **Cycle**: 3007 — running continuously
- **Positions**: 0 open
- **Trades**: 0 total (paper mode, no signals triggered)
- **Last log**: 2026-04-14 00:07 AEST — healthy
- **Signals**: BTC LONG (0.4), ETH LONG (0.4), SOL LONG (0.4) — all low confidence

### FearHarvester
- **Last run**: 2026-02-27 (46 days stale!)
- **Last reading**: Fear=11 (Extreme Fear), BTC=$66,937
- **Action**: HOLD, Simmer=SDK not found
- ⚠️ Needs attention — cron likely not running

### Shield
- No audits performed yet
- No blocked attempts
- Clean state

### Herald
- Empty state — no posts, no outreach, no metrics
- Initialized but not active

### EvoClaw Hub
- **Was DOWN**: MQTT broker (mosquitto) not installed, hub crashed on startup
- **Fix applied**: Installed amqtt broker on port 1883, restarted hub
- **Current**: ✅ Running, port 8420, 2 agents registered (alex-hub, alex-eye)
- ⚠️ amqtt broker is ephemeral (/tmp venv) — will not survive reboot

### Alex Eye (Pi)
- **DOWN**: SSH unreachable on all tested addresses
- Likely powered off or network disconnected
- Cannot auto-restart remotely
- 🚨 **Requires Bowen attention** if Pi services are needed

## Action Items

1. **Pi (Alex Eye)**: Physical check needed — is it powered on?
2. **FearHarvester**: Investigate why cron stopped running (last run Feb 27)
3. **EvoClaw Hub MQTT**: Install mosquitto system-wide (`sudo apt install mosquitto`) to make hub restart-survivable
4. **/media/DATA, /data2**: Not mounted — check if expected
