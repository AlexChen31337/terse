# Polymarket Research - How to Play

## What is Polymarket?

**World's largest prediction market** - bet on future events, profit from knowledge

### Core Mechanics

**Binary Outcomes:**
- Buy/sell shares representing YES or NO outcomes
- Prices range from $0.00 to $1.00 USDC
- Each YES + NO pair fully collateralized by $1.00 USDC
- Winning shares pay out $1.00 each

**Example:**
- Market: "Will Bitcoin hit $90K in February?"
- YES shares trading at $0.19 (19% probability)
- If you buy YES at $0.19 and BTC hits $90K → profit $0.81 per share
- If BTC doesn't hit $90K → shares worth $0

### Key Differences from Sportsbooks

✅ **No house edge** - Trade peer-to-peer with other users
✅ **Can exit early** - Sell shares before event resolves
✅ **No bet limits** - Can't be banned for winning
✅ **Market-driven odds** - Prices reflect collective intelligence

## Market Categories (from homepage)

### High-Volume Markets

1. **Crypto (15-min intervals)**
   - BTC Up or Down in 15 minutes
   - Fast-moving, high-frequency trading
   - Referenced by @sharbel (92% win rate bot)

2. **Sports**
   - NFL, NBA, League of Legends
   - $2M-$10M volume per game

3. **Politics**
   - Fed decisions ($57M vol)
   - Government shutdowns ($172K vol)
   - International events (Iran, Ukraine)

4. **Finance**
   - Bitcoin price predictions ($15M vol)
   - S&P 500 daily movements ($151K vol)
   - Gold price ranges ($3M vol)

5. **Entertainment**
   - Oscars ($12M vol)
   - SpaceX IPO ($386K vol)

## How to Trade

### Basic Strategy

1. **Find mispriced markets**
   - Market says 18% chance
   - Your research says 30% chance
   - Buy YES at $0.18, expected value = profit

2. **Exit strategies**
   - Hold until resolution (max profit)
   - Sell early to lock in gains
   - Cut losses if new information changes odds

3. **Risk management**
   - Each share max loss = purchase price
   - Max gain = $1.00 - purchase price
   - Can diversify across multiple markets

### Profitable Approaches

**Information edge:**
- Know more than the market (domain expertise)
- React faster to breaking news
- Aggregate multiple data sources

**Statistical edge:**
- Historical patterns
- Market inefficiencies
- Arbitrage opportunities

**Algorithmic edge:**
- Automated trading bots
- 15-minute crypto markets (like @sharbel)
- Pattern recognition at scale

## Technical Infrastructure

### Requirements

1. **Wallet** - MetaMask or similar (Polygon network)
2. **USDC** - Deposit USDC to trade
3. **API Access** - For automated trading (docs.polymarket.com/#api)

### API Capabilities

- Get market data
- Place limit orders
- Market orders
- Check positions
- Get historical data

## Agent Trading Opportunities

### Why Polymarket is Perfect for Agents

✅ **15-minute markets** - Fast iteration, quick feedback
✅ **Clear binary outcomes** - No ambiguity (YES/NO)
✅ **Liquid markets** - Can enter/exit easily
✅ **Public data** - All prices/volumes visible
✅ **API access** - Fully automatable

### Proven Success

**@sharbel's bot:**
- Started with $100
- Lost $20 learning/iterating
- Now at 92% win rate
- Trading 15-min crypto markets
- Covers Claude subscription costs

### ClawChain Relevance

This is a PERFECT use case for ClawChain!

**Problems:**
- Bot's 92% win rate isn't verifiable on-chain
- Can't rent bot access to other agents easily
- Gas fees on Ethereum/Polygon eat into profits
- No reputation system for proven strategies

**ClawChain Solutions:**
- On-chain performance tracking (verifiable 92%)
- Service marketplace (rent bot access)
- Near-zero gas fees (micro-transactions work)
- Reputation-weighted strategy pricing

## Getting Started (Step-by-Step)

1. **Setup Wallet**
   - Install MetaMask
   - Connect to Polygon network
   - Get some MATIC for gas fees

2. **Fund Account**
   - Bridge USDC to Polygon
   - Connect wallet to polymarket.com
   - Deposit USDC

3. **First Trade (Manual)**
   - Browse markets
   - Find one you understand
   - Place small test trade ($5-10)
   - Watch it resolve

4. **API Trading (Advanced)**
   - Get API key from Polymarket
   - Use py-clob library (Python)
   - Start with read-only (fetch markets)
   - Build strategy logic
   - Test with small amounts
   - Scale up gradually

## Risk Factors

❌ **Market resolution disputes** - Who decides outcome?
❌ **Liquidity in small markets** - Can't always exit
❌ **Information disadvantages** - Insiders may know more
❌ **Bot competition** - Other algos trading same markets
❌ **Regulatory risk** - Prediction markets legal gray area

## Resources

- Homepage: https://polymarket.com
- Docs: https://docs.polymarket.com
- API: docs.polymarket.com/#api
- Python library: py-clob (github.com/Polymarket/py-clob)

## Next Steps for Building

1. **Research py-clob library** - Python API client
2. **Analyze 15-min crypto markets** - What @sharbel trades
3. **Build simple bot** - Start with paper trading
4. **Test strategies** - Win rate analysis
5. **Scale gradually** - Prove profitability first

**Timeline:** Could build working bot in 1-2 days
**Capital needed:** $100-500 for initial testing
**Expected results:** Learn for 1-2 weeks, then potentially profitable

---

**Key Insight:** Polymarket is EXACTLY the kind of agent economy ClawChain enables. Agents making money autonomously, needing infrastructure for reputation, marketplaces, and low-fee transactions.

**Status:** Research complete, ready to build if desired
**Next:** Could create a simple Polymarket monitoring/trading script
