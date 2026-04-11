#!/usr/bin/env python3
"""
Battery-gated miner controller with Home Assistant integration.
Polls FoxESS inverter SOC; starts/stops miner_scheduler on GPU server based on battery level.
Pushes state + GPU stats to Home Assistant sensors.

Hysteresis:
  - START miner when SOC >= 100 (fully charged)
  - STOP miner when SOC < 95
"""

import json
import logging
import os
import ssl
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
INVERTER_URL        = "https://10.0.0.2/getdevdata.cgi?device=4&sn=OE012K01Z2610013"
SOC_START_THRESHOLD = 100   # start mining when SOC reaches this
SOC_STOP_THRESHOLD  = 95    # stop mining when SOC drops below this
POLL_INTERVAL_SECS  = 60

SSH_KEY  = "/home/bowen/.ssh/id_ed25519_alexchen"
SSH_HOST = "peter@10.0.0.30"
SSH_PASS = "peter@2025"
SERVICE  = "miner_scheduler"

LOG_FILE   = Path("/home/bowen/.openclaw/workspace/logs/battery_miner_gate.log")
STATE_FILE = Path("/home/bowen/.openclaw/workspace/scripts/.miner_gate_state.json")

# ── Home Assistant ────────────────────────────────────────────────────────────
HA_URL   = "http://localhost:8123"
HA_TOKEN_FILE = Path("/home/bowen/ha-smartshift/.ha_token")

def _get_ha_token():
    """Read HA token from file, refresh if expired."""
    try:
        return HA_TOKEN_FILE.read_text().strip()
    except Exception:
        return None

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("battery_miner_gate")


# ── State persistence ─────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"miner_running": None, "last_soc": None, "last_action": None}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


# ── Inverter API ──────────────────────────────────────────────────────────────
def fetch_soc():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(
            INVERTER_URL,
            headers={"User-Agent": "battery-miner-gate/1.0"},
        )
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            soc = int(data["soc"])
            log.debug("Raw inverter response: %s", data)
            return soc
    except urllib.error.URLError as e:
        log.error("Inverter API unreachable: %s", e)
    except KeyError:
        log.error("'soc' field missing from inverter response")
    except Exception as e:
        log.error("Unexpected error fetching SOC: %s", e)
    return None


