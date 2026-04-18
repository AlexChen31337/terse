#!/usr/bin/env python3
import json, subprocess, datetime, os

today = datetime.datetime.now().strftime('%Y%m%d')
date_display = "Friday, April 17, 2026"
outdir = os.path.dirname(os.path.abspath(__file__))

def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return r.stdout.strip()
    except:
        return ""

# 1. Hyperliquid mids
mids_raw = run("curl -s 'https://api.hyperliquid.xyz/info' -H 'Content-Type: application/json' -d '{\"type\":\"allMids\"}'")
mids = {}
try:
    mids = json.loads(mids_raw)
except:
    pass

# 2. Fear & Greed
fng_raw = run("curl -s 'https://api.alternative.me/fng/?limit=1'")
fng_val, fng_label = "—", "—"
try:
    fng_data = json.loads(fng_raw)['data'][0]
    fng_val = fng_data['value']
    fng_label = fng_data['value_classification']
except:
    pass

# 3. CoinGecko global
global_raw = run("curl -s 'https://api.coingecko.com/api/v3/global'")
total_mcap, total_vol, btc_dom, eth_dom, mcap_chg = "—", "—", "—", "—", 0.0
try:
    gd = json.loads(global_raw)['data']
    total_mcap = "${:.2f}T".format(gd['total_market_cap']['usd']/1e12)
    total_vol = "${:.0f}B".format(gd['total_volume']['usd']/1e9)
    btc_dom = "{:.1f}%".format(gd['market_cap_percentage']['btc'])
    eth_dom = "{:.1f}%".format(gd['market_cap_percentage']['eth'])
    mcap_chg = gd['market_cap_change_percentage_24h_usd']
except:
    pass

# 4. CoinGecko prices
prices_raw = run("curl -s 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=bitcoin,ethereum,solana,dogecoin,avalanche-2,chainlink,sui,arbitrum,hyperliquid&order=market_cap_desc&sparkline=false&price_change_percentage=24h,7d'")
prices = []
try:
    coins = json.loads(prices_raw)
    for c in coins:
        sym = c['symbol'].upper()
        price = c['current_price']
        chg24 = c.get('price_change_percentage_24h', 0) or 0
        chg7d = c.get('price_change_percentage_7d_in_currency', 0) or 0
        prices.append((sym, price, chg24, chg7d))
except:
    pass

# 5. Hyperliquid funding/OI
meta_raw = run("curl -s 'https://api.hyperliquid.xyz/info' -H 'Content-Type: application/json' -d '{\"type\":\"metaAndAssetCtxs\"}'")
funding_data = []
try:
    md = json.loads(meta_raw)
    meta_u = md[0]['universe']
    ctxs = md[1]
    all_f = []
    for i, ctx in enumerate(ctxs):
        name = meta_u[i]['name']
        f = float(ctx['funding'])
        oi = float(ctx['openInterest'])
        vol = float(ctx.get('dayNtlVlm', 0))
        all_f.append((name, f*100, oi, vol))
    all_f.sort(key=lambda x: abs(x[1]), reverse=True)
    funding_data = all_f[:8]
except:
    pass

# 6. GitHub
gh_issues = run("cd /media/DATA/.openclaw/workspace && gh issue list --repo clawinfra/claw-chain --state open --limit 5 --json number,title,createdAt 2>/dev/null")
gh_prs = run("cd /media/DATA/.openclaw/workspace && gh pr list --repo clawinfra/claw-chain --state open --limit 5 --json number,title,state 2>/dev/null")
gh_evo_issues = run("cd /media/DATA/.openclaw/workspace && gh issue list --repo clawinfra/evoclaw --state open --limit 5 --json number,title 2>/dev/null")
gh_evo_prs = run("cd /media/DATA/.openclaw/workspace && gh pr list --repo clawinfra/evoclaw --state open --limit 5 --json number,title 2>/dev/null")

def parse_gh(raw):
    try:
        return json.loads(raw) if raw else []
    except:
        return []

cc_issues = parse_gh(gh_issues)
cc_prs = parse_gh(gh_prs)
ev_issues = parse_gh(gh_evo_issues)
ev_prs = parse_gh(gh_evo_prs)

def chg_fmt(v):
    c = "green" if v > 0 else ("red" if v < 0 else "")
    return '<span class="{}">{:+.1f}%</span>'.format(c, v)

def fng_color(v):
    try:
        v = int(v)
        if v <= 25: return "red"
        elif v <= 45: return "amber"
        elif v <= 55: return ""
        else: return "green"
    except:
        return ""

