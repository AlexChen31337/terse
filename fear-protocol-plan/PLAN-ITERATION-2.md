# PLAN-ITERATION-2.md — fear-protocol Patch Plan
> Planner: Alex Chen (Iteration 2)
> Date: 2026-02-27
> Scope: Fix remaining review warnings from Phase 1. No rewrites — surgical patches only.

---

## Item 1 — README: Remove Binance from supported adapters
**Priority: must-fix** (misleads users; binance.py doesn't exist)

**File:** `README.md`

**Change:**
- In the exchange adapters table (line ~59), change `binance` row to:
  ```
  | `binance` | Coming soon | BTC/USDT spot |
  ```
  Or remove the row entirely and add a note: `> Binance adapter planned for Phase 2.`
- In the architecture tree (line ~37), change `← exchange adapters (HL, Binance, Mock, Paper)` to `← exchange adapters (HL, Mock, Paper; Binance coming Phase 2)`

---

## Item 2 — README: Add `--json` flag docs
**Priority: must-fix** (plan spec; agent-first design)

**File:** `README.md`

**Change:** Add a "JSON Output" section after the quickstart commands:
```markdown
### JSON Output
All commands support `--json` for machine-readable output (ideal for agent integration):

```bash
fear-protocol signal --json
fear-protocol status --json
fear-protocol backtest run --start 2024-01-01 --end 2024-12-31 --json
```
```

---

## Item 3 — README: Add TOML config example
**Priority: must-fix** (plan spec; users need this to configure the tool)

**File:** `README.md`

**Change:** Add a "Configuration" section:
```markdown
## Configuration

Create `fear-protocol.toml` in your project root (or pass via `--config`):

```toml
[strategy]
name = "fear-greed-dca"
dca_amount = 100.0
fear_threshold = 30
greed_threshold = 70

[exchange]
name = "paper"
initial_balance = 10000.0

[agent]
mode = "dry-run"
```
```

---

## Item 4 — Tests: backtest `run_streaming()` coverage
**Priority: must-fix** (86% coverage; streaming path lines 48-57, 289-304 uncovered)

**File:** `tests/test_backtest_engine.py` (add new test cases)

**Change:** Add tests that call `engine.run_streaming()` directly:
```python
def test_run_streaming_yields_ticks():
    config = BacktestConfig(start_date="2024-01-01", end_date="2024-01-07", ...)
    engine = BacktestEngine(config=config, strategy=strategy)
    ticks = list(engine.run_streaming(fg_data=fg_dict, price_data=price_dict))
    assert len(ticks) > 0
    assert ticks[0].timestamp is not None

def test_run_streaming_empty_data():
    # Test edge case: no overlapping dates
    ticks = list(engine.run_streaming(fg_data={}, price_data={}))
    assert ticks == []
```

---

## Item 5 — Tests: backtest `report.to_html()` coverage
**Priority: must-fix** (85% coverage; HTML path lines 123-131 uncovered)

**File:** `tests/test_backtest_report.py` (add new test cases)

**Change:** Add:
```python
def test_to_html_returns_string():
    report = BacktestReport(...)
    html = report.to_html()
    assert "<html" in html
    assert "fear-protocol" in html.lower()

def test_to_html_includes_metrics():
    report = BacktestReport(...)
    html = report.to_html()
    assert str(report.total_return) in html
```

---

## Item 6 — Tests: `agent/api.py` smoke tests
**Priority: must-fix** (zero tests; API is the primary integration surface)

**File:** `tests/test_agent_api.py` (new file)

**Change:** Create with mocked HTTP providers:
```python
@pytest.fixture
def agent(monkeypatch):
    monkeypatch.setattr(FearGreedProvider, "get_current", lambda _: {"value": 25, "label": "Fear"})
    monkeypatch.setattr(BinancePriceProvider, "get_price", lambda _: Decimal("50000"))
    return FearProtocolAgent(strategy="fear-greed-dca", exchange="mock", mode="dry-run")

def test_get_signal_returns_dict(agent):
    result = agent.get_signal()
    assert "action" in result
    assert "confidence" in result
    assert "fear_greed" in result

def test_get_signal_schema_valid(agent):
    result = agent.get_signal()
    schema = SignalSchema(**result)
    assert schema.action in ("buy", "sell", "hold")

def test_execute_dry_run(agent):
    result = agent.execute(portfolio_value=Decimal("10000"), total_invested=Decimal("0"))
    assert "action" in result
    assert result.get("mode") == "dry-run"
```

Remove `fear_protocol/agent/api.py` from the coverage omit list in `pyproject.toml` once tests are added.

---

## Item 7 — Tests: CLI smoke tests
**Priority: nice-to-have** (exempted in pyproject.toml; useful but not blocking)

**File:** `tests/test_cli.py` (new file)

**Change:** Use `typer.testing.CliRunner`:
```python
from typer.testing import CliRunner
from fear_protocol.cli.main import app

runner = CliRunner()

def test_signal_help():
    result = runner.invoke(app, ["signal", "--help"])
    assert result.exit_code == 0

def test_status_dry_run(monkeypatch):
    monkeypatch.setattr(...)  # mock providers
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0

def test_signal_json_flag(monkeypatch):
    monkeypatch.setattr(...)
    result = runner.invoke(app, ["signal", "--json"])
    data = json.loads(result.stdout)
    assert "action" in data
```

Remove `fear_protocol/cli/*` from the coverage omit list once tests pass.

---

## Item 8 — Pyright strict mode
**Priority: nice-to-have** (plan spec said `strict`; `basic` is working fine currently)

**File:** `pyproject.toml`

**Change:**
```toml
[tool.pyright]
typeCheckingMode = "strict"
```

**Note:** This will surface new type errors. Run `uv run pyright` first to get the full error list, then fix annotations in a separate commit. Common fixes: explicit `-> None` returns, typed `dict[str, Any]` parameters, `Optional[X]` → `X | None`. Do this *after* all test fixes land so CI stays green.

---

## Execution Order

1. **README fixes** (Items 1, 2, 3) — 15 min, no risk
2. **Test: agent/api.py** (Item 6) — highest value, covers the main integration surface
3. **Test: backtest streaming + HTML** (Items 4, 5) — push coverage above 90% for those modules
4. **Test: CLI** (Item 7) — nice-to-have, do after above
5. **Pyright strict** (Item 8) — last; tackle after all tests green

---

## Out of Scope (Phase 2/3)
- `exchanges/binance.py` — Phase 2
- `agent/rpc.py` — Phase 3
- `core/signals.py` — Phase 2
- `release.yml` / `docs.yml` CI workflows — Phase 3
