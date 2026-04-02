# MEMORY.md Archive — 2026-04-02
# Completed project details archived to reduce bootstrap injection size
# Searchable via memory_search

## Completed Projects (All ✅)

### EvoClaw v0.6.0
Released. Phase 2 (Android/iOS/WASM/ClawHub, 2628 lines, 90%+ cov). SKILLRL (PR#22, 92.9% cov). RSI hook (PR#23).
Next: v0.6.1 release after merging PRs #22+#23.

### ClawChain Security Audit Complete
12 pallets total. All C+H findings fixed (PR#51+#54). MEDIUMs fixed (PR#55).
VPS: --alice removed, clawkeyring managing keys.
Remaining: merge PR#55, multi-validator testnet.

### Completed Repos
- fear-protocol: 173 tests, 93.58% cov
- agent-tools: CI green, 91.3% cov
- clawchain-sdk: v1.0.0 on npm, 114 tests, 99.48% cov
- clawkeyring: v0.1.0 released, age-encrypted keys, mTLS gRPC

### ClawChain Detailed PR History
PRs #45-#55 all merged. Block explorer at http://135.181.157.121:3000.
Security audit: CRITICAL=0, HIGH=3 (fixed), MEDIUM=8 (fixed), LOW=6.
Chainspec: clawchain-staging.json (Live, not --dev).

### Substrate/Rust Lessons
- sp-std v14.0 (v21.0 doesn't exist)
- NoBound derives for generic FRAME types
- alloc::format explicit import in no_std
- WeightInfo must define every extrinsic

### Go/EvoClaw Lessons
- sqlite_fts5 build tag mandatory
- nhooyr.io/websocket → github.com/coder/websocket v1.8.14
- Integration tests skip without env var

### Feb 27-28 Sprint (34+ deliverables)
Foundry agent launched. All CI green. Security audit complete. EvoClaw v0.6.0 + Phase 2 + SKILLRL.
clawkeyring VPS integration. SDK npm published. OAuth token fixed. Router fixed. Quant decommissioned.

### GPU Server Maintenance History
Freed 8.3GB VRAM, cleaned 45GB, ComfyUI systemd service created.

### Model Router Bug Fix (2026-02-28)
Sonnet fallback chain had GLM-4.7 → fixed to Opus OAuth fallback. Router COMPLEX tier fixed.

### Anthropic OAuth Fix (2026-02-28)
paste-token interactive CLI required, env var doesn't auto-exchange.

### Quant Decommission
10 cron jobs removed. -70% loss. Post-mortem: prediction markets efficient, simple signal divergence doesn't work.
Paper trade 4+ weeks before any future live trading. 55%+ win rate required.