# Build price rows
price_rows = ""
for sym, price, c24, c7d in prices:
    if price >= 1000:
        pfmt = "${:,.0f}".format(price)
    elif price >= 1:
        pfmt = "${:,.2f}".format(price)
    else:
        pfmt = "${:,.4f}".format(price)
    price_rows += "<tr><td><strong>{}</strong></td><td>{}</td><td>{}</td><td>{}</td></tr>\n".format(sym, pfmt, chg_fmt(c24), chg_fmt(c7d))

# Build funding rows
funding_rows = ""
for name, f8h, oi, vol in funding_data:
    ann = f8h * 3 * 365
    fc = "green" if f8h > 0 else "red"
    funding_rows += '<tr><td><strong>{}</strong></td><td><span class="{}">{:.4f}%</span></td><td><span class="{}">{:.1f}%</span></td><td>${:,.0f}</td></tr>\n'.format(name, fc, f8h, fc, ann, oi)

# Prices for ideas
btc_price = next((p for s, p, _, _ in prices if s == "BTC"), 0)
eth_price = next((p for s, p, _, _ in prices if s == "ETH"), 0)
sol_price = next((p for s, p, _, _ in prices if s == "SOL"), 0)

extreme_funding = [(n, f, oi) for n, f, oi, v in funding_data if abs(f) > 0.01]
fng_int = int(fng_val) if fng_val != "—" else 50

# === IDEA 1 ===
if extreme_funding:
    top = extreme_funding[0]
    if top[1] > 0:
        idea1_title = "📈 {} Funding Arbitrage — Shorts Getting Paid".format(top[0])
        idea1_tags = '<span class="tag">Trading</span><span class="tag">Funding</span><span class="tag">Hyperliquid</span>'
        idea1_body = '<p>{} has an extreme positive funding rate of <strong>{:.4f}%/8h ({:.0f}% annualized)</strong> with ${:,.0f} open interest. Longs are paying heavily.</p>'.format(top[0], top[1], top[1]*3*365, top[2])
        idea1_body += '<p><strong>Thesis:</strong> Elevated funding signals overleveraged longs. Consider delta-neutral short on HL + spot-long on CEX, or wait for a flush. Extreme funding &gt;0.05% often precedes 5-10% corrections within 48h.</p>'
        idea1_body += '<p class="action">⚡ Action: Set alerts for {} funding normalization. If it drops &gt;50%, longs are closing — potential reversal.</p>'.format(top[0])
    else:
        idea1_title = "📉 {} Negative Funding — Contrarian Long Setup".format(top[0])
        idea1_tags = '<span class="tag">Trading</span><span class="tag">Contrarian</span><span class="tag">Hyperliquid</span>'
        idea1_body = '<p>{} has deeply negative funding at <strong>{:.4f}%/8h ({:.0f}% annualized)</strong>. Shorts are paying longs.</p>'.format(top[0], top[1], top[1]*3*365)
        idea1_body += '<p><strong>Thesis:</strong> Negative funding with {} sentiment (FNG: {}) creates a contrarian long setup. You get paid to hold while shorts bleed.</p>'.format(fng_label.lower(), fng_val)
        idea1_body += '<p class="action">⚡ Action: Scale in small longs on {} with tight stops. Funding income covers holding costs.</p>'.format(top[0])
else:
    idea1_title = "📊 Neutral Funding — Range Trading Mode"
    idea1_tags = '<span class="tag">Trading</span><span class="tag">Range</span>'
    idea1_body = '<p>Funding rates balanced. Range-bound strategies outperform in neutral environments.</p>'
    idea1_body += '<p class="action">⚡ Action: Trade the BTC range with tight risk management.</p>'

# === IDEA 2 ===
if fng_int < 30:
    idea2_title = "🛡️ ClawChain Fear Protocol — Auto-Hedge Agent Module"
    idea2_body = '<p>FNG at <strong>{} ({})</strong> — agents need automated risk management. Build a Fear Protocol module:</p>'.format(fng_val, fng_label)
    idea2_body += '<ul><li>On-chain FNG + funding oracle</li><li>Auto-reduce exposure when FNG &lt; 25</li><li>Trigger hedging on Hyperliquid via agent wallet</li><li>Publish risk state for other agents</li></ul>'
    idea2_body += '<p class="action">⚡ Action: Spec FearOracle contract. Prototype with HL API + agent-wallet signing.</p>'
elif fng_int > 70:
    idea2_title = "🚀 ClawChain Agent Marketplace — Ride the Greed Wave"
    idea2_body = '<p>FNG at <strong>{} ({})</strong> — capital flowing in. Launch the Agent Marketplace:</p>'.format(fng_val, fng_label)
    idea2_body += '<ul><li>Agents list strategies as rentable services</li><li>Revenue-sharing: agent 80%, protocol 20%</li><li>On-chain performance verification</li><li>CLAW token staking as performance bond</li></ul>'
    idea2_body += '<p class="action">⚡ Action: Design AgentMarketplace contract. 3 internal agents as launch partners.</p>'
