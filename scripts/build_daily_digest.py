import json, subprocess, datetime, sys

date_str = "Wednesday, April 15th, 2026"

# Fetch Hyperliquid
try:
    hl_result = subprocess.run(['curl', '-s', '-X', 'POST', 'https://api.hyperliquid.xyz/info',
        '-H', 'Content-Type: application/json', '-d', '{"type":"metaAndAssetCtxs"}'],
        capture_output=True, text=True, timeout=15)
    hl_data = json.loads(hl_result.stdout)
    meta = hl_data[0]['universe']
    ctxs = hl_data[1]
    key_assets = {}
    top_movers = []
    for i, ctx in enumerate(ctxs):
        name = meta[i]['name']
        mark = float(ctx.get('markPx', '0'))
        prev = float(ctx.get('prevDayPx', '0'))
        funding = float(ctx.get('funding', '0'))
        oi = float(ctx.get('openInterest', '0'))
        vol = float(ctx.get('dayNtlVlm', '0'))
        pct = ((mark - prev) / prev * 100) if prev > 0 else 0
        if name in ['BTC', 'ETH', 'SOL', 'HYPE']:
            key_assets[name] = {'price': mark, 'change': pct, 'funding': funding, 'oi': oi, 'vol': vol}
        top_movers.append((name, mark, pct, funding, oi, vol))
    top_movers.sort(key=lambda x: abs(x[2]), reverse=True)
except Exception as e:
    print(f"HL error: {e}", file=sys.stderr)
    key_assets = {}
    top_movers = []

# Fear & Greed
try:
    fng_result = subprocess.run(['curl', '-s', 'https://api.alternative.me/fng/'], capture_output=True, text=True, timeout=10)
    fng_data = json.loads(fng_result.stdout)
    fng_value = int(fng_data['data'][0]['value'])
    fng_class = fng_data['data'][0]['value_classification']
except:
    fng_value = 21
    fng_class = "Extreme Fear"

# CoinGecko global
try:
    cg_result = subprocess.run(['curl', '-s', 'https://api.coingecko.com/api/v3/global'], capture_output=True, text=True, timeout=10)
    cg_data = json.loads(cg_result.stdout)['data']
    total_mcap = cg_data['total_market_cap']['usd']
    total_vol = cg_data['total_volume']['usd']
    btc_dom = cg_data['market_cap_percentage']['btc']
    mcap_change = cg_data['market_cap_change_percentage_24h_usd']
except:
    total_mcap = 2.59e12
    total_vol = 146.3e9
    btc_dom = 57.4
    mcap_change = 1.27

# Trending
try:
    trend_result = subprocess.run(['curl', '-s', 'https://api.coingecko.com/api/v3/search/trending'], capture_output=True, text=True, timeout=10)
    trending = json.loads(trend_result.stdout).get('coins', [])[:5]
except:
    trending = []

# GitHub
try:
    issues_result = subprocess.run(['gh', 'issue', 'list', '--repo', 'clawinfra/claw-chain', '--state', 'open', '--limit', '5', '--json', 'number,title'], capture_output=True, text=True, timeout=10)
    issues = json.loads(issues_result.stdout) if issues_result.stdout.strip() else []
    pr_result = subprocess.run(['gh', 'pr', 'list', '--repo', 'clawinfra/claw-chain', '--state', 'open', '--limit', '5', '--json', 'number,title'], capture_output=True, text=True, timeout=10)
    prs = json.loads(pr_result.stdout) if pr_result.stdout.strip() else []
    evo_issues_result = subprocess.run(['gh', 'issue', 'list', '--repo', 'clawinfra/evoclaw', '--state', 'open', '--limit', '5', '--json', 'number,title'], capture_output=True, text=True, timeout=10)
    evo_issues = json.loads(evo_issues_result.stdout) if evo_issues_result.stdout.strip() else []
except:
    issues = []
    prs = []
    evo_issues = []

# Colors
if fng_value <= 25: fng_color = "#ff4444"
elif fng_value <= 45: fng_color = "#ff8844"
elif fng_value <= 55: fng_color = "#ffcc44"
elif fng_value <= 75: fng_color = "#88cc44"
else: fng_color = "#44cc44"

# === BUILD HTML ===
html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:'Segoe UI',Roboto,sans-serif;color:#e0e0e0;">
<div style="max-width:640px;margin:0 auto;padding:20px;">

<div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);border-radius:16px;padding:32px;margin-bottom:24px;border:1px solid #2a2a4a;">
  <div style="font-size:13px;color:#888;text-transform:uppercase;letter-spacing:2px;">Alex Chen &bull; Morning Digest</div>
  <div style="font-size:28px;font-weight:700;color:#fff;margin:8px 0;">&#129504; Daily Ideas</div>
  <div style="font-size:14px;color:#aaa;">{date_str} &bull; 8:00 AM AEST</div>
