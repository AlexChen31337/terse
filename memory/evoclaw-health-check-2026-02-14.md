# EvoClaw Health Check - 2026-02-14 08:43 AEDT

## 🟢 Orchestrator Status
**Process:** Running (PID 1260132)
**Port:** 8420 (API responding)
**Config:** `/home/bowen/.evoclaw-hub/config.json`
**Log:** `/home/bowen/.evoclaw-hub/evoclaw.log`
**Dashboard:** http://localhost:8420

## 🤖 Agents (2/2 Active)

### alex-hub (Desktop Hub)
- **ID:** alex-hub
- **Type:** monitor
- **Model:** nvidia/meta/llama-3.3-70b-instruct (Llama 3.3 70B, $0.40/M tokens)
- **Status:** idle
- **Skills:** desktop-tools
- **Location:** Local orchestrator

### alex-eye (Pi Camera)
- **ID:** alex-eye
- **Type:** monitor
- **Model:** nvidia/deepseek-ai/deepseek-r1-distill-qwen-32b (R1 32B, $0.20/M tokens)
- **Status:** idle
- **Skills:** desktop-tools
- **Location:** Raspberry Pi (192.168.99.25)
- **Connection:** MQTT (connected)
- **Pi Temp:** 48.2°C (healthy)
- **Pi Uptime:** 6 days, 22 hours

## 🧠 Models (19 Available)

### Ollama (1)
- qwen2.5:1.5b

### Nvidia NIM (16)
- Mistral Small 3.1 24B ($0.15/M)
- Llama 3.3 70B ($0.40/M)
- DeepSeek V3.2 ($0.40-$1.30/M)
- Nemotron Ultra 253B ($2.50-$5.00/M)
- Qwen3 235B MoE ($0.80/M)
- R1 32B ($0.20/M) ⭐ Reasoning
- R1 14B ($0.10/M) ⭐ Reasoning
- QwQ 32B ($0.20/M) ⭐ Reasoning
- Qwen3 Thinking 80B ($0.60/M) ⭐ Reasoning
- Kimi K2 Thinking ($1.00/M) ⭐ Reasoning
- Phi-4 Mini ($0.05/M) ⭐ Reasoning
- Llama 4 Maverick 17B ($0.30/M)
- Llama 4 Scout 17B ($0.30/M)
- Nemotron Super 49B ($1.50/M)
- Nemotron 51B ($1.50/M)
- Mistral Large 3 675B ($3.00/M)

### Zhipu (2) ⚠️ FAILING
- GLM 4.7 (Key 1) - z.ai proxy
- GLM 4.7 (Key 2) - z.ai proxy
**Status:** Both accounts failing API calls

## 🎯 Intelligent Router
**Enabled:** ✅ Yes
**Log Decisions:** ✅ Yes

### Tier Models
- **SIMPLE:** Phi-4 Mini ($0.05/M)
- **MEDIUM:** Llama 3.3 70B ($0.40/M)
- **COMPLEX:** DeepSeek V3.2 ($0.85/M avg)
- **REASONING:** R1 32B ($0.20/M)

### Thresholds
- SIMPLE→MEDIUM: 0.25
- MEDIUM→COMPLEX: 0.50
- COMPLEX→REASONING: 0.75

## 🛠️ Skills

### desktop-tools (2.0.0)
**Location:** `/home/bowen/.evoclaw/skills/desktop-tools/`
**Binaries:** 30/30 built ✅
**Assigned to:** alex-hub, alex-eye

**Categories:**
- File Operations: read, write, edit, glob, grep (5)
- Web Access: websearch, webfetch, codesearch (3)
- Execution: bash (1)
- Interaction: question (1)
- Project Mgmt: todowrite, todoread, task, skill (4)
- Sessions: list, history, send, spawn, status, agents_list (6)
- Git: status, diff, commit, log, branch (5)
- Advanced: apply_patch, browser, canvas, nodes, image (5)

## 🧬 Memory System

### Tiered Memory
- **Hot:** Max 5KB, 20 lessons, 5 projects
- **Warm:** Max 50KB, 30-day retention
- **Cold:** Turso (10-year retention)

### Cloud Sync
- **Enabled:** ✅ Yes
- **Database:** libsql://agentmemory-bowen31337.aws-ap-northeast-1.turso.io
- **Heartbeat:** 60s
- **Critical Sync:** ✅ Enabled
- **Warm Sync:** 60 min
- **Full Sync:** 24h

### Distillation
- **Aggression:** 0.7
- **Model:** local
- **Max Bytes:** 512

## 🔒 Self-Governance

### WAL (Write-Ahead Log)
- **Enabled:** ✅ Yes
- **Path:** `/home/bowen/.evoclaw-hub/data/wal`
- **Max Entries:** 1000
- **Auto Replay:** ✅ Yes

### VBR (Verify Before Reporting)
- **Enabled:** ✅ Yes
- **Require Verification:** external_action, config_change, critical_decision

### ADL (Anti-Divergence Limit)
- **Enabled:** ✅ Yes
- **Max Divergence:** 0.3
- **Check Interval:** 300s

### VFM (Value-For-Money)
- **Enabled:** ✅ Yes
- **Cost Threshold:** $0.10
- **Log Expensive Ops:** ✅ Yes

## 🧬 Evolution
- **Enabled:** ✅ Yes
- **Eval Interval:** 3600s
- **Min Samples:** 10
- **Max Mutation Rate:** 0.2

## 📊 System Resources

### Desktop (Dell XPS)
- **Disk:** 383GB / 937GB (44% used)
- **Memory:** 6.5GB / 15GB used
- **Swap:** 2.4GB / 255GB used

### Pi (Raspberry Pi)
- **Uptime:** 6 days, 22 hours
- **Temperature:** 48.2°C (healthy)
- **Load:** 0.35, 0.18, 0.11 (light)

## ⚠️ Known Issues

1. **GLM 4.7 accounts failing** - Both z.ai API keys returning errors
   - **Impact:** alex-hub model fallback to NIM
   - **Workaround:** Switched to NIM models
   - **Action:** Consider removing zhipu providers from config

2. **Pi edge agent systemd service not configured**
   - **Impact:** Agent won't auto-restart on reboot
   - **Status:** Manual start via bash script
   - **Action:** Create systemd service for production use

3. **Old alex-eye logs show command parsing errors**
   - **Last Error:** 2026-02-13 21:41
   - **Status:** Agent restarted today, no new errors
   - **Action:** Monitor for recurrence

## ✅ Overall Health: GREEN

All critical systems operational:
- ✅ Orchestrator running
- ✅ Both agents active and connected
- ✅ Desktop-tools skill loaded (30/30 tools)
- ✅ Memory system initialized
- ✅ Cloud sync active
- ✅ Self-governance enabled
- ✅ Intelligent router configured
- ⚠️ GLM models failing (non-blocking, NIM fallback works)

**Next Actions:**
1. Consider removing failing zhipu providers from config
2. Set up systemd service for alex-eye on Pi
3. Monitor GLM API status for resolution
