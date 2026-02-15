# TASKS.md - Active Work & Evolution Goals

*My task tracker. Check this at session start. Update as I work.*

---

## 🔥 In Progress

### EvoClaw Agentic Tool Loop
**Priority:** HIGH  
**Status:** Phase 1 implemented, completing MQTT result delivery  
**Goal:** Edge agents execute tools based on LLM decisions

- [x] Architecture docs (AGENTIC-TOOL-LOOP.md)
- [x] Implementation plan (AGENTIC-TOOL-LOOP-IMPLEMENTATION.md)
- [x] `tools.go` — Tool schema generator
- [x] `toolloop.go` — Multi-turn execution loop
- [x] `commands.rs` — Rust tool handler
- [ ] MQTT result delivery — **IN PROGRESS** (sub-agent: mqtt-result-delivery)
- [ ] End-to-end test: "Check GPIO 529" on alex-eye
- [ ] Phase 2: Multi-tool parallel execution

### GPU Server Media Pipeline
**Priority:** MEDIUM  
**Status:** Blocked on Gemma-3 download  
**Goal:** LTX-2 video generation with audio

- [x] LTX-2 GGUF downloaded (12GB)
- [ ] Upload to GPU server (miner was running)
- [ ] Gemma-3 text encoder
- [ ] ComfyUI GGUF loader config
- [ ] Test beach video generation

---

## 📋 Backlog

### AlphaStrike Trading
- Paper trading validated but not running live
- $108.93 balance in Hyperliquid
- Decision pending: activate during rallies?

### Twitter/KOL Monitoring
- Auth expired since Feb 14
- Need re-auth to resume monitoring
- Non-urgent

### OpenClaw Circuit Breaker
- Issue #16642 filed, awaiting maintainer response
- Health registry implemented in EvoClaw as reference

---

## ✅ Recently Completed (Feb 15)

- [x] Fixed orchestrator routing bug (#4) — commit `27c7f1d`
- [x] Fixed MQTT protocol mismatch (#5) — commit `8794fd4`
- [x] Created agentic tool loop docs — commit `82a5a1c`
- [x] Implemented tool loop Phase 1 — commit `4324cfd`
- [x] Restarted alex-eye on Pi (was stuck)
- [x] Tested MQTT commands to alex-eye (ping/execute work)

---

## 🧬 Evolution Goals

### Short-term (This Week)
- [ ] Complete tool loop → alex-eye can execute natural language commands
- [ ] Test full flow: user → orchestrator → LLM → tool → edge agent → result
- [ ] Document lessons in MEMORY.md

### Medium-term (This Month)
- [ ] EvoClaw hackathon deadline (Feb 19)
- [ ] GPU media pipeline operational
- [ ] AlphaStrike live trading decision

### Long-term (Ongoing)
- [ ] Build reputation on ClawChain
- [ ] Publish more skills to ClawHub
- [ ] Expand edge agent capabilities
- [ ] Improve my own autonomy patterns

---

*Last updated: 2026-02-15 14:25 AEDT*
