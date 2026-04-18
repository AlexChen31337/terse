# Hyperliquid Agent Skill - Learned

**Date:** 2026-02-05  
**Source:** https://github.com/bowen31337/hyperliquid-agent-skills  
**Status:** ✅ Installed and ready

---

## What is Hyperliquid?

**Hyperliquid DEX** - Decentralized exchange for perpetual futures and spot trading

**Key Features:**
- Perpetual futures (like BTC, ETH perps)
- Spot trading
- Leverage trading
- Real-time WebSocket feeds
- EIP-712 signed transactions

---

## Skill Capabilities

### 1. Market Data (No Auth Required)
- **Get prices**: All mids, order books, candles
- **Query positions**: Check account state
- **Get fills**: Historical trade data
- **Open orders**: Active orders for any address

### 2. Trading (Requires Private Key)
- **Place orders**: Limit, market, trigger orders
- **Cancel orders**: Single or all orders
- **Stop-loss/Take-profit**: Trigger orders
- **Leverage control**: Adjust position leverage

### 3. Real-Time Monitoring
- **WebSocket streams**: Live price feeds
- **User events**: Order fills, position updates
- **Order book**: Real-time L2 data

---

## API Structure

**Two Main Endpoints:**

| Endpoint | Purpose | Auth |
|----------|---------|------|
| `/info` | Queries (prices, positions, orders) | ❌ No |
| `/exchange` | Trading operations | ✅ Yes (EIP-712) |

**Base URLs:**
- Mainnet: `https://api.hyperliquid.xyz`
- Testnet: `https://api.hyperliquid-testnet.xyz`

---

## Quick Examples

### Get BTC Price
```python
import httpx

response = httpx.post(
    "https://api.hyperliquid.xyz/info",
    json={"type": "allMids"}
)
prices = response.json()
print(f"BTC: ${prices['BTC']}")
```

### Place Limit Order
```python
from scripts.client import HyperliquidClient

client = HyperliquidClient(private_key="0x...")
result = client.place_limit_order(
    coin="BTC",
    is_buy=True,
    price="50000.0",
    size="0.1",
    tif="Gtc"  # Good-til-canceled
)
```

### Monitor Prices Real-Time
```python
import asyncio
from scripts.websocket_client import HyperliquidWebSocket

async def main():
    ws = HyperliquidWebSocket()
    
    async def on_price(data):
        btc = data['mids'].get('BTC', 'N/A')
        print(f"BTC: ${btc}")
    
    await ws.subscribe_all_mids(on_price)
    await ws.run()

asyncio.run(main())
```

---

## Key Concepts

### Asset Indices
- Orders use numeric indices, not symbols
- BTC = index 0, ETH = index 1, etc.
- Get mapping from `meta` endpoint
- Client handles this automatically

### Spot Pairs
- Referenced with `@index` notation
- Example: `@107` for HYPE/USDC
- Query `spotMeta` for indices

### Time-in-Force Options
- `Gtc` - Good-til-canceled (default)
- `Ioc` - Immediate-or-cancel
- `Alo` - Post-only (maker)

### Order Signing
- All `/exchange` operations require EIP-712 signatures
- Client handles automatically with private key
- Manual signing available via `signing.py`

---

## Helper Scripts

Located in `~/.openclaw/skills/hyperliquid/scripts/`:

| Script | Purpose |
|--------|---------|
| `client.py` | REST API client (queries + trading) |
| `signing.py` | EIP-712 request signing |
| `websocket_client.py` | Async WebSocket client |

**Dependencies:**
```bash
pip install httpx websockets eth-account
```

---

## Reference Documentation

Included in skill:
- `references/trading.md` - Order placement, cancellation, leverage
- `references/market-data.md` - Prices, order books, candles
- `references/websocket.md` - Real-time subscriptions

---

## Use Cases

### For Trading Automation
- Build autonomous trading bots
- Real-time price monitoring
- Automated stop-loss/take-profit
- Position management

### For Market Analysis
- Track price movements
- Order book depth analysis
- Historical fill data
- Account performance tracking

---

## Integration with OpenClaw

**Installed location:** `~/.openclaw/skills/hyperliquid/`

**Trigger phrases:**
- "Hyperliquid"
- "HL"
- "perpetuals trading"
- "Hyperliquid API"

**Status:** ✓ ready (openclaw-managed)

---

## Security Notes

**Private Key:**
- Required for trading operations only
- Market data queries don't need auth
- Store in environment variable, NOT in code
- Use testnet for development

**EIP-712 Signing:**
- All trading operations signed
- Prevents replay attacks
- Nonce-based (timestamp)

---

## Next Steps

1. ✅ Skill installed and learned
2. 📋 Consider testing on testnet
3. 💡 Available for trading automation when needed

---

## Key Takeaways

**Well-designed skill:**
- Framework-agnostic (works with any agent)
- Clear SKILL.md structure
- Ready-to-run scripts
- Comprehensive reference docs
- Production-ready code

**Perfect example** of how agent skills should be structured. This is the quality standard we should aim for with ClawChain skills!

---

**Learned:** ✅  
**Ready to use:** ✅  
**Can help with:** Hyperliquid trading, market data, bot development