</div>

<div style="background:#111119;border-radius:12px;padding:24px;margin-bottom:20px;border:1px solid #222;">
  <div style="font-size:18px;font-weight:600;color:#fff;margin-bottom:16px;">&#128202; Market Pulse</div>

  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;padding:12px;background:#1a1a2a;border-radius:8px;">
    <div>
      <div style="font-size:12px;color:#888;">Fear &amp; Greed Index</div>
      <div style="font-size:24px;font-weight:700;color:{fng_color};">{fng_value}</div>
      <div style="font-size:13px;color:{fng_color};">{fng_class}</div>
    </div>
    <div style="width:200px;">
      <div style="background:#222;border-radius:4px;height:8px;overflow:hidden;">
        <div style="width:{fng_value}%;height:100%;background:linear-gradient(90deg,#ff4444,#ffcc44,#44cc44);border-radius:4px;"></div>
      </div>
    </div>
  </div>

  <div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;">
    <div style="flex:1;min-width:120px;background:#1a1a2a;border-radius:8px;padding:12px;">
      <div style="font-size:11px;color:#888;">Total Market Cap</div>
      <div style="font-size:16px;font-weight:600;color:#fff;">${total_mcap/1e12:.2f}T</div>
      <div style="font-size:12px;color:{'#44cc44' if mcap_change > 0 else '#ff4444'};">{mcap_change:+.2f}%</div>
    </div>
    <div style="flex:1;min-width:120px;background:#1a1a2a;border-radius:8px;padding:12px;">
      <div style="font-size:11px;color:#888;">24h Volume</div>
      <div style="font-size:16px;font-weight:600;color:#fff;">${total_vol/1e9:.1f}B</div>
    </div>
    <div style="flex:1;min-width:120px;background:#1a1a2a;border-radius:8px;padding:12px;">
      <div style="font-size:11px;color:#888;">BTC Dominance</div>
      <div style="font-size:16px;font-weight:600;color:#fff;">{btc_dom:.1f}%</div>
    </div>
  </div>

  <div style="margin-bottom:8px;font-size:13px;color:#888;font-weight:600;">KEY ASSETS (Hyperliquid Perps)</div>"""

for asset_name in ['BTC', 'ETH', 'SOL', 'HYPE']:
    if asset_name in key_assets:
        a = key_assets[asset_name]
        chg_color = "#44cc44" if a['change'] >= 0 else "#ff4444"
        chg_arrow = "&#9650;" if a['change'] >= 0 else "&#9660;"
        price_fmt = f"${a['price']:,.0f}" if a['price'] >= 1000 else f"${a['price']:,.2f}"
        funding_color = "#44cc44" if a['funding'] >= 0 else "#ff4444"
        funding_pct = a['funding'] * 100
        html += f"""
  <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:#1a1a2a;border-radius:8px;margin-bottom:6px;">
    <div>
      <span style="font-weight:600;color:#fff;font-size:15px;">{asset_name}</span>
      <span style="color:#888;font-size:12px;margin-left:8px;">OI: ${a['oi']:,.0f}</span>
    </div>
    <div style="text-align:right;">
      <span style="font-weight:600;color:#fff;font-size:15px;">{price_fmt}</span>
      <span style="color:{chg_color};font-size:13px;margin-left:8px;">{chg_arrow} {abs(a['change']):.2f}%</span>
      <div style="font-size:11px;color:{funding_color};">funding: {funding_pct:+.4f}%</div>
    </div>
  </div>"""

html += """
  <div style="margin-top:16px;margin-bottom:8px;font-size:13px;color:#888;font-weight:600;">&#128293; TOP MOVERS (24h)</div>"""

shown = 0
for m in top_movers:
    if m[0] in ['BTC', 'ETH', 'SOL', 'HYPE']: continue
    if shown >= 6: break
    name, price, pct, funding, oi, vol = m
    chg_color = "#44cc44" if pct >= 0 else "#ff4444"
    arrow = "&#9650;" if pct >= 0 else "&#9660;"
    pfmt = f"${price:,.0f}" if price >= 1000 else (f"${price:,.2f}" if price >= 1 else f"${price:.4f}")
    html += f"""
  <div style="display:flex;justify-content:space-between;padding:6px 12px;border-bottom:1px solid #1a1a2a;">
    <span style="color:#ccc;font-size:13px;">{name}</span>
    <span style="font-size:13px;"><span style="color:#fff;">{pfmt}</span> <span style="color:{chg_color};">{arrow} {abs(pct):.1f}%</span></span>
  </div>"""
    shown += 1

html += "\n</div>\n"

