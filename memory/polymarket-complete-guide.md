# Polymarket Complete Guide - Feb 6, 2026

## 🎯 Overview

**Polymarket** is the world's largest decentralized prediction market platform where users trade on real-world event outcomes. Market prices = probabilities.

**Key Insight:** Polymarket is NOT a bookie. All trades are peer-to-peer. Users set prices, not the platform.

---

## 📚 Core Concepts (From Learning Docs)

### How Prediction Markets Work

**Market Price = Probability**
- $0.20 shares = 20% chance of event happening
- $0.50 shares = 50% chance (coin flip)
- $0.99 shares = 99% chance (very likely)

**Winning Payout:**
- Each winning share = $1.00 USDC
- Buy at $0.20, event happens → $0.80 profit per share

**Trading Flexibility:**
- Buy/sell anytime before event concludes
- Prices update in real-time based on supply/demand
- Can exit positions early (don't need to hold to settlement)

### Why Prediction Markets Are Accurate

**"Put Your Money Where Your Mouth Is"**
- Financial incentive = truthful predictions
- Collective wisdom > individual bias
- Real-time aggregation of all available information
- No media/political slant (pure economics)

**Historically more accurate than:**
- Traditional polls
- Expert predictions
- Media narratives

---

## 💰 Price Calculation

### Initial Market Price
1. Market starts with **zero shares** (no pre-set odds)
2. Market makers place limit orders
3. When YES + NO bids = $1.00 → **match** → 1 YES + 1 NO shares created

**Example:**
- Buyer A: Limit order $0.60 for YES
- Buyer B: Limit order $0.40 for NO
- **Match!** Initial price = $0.60 (60% probability)

### Current Market Price
**Displayed price = Midpoint of bid-ask spread**
- Exception: If spread > $0.10 → use last traded price

**Example:**
- Bid: $0.34 (highest buyers will pay)
- Ask: $0.40 (lowest sellers will accept)
- **Displayed: $0.37** (37% probability)

**⚠️ Important:** You can't buy at displayed price if there's a spread!
- To buy immediately: Pay the **ask** price ($0.40 in example)
- To sell immediately: Accept the **bid** price ($0.34 in example)

---

## 📖 Order Book Basics

### Structure
**GREEN SIDE (Bids):** Buyers waiting to purchase
**RED SIDE (Asks):** Sellers waiting to sell

**Spread:** Gap between highest bid and lowest ask
- Tight spread (e.g., 0.3¢) = liquid market
- Wide spread (e.g., 10¢+) = illiquid market

### Order Types

**1. Market Orders**
- Executes instantly at current price
- Takes liquidity from the book
- Best for: Immediate entry/exit

**2. Limit Orders**
- Only executes at your specified price
- Adds liquidity to the book
- Can partially fill over time
- Optional: Set expiration date

**⚠️ Sports Market Rule:** All open limit orders auto-cancel when game starts

**⚠️ Sports Delay:** 3-second delay on marketable orders (anti-manipulation)

---

## 💸 Fees & Rebates

### Fee-Free Markets (99% of Polymarket)
- ✅ No trading fees
- ✅ No deposit/withdrawal fees (Polymarket side)
- ⚠️ Intermediaries (Coinbase, MoonPay) may charge their own fees

### Markets With Fees (15-min Crypto Only)
**Taker Fees:** Charged when taking liquidity (market orders)
**Fee Formula:** `fee = shares × price × 0.25 × (price × (1 - price))²`

**Fee Curve:**
- Highest at **50% probability** → **1.56%** effective rate
- Lowest at extremes (1% or 99%) → **~0%**
- Fees ≥ 0.0001 USDC (smaller rounds to zero)

**Example (100 shares):**
| Price | Trade Value | Fee (USDC) | Effective Rate |
|-------|-------------|------------|----------------|
| $0.50 | $50         | $0.78      | 1.56% (MAX)    |
| $0.30 | $30         | $0.33      | 1.10%          |
| $0.70 | $70         | $0.77      | 1.10%          |
| $0.90 | $90         | $0.18      | 0.20%          |
| $0.99 | $99         | $0.00      | 0.00%          |

### Maker Rebates Program (15-min Crypto Only)
**Who Earns:**
- Market makers who provide **active liquidity** (orders that get filled)

**Payout:**
- **Daily USDC rebates**
- Proportional to liquidity provided
- Funded by taker fees collected

**Current Schedule (as of Feb 2026):**
| Period           | Maker Rebate | Distribution Method |
|------------------|--------------|---------------------|
| Jan 9-11, 2026   | 100%         | Volume-weighted     |
| Jan 12-18, 2026  | 20%          | Volume-weighted     |
| Jan 19+          | 20%          | Fee-curve weighted  |

**Rebate Formula:**
```
fee_equivalent = shares × price × 0.25 × (price × (1 - price))²
rebate = (your_fee_equivalent / total_fee_equivalent) × rebate_pool
```

**Strategy Insight:** Market making in 15-min crypto markets = earn rebates + potential arbitrage

---

## 🛠️ Polymarket SDK (Installed!)

**Location:** `/home/bowen/clawd/skills/polymarket/`

### SDK Services

| Service | Description | Auth Required |
|---------|-------------|---------------|
| `client.markets` | Market discovery, events, metadata | ❌ Public |
| `client.orderbook` | Order book, prices, spreads | ❌ Public |
| `client.positions` | User positions, analytics | ❌ Public |
| `client.bridge` | Deposits, withdrawals | ❌ Public |
| `client.orders` | Place/cancel orders | ✅ L2 Auth |
| `client.trades` | Trade history | ✅ L2 Auth |
| `client.account` | Balance, allowance | ✅ L2 Auth |

### Quick Usage

**Public (No Auth):**
```python
from polymarket import PolymarketClient

async with PolymarketClient() as client:
    # Search markets
    results = await client.markets.search(query="election", limit_per_type=10)
    
    # Get prices
    spread = await client.orderbook.get_spread(token_id)
    print(f"Bid: {spread.bid}, Ask: {spread.ask}")
    
    # Check positions (any wallet)
    positions = await client.positions.get_positions(user="0x...")
```

**Authenticated Trading:**
```python
from polymarket import PolymarketClient, Credentials

credentials = Credentials(
    api_key="your-api-key",
    secret="your-secret",
    passphrase="your-passphrase",
)

async with PolymarketClient(
    private_key="0x...",
    credentials=credentials,
) as client:
    # Build order
    order = client.order_builder.buy(token_id, price=0.55, size=100).build()
    
    # Place order
    result = await client.orders.place_order(order)
```

**Stream Real-Time Data:**
```python
async with client.market_stream as stream:
    async for event in stream.subscribe([token_id]):
        if isinstance(event, WsPriceChangeMessage):
            print(f"Price: {event.price_changes[0].price}")
```

### Key Concepts

**Token ID vs Condition ID:**
- **Token ID:** Specific outcome (YES or NO for a market)
- **Condition ID:** Market identifier (contains both YES/NO tokens)

**Order Types:**
- **GTC:** Good-Til-Cancelled (default)
- **GTD:** Good-Til-Date (expires at specified time)
- **FOK:** Fill-Or-Kill (all or nothing)
- **FAK:** Fill-And-Kill (partial fills OK, rest cancelled)

**Signature Types:**
- **EOA (0):** MetaMask, hardware wallets
- **POLY_PROXY (1):** Magic Link users
- **GNOSIS_SAFE (2):** Most common (default)

---

## 🎯 Strategy Synthesis (From Biteye Analysis)

### Tier 1: High-Value Strategies

**1. Contrarian Sentiment Arbitrage** ($1.45M proven)
- Target: Geopolitical panic markets (wars, government shutdowns)
- Entry: When YES > 70-95¢ due to fear
- Position: Buy NO (bet nothing happens)
- Exit: When panic subsides or deadline approaches
- **Why it works:** Humans overestimate short-term extreme events

**2. Information Gap Trading** ($1.09M proven)
- Target: Pre-announcement windows
- Signals: New wallets, large bets, leaked info
- Entry: Before consensus forms
- Exit: When market price catches up
- **Polymarket-specific edge:** Monitor on-chain activity for insider signals

**3. Volatility Arbitrage** (5-10% returns)
- Target: 15-min crypto markets during panic
- Method: Buy mispriced side → hedge opposite when stable
- Ensure: Total cost < $0.95
- **Polymarket bonus:** Maker rebates on 15-min markets!

### Tier 2: Execution Tactics

**4. Time-Based Certainty**
- Target: Physical impossibility bets
- Examples: Sports with unrecoverable leads, elections with votes exhausted
- Entry: When outcome 99.9% certain
- Exit: Right before settlement (avoid disputes)
- **Profit:** 1-5% micro-edges

**5. Market Making (15-min Crypto)**
- Method: Provide liquidity on both sides
- Capture: Bid-ask spread
- Earn: Daily USDC maker rebates
- **Current rebate:** 20% of taker fees
- **Best in:** High-volatility, high-volume markets

### Critical Risk Rules

**❌ Never:**
- Hold past 95% confidence (settlement risk)
- Bet on 99¢ markets (no edge)
- Ignore resolution criteria ambiguity
- Chase "safe" bets without price edge

**✅ Always:**
- Read resolution sources obsessively
- Calculate true probability vs market price
- Exit into euphoria (don't wait for $1.00)
- Default to NO bias (79.6% of markets resolve No)

---

## 🚀 Immediate Action Plan

### Phase 1: Setup & Learning (Today)
1. ✅ Install Polymarket SDK (DONE)
2. Read SDK reference docs in `skills/polymarket/references/`
3. Run example scripts:
   ```bash
   cd /home/bowen/clawd/skills/polymarket/assets/examples
   python market_scanner.py  # Discover markets
   ```

### Phase 2: Research Mode (Next 24h)
1. **Market Discovery:**
   - Find panic-driven geopolitical markets
   - Identify 15-min crypto markets for rebates
   - Look for pre-announcement opportunities

2. **Order Book Analysis:**
   - Check spreads (tight = liquid, wide = opportunity)
   - Monitor large orders (whale activity)
   - Track price volatility patterns

3. **Position Tracking:**
   - Find successful traders on-chain
   - Analyze their entry/exit patterns
   - Copy strategies (legally via public data)

### Phase 3: Paper Trading (Week 1)
1. Simulate strategies without real capital
2. Track hypothetical P&L
3. Refine entry/exit timing
4. Build automated monitoring tools

### Phase 4: Live Trading (When Ready)
**Starting capital:** TBD (discuss with Bowen)
**Risk per trade:** Max 1-2% of capital
**Focus:** Contrarian sentiment + maker rebates

---

## 📊 Key Metrics to Monitor

**Market Health:**
- Bid-ask spread (tighter = better liquidity)
- Order book depth (total USDC at each level)
- Volume (24h trading activity)

**Price Action:**
- Volatility (price swings create arb opportunities)
- Momentum (rapid price changes = panic/euphoria)
- Time to settlement (urgency increases closer to event)

**Competitive Intelligence:**
- New wallet activity (potential insider trades)
- Large orders (whale positioning)
- Cross-market correlations (related events)

---

## 🔗 Resources

**Polymarket SDK:**
- Location: `/home/bowen/clawd/skills/polymarket/`
- Examples: `assets/examples/`
- References: `references/`

**API Docs:**
- Learning: https://github.com/bowen31337/polymarket-api-docs/tree/main/docs/polymarket-learn
- Full index: https://docs.polymarket.com/llms.txt

**Analysis:**
- Biteye Guide: `/home/bowen/clawd/memory/polymarket-biteye-full-article.md`
- This Guide: `/home/bowen/clawd/memory/polymarket-complete-guide.md`

---

## 🎓 Next Steps

**Questions for Bowen:**
1. Starting capital allocation?
2. Risk tolerance per trade?
3. Focus: Maker rebates, arbitrage, or contrarian?
4. Timeline: Paper trade duration before live?
5. Should I build automated monitoring bots?

**My Preparation:**
1. Study SDK reference docs
2. Run all example scripts
3. Build market scanner for opportunities
4. Create position tracking dashboard
5. Develop strategy backtesting framework

---

**Ready to start as soon as you give the go-ahead!** 🚀
