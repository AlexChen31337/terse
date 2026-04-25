# Daily GitHub Maintenance Report — 2026-04-25

**Run time:** 2026-04-25 10:02 AEST  
**Orgs scanned:** bowen31337, AlexChen31337, clawinfra  
**Auth:** AlexChen31337 (gh CLI, keyring)  
**Total repos:** 123 (119 active, 4 archived)

---

## PRs Merged
None — zero open PRs found across all 123 repos.

---

## Security Issues

### 🔴 HIGH PRIORITY — clawinfra/claw-chain: 22 vulnerabilities found

`cargo audit` on `/media/DATA/.openclaw/workspace/claw-chain` returned **22 vulnerabilities**:

#### wasmtime 35.0.0 — multiple CVEs (11 advisories, all require upgrade to ≥36.0.7)
| Advisory | Title | Severity |
|----------|-------|----------|
| RUSTSEC-2026-0096 | Miscompiled guest heap access — sandbox escape on aarch64 Cranelift | **Critical** CVSS 9.3 |
| RUSTSEC-2026-0095 | Winch compiler backend sandbox-escaping memory access | **Critical** CVSS 9.3 |
| RUSTSEC-2026-0091 | OOB write/crash when transcoding component model strings | High |
| RUSTSEC-2026-0094 | Improperly masked return value from `table.grow` (Winch) | Medium |
| RUSTSEC-2026-0088 | Data leakage between pooling allocator instances | Medium |
| RUSTSEC-2026-0086 | Host data leakage with 64-bit tables and Winch | Medium |
| RUSTSEC-2026-0089 | Host panic when Winch executes `table.fill` | Medium |
| RUSTSEC-2026-0085 | Panic when lifting `flags` component value | Medium |
| RUSTSEC-2026-0093 | Heap OOB read in component model UTF-16 transcoding | Medium |
| RUSTSEC-2026-0087 | Segfault with `f64x2.splat` on Cranelift x86-64 | Medium |
| RUSTSEC-2026-0006 | Segfault with `f64.copysign` on x86-64 | Medium |
| RUSTSEC-2025-0118 | Unsound API access to WebAssembly shared linear memory | Low |
| RUSTSEC-2026-0021 | Guest-controlled resource exhaustion in WASI | Medium |
| RUSTSEC-2026-0020 | Guest-controlled resource exhaustion in WASI implementations | Medium |

**Fix:** Upgrade `wasmtime` from `35.0.0` → `≥43.0.1` (or minimum `≥36.0.7`)

#### rustls-webpki — 3 advisories across 2 versions (0.101.7 and 0.103.10)
| Advisory | Title |
|----------|-------|
| RUSTSEC-2026-0098 | Name constraints for URI names incorrectly accepted |
| RUSTSEC-2026-0104 | Reachable panic in CRL parsing |
| RUSTSEC-2026-0099 | Name constraints accepted for wildcard certificate names |

**Fix:** Upgrade to `rustls-webpki ≥0.103.13`

#### ring 0.16.20 — 1 advisory
| Advisory | Title |
|----------|-------|
| RUSTSEC-2025-0009 | AES functions may panic with overflow checking enabled |

**Fix:** Upgrade `ring` to `≥0.17.12`

#### Unmaintained crates (11 warnings, not vulnerabilities)
- `core2 0.4.0` — yanked, use `embedded-io` instead
- `derivative 2.2.0` — use `derive_more` or `educe`
- `fxhash 0.2.1` — use `rustc-hash`
- `instant 0.1.13` — use `web-time`
- + 7 more unmaintained warnings

---

### clawchain-sdk (Node) — 6 moderate vulnerabilities
`npm audit` found: 6 moderate, 0 high, 0 critical. No immediate action required but should be addressed.

### fear-protocol — Python, no Cargo.lock
No Rust deps. pip-audit not available in path. Skipped.

### clawkeyring — cargo audit returned clean
No vulnerabilities found.

### whalecli — pip-audit not available
pip-audit not in PATH. Skipped.

### AlexChen31337/claw-chain (local clone) — CLEAN
No non-default branches, no open PRs.

---

### NOT Audited (remote-only, not locally cloned)
- bowen31337/alphastrike-ai (Python/Node)
- bowen31337/dataViz-agent (Node/Next.js)
- clawinfra/evoclaw-browser (Node)
- clawinfra/clawinfra-web (Node)
- Multiple AlexChen31337 skill repos

---

## Branches Found

### clawinfra/claw-chain — 6 non-default branches
- `docs/audit-cranelift-non-exposure`
- `feat/anon-messaging-minimal`
- `fix/cargo-audit-ignore-format`
- `fix/ci-audit-ignore-format`
- `fix/ci-audit-ignore-ring-vuln`
- `fix/vendor-core2-missing`

**Action:** Did NOT auto-delete — these appear to be active security fix branches based on names. Requires manual review before deletion.

### clawinfra/evoclaw — 2 non-default branches
- `beta-release`
- `feat/connect-skillbank-to-rsi-loop`

**Action:** Did NOT auto-delete — `beta-release` is likely intentional. Requires manual review.

### All other scanned repos — CLEAN (0 non-default branches)

---

## Branches Deleted
**0 branches deleted.** Found 8 non-default branches across 2 repos but did not auto-delete — branch names suggest active work (security fixes, feature work, beta release).

---

## Dependabot PRs Merged
None — Dependabot not configured on any repo.

---

## Blockers for Bowen

### 🔴 ACTION REQUIRED: clawinfra/claw-chain has 22 Rust vulnerabilities
Two are **critical sandbox-escape CVEs** in `wasmtime 35.0.0`:
- **CVE-2026-34971** (RUSTSEC-2026-0096): Miscompiled heap access enables aarch64 sandbox escape
- **CVE-2026-34987** (RUSTSEC-2026-0095): Winch compiler backend sandbox escape

**Recommended action:** Upgrade `wasmtime` to `≥43.0.1` in Cargo.toml. The existing `fix/ci-audit-ignore-ring-vuln` branch suggests this has been noted before — check if there's a pending upgrade PR.

### ⚠️ Review 8 non-default branches in claw-chain + evoclaw
These look like active work, not stale branches. Suggest reviewing and either merging or closing.

### ℹ️ pip-audit not installed
Install via: `uv tool install pip-audit` to enable Python dependency scanning on future runs.

---

*Report generated by GitHub maintenance subagent. Next run: 2026-04-26.*