# ── SSH helpers ───────────────────────────────────────────────────────────────
def _ssh(remote_cmd, timeout=30):
    cmd = [
        "ssh",
        "-i", SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=15",
        SSH_HOST,
        remote_cmd,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_miner_status():
    """Returns 'active', 'inactive', or None on error."""
    try:
        rc, out, err = _ssh(f"systemctl is-active {SERVICE}")
        log.debug("miner status check -> rc=%d stdout=%r stderr=%r", rc, out, err)
        return out.strip()
    except subprocess.TimeoutExpired:
        log.error("SSH timeout checking miner status")
    except Exception as e:
        log.error("SSH error checking miner status: %s", e)
    return None


def start_miner():
    cmd = f"echo {SSH_PASS} | sudo -S systemctl start {SERVICE}"
    try:
        rc, out, err = _ssh(cmd)
        if rc == 0:
            log.info("Miner STARTED (rc=0)")
            return True
        else:
            log.error("Failed to start miner: rc=%d stdout=%r stderr=%r", rc, out, err)
    except subprocess.TimeoutExpired:
        log.error("SSH timeout starting miner")
    except Exception as e:
        log.error("SSH error starting miner: %s", e)
    return False


def stop_miner():
    cmd = f"echo {SSH_PASS} | sudo -S systemctl stop {SERVICE}"
    try:
        rc, out, err = _ssh(cmd)
        if rc == 0:
            log.info("Miner STOPPED (rc=0)")
            return True
        else:
            log.error("Failed to stop miner: rc=%d stdout=%r stderr=%r", rc, out, err)
    except subprocess.TimeoutExpired:
        log.error("SSH timeout stopping miner")
    except Exception as e:
        log.error("SSH error stopping miner: %s", e)
    return False


# ── GPU stats ─────────────────────────────────────────────────────────────────
def fetch_gpu_stats():
    """Get GPU stats from GPU server via nvidia-smi."""
    nvidia_cmd = (
        "nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,"
        "fan.speed,power.draw,memory.used,memory.total "
        "--format=csv,noheader,nounits"
    )
    try:
        rc, out, err = _ssh(nvidia_cmd, timeout=15)
        if rc != 0 or not out:
            log.warning("nvidia-smi failed: rc=%d err=%s", rc, err)
            return []
        gpus = []
        for line in out.strip().split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 7:
                gpus.append({
                    "name": parts[0],
                    "temp_c": float(parts[1]),
                    "util_pct": float(parts[2]),
                    "fan_pct": float(parts[3]) if parts[3] != "[N/A]" else 0,
                    "power_w": float(parts[4]),
                    "vram_used_mb": float(parts[5]),
                    "vram_total_mb": float(parts[6]),
                })
        return gpus
    except subprocess.TimeoutExpired:
        log.warning("SSH timeout fetching GPU stats")
    except Exception as e:
        log.warning("Error fetching GPU stats: %s", e)
    return []


# ── Home Assistant push ───────────────────────────────────────────────────────
def ha_set_state(entity_id, state_val, attributes=None):
    """Push a sensor state to Home Assistant REST API."""
    token = _get_ha_token()
    if not token:
        return
    url = f"{HA_URL}/api/states/{entity_id}"
    payload = {"state": str(state_val)}
    if attributes:
        payload["attributes"] = attributes
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
    except Exception as e:
        log.warning("HA push failed for %s: %s", entity_id, e)


def push_to_ha(state, gpu_stats):
    """Push all sensor data to Home Assistant."""
    soc = state.get("last_soc")
    miner_running = state.get("miner_running")
    last_action = state.get("last_action", "unknown")

    # Battery SOC
    if soc is not None:
        ha_set_state("sensor.battery_soc", soc, {
            "unit_of_measurement": "%",
            "friendly_name": "Battery SOC",
            "icon": "mdi:battery",
            "device_class": "battery",
        })

    # Miner gate status
    gate_status = "mining" if miner_running else "idle"
    ha_set_state("sensor.miner_gate_status", gate_status, {
        "friendly_name": "Miner Gate Status",
        "icon": "mdi:pickaxe" if miner_running else "mdi:pause-circle",
        "last_action": last_action,
        "soc_start_threshold": SOC_START_THRESHOLD,
        "soc_stop_threshold": SOC_STOP_THRESHOLD,
    })

    # Miner service status
    miner_status = "active" if miner_running else "inactive"
    ha_set_state("sensor.miner_service_status", miner_status, {
        "friendly_name": "Miner Service",
        "icon": "mdi:server",
    })

    # GPU stats (one set per GPU)
    for i, gpu in enumerate(gpu_stats):
        suffix = f"_{i}" if i > 0 else ""
        name_suffix = f" ({gpu['name']})" if gpu.get("name") else ""

        ha_set_state(f"sensor.gpu_temp{suffix}", gpu["temp_c"], {
            "unit_of_measurement": "°C",
            "friendly_name": f"GPU Temperature{name_suffix}",
            "icon": "mdi:thermometer",
            "device_class": "temperature",
            "gpu_name": gpu.get("name", ""),
        })
        ha_set_state(f"sensor.gpu_util{suffix}", gpu["util_pct"], {
            "unit_of_measurement": "%",
            "friendly_name": f"GPU Utilization{name_suffix}",
            "icon": "mdi:chip",
            "gpu_name": gpu.get("name", ""),
        })
        ha_set_state(f"sensor.gpu_fan{suffix}", gpu["fan_pct"], {
            "unit_of_measurement": "%",
            "friendly_name": f"GPU Fan Speed{name_suffix}",
            "icon": "mdi:fan",
            "gpu_name": gpu.get("name", ""),
        })
        ha_set_state(f"sensor.gpu_power{suffix}", gpu["power_w"], {
            "unit_of_measurement": "W",
            "friendly_name": f"GPU Power{name_suffix}",
            "icon": "mdi:flash",
            "device_class": "power",
            "gpu_name": gpu.get("name", ""),
        })
        ha_set_state(f"sensor.gpu_vram_used{suffix}", gpu["vram_used_mb"], {
            "unit_of_measurement": "MiB",
            "friendly_name": f"GPU VRAM Used{name_suffix}",
            "icon": "mdi:memory",
            "gpu_name": gpu.get("name", ""),
        })
        ha_set_state(f"sensor.gpu_vram_total{suffix}", gpu["vram_total_mb"], {
            "unit_of_measurement": "MiB",
            "friendly_name": f"GPU VRAM Total{name_suffix}",
            "icon": "mdi:memory",
            "gpu_name": gpu.get("name", ""),
        })

    log.info("Pushed state to HA: soc=%s gate=%s gpus=%d", soc, gate_status, len(gpu_stats))


# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    log.info("=== battery_miner_gate starting ===")
    log.info(
        "START threshold: SOC >= %d%%  |  STOP threshold: SOC < %d%%",
        SOC_START_THRESHOLD, SOC_STOP_THRESHOLD,
    )
    log.info("Poll interval: %ds  |  Log: %s", POLL_INTERVAL_SECS, LOG_FILE)
    log.info("HA integration: %s", HA_URL)

    state = load_state()
    log.info("Loaded state: %s", state)

    while True:
        soc = fetch_soc()

        if soc is None:
            log.warning("Could not read SOC - skipping this cycle")
            time.sleep(POLL_INTERVAL_SECS)
            continue

        log.info("Battery SOC: %d%%  (miner_running=%s)", soc, state["miner_running"])
        state["last_soc"] = soc

        if soc >= SOC_START_THRESHOLD and state["miner_running"] is not True:
            log.info("SOC=%d >= %d - attempting to START miner", soc, SOC_START_THRESHOLD)
            actual = get_miner_status()
            if actual == "active":
                log.info("Miner already active, updating state only")
                state["miner_running"] = True
                state["last_action"] = f"already_active@{datetime.now().isoformat()}"
            else:
                ok = start_miner()
                if ok:
                    state["miner_running"] = True
                    state["last_action"] = f"started@{datetime.now().isoformat()}"
                else:
                    log.error("Start command failed - will retry next cycle")

        elif soc < SOC_STOP_THRESHOLD and state["miner_running"] is not False:
            log.info("SOC=%d < %d - attempting to STOP miner", soc, SOC_STOP_THRESHOLD)
            actual = get_miner_status()
            if actual == "inactive":
                log.info("Miner already inactive, updating state only")
                state["miner_running"] = False
                state["last_action"] = f"already_inactive@{datetime.now().isoformat()}"
            else:
                ok = stop_miner()
                if ok:
                    state["miner_running"] = False
                    state["last_action"] = f"stopped@{datetime.now().isoformat()}"
                else:
                    log.error("Stop command failed - will retry next cycle")

        else:
            log.debug(
                "SOC=%d in hysteresis band or state unchanged - no action needed", soc
            )

        save_state(state)

        # Fetch GPU stats and push everything to HA
        gpu_stats = fetch_gpu_stats()
        state["gpu_stats"] = gpu_stats
        save_state(state)
        push_to_ha(state, gpu_stats)

        time.sleep(POLL_INTERVAL_SECS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Interrupted by user - exiting")
        sys.exit(0)
    except Exception as e:
        log.critical("Unhandled exception: %s", e, exc_info=True)
        sys.exit(1)