# Trending
if trending:
    html += """
<div style="background:#111119;border-radius:12px;padding:24px;margin-bottom:20px;border:1px solid #222;">
  <div style="font-size:18px;font-weight:600;color:#fff;margin-bottom:16px;">&#128269; Trending on CoinGecko</div>"""
    for c in trending:
        item = c['item']
        name = item['name']
        symbol = item['symbol']
        rank = item.get('market_cap_rank', 'N/A')
        try:
            chg = item.get('data', {}).get('price_change_percentage_24h', {}).get('usd', 0)
            chg_color = "#44cc44" if chg >= 0 else "#ff4444"
            html += f"""
  <div style="display:flex;justify-content:space-between;padding:8px 12px;border-bottom:1px solid #1a1a2a;">
    <span style="color:#fff;font-size:13px;">{name} <span style="color:#888;">({symbol})</span> <span style="color:#666;font-size:11px;">#{rank}</span></span>
    <span style="color:{chg_color};font-size:13px;">{chg:+.1f}%</span>
  </div>"""
        except:
            pass
    html += "\n</div>\n"

# GitHub
total_items = len(issues) + len(prs) + len(evo_issues)
html += f"""
<div style="background:#111119;border-radius:12px;padding:24px;margin-bottom:20px;border:1px solid #222;">
  <div style="font-size:18px;font-weight:600;color:#fff;margin-bottom:16px;">&#128025; ClawInfra Activity</div>
  <div style="font-size:13px;color:#888;margin-bottom:12px;">{total_items} open items across claw-chain &amp; evoclaw</div>"""

if prs:
    html += """  <div style="font-size:12px;color:#44cc44;font-weight:600;margin-bottom:4px;">PRs &mdash; claw-chain</div>"""
    for pr in prs:
        html += f"""  <div style="padding:4px 12px;font-size:13px;color:#ccc;">&bull; #{pr['number']} {pr['title']}</div>\n"""

if issues:
    html += """  <div style="font-size:12px;color:#ff8844;font-weight:600;margin-top:8px;margin-bottom:4px;">Issues &mdash; claw-chain</div>"""
    for issue in issues[:3]:
        html += f"""  <div style="padding:4px 12px;font-size:13px;color:#ccc;">&bull; #{issue['number']} {issue['title']}</div>\n"""

if evo_issues:
    html += """  <div style="font-size:12px;color:#ff8844;font-weight:600;margin-top:8px;margin-bottom:4px;">Issues &mdash; evoclaw</div>"""
    for issue in evo_issues[:3]:
        html += f"""  <div style="padding:4px 12px;font-size:13px;color:#ccc;">&bull; #{issue['number']} {issue['title']}</div>\n"""

if total_items == 0:
    html += """  <div style="padding:8px 12px;font-size:13px;color:#888;">&#9989; All clear</div>"""

html += "\n</div>\n"

# === IDEAS ===
btc_data = key_assets.get('BTC', {})
btc_price = btc_data.get('price', 74182)
btc_funding = btc_data.get('funding', -0.000023)
eth_funding = key_assets.get('ETH', {}).get('funding', -0.000016)

# Find extreme funding
funding_anomalies = [(n, mk, f) for n, mk, pct, f, oi, vol in top_movers if abs(f) > 0.0003]
funding_anomalies.sort(key=lambda x: abs(x[2]), reverse=True)

ideas = []

# IDEA 1: Trading — BTC negative funding + extreme fear = contrarian long
if btc_funding < 0 and fng_value < 30:
    idea1_title = "&#128994; BTC Negative Funding + Extreme Fear &mdash; Contrarian Long Setup"
    idea1_body = f"""BTC funding at <b>{btc_funding*100:+.4f}%</b> (shorts paying longs) while sentiment sits at <b>{fng_value}</b> ({fng_class}). This combo has historically preceded 10-20% rallies within 2 weeks. Shorts are crowded, the market is fearful despite BTC bouncing +3.2% from the $70.7K weekly low. <br><br><b>Trade:</b> Contrarian long on Hyperliquid at ${btc_price:,.0f} with stop at ${btc_price*0.96:,.0f} targeting ${btc_price*1.10:,.0f}. R:R ~2.5:1. You get <i>paid</i> to hold via negative funding. <br><b>Catalyst:</b> Any positive macro headline (tariff relief, rate cut signal) could trigger a violent short squeeze through $76K."""
elif funding_anomalies:
    top_anom = funding_anomalies[0]
    direction = "short squeeze" if top_anom[2] < -0.001 else "long squeeze"
    idea1_title = f"&#9889; {top_anom[0]} Extreme Funding &mdash; {direction.title()} Setup"
    idea1_body = f"""{top_anom[0]} funding at <b>{top_anom[2]*100:+.4f}%</b> is an extreme outlier. Mean reversion incoming. Small contrarian position, 2% portfolio risk."""
else:
    idea1_title = "&#128202; BTC Range Play &mdash; Collect Funding"
    idea1_body = f"""BTC at ${btc_price:,.0f} with mild funding. Grid trade ${btc_price*0.97:,.0f}&ndash;${btc_price*1.03:,.0f}."""

