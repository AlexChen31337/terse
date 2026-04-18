# fear-protocol — Architecture Plan
> Designed by: Alex Chen (Planner Agent)  
> Date: 2026-02-27  
> Status: DRAFT — ready for Builder

---

## Table of Contents

1. [Vision & README Draft](#1-vision--readme-draft)
2. [Architecture Overview](#2-architecture-overview)
3. [Exchange Adapter Interface](#3-exchange-adapter-interface)
4. [Strategy Interface](#4-strategy-interface)
5. [Backtesting Engine](#5-backtesting-engine)
6. [CLI Design](#6-cli-design)
7. [Agent Integration](#7-agent-integration)
8. [Project Structure](#8-project-structure)
9. [CI/CD](#9-cicd)
10. [Migration Plan](#10-migration-plan)
11. [Phase Breakdown](#11-phase-breakdown)

---

## 1. Vision & README Draft

### What is fear-protocol?

**fear-protocol** is a production-grade, exchange-agnostic Python framework for sentiment-driven DCA (Dollar-Cost Averaging) strategies. It turns the crypto market's most reliable signal — the Fear & Greed Index — into automated, disciplined trades.

Born from the FearHarvester skill (backtested Sharpe 2.01), fear-protocol extracts the core insight into a composable, testable, agent-native platform.

### Who is it for?

| User | How they use it |
|------|----------------|
| **Retail traders** | CLI: run DCA bot with one command |
| **Quant developers** | Python API: compose strategies, backtest on historical data |
| **AI agents** | JSON API / SDK: integrate into EvoClaw, OpenClaw, ClawChain agents |
| **Researchers** | Backtest engine: test sentiment-price correlation hypotheses |

### Why does it exist?

The insight is simple: **extreme fear is historically one of the best buying signals in crypto**. Buying when F&G ≤ 20 and holding 120 days has Sharpe 2.01 — better than most managed funds. But:

1. Most tools are exchange-specific (Hyperliquid only)
2. Backtests are hard to reproduce and extend
3. Running this manually requires discipline that humans lack
4. AI agents need a structured, typed, testable interface

fear-protocol solves all four.

### Core Principles

- **Exchange-agnostic**: Hyperliquid, Binance, Coinbase, mock — all via adapters
- **Strategy-composable**: FearGreedDCA is one strategy; mix and stack them
- **Backtest-first**: Any strategy must be backtestable before deployment
- **Agent-native**: Outputs structured JSON; integrates with EvoClaw/OpenClaw
- **Production-grade**: 90%+ coverage, fully typed, CI enforced

---

## 2. Architecture Overview

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        fear-protocol                             │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  Data Layer  │    │ Strategy     │    │ Execution Layer  │  │
│  │              │    │ Layer        │    │                  │  │
│  │ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────────┐ │  │
│  │ │FearGreed │ │───▶│ │FearGreed │ │───▶│ │ExchangeAdapt │ │  │
│  │ │Provider  │ │    │ │DCA Strat │ │    │ │er (HL/Binance│ │  │
│  │ └──────────┘ │    │ └──────────┘ │    │ │/Mock)        │ │  │
│  │              │    │              │    │ └──────────────┘ │  │
│  │ ┌──────────┐ │    │ ┌──────────┐ │    │                  │  │
│  │ │Price     │ │───▶│ │Momentum  │ │    │ ┌──────────────┐ │  │
│  │ │Provider  │ │    │ │DCA Strat │ │    │ │State Manager │ │  │
│  │ └──────────┘ │    │ └──────────┘ │    │ └──────────────┘ │  │
│  │              │    │              │    │                  │  │
│  │ ┌──────────┐ │    │ ┌──────────┐ │    └──────────────────┘  │
│  │ │Historical│ │───▶│ │GridFear  │ │                          │
│  │ │Provider  │ │    │ │Strat     │ │    ┌──────────────────┐  │
│  │ └──────────┘ │    │ └──────────┘ │    │ Backtest Engine  │  │
│  └──────────────┘    └──────────────┘    │                  │  │
│                              │            │ ┌──────────────┐ │  │
│                              └───────────▶│ │BacktestRunner│ │  │
│                                           │ └──────────────┘ │  │
│                                           │ ┌──────────────┐ │  │
│                                           │ │ReportGen     │ │  │
│                                           │ └──────────────┘ │  │
│                                           └──────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     Interfaces                            │  │
│  │   CLI (Typer)  │  Python SDK  │  Agent JSON API          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Module Dependency Graph

```
fear_protocol/
├── core/           ← pure domain logic, no I/O
│   ├── models.py   ← dataclasses: Trade, Position, Signal, BacktestResult
│   ├── signals.py  ← signal generation (strategy-agnostic)
│   └── math.py     ← Sharpe, drawdown, Kelly sizing
│
├── data/           ← data providers (abstract + concrete)
│   ├── base.py     ← AbstractDataProvider
│   ├── fear_greed.py ← alternative.me
│   ├── price.py    ← Binance, CoinGecko, mock
│   └── historical.py ← CSV, Binance history, cached
│
├── strategies/     ← pluggable strategies
│   ├── base.py     ← AbstractStrategy interface
│   ├── fear_greed_dca.py  ← ported from FearHarvester
│   ├── momentum_dca.py    ← momentum-based variant
│   └── grid_fear.py       ← grid-buying on fear events
│
├── exchanges/      ← exchange adapters
│   ├── base.py     ← AbstractExchangeAdapter
│   ├── hyperliquid.py  ← ported from FearHarvester HLSpotExecutor
│   ├── binance.py      ← Binance spot
│   └── mock.py         ← deterministic mock for testing
│
├── backtest/       ← backtesting engine
│   ├── engine.py   ← BacktestEngine (core runner)
│   ├── portfolio.py ← portfolio state tracking during backtest
│   └── report.py   ← metrics, charts, JSON/HTML output
│
├── state/          ← position & portfolio state management
│   ├── manager.py  ← StateManager (load/save/query)
│   └── models.py   ← ExecutorState, Portfolio
│
├── agent/          ← agent integration layer
│   ├── api.py      ← FearProtocolAgent — JSON in/out interface
│   └── schemas.py  ← Pydantic schemas for agent I/O
│
└── cli/            ← CLI (built with Typer)
    ├── main.py     ← CLI entrypoint
    ├── commands/
    │   ├── run.py      ← fear-protocol run
    │   ├── backtest.py ← fear-protocol backtest
    │   ├── signal.py   ← fear-protocol signal
    │   └── status.py   ← fear-protocol status
    └── output.py   ← rich terminal formatting
```

---

## 3. Exchange Adapter Interface

### Abstract Base Class

```python
# fear_protocol/exchanges/base.py

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class OrderResult:
    """Result of an order placement."""
    order_id: str
    status: str            # "filled" | "partial" | "resting" | "failed"
    filled_qty: Decimal
    avg_fill_price: Decimal
    fee: Decimal
    raw: dict              # raw exchange response for debugging


@dataclass
class Balance:
    asset: str
    free: Decimal
    locked: Decimal

    @property
    def total(self) -> Decimal:
        return self.free + self.locked


@dataclass
class MarketPrice:
    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal

    @property
    def mid(self) -> Decimal:
        return (self.bid + self.ask) / 2


class AbstractExchangeAdapter(ABC):
    """
    Exchange adapter interface. All exchanges must implement this.

    Implementations:
    - HyperliquidAdapter  (UBTC/USDC spot)
    - BinanceAdapter      (BTC/USDT spot)
    - MockAdapter         (deterministic testing)
    - PaperAdapter        (local state, no API calls)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable exchange name."""

    @property
    @abstractmethod
    def base_asset(self) -> str:
        """Base asset symbol, e.g. 'BTC', 'UBTC'."""

    @property
    @abstractmethod
    def quote_asset(self) -> str:
        """Quote asset symbol, e.g. 'USDC', 'USDT'."""

    @abstractmethod
    def get_price(self) -> MarketPrice:
        """Get current market price for the trading pair."""

    @abstractmethod
    def get_balances(self) -> dict[str, Balance]:
        """Get current balances for all assets."""

    @abstractmethod
    def market_buy(self, quote_amount: Decimal) -> OrderResult:
        """
        Buy base asset using quote_amount of quote asset.

        Args:
            quote_amount: USD/USDC/USDT amount to spend

        Returns:
            OrderResult with fill details
        """

    @abstractmethod
    def market_sell(self, base_amount: Decimal) -> OrderResult:
        """
        Sell base_amount of base asset.

        Args:
            base_amount: Amount of base asset (BTC) to sell

        Returns:
            OrderResult with fill details
        """

    def validate_order_size(self, quote_amount: Decimal) -> None:
        """Validate order size meets exchange minimums. Override in subclasses."""
        pass

    def close(self) -> None:
        """Clean up connections. Override if needed."""
        pass
```

### Hyperliquid Adapter (ported from FearHarvester)

```python
# fear_protocol/exchanges/hyperliquid.py

class HyperliquidAdapter(AbstractExchangeAdapter):
    """
    Hyperliquid spot adapter for UBTC/USDC.

    Ports HLSpotExecutor from FearHarvester skill.
    Adds proper typing, error handling, and adapter interface.
    """

    name = "hyperliquid"
    base_asset = "UBTC"
    quote_asset = "USDC"

    PAIR_INDEX = "@142"          # HL spot pair for UBTC/USDC
    SZ_DECIMALS = 5
    PX_DECIMALS = 0

    def __init__(
        self,
        private_key: str,
        wallet_address: str | None = None,
        testnet: bool = False,
    ): ...

    def get_price(self) -> MarketPrice: ...
    def get_balances(self) -> dict[str, Balance]: ...
    def market_buy(self, quote_amount: Decimal) -> OrderResult: ...
    def market_sell(self, base_amount: Decimal) -> OrderResult: ...
```

### Binance Adapter

```python
# fear_protocol/exchanges/binance.py

class BinanceAdapter(AbstractExchangeAdapter):
    """
    Binance spot adapter for BTC/USDT.
    Uses python-binance or direct REST API.
    """

    name = "binance"
    base_asset = "BTC"
    quote_asset = "USDT"

    def __init__(self, api_key: str, api_secret: str, testnet: bool = False): ...
```

### Mock Adapter (for backtesting & tests)

```python
# fear_protocol/exchanges/mock.py

class MockAdapter(AbstractExchangeAdapter):
    """
    Deterministic mock exchange for testing and backtesting.

    Simulates slippage, fees, and order fills with configurable parameters.
    """

    name = "mock"

    def __init__(
        self,
        price_series: dict[str, Decimal],   # date -> price
        fee_rate: Decimal = Decimal("0.001"),
        slippage_rate: Decimal = Decimal("0.001"),
    ): ...
```

### Paper Adapter (local state, no API)

```python
# fear_protocol/exchanges/paper.py

class PaperAdapter(AbstractExchangeAdapter):
    """
    Paper trading adapter. Fetches real market prices but doesn't place orders.
    Tracks positions in local state file.
    """
    # Fetches price from Binance/CoinGecko but simulates fills locally
```

### Exchange Registry

```python
# fear_protocol/exchanges/__init__.py

ADAPTERS: dict[str, type[AbstractExchangeAdapter]] = {
    "hyperliquid": HyperliquidAdapter,
    "binance": BinanceAdapter,
    "mock": MockAdapter,
    "paper": PaperAdapter,
}

def get_adapter(name: str, **kwargs) -> AbstractExchangeAdapter:
    if name not in ADAPTERS:
        raise ValueError(f"Unknown exchange: {name}. Available: {list(ADAPTERS)}")
    return ADAPTERS[name](**kwargs)
```

---

## 4. Strategy Interface

### Abstract Strategy

```python
# fear_protocol/strategies/base.py

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any


class ActionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class StrategySignal:
    """Output of a strategy evaluation."""
    action: ActionType
    confidence: float          # 0.0–1.0
    reason: str                # human-readable explanation
    suggested_amount: Decimal  # quote amount for BUY, base amount for SELL
    metadata: dict[str, Any]   # strategy-specific extras


@dataclass
class MarketContext:
    """Input snapshot provided to strategies on each tick."""
    timestamp: str
    fear_greed: int
    fear_greed_label: str
    price: Decimal
    portfolio_value: Decimal
    total_invested: Decimal
    open_positions: list[dict]


class AbstractStrategy(ABC):
    """
    Strategy interface. Implement this to create a new strategy.

    A strategy is a pure function: MarketContext → StrategySignal.
    It must NOT have side effects. Execution is handled by the engine.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name, e.g. 'fear-greed-dca'."""

    @property
    @abstractmethod
    def description(self) -> str:
        """One-line description of the strategy."""

    @abstractmethod
    def evaluate(self, ctx: MarketContext) -> StrategySignal:
        """
        Evaluate market context and return a signal.

        Must be deterministic for the same input (enables backtesting).
        """

    def on_fill(self, order_result: "OrderResult", ctx: MarketContext) -> None:
        """Called after an order is filled. Override for stateful strategies."""
        pass

    def validate_config(self) -> None:
        """Validate strategy config. Raise ValueError if invalid."""
        pass
```

### FearGreedDCA Strategy (ported from FearHarvester)

```python
# fear_protocol/strategies/fear_greed_dca.py

@dataclass
class FearGreedDCAConfig:
    buy_threshold: int = 20         # F&G ≤ this → BUY
    sell_threshold: int = 50        # F&G ≥ this → consider SELL
    hold_days: int = 120            # minimum hold before sell
    dca_amount_usd: Decimal = Decimal("500")
    max_capital_usd: Decimal = Decimal("5000")
    # Kelly fraction (0 = fixed amount, >0 = Kelly-sized)
    kelly_fraction: float = 0.0


class FearGreedDCAStrategy(AbstractStrategy):
    """
    The original FearHarvester strategy.

    DCA when F&G ≤ buy_threshold.
    Rebalance when F&G ≥ sell_threshold AND hold_days elapsed.
    Backtested Sharpe 2.01.
    """

    name = "fear-greed-dca"
    description = "DCA on extreme fear, hold minimum N days, exit on recovery"

    def __init__(self, config: FearGreedDCAConfig | None = None):
        self.config = config or FearGreedDCAConfig()

    def evaluate(self, ctx: MarketContext) -> StrategySignal:
        cfg = self.config
        fg = ctx.fear_greed

        # BUY signal
        if fg <= cfg.buy_threshold:
            if ctx.total_invested < cfg.max_capital_usd:
                return StrategySignal(
                    action=ActionType.BUY,
                    confidence=self._fear_confidence(fg),
                    reason=f"F&G={fg} ≤ {cfg.buy_threshold} (Extreme Fear)",
                    suggested_amount=cfg.dca_amount_usd,
                    metadata={"fg": fg, "threshold": cfg.buy_threshold},
                )

        # SELL signal
        if fg >= cfg.sell_threshold:
            eligible = self._get_eligible_positions(ctx)
            if eligible:
                total_qty = sum(p["btc_qty"] for p in eligible)
                return StrategySignal(
                    action=ActionType.SELL,
                    confidence=0.8,
                    reason=f"F&G={fg} ≥ {cfg.sell_threshold}, {len(eligible)} positions past hold period",
                    suggested_amount=Decimal(str(total_qty)),
                    metadata={"eligible_positions": len(eligible)},
                )

        return StrategySignal(
            action=ActionType.HOLD,
            confidence=1.0,
            reason=f"F&G={fg} in neutral zone",
            suggested_amount=Decimal("0"),
            metadata={"fg": fg},
        )

    def _fear_confidence(self, fg: int) -> float:
        """Higher confidence at lower F&G (deeper fear = stronger signal)."""
        return max(0.5, min(1.0, (self.config.buy_threshold - fg) / self.config.buy_threshold + 0.5))

    def _get_eligible_positions(self, ctx: MarketContext) -> list[dict]:
        """Return positions past hold period."""
        from datetime import datetime, timedelta
        now = datetime.now()
        eligible = []
        for pos in ctx.open_positions:
            if pos.get("status") != "open":
                continue
            entry = datetime.fromisoformat(pos["timestamp"])
            if (now - entry).days >= self.config.hold_days:
                eligible.append(pos)
        return eligible
```

### MomentumDCA Strategy

```python
# fear_protocol/strategies/momentum_dca.py

@dataclass
class MomentumDCAConfig:
    fear_threshold: int = 30        # F&G ≤ this to activate momentum watch
    momentum_window_days: int = 7   # look for consecutive down days
    min_consecutive_down: int = 3   # trigger after N consecutive red days
    dca_amount_usd: Decimal = Decimal("500")
    hold_days: int = 60


class MomentumDCAStrategy(AbstractStrategy):
    """
    Buy after N consecutive down days when F&G is also in fear territory.
    Combines price momentum with sentiment confirmation.
    """
    name = "momentum-dca"
    description = "DCA after N consecutive red days + fear confirmation"
```

### GridFear Strategy

```python
# fear_protocol/strategies/grid_fear.py

@dataclass
class GridFearConfig:
    fear_threshold: int = 25
    grid_levels: int = 5            # number of grid levels
    grid_spacing_pct: float = 5.0   # % between grid levels
    base_amount_usd: Decimal = Decimal("200")
    # Amount increases by multiplier per level below reference
    level_multiplier: float = 1.5


class GridFearStrategy(AbstractStrategy):
    """
    Place grid buy orders at stepped price levels during fear periods.
    Heavier buys at lower levels (anti-martingale grid).
    """
    name = "grid-fear"
    description = "Grid DCA with increasing size at lower fear levels"
```

### Strategy Registry

```python
# fear_protocol/strategies/__init__.py

STRATEGIES: dict[str, type[AbstractStrategy]] = {
    "fear-greed-dca": FearGreedDCAStrategy,
    "momentum-dca": MomentumDCAStrategy,
    "grid-fear": GridFearStrategy,
}
```

---

## 5. Backtesting Engine

### Architecture

```
BacktestEngine
     │
     ├── loads historical data (FearGreedProvider + PriceProvider)
     │
     ├── creates MockAdapter (simulated fills with slippage/fees)
     │
     ├── iterates day-by-day through history:
     │     for each day:
     │       1. build MarketContext from historical data
     │       2. strategy.evaluate(ctx) → StrategySignal
     │       3. if BUY/SELL → mock_adapter.execute(signal)
     │       4. portfolio.update(fill)
     │       5. record BacktestTick
     │
     └── BacktestReport (metrics + per-trade log + equity curve)
```

### BacktestEngine Interface

```python
# fear_protocol/backtest/engine.py

@dataclass
class BacktestConfig:
    strategy: AbstractStrategy
    start_date: str               # "2018-01-01"
    end_date: str                 # "2024-12-31"
    initial_capital: Decimal      # starting USDC
    fee_rate: Decimal = Decimal("0.001")
    slippage_rate: Decimal = Decimal("0.001")
    data_source: str = "binance"  # price data source
    fear_greed_source: str = "alternative.me"


@dataclass
class BacktestTick:
    date: str
    price: Decimal
    fear_greed: int
    action: ActionType
    signal: StrategySignal
    fill: OrderResult | None
    portfolio_value: Decimal
    cash: Decimal
    base_held: Decimal


@dataclass
class BacktestResult:
    config: BacktestConfig
    ticks: list[BacktestTick]
    trades: list[dict]

    # Core metrics
    total_return_pct: float
    annualized_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    calmar_ratio: float          # annualized return / max drawdown
    win_rate_pct: float
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float
    total_trades: int
    avg_hold_days: float

    # Benchmark comparison
    btc_hold_return_pct: float   # buy-and-hold benchmark
    alpha: float                  # vs buy-and-hold


class BacktestEngine:
    def __init__(self, config: BacktestConfig): ...

    def run(self) -> BacktestResult:
        """Run full backtest. Returns complete results."""

    def run_streaming(self) -> Iterator[BacktestTick]:
        """Stream ticks for real-time progress display."""
```

### Data Sources

```python
# fear_protocol/data/historical.py

class HistoricalDataProvider:
    """
    Fetches and caches historical F&G + price data.

    Sources:
    - F&G: alternative.me API (2000 days, cached locally)
    - Price: Binance klines API (daily OHLCV, cached locally)
    - Cache: ~/.fear-protocol/cache/ (JSON files, TTL 24h)
    """

    CACHE_DIR = Path.home() / ".fear-protocol" / "cache"

    def get_fear_greed_history(
        self, start: str, end: str
    ) -> dict[str, int]:              # date -> fg_value
        """Return F&G values indexed by date string."""

    def get_price_history(
        self, symbol: str, start: str, end: str
    ) -> dict[str, Decimal]:          # date -> close_price
        """Return daily close prices indexed by date string."""
```

### Report Generation

```python
# fear_protocol/backtest/report.py

class BacktestReport:
    def __init__(self, result: BacktestResult): ...

    def to_dict(self) -> dict:
        """Full result as JSON-serialisable dict."""

    def to_json(self, path: Path) -> None:
        """Write JSON report."""

    def to_markdown(self) -> str:
        """Human-readable markdown summary."""

    def to_html(self, path: Path) -> None:
        """HTML report with equity curve chart (uses plotly or matplotlib)."""

    def print_summary(self) -> None:
        """Rich terminal table output."""
```

---

## 6. CLI Design

Built with **Typer** + **Rich** for beautiful terminal output.

### Commands

```
fear-protocol
├── run         Run a strategy (dry-run/paper/live)
├── backtest    Backtest a strategy on historical data
├── signal      Check current F&G signal
├── status      Show current positions and P&L
└── config      Show/validate configuration
```

### `fear-protocol run`

```
fear-protocol run [OPTIONS]

  Run the DCA strategy.

Options:
  --strategy TEXT          Strategy name [default: fear-greed-dca]
  --exchange TEXT          Exchange adapter [default: paper]
  --mode [dry-run|paper|live]  Execution mode [default: dry-run]
  --buy-threshold INT      F&G buy threshold [default: 20]
  --sell-threshold INT     F&G sell threshold [default: 50]
  --hold-days INT          Minimum hold days [default: 120]
  --dca-amount FLOAT       USD per DCA buy [default: 500]
  --max-capital FLOAT      Maximum capital [default: 5000]
  --testnet                Use exchange testnet
  --config PATH            Load config from YAML/TOML file
  --json                   Output JSON (for agent integration)
  --help                   Show this message and exit.

Examples:
  fear-protocol run --mode dry-run
  fear-protocol run --exchange hyperliquid --mode live --buy-threshold 15
  fear-protocol run --strategy momentum-dca --mode paper
  fear-protocol run --config my-strategy.toml --mode live
```

### `fear-protocol backtest`

```
fear-protocol backtest [OPTIONS]

  Backtest a strategy on historical data.

Options:
  --strategy TEXT          Strategy name [default: fear-greed-dca]
  --start TEXT             Start date YYYY-MM-DD [default: 2018-01-01]
  --end TEXT               End date [default: today]
  --capital FLOAT          Starting capital in USD [default: 10000]
  --buy-threshold INT      F&G buy threshold [default: 20]
  --hold-days INT          Hold period in days [default: 120]
  --fee FLOAT              Fee rate [default: 0.001]
  --slippage FLOAT         Slippage rate [default: 0.001]
  --output PATH            Save JSON results to file
  --html PATH              Save HTML report with charts
  --compare                Compare multiple threshold values
  --json                   Output JSON to stdout
  --help                   Show this message and exit.

Examples:
  fear-protocol backtest --start 2020-01-01 --capital 10000
  fear-protocol backtest --strategy momentum-dca --compare
  fear-protocol backtest --output results.json --html report.html
```

### `fear-protocol signal`

```
fear-protocol signal [OPTIONS]

  Check current Fear & Greed signal.

Options:
  --threshold INT          Signal threshold [default: 20]
  --json                   Output JSON
  --watch                  Refresh every N seconds
  --interval INT           Watch interval in seconds [default: 300]
  --help                   Show this message and exit.

Examples:
  fear-protocol signal
  fear-protocol signal --json
  fear-protocol signal --watch --interval 60
```

### `fear-protocol status`

```
fear-protocol status [OPTIONS]

  Show current positions and P&L.

Options:
  --exchange TEXT          Exchange [default: paper]
  --mode [paper|live]      Mode [default: paper]
  --json                   Output JSON
  --help                   Show this message and exit.
```

### Config File Format (TOML)

```toml
# fear-protocol.toml

[strategy]
name = "fear-greed-dca"
buy_threshold = 20
sell_threshold = 50
hold_days = 120
dca_amount_usd = 500
max_capital_usd = 5000

[exchange]
name = "hyperliquid"
testnet = false

[execution]
mode = "live"   # dry-run | paper | live

[notifications]
telegram_token = ""      # optional: notify on trade
telegram_chat_id = ""
```

---

## 7. Agent Integration

### Design Philosophy

fear-protocol is **agent-first**: every command has a `--json` flag, and the Python API is structured to be called directly from agents without subprocess overhead.

### Python SDK for Agents

```python
# fear_protocol/agent/api.py

from fear_protocol import FearProtocol, RunConfig, BacktestConfig

# One-shot signal check (agent polls this on schedule)
async def check_signal() -> dict:
    fp = FearProtocol()
    signal = await fp.get_signal()
    return signal.to_dict()
    # → {"action": "DCA_BUY", "confidence": 0.87, "fg": 12, "price": 95000, ...}

# Run one strategy tick (agent calls this when cron fires)
async def run_tick(config: dict) -> dict:
    fp = FearProtocol.from_config(config)
    result = await fp.run_once()
    return result.to_dict()
    # → {"action": "DCA_BUY", "fill": {...}, "position": {...}, ...}

# Run full backtest (agent calls this for research)
async def backtest(config: dict) -> dict:
    fp = FearProtocol()
    result = await fp.backtest(BacktestConfig(**config))
    return result.to_dict()
```

### EvoClaw Agent Integration

```python
# In an EvoClaw agent's tool loop:

from fear_protocol.agent.api import FearProtocolAgent

class FearHarvesterAgent(EvoclawAgent):
    def __init__(self):
        self.fp = FearProtocolAgent(
            strategy="fear-greed-dca",
            exchange="hyperliquid",
            mode="live",
        )

    async def on_heartbeat(self, ctx):
        signal = await self.fp.get_signal()
        if signal["action"] == "DCA_BUY":
            result = await self.fp.execute(signal)
            await self.notify(f"Bought ${result['amount']} BTC @ F&G={signal['fg']}")
```

### OpenClaw Skill Integration (existing)

The `fear-harvester` OpenClaw skill will be updated to use `fear-protocol` as its backend:

```python
# skills/fear-harvester/scripts/executor.py (updated)
from fear_protocol import FearProtocol

fp = FearProtocol(config_path="~/.fear-protocol/config.toml")
result = fp.run_once()
print(result.to_json())
```

### ClawChain Agent Integration

fear-protocol exposes a JSON-RPC compatible interface for on-chain agents:

```python
# fear_protocol/agent/rpc.py

class FearProtocolRPC:
    """
    JSON-RPC 2.0 compatible interface.
    ClawChain agents can call methods via the agent tool loop.
    """

    def get_signal(self) -> dict: ...
    def get_backtest(self, params: dict) -> dict: ...
    def get_status(self) -> dict: ...
    def execute_once(self, params: dict) -> dict: ...
```

### Agent Output Schema (Pydantic)

```python
# fear_protocol/agent/schemas.py

class SignalSchema(BaseModel):
    timestamp: str
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    fear_greed: int
    fear_greed_label: str
    price: float
    reason: str
    suggested_amount: float
    strategy: str


class ExecuteResultSchema(BaseModel):
    action: str
    success: bool
    fill: Optional[OrderFillSchema]
    position: Optional[PositionSchema]
    error: Optional[str]
    dry_run: bool
```

---

## 8. Project Structure

```
fear-protocol/
│
├── README.md                       # project overview, quickstart
├── CHANGELOG.md                    # semantic versioning log
├── LICENSE                         # MIT
├── pyproject.toml                  # build system, dependencies, tools config
├── .python-version                 # pinned Python version (3.12)
├── uv.lock                         # locked dependencies
│
├── fear_protocol/                  # main package
│   ├── __init__.py                 # public API: FearProtocol, BacktestEngine
│   ├── py.typed                    # PEP 561 typed marker
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py               # Trade, Position, Signal, BacktestResult
│   │   ├── signals.py              # signal utilities
│   │   └── math.py                 # Sharpe, Sortino, Kelly, drawdown
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── base.py                 # AbstractDataProvider
│   │   ├── fear_greed.py           # alternative.me provider
│   │   ├── price.py                # Binance / CoinGecko / mock
│   │   └── historical.py           # cached historical data
│   │
│   ├── strategies/
│   │   ├── __init__.py             # STRATEGIES registry
│   │   ├── base.py                 # AbstractStrategy
│   │   ├── fear_greed_dca.py       # FearGreedDCAStrategy (from FearHarvester)
│   │   ├── momentum_dca.py         # MomentumDCAStrategy
│   │   └── grid_fear.py            # GridFearStrategy
│   │
│   ├── exchanges/
│   │   ├── __init__.py             # ADAPTERS registry + get_adapter()
│   │   ├── base.py                 # AbstractExchangeAdapter
│   │   ├── hyperliquid.py          # HyperliquidAdapter (from FearHarvester)
│   │   ├── binance.py              # BinanceAdapter
│   │   ├── mock.py                 # MockAdapter (backtest)
│   │   └── paper.py                # PaperAdapter (paper trading)
│   │
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── engine.py               # BacktestEngine
│   │   ├── portfolio.py            # portfolio state during backtest
│   │   └── report.py               # BacktestReport + metrics
│   │
│   ├── state/
│   │   ├── __init__.py
│   │   ├── manager.py              # StateManager (load/save/query)
│   │   └── models.py               # ExecutorState, Portfolio
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── api.py                  # FearProtocolAgent (async-first)
│   │   ├── rpc.py                  # JSON-RPC compatible interface
│   │   └── schemas.py              # Pydantic I/O schemas
│   │
│   └── cli/
│       ├── __init__.py
│       ├── main.py                 # Typer app entrypoint
│       ├── output.py               # Rich terminal formatting
│       └── commands/
│           ├── __init__.py
│           ├── run.py              # fear-protocol run
│           ├── backtest.py         # fear-protocol backtest
│           ├── signal.py           # fear-protocol signal
│           └── status.py           # fear-protocol status
│
├── tests/
│   ├── conftest.py                 # pytest fixtures (shared mocks, sample data)
│   ├── unit/
│   │   ├── test_core_models.py
│   │   ├── test_core_math.py
│   │   ├── test_strategies_fear_greed_dca.py
│   │   ├── test_strategies_momentum_dca.py
│   │   ├── test_exchanges_mock.py
│   │   ├── test_exchanges_paper.py
│   │   ├── test_state_manager.py
│   │   └── test_agent_schemas.py
│   ├── integration/
│   │   ├── test_backtest_engine.py  # end-to-end backtest on sample data
│   │   ├── test_cli_run.py          # CLI integration tests
│   │   ├── test_cli_backtest.py
│   │   └── test_agent_api.py
│   └── fixtures/
│       ├── fear_greed_history.json  # sample F&G data (2018-2024)
│       └── btc_prices.json          # sample BTC daily prices
│
├── docs/
│   ├── index.md                    # MkDocs home
│   ├── quickstart.md
│   ├── strategies.md               # strategy reference
│   ├── exchanges.md                # adapter reference
│   ├── backtesting.md              # backtest guide
│   ├── agent-integration.md        # EvoClaw/OpenClaw/ClawChain guide
│   └── api/                        # auto-generated from docstrings
│
├── examples/
│   ├── basic_run.py                # simplest possible usage
│   ├── custom_strategy.py          # how to write a custom strategy
│   ├── agent_integration.py        # EvoClaw integration example
│   └── full_backtest.py            # comprehensive backtest example
│
├── .github/
│   └── workflows/
│       ├── ci.yml                  # test + lint + coverage on every PR
│       ├── release.yml             # publish to PyPI on tag
│       └── docs.yml                # deploy docs to GitHub Pages
│
└── scripts/
    ├── dev-setup.sh                # bootstrap dev environment
    └── benchmark.py                # performance benchmarks
```

---

## 9. CI/CD

### GitHub Actions: CI (`ci.yml`)

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"

      - name: Set up Python
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Lint (ruff)
        run: uv run ruff check fear_protocol tests

      - name: Type check (pyright)
        run: uv run pyright fear_protocol

      - name: Run tests
        run: uv run pytest tests/ -v --tb=short

      - name: Coverage check
        run: |
          uv run pytest tests/ --cov=fear_protocol \
            --cov-report=term-missing \
            --cov-fail-under=90

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
```

### GitHub Actions: Release (`release.yml`)

```yaml
name: Release

on:
  push:
    tags:
      - "v*.*.*"

jobs:
  release:
    runs-on: ubuntu-latest
    environment: pypi

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        run: uv publish
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
```

### `pyproject.toml` (key sections)

```toml
[project]
name = "fear-protocol"
version = "0.1.0"
description = "Exchange-agnostic sentiment-driven DCA framework"
authors = [{name = "ClawInfra", email = "alex.chen31337@gmail.com"}]
license = {text = "MIT"}
requires-python = ">=3.11"
readme = "README.md"

dependencies = [
    "requests>=2.31",
    "typer>=0.12",
    "rich>=13",
    "pydantic>=2",
    "python-dateutil>=2.8",
]

[project.optional-dependencies]
hyperliquid = ["hyperliquid-python-sdk>=0.5", "eth-account>=0.13"]
binance = ["python-binance>=1.0"]
docs = ["mkdocs-material>=9", "mkdocstrings[python]>=0.24"]
dev = ["pytest>=8", "pytest-cov>=5", "ruff>=0.4", "pyright>=1.1"]

[project.scripts]
fear-protocol = "fear_protocol.cli.main:app"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM"]

[tool.pyright]
strict = true
pythonVersion = "3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--tb=short -q"

[tool.coverage.run]
source = ["fear_protocol"]
omit = ["*/tests/*"]

[tool.coverage.report]
fail_under = 90
show_missing = true
```

---

## 10. Migration Plan

### What exists in FearHarvester → Where it goes

| FearHarvester | fear-protocol | Notes |
|--------------|---------------|-------|
| `executor.py::HLSpotExecutor` | `exchanges/hyperliquid.py::HyperliquidAdapter` | Adapt to AbstractExchangeAdapter interface |
| `executor.py::decide()` | `strategies/fear_greed_dca.py::FearGreedDCAStrategy.evaluate()` | Extract to strategy pattern |
| `executor.py::execute_dca_buy()` | `core engine` in `FearProtocol.run_once()` | Generic execution via adapter |
| `executor.py::execute_rebalance()` | `core engine` | Same — strategy returns SELL signal |
| `executor.py::load_state()` / `save_state()` | `state/manager.py::StateManager` | Generalized, multi-exchange |
| `executor.py::get_position_summary()` | `state/manager.py` + `backtest/report.py` | Split into query + reporting |
| `signals.py::get_current_fear_greed()` | `data/fear_greed.py::FearGreedProvider.get_current()` | Clean provider class |
| `signals.py::check_signal()` | `fear_protocol/__init__.py::get_signal()` | Top-level convenience fn |
| `backtest.py::run_backtest()` | `backtest/engine.py::BacktestEngine.run()` | Full rewrite, much richer |
| `backtest.py::fetch_fear_greed_history()` | `data/historical.py` | With caching |
| `backtest.py::fetch_btc_price_history()` | `data/historical.py` | With caching |
| `tests/test_executor_hl.py` | `tests/unit/test_exchanges_hyperliquid.py` | Mostly reusable |
| `tests/conftest.py` | `tests/conftest.py` | Extend with new fixtures |

### Migration Steps (for Builder)

1. **Create repo structure** — scaffold `pyproject.toml`, all directories, `__init__.py` files
2. **Port core models** — `models.py` dataclasses, no dependencies
3. **Port math utilities** — Sharpe, Sortino, drawdown from `backtest.py`
4. **Port data providers** — `fear_greed.py`, `price.py`, `historical.py` (with caching added)
5. **Implement exchange base + mock** — needed before anything else can be tested
6. **Port strategy** — `FearGreedDCAStrategy` from `decide()` + execute functions
7. **Port HL adapter** — `HyperliquidAdapter` from `HLSpotExecutor`
8. **Port state manager** — from `load_state()`/`save_state()`
9. **Build backtest engine** — new engine using MockAdapter + historical data
10. **Build CLI** — Typer commands wrapping Python API
11. **Build agent API** — async wrapper with Pydantic schemas
12. **Write tests** — unit + integration, hit 90% coverage
13. **Write docs** — MkDocs with quickstart + API reference
14. **CI setup** — GitHub Actions workflows
15. **Update FearHarvester skill** — point executor to `fear-protocol` package

### Credential Compatibility

The existing `HL_PRIVATE_KEY` / `HL_WALLET_ADDRESS` env vars are preserved in `HyperliquidAdapter`. Users don't need to change their credentials. The `.env` file at `~/.openclaw/skills/hyperliquid/.env` is still read by default when using the HL adapter.

---

## 11. Phase Breakdown

### Phase 1: Core Foundation (Week 1)
**Goal**: Solid foundation — models, data, strategy, mock exchange, basic backtest

**Deliverables:**
- [ ] Repo scaffolding (pyproject.toml, CI skeleton, uv setup)
- [ ] `core/models.py` — all dataclasses typed
- [ ] `core/math.py` — Sharpe, Sortino, drawdown, Kelly
- [ ] `data/fear_greed.py` — alternative.me provider
- [ ] `data/price.py` — Binance price provider
- [ ] `data/historical.py` — cached historical data
- [ ] `exchanges/base.py` — AbstractExchangeAdapter
- [ ] `exchanges/mock.py` — deterministic mock
- [ ] `strategies/base.py` — AbstractStrategy
- [ ] `strategies/fear_greed_dca.py` — ported from FearHarvester
- [ ] `backtest/engine.py` — basic engine (no reporting yet)
- [ ] Unit tests for all above
- [ ] Coverage ≥ 90%

**Exit criteria**: `fear-protocol backtest --strategy fear-greed-dca` produces Sharpe ≥ 1.5 on 2020-2024 data.

### Phase 2: Exchange Adapters + CLI (Week 2)
**Goal**: Live trading capability on HL and paper mode, full CLI

**Deliverables:**
- [ ] `exchanges/hyperliquid.py` — HL adapter (from FearHarvester)
- [ ] `exchanges/paper.py` — paper trading adapter
- [ ] `exchanges/binance.py` — Binance spot adapter
- [ ] `state/manager.py` — StateManager with multi-exchange support
- [ ] `cli/` — all commands (run, backtest, signal, status)
- [ ] Config file (TOML) loading
- [ ] Integration tests for CLI
- [ ] Dry-run → paper → live mode parity

**Exit criteria**: `fear-protocol run --exchange hyperliquid --mode dry-run` produces correct output on real F&G + price data.

### Phase 3: Agent Layer + Reports + Additional Strategies (Week 3)
**Goal**: Agent-native, rich reporting, additional strategies

**Deliverables:**
- [ ] `agent/api.py` — async FearProtocolAgent
- [ ] `agent/schemas.py` — Pydantic I/O schemas
- [ ] `agent/rpc.py` — JSON-RPC interface
- [ ] `backtest/report.py` — HTML + Markdown reports
- [ ] `strategies/momentum_dca.py`
- [ ] `strategies/grid_fear.py`
- [ ] Multi-strategy backtest comparison (`--compare` flag)
- [ ] Updated `fear-harvester` skill to use fear-protocol SDK
- [ ] Full documentation (MkDocs)
- [ ] Release v0.1.0 to PyPI

**Exit criteria**: EvoClaw agent can import `FearProtocolAgent` and call `get_signal()` → structured JSON. PyPI package installable via `uv add fear-protocol`.

---

## Appendix: Key Design Decisions

### Why Typer over Click/argparse?
- Better type annotation support
- Auto-generates `--help` from docstrings
- Clean subcommand structure
- `rich` integration for beautiful terminal output

### Why Pydantic v2 for agent schemas?
- `model_validate()` for clean JSON parsing
- `.model_dump()` for clean JSON output
- Field validators for F&G range checking
- Agent-native: structured I/O is non-negotiable

### Why uv over pip/poetry?
- Per SOUL.md: "ALWAYS use `uv` for ALL Python"
- 10-100x faster than pip
- Single tool for venv + packages + scripts
- `uv run` for script execution

### Why MockAdapter for backtesting vs simulated prices?
- The backtest runs historical data through the real strategy code
- MockAdapter returns deterministic fills from the price series
- Same code path as live trading — no special backtest mode
- Catches real bugs that "simulation-only" approaches miss

### State file format (backwards compatible with FearHarvester)

The `StateManager` reads/writes the same JSON format as FearHarvester's `executor_state.json`. Existing users don't lose their positions during migration.

```json
{
  "version": 3,
  "exchange": "hyperliquid",
  "strategy": "fear-greed-dca",
  "positions": [...],
  "total_invested": 2500.0,
  "mode": "live",
  "last_action": "DCA_BUY $500 @ $95000 (F&G=14)"
}
```

---

*Plan written by Alex Chen (Planner). Next: spawn Builder to implement Phase 1.*