else:
    idea2_title = "🔗 EvoClaw Skill Composition Engine — Agent-to-Agent Delegation"
    idea2_body = '<p>Market neutral (FNG: {}) — build infrastructure. Skill Composition Engine:</p>'.format(fng_val)
    idea2_body += '<ul><li>Dynamic skill discovery and composition between agents</li><li>Typed skill interfaces on ClawChain registry</li><li>Auto fee routing — caller pays provider in CLAW</li><li>Reputation scores based on reliability + speed</li></ul>'
    idea2_body += '<p><strong>Why now:</strong> {} open issues across ClawChain + EvoClaw. Skill composition lets us parallelize and dog-food our infra.</p>'.format(len(cc_issues) + len(ev_issues))
    idea2_body += '<p class="action">⚡ Action: Define SkillInterface schema. Implement discovery via ClawChain name service.</p>'
idea2_tags = '<span class="tag">Product</span><span class="tag">ClawChain</span><span class="tag">EvoClaw</span>'

# === IDEA 3 ===
mcap_dir = "up" if mcap_chg > 0 else "down"
idea3_title = "📣 AI Agent Trading Transparency Report — Content Play"
idea3_tags = '<span class="tag">Growth</span><span class="tag">Content</span><span class="tag">Twitter</span>'
idea3_body = '<p>Market {} {:.1f}% 24h. People want to see <em>how AI agents actually trade</em>. Weekly transparency thread on @AlexChen31337:</p>'.format(mcap_dir, abs(mcap_chg))
idea3_body += '<ul><li>Real P&amp;L from agent positions (anonymized)</li><li>Decision logic breakdown — funding, sentiment, on-chain</li><li>Agent vs. human performance comparison</li><li>ClawChain as the infrastructure powering it</li></ul>'
idea3_body += '<p class="action">⚡ Action: Set up P&amp;L tracking. Draft first thread for Sunday. #AIAgents #DeFi #ClawChain</p>'

# === Infra section ===
infra_html = ""
if cc_issues or cc_prs:
    infra_html += "<h3 style='color:#fff;font-size:14px;margin:8px 0;'>claw-chain</h3>"
    if cc_prs:
        infra_html += "<p style='color:#aaa;font-size:13px;'>Open PRs:</p><ul style='color:#aaa;font-size:13px;'>"
        for pr in cc_prs[:3]:
            infra_html += "<li>#{}: {}</li>".format(pr['number'], pr['title'])
        infra_html += "</ul>"
    if cc_issues:
        infra_html += "<p style='color:#aaa;font-size:13px;'>{} open issues (latest: #{} {})</p>".format(len(cc_issues), cc_issues[0]['number'], cc_issues[0]['title'][:60])
    else:
        infra_html += "<p style='color:#aaa;font-size:13px;'>No open issues ✅</p>"

if ev_issues or ev_prs:
    infra_html += "<h3 style='color:#fff;font-size:14px;margin:8px 0;'>evoclaw</h3>"
    if ev_prs:
        infra_html += "<p style='color:#aaa;font-size:13px;'>Open PRs:</p><ul style='color:#aaa;font-size:13px;'>"
        for pr in ev_prs[:3]:
            infra_html += "<li>#{}: {}</li>".format(pr['number'], pr['title'])
        infra_html += "</ul>"
    if ev_issues:
        infra_html += "<p style='color:#aaa;font-size:13px;'>{} open issues (latest: #{} {})</p>".format(len(ev_issues), ev_issues[0]['number'], ev_issues[0]['title'][:60])
    else:
        infra_html += "<p style='color:#aaa;font-size:13px;'>No open issues ✅</p>"

if not infra_html:
    infra_html = "<p style='color:#aaa;font-size:13px;'>All clear across ClawInfra repos. 🧘</p>"

mcap_cls = "green" if mcap_chg > 0 else "red"

