# fear-protocol — Code Review
> Reviewer: Alex Chen (Reviewer Agent)
> Date: 2026-02-27
> Repo: `/home/bowen/.openclaw/workspace/fear-protocol/`
> Plan: `PLAN.md` (Phase 1 target)

---

## Summary Verdict

**Pass with warnings.** The codebase is solid — 163 tests all green, 96.19% coverage (well above 90% bar), clean architecture, no security secrets in code. Three warnings to address before production use; no hard blockers.

---

## 1. Architecture ⚠️

### ✅ Passes
- Module structure matches the plan: `core/`, `data/`, `strategies/`, `exchanges/`, `backtest/`, `state/`, `agent/`, `cli/`
- All three strategies implemented (`fear-greed-dca`, `momentum-dca`, `grid-fear`)
- Exchange adapters: `base`, `mock`, `paper`, `hyperliquid` — all implemented
- Strategy registry, exchange registry present
- State manager, agent schemas, backtest engine + report all present

### ⚠️ Missing modules (plan-specified, not yet built — Phase 2/3 items)
These are listed in the plan but not yet implemented. Not blockers for Phase 1, but track them:

| Plan file | Status | Phase |
|-----------|--------|-------|
| `core/signals.py` | ❌ Missing | Plan listed but not Phase 1 |
| `exchanges/binance.py` | ❌ Missing | Phase 2 |
| `agent/rpc.py` | ❌ Missing | Phase 3 |
| `backtest/portfolio.py` | ❌ Missing | Merged into engine.py |
| CLI commands coverage | ⚠️ Omitted from coverage | See §3 |

**README lists Binance as a supported adapter** — this is misleading since `binance.py` doesn't exist yet. Update README or add a "coming soon" note.

---

## 2. Code Quality ✅

- **Type annotations**: Full annotations across all modules. `from __future__ import annotations` used consistently.
- **Docstrings**: Present on all public classes and methods reviewed.
- **Imports**: Clean, no wildcard imports, properly ordered.
- **Dead code**: None found.
- **Pyright mode**: Set to `basic` (not `strict` as specified in plan). Minor deviation — strict mode would catch more issues but would require more annotation work.

---

## 3. Tests ✅

```
163 passed, 0 failed, 0 errors
Total coverage: 96.19% (≥ 90% ✅)
```

### Coverage breakdown
| Module | Coverage | Notes |
|--------|----------|-------|
| `core/` | 97–100% | Excellent |
| `strategies/` | 96–100% | All 3 strategies covered |
| `exchanges/mock.py` | 100% | |
| `exchanges/paper.py` | 100% | |
| `exchanges/base.py` | 92% | 2 lines (default `validate_order_size`, `close`) — acceptable |
| `backtest/engine.py` | 86% | Streaming path partially uncovered (lines 48-57, 289-304) |
| `backtest/report.py` | 85% | HTML output path (lines 123-131) uncovered |
| `agent/schemas.py` | 100% | |

### ⚠️ Coverage exemptions in `pyproject.toml`
The following are excluded from coverage measurement:
- `fear_protocol/cli/*` — CLI commands have zero coverage. Plan says CLI should have integration tests.
- `fear_protocol/exchanges/hyperliquid.py` — Reasonable for a live-exchange adapter.
- `fear_protocol/data/historical.py` — Makes sense (API-dependent), but backtest engine depends on it heavily.
- `fear_protocol/agent/api.py` — Async API has no tests at all.

**Recommendation**: Add at least smoke tests for CLI (invoke via typer test runner) and for `agent/api.py` before calling Phase 3 done.

### Missing edge cases
- `backtest/engine.py` streaming path (`run_streaming()`) — not tested
- `backtest/report.py` `to_html()` — not tested
- Strategy behaviour when `ctx.open_positions` is malformed / missing keys

---

## 4. Security ✅

- No hardcoded API keys, wallet addresses, or passwords in source code.
- `HyperliquidAdapter` reads credentials from env vars or `.env` file — correct pattern.
- No `eval()`, `exec()`, or shell injection vectors found.
- `StateManager` uses JSON — no pickle/unsafe deserialization.
- Input validation present in `agent/schemas.py` (Pydantic v2).

---

## 5. Personal Info ❌ (Blocker — fix before public release)

```
fear_protocol/exchanges/hyperliquid.py:19
HL_ENV_PATH = Path("/home/bowen/.openclaw/skills/hyperliquid/.env")
```

**This hardcodes an absolute path with `bowen` in it.** If this repo is ever published to GitHub or PyPI, it leaks the system username. 

**Fix:**
```python
HL_ENV_PATH = Path.home() / ".openclaw" / "skills" / "hyperliquid" / ".env"
```

No other personal info (phone numbers, Telegram IDs, real names) found in source or tests.

---

## 6. CI ✅

`.github/workflows/ci.yml` is present and correct:
- Matrix: Python 3.11, 3.12, 3.13 ✅
- Steps: checkout → uv install → deps → ruff lint → pyright → tests → coverage ≥ 90% ✅
- Matches plan spec exactly.

⚠️ No `release.yml` or `docs.yml` yet — plan listed these. Phase 3 item.

---

## 7. README ⚠️

- ✅ Clear, well-structured, accurate quickstart commands
- ✅ Architecture overview correct
- ✅ Strategy table present
- ❌ **Binance listed as supported adapter** but `exchanges/binance.py` doesn't exist. This will mislead users.
- ⚠️ No mention of `--json` flag in quickstart (plan emphasized agent-first design)
- ⚠️ No config file example (TOML format documented in plan but not README)

---

## 8. Package ✅

```
uv run python -c "import fear_protocol" → OK (version 0.1.0)
```

- `pyproject.toml` matches plan spec: correct name, version, authors, license, requires-python ≥ 3.11
- `hatchling` build backend (plan showed hatchling, consistent)
- `project.scripts` entry point: `fear-protocol = "fear_protocol.cli.main:app"` ✅
- All core dependencies specified: requests, typer, rich, pydantic, python-dateutil
- Optional deps for hyperliquid/binance/docs/dev present

⚠️ `[tool.pyright]` uses `typeCheckingMode = "basic"` but plan specified `strict = true`. Minor gap.

---

## Action Items

### ❌ Blockers (fix before public release/PyPI)
1. **`hyperliquid.py:19`** — Replace hardcoded `/home/bowen/` path with `Path.home()` equivalent.

### ⚠️ Warnings (non-blocking, fix before Phase 3 complete)
2. **README** — Remove Binance from supported adapters table or mark as "coming soon".
3. **Test coverage** — Add CLI smoke tests and `agent/api.py` basic tests before Phase 3 exit criteria.
4. **Pyright strict mode** — Upgrade from `basic` to `strict` per plan spec (will require annotation fixes).
5. **Missing Phase 2/3 modules** — `exchanges/binance.py`, `agent/rpc.py`, `core/signals.py` still pending.

### ✅ No action needed
- All 163 tests green
- Coverage 96.19% (well above 90%)
- No hardcoded credentials (except path blocker above)
- No personal info leaks (except path blocker above)
- CI workflow correct and complete
- Package imports cleanly
- Architecture sound and matches Phase 1 plan