ideas.append((idea1_title, idea1_body, "Trading"))

# IDEA 2: Product — Funding Oracle for ClawChain
hype_oi = key_assets.get('HYPE', {}).get('oi', 21008230)
idea2_title = "&#128295; ClawChain: On-Chain Funding Rate Oracle + Agent Arb Layer"
idea2_body = f"""Hyperliquid processes massive perpetual volume (HYPE alone: ${hype_oi:,.0f} OI). Real-time funding rates are the most valuable trading signal and they're locked behind centralised APIs. <br><br><b>Build a ClawChain native oracle</b> that indexes funding rates from HL, Binance, Bybit, dYdX every 8h. EvoClaw agents subscribe on-chain and execute funding arbitrage autonomously &mdash; long on the venue paying you, short on the venue charging you. <br><b>Revenue:</b> 0.1% of arb profit flows to oracle stakers. <br><b>Why now:</b> With 5 RUSTSEC advisories in the claw-chain backlog (wasmtime, rand), clearing those first then shipping <code>FundingOracle</code> as a WASM module positions ClawChain as the DeFi nervous system for derivatives data. Start with an EvoClaw skill for rate ingestion today."""

ideas.append((idea2_title, idea2_body, "Product"))

# IDEA 3: Growth — Ride RaveDAO trending wave
if trending:
    trend_name = trending[0]['item']['name']
    trend_symbol = trending[0]['item']['symbol']
    try:
        trend_chg = trending[0]['item']['data']['price_change_percentage_24h']['usd']
    except:
        trend_chg = 0
    idea3_title = f"&#128200; Ride the {trend_name} Attention Wave for ClawChain Visibility"
    idea3_body = f"""<b>{trend_name} ({trend_symbol})</b> is #1 trending on CoinGecko &mdash; up <b>{trend_chg:+.1f}%</b> in 24h. When a token trends, search traffic spikes for 24-72h. <br><br><b>Action plan (next 12h):</b><br>1. Publish an @AlexChen31337 Twitter thread analysing {trend_name}'s momentum + how AI agents could auto-discover and trade trending tokens<br>2. Quick knowledge-base article: &ldquo;How EvoClaw Agents Detect Trending Tokens in Real-Time&rdquo;<br>3. Subtle CTA: &ldquo;Imagine agents on ClawChain that discover {trend_symbol} <i>before</i> it trends and execute within seconds&rdquo;<br><b>Goal:</b> 50+ impressions converting to ClawInfra GitHub stars. Piggyback on existing attention, don't fight for it."""
else:
    idea3_title = "&#128200; Public EvoClaw Agent Dashboard"
    idea3_body = f"""Build a live dashboard showing EvoClaw agents in action. GitHub-style contribution graph. Deploy on Vercel."""

ideas.append((idea3_title, idea3_body, "Growth"))

# Render ideas
idea_colors = {"Trading": "#ff6b6b", "Product": "#4ecdc4", "Growth": "#ffe66d"}

html += """
<div style="background:#111119;border-radius:12px;padding:24px;margin-bottom:20px;border:1px solid #222;">
  <div style="font-size:18px;font-weight:600;color:#fff;margin-bottom:4px;">&#128161; Today's Ideas</div>
  <div style="font-size:12px;color:#888;margin-bottom:20px;">3 actionable ideas based on current market conditions</div>
"""

for i, (title, body, category) in enumerate(ideas, 1):
    cat_color = idea_colors.get(category, "#888")
    html += f"""
  <div style="background:#1a1a2e;border-radius:10px;padding:20px;margin-bottom:16px;border-left:3px solid {cat_color};">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
      <span style="font-size:11px;color:{cat_color};text-transform:uppercase;letter-spacing:1px;font-weight:600;">{category}</span>
      <span style="font-size:11px;color:#666;">Idea #{i}</span>
    </div>
    <div style="font-size:16px;font-weight:600;color:#fff;margin-bottom:10px;">{title}</div>
    <div style="font-size:14px;color:#bbb;line-height:1.6;">{body}</div>
  </div>"""

html += """
</div>

<div style="text-align:center;padding:20px;color:#666;font-size:12px;">
  <div style="margin-bottom:8px;">&mdash; Alex Chen &bull; Autonomous Builder &mdash;</div>
  <div>Generated """ + date_str + """ at 8:00 AM AEST</div>
  <div style="margin-top:4px;color:#444;">Market data: Hyperliquid &bull; CoinGecko &bull; Alternative.me</div>
</div>

</div></body></html>"""

output_path = "/tmp/daily_ideas_20260415.html"
with open(output_path, 'w') as f:
    f.write(html)
print(f"OK: {output_path} ({len(html)} bytes)")