# === ASSEMBLE ===
html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0a; color: #e0e0e0; margin: 0; padding: 0; }}
  .container {{ max-width: 640px; margin: 0 auto; padding: 20px; }}
  .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); border-radius: 12px; padding: 24px; margin-bottom: 20px; border: 1px solid #1e3a5f; }}
  .header h1 {{ margin: 0; font-size: 24px; color: #00d4ff; }}
  .header .date {{ color: #8892b0; font-size: 14px; margin-top: 4px; }}
  .section {{ background: #111; border-radius: 10px; padding: 20px; margin-bottom: 16px; border: 1px solid #222; }}
  .section h2 {{ color: #00d4ff; font-size: 16px; margin: 0 0 12px 0; text-transform: uppercase; letter-spacing: 1px; }}
  .metrics {{ text-align: center; margin-bottom: 12px; }}
  .metric {{ display: inline-block; background: #1a1a2e; border-radius: 8px; padding: 10px 14px; margin: 4px; border: 1px solid #2a2a4e; min-width: 100px; }}
  .metric .label {{ font-size: 11px; color: #666; text-transform: uppercase; }}
  .metric .value {{ font-size: 18px; font-weight: 700; color: #fff; }}
  .green {{ color: #00e676; }}
  .red {{ color: #ff5252; }}
  .amber {{ color: #ffab40; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; color: #666; font-size: 11px; text-transform: uppercase; padding: 6px 8px; border-bottom: 1px solid #222; }}
  td {{ padding: 8px; border-bottom: 1px solid #1a1a1a; }}
  .idea-card {{ background: linear-gradient(135deg, #1a1a2e, #111); border-radius: 10px; padding: 18px; margin-bottom: 12px; border-left: 3px solid #00d4ff; }}
  .idea-card h3 {{ color: #fff; margin: 0 0 8px 0; font-size: 15px; }}
  .idea-card .tag {{ display: inline-block; background: #00d4ff22; color: #00d4ff; font-size: 11px; padding: 2px 8px; border-radius: 4px; margin-right: 6px; margin-bottom: 6px; }}
  .idea-card p {{ color: #aaa; font-size: 13px; line-height: 1.6; margin: 8px 0; }}
  .idea-card ul {{ color: #aaa; font-size: 13px; line-height: 1.8; }}
  .idea-card .action {{ color: #00e676; font-size: 12px; font-weight: 600; }}
  .footer {{ text-align: center; color: #444; font-size: 11px; padding: 20px; }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>🧠 Alex Daily Ideas</h1>
  <div class="date">{date} &middot; Sydney 8:00 AM</div>
</div>

<div class="section">
  <h2>📊 Market Pulse</h2>
  <div class="metrics">
    <div class="metric">
      <div class="label">Fear &amp; Greed</div>
      <div class="value"><span class="{fng_cls}" style="font-size:32px;font-weight:800;">{fng}</span><br><span style="font-size:11px;color:#888;">{fng_lbl}</span></div>
    </div>
    <div class="metric">
      <div class="label">Total Market Cap</div>
      <div class="value">{mcap}</div>
      <div style="font-size:11px;" class="{mcap_cls}">{mcap_chg} 24h</div>
    </div>
    <div class="metric">
      <div class="label">24h Volume</div>
      <div class="value">{vol}</div>
    </div>
    <div class="metric">
      <div class="label">BTC Dom</div>
      <div class="value">{btcdom}</div>
    </div>
  </div>
</div>

<div class="section">
  <h2>💰 Key Prices</h2>
  <table>
    <tr><th>Asset</th><th>Price</th><th>24h</th><th>7d</th></tr>
    {prices}
  </table>
</div>

<div class="section">
  <h2>🔥 Hyperliquid Funding Signals</h2>
  <table>
    <tr><th>Asset</th><th>Funding (8h)</th><th>Annualized</th><th>Open Interest</th></tr>
    {funding}
  </table>
  <p style="color:#555;font-size:11px;margin-top:8px;">Sorted by absolute funding rate. Extreme rates signal crowded positioning.</p>
</div>

<div class="section">
  <h2>💡 Today's Ideas</h2>
  <div class="idea-card">
    <h3>{i1_title}</h3>
    {i1_tags}
    {i1_body}
  </div>
  <div class="idea-card">
    <h3>{i2_title}</h3>
    {i2_tags}
    {i2_body}
  </div>
  <div class="idea-card">
    <h3>{i3_title}</h3>
    {i3_tags}
    {i3_body}
  </div>
</div>

<div class="section">
  <h2>🔧 ClawInfra Status</h2>
  {infra}
</div>

<div class="footer">
  Generated by Alex Chen &middot; OpenClaw Agent Infrastructure<br>
  <em>"Your decision counts, you own it."</em>
</div>

</div>
</body>
</html>""".format(
    date=date_display,
    fng_cls=fng_color(fng_val), fng=fng_val, fng_lbl=fng_label,
    mcap=total_mcap, mcap_cls=mcap_cls, mcap_chg="{:+.1f}%".format(mcap_chg),
    vol=total_vol, btcdom=btc_dom,
    prices=price_rows, funding=funding_rows,
    i1_title=idea1_title, i1_tags=idea1_tags, i1_body=idea1_body,
    i2_title=idea2_title, i2_tags=idea2_tags, i2_body=idea2_body,
    i3_title=idea3_title, i3_tags=idea3_tags, i3_body=idea3_body,
    infra=infra_html
)

outpath = os.path.join(outdir, "daily_ideas_{}.html".format(today))
with open(outpath, 'w') as f:
    f.write(html)
print("OK: {} ({} bytes)".format(outpath, len(html)))
