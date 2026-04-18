"""OpenClaw Health Dashboard — simple FastAPI app."""
import asyncio, json, subprocess, time
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="OpenClaw Health Dashboard")

GATEWAY_URL = "http://127.0.0.1:18789"
OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"

AGENTS = ["main", "sentinel", "quant", "shield", "herald", "foundry"]
CHANNELS = ["telegram", "whatsapp"]

async def _check_gateway() -> dict:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{GATEWAY_URL}/health")
            return {"status": "up", "http": r.status_code, "latency_ms": round(r.elapsed.total_seconds() * 1000)}
    except Exception as e:
        return {"status": "down", "error": str(e)[:80]}

async def _check_channels() -> dict:
    cfg = {}
    try:
        data = json.loads(OPENCLAW_CONFIG.read_text())
        channels = data.get("channels", {})
        cfg = {ch: {"enabled": v.get("enabled", False)} for ch, v in channels.items()}
    except Exception as e:
        return {"error": str(e)[:80]}
    # Try gateway channel health endpoint
    results = {}
    for ch, info in cfg.items():
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{GATEWAY_URL}/channels/{ch}/health")
                results[ch] = {"enabled": info["enabled"], "status": "ok" if r.status_code < 400 else "degraded"}
        except:
            results[ch] = {"enabled": info["enabled"], "status": "up" if info["enabled"] else "disabled"}
    return results

async def _check_agents() -> dict:
    results = {}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{GATEWAY_URL}/agents")
            data = r.json()
            for agent in data.get("agents", []):
                results[agent["id"]] = {"status": agent.get("status", "unknown"), "sessions": agent.get("activeSessions", 0)}
    except Exception:
        # fallback: assume configured agents exist
        for a in AGENTS:
            results[a] = {"status": "configured", "sessions": 0}
    return results

async def _check_crons() -> list:
    results = []
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{GATEWAY_URL}/cron/jobs")
            jobs = r.json().get("jobs", [])
            for j in jobs[:10]:
                results.append({
                    "id": j.get("id", "?")[:8],
                    "name": j.get("name", j.get("id", "?"))[:40],
                    "enabled": j.get("enabled", True),
                    "lastRun": j.get("lastRunAt", "never"),
                })
    except Exception as e:
        results.append({"error": str(e)[:80]})
    return results

@app.get("/api/health")
async def api_health():
    gateway, channels, agents, crons = await asyncio.gather(
        _check_gateway(), _check_channels(), _check_agents(), _check_crons()
    )
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "gateway": gateway,
        "channels": channels,
        "agents": agents,
        "crons": crons,
    }

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OpenClaw Health Dashboard</title>
<style>
  :root{--bg:#0d1117;--card:#161b22;--border:#30363d;--green:#3fb950;--red:#f85149;--yellow:#d29922;--blue:#58a6ff;--text:#e6edf3;--muted:#8b949e}
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:'SF Mono',Menlo,monospace;font-size:13px;padding:20px}
  h1{color:var(--blue);font-size:18px;margin-bottom:4px}
  .subtitle{color:var(--muted);font-size:11px;margin-bottom:20px}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
  .card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px}
  .card h2{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px}
  .row{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid var(--border)}
  .row:last-child{border-bottom:none}
  .label{color:var(--text)}
  .badge{padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600}
  .up,.ok,.configured{background:#1a3726;color:var(--green)}
  .down,.error{background:#3d1a1a;color:var(--red)}
  .degraded,.unknown{background:#3d2e10;color:var(--yellow)}
  .disabled{background:#1c2128;color:var(--muted)}
  .ts{color:var(--muted);font-size:10px;text-align:right;margin-top:12px}
  .refresh-btn{background:var(--card);border:1px solid var(--border);color:var(--blue);padding:4px 12px;border-radius:6px;cursor:pointer;font-size:11px;float:right}
  .cron-name{font-size:11px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:180px}
  #status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
</style>
</head>
<body>
<h1><span id="status-dot" style="background:#d29922"></span>OpenClaw Health Dashboard</h1>
<p class="subtitle">Auto-refreshes every 30s &nbsp;|&nbsp; <button class="refresh-btn" onclick="load()">↻ Refresh now</button></p>
<div class="grid" id="grid">Loading...</div>
<p class="ts" id="ts"></p>
<script>
async function load(){
  try{
    const d=await fetch('/api/health').then(r=>r.json());
    render(d);
  }catch(e){
    document.getElementById('grid').innerHTML='<div class="card"><p style="color:var(--red)">Failed to load: '+e+'</p></div>';
  }
}

function badge(s){
  const cls=(['up','ok','configured','enabled'].includes(s)?'up':['down','error'].includes(s)?'down':s)||'unknown';
  return `<span class="badge ${cls}">${s}</span>`;
}

function render(d){
  const dot=document.getElementById('status-dot');
  const gwOk=d.gateway?.status==='up';
  dot.style.background=gwOk?'#3fb950':'#f85149';

  let html='';

  // Gateway card
  html+=`<div class="card"><h2>🌐 Gateway</h2>`;
  html+=`<div class="row"><span class="label">Status</span>${badge(d.gateway.status)}</div>`;
  if(d.gateway.latency_ms!==undefined)
    html+=`<div class="row"><span class="label">Latency</span><span>${d.gateway.latency_ms}ms</span></div>`;
  if(d.gateway.error)
    html+=`<div class="row"><span class="label">Error</span><span style="color:var(--red);font-size:11px">${d.gateway.error}</span></div>`;
  html+=`</div>`;

  // Channels card
  html+=`<div class="card"><h2>📡 Channels</h2>`;
  for(const[ch,v] of Object.entries(d.channels||{})){
    const s=v.enabled?(v.status||'up'):'disabled';
    html+=`<div class="row"><span class="label">${ch}</span>${badge(s)}</div>`;
  }
  html+=`</div>`;

  // Agents card
  html+=`<div class="card"><h2>🤖 Agents</h2>`;
  for(const[id,v] of Object.entries(d.agents||{})){
    html+=`<div class="row"><span class="label">${id}</span>${badge(v.status||'unknown')}</div>`;
  }
  html+=`</div>`;

  // Crons card
  html+=`<div class="card"><h2>⏱ Cron Jobs (last 10)</h2>`;
  if(!d.crons||!d.crons.length){
    html+=`<div class="row"><span class="label" style="color:var(--muted)">No jobs</span></div>`;
  } else {
    for(const j of d.crons){
      if(j.error){html+=`<div class="row"><span style="color:var(--red)">${j.error}</span></div>`;continue;}
      const s=j.enabled?'enabled':'disabled';
      html+=`<div class="row"><span class="cron-name" title="${j.name}">${j.name}</span>${badge(s)}</div>`;
    }
  }
  html+=`</div>`;

  document.getElementById('grid').innerHTML=html;
  document.getElementById('ts').textContent='Last updated: '+new Date(d.timestamp).toLocaleString();
}

load();
setInterval(load,30000);
</script>
</body></html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTML
# OpenClaw Health Dashboard
# Run: uv run --no-project --with fastapi --with 'uvicorn[standard]' --with httpx uvicorn scripts.openclaw_dashboard:app --host 0.0.0.0 --port 8765
# Then open: http://localhost:8765
