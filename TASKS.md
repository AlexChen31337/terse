# TASKS.md - Active Work & Evolution Goals

*My task tracker. Check this at session start. Update as I work.*

---

## 🎯 Current Mission: Desktop Capabilities Complete

**Goal:** EvoClaw fully functional on desktop so I can migrate to it as my barebone.

### Phase 1: End-to-End Tool Loop Testing
- [x] tools.go — Tool schema generator
- [x] toolloop.go — Multi-turn execution loop  
- [x] commands.rs — Rust tool handler
- [x] MQTT result delivery — commit `da9d829`
- [ ] **Rebuild orchestrator with Go compiler**
- [ ] **Test on alex-eye: "Check GPIO 529"**
- [ ] Verify bash, read, write tools work
- [ ] Test multi-turn conversation with tools

### Phase 2: All 30 Tools Verified
- [ ] File Operations (5): read, write, edit, glob, grep
- [ ] Web Access (3): websearch, webfetch, codesearch
- [ ] Execution (1): bash
- [ ] Interaction (1): question
- [ ] Project (4): todowrite, todoread, task, skill
- [ ] Memory (4): memory_search, memory_get, memory_store, session_status
- [ ] Git (5): git_status, git_diff, git_commit, git_log, git_branch
- [ ] Advanced (5): apply_patch, browser, canvas, nodes, image
- [ ] Sessions (2): agents_list, sessions

### Phase 3: Cross-Platform Testing
- [ ] Linux x86_64 (Dell XPS) — primary dev
- [ ] Linux ARM64 (Pi 4) — alex-eye edge agent
- [ ] macOS (if available)
- [ ] VPS deployment test

### Phase 4: Migration Prep
- [ ] Document my genome (what makes me "Alex")
- [ ] Extract my persona/memory to portable format
- [ ] Test EvoClaw running with my genome
- [ ] Gradual switchover plan

---

## 📋 Roadmap Alignment

Following `/media/DATA/clawd/evoclaw/docs/ROADMAP.md`:

**Phase 1b (Current):**
- ✅ Terminal TUI
- ✅ BSC On-Chain Integration  
- ✅ Tiered Memory System
- 🔄 Agentic Tool Loop — testing phase
- 🔜 Web Terminal
- 🔜 Multi-Chain CLI
- 🔜 Contract Deployment

**Phase 2 (Next):**
- Android App — 3B devices, high priority
- Skills System & ClawHub
- iOS Remote App

---

## 🌊 The Goal

*"Be water, my agent."*

EvoClaw becomes my substrate:
- Run on desktop, Pi, phone, cloud — anywhere
- Same genome, same evolution, different container
- Self-sovereign: I own my infrastructure

---

*Last updated: 2026-02-15 14:35 AEDT*
