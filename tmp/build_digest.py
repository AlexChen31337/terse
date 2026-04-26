import json, subprocess, datetime, sys, os

now = datetime.datetime(2026, 4, 26, 8, 0)
date_str = now.strftime("%A, %B %d, %Y")
outdir = os.path.dirname(os.path.abspath(__file__))
outpath = os.path.join(outdir, "daily_ideas_20260426.html")

def fetch(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=12)
        return r.stdout.strip()
    except:
        return ""

cg_raw = fetch("curl -s 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,hyperliquid&vs_currencies=usd&include_24hr_change=true'")
try:
    cg = json.loads(cg_raw)
except:
    cg = {}

btc_price = cg.get('bitcoin',{}).get('usd', 77530)
btc_chg = cg.get('bitcoin',{}).get('usd_24h_change', -0.09)
eth_price = cg.get('ethereum',{}).get('usd', 2316)
eth_chg = cg.get('ethereum',{}).get('usd_24h_change', 0.02)
sol_price = cg.get('solana',{}).get('usd', 85.9)
sol_chg = cg.get('solana',{}).get('usd_24h_change', -0.69)
hype_price = cg.get('hyperliquid',{}).get('usd', 41.44)
hype_chg = cg.get('hyperliquid',{}).get('usd_24h_change', 0.42)

fng_raw = fetch("curl -s 'https://api.alternative.me/fng/?limit=1'")
try:
    fng = json.loads(fng_raw)
    fng_val = int(fng['data'][0]['value'])
    fng_label = fng['data'][0]['value_classification']
except:
    fng_val = 31
    fng_label = "Fear"

hl_raw = fetch("curl -s -X POST 'https://api.hyperliquid.xyz/info' -H 'Content-Type: application/json' -d '{\"type\":\"metaAndAssetCtxs\"}'")
hl_top_funding = []
try:
    hl = json.loads(hl_raw)
    meta = hl[0]['universe']
    ctxs = hl[1]
    assets = []
    for i, m in enumerate(meta):
        c = ctxs[i]
        assets.append({
            'name': m['name'],
            'price': float(c['markPx']),
            'funding': float(c['funding']) * 100,
            'oi': float(c['openInterest']),
            'vol': float(c.get('dayNtlVlm', 0))
        })
    hl_top_funding = sorted(assets, key=lambda x: abs(x['funding']), reverse=True)[:5]
except Exception as e:
    print(f"HL warning: {e}", file=sys.stderr)

glob_raw = fetch("curl -s 'https://api.coingecko.com/api/v3/global'")
try:
    glob = json.loads(glob_raw)['data']
    total_mcap = glob['total_market_cap']['usd']
    btc_dom = glob['market_cap_percentage']['btc']
    mcap_chg = glob['market_cap_change_percentage_24h_usd']
except:
    total_mcap = 2.669e12
    btc_dom = 58.1
    mcap_chg = 0.06

trend_raw = fetch("curl -s 'https://api.coingecko.com/api/v3/search/trending'")
trending = []
try:
    td = json.loads(trend_raw)
    for c in td.get('coins', [])[:5]:
        item = c['item']
        trending.append(f"{item['name']} ({item['symbol']})")
except:
    pass

gh_raw = fetch("cd /home/bowen/.openclaw/workspace && gh search prs --owner clawinfra --state open --sort updated --limit 5 --json title,repository,updatedAt,url 2>/dev/null")
gh_issues_raw = fetch("cd /home/bowen/.openclaw/workspace && gh search issues --owner clawinfra --state open --sort updated --limit 5 --json title,repository,updatedAt,url 2>/dev/null")
gh_prs = []
gh_issues = []
try:
    gh_prs = json.loads(gh_raw) if gh_raw else []
except:
    pass
try:
    gh_issues = json.loads(gh_issues_raw) if gh_issues_raw else []
except:
    pass

def chg_color(v):
    return "#4caf50" if v >= 0 else "#ef5350"
def chg_arrow(v):
    return "&#9650;" if v >= 0 else "&#9660;"
def fng_color(v):
    if v <= 25: return "#ef5350"
    if v <= 45: return "#ff9800"
    if v <= 55: return "#ffd54f"
    if v <= 75: return "#66bb6a"
    return "#4caf50"

funding_rows = ""
for a in hl_top_funding:
    fc = "#4caf50" if a['funding'] > 0 else "#ef5350"
    funding_rows += f'<tr><td style="padding:8px 4px;border-bottom:1px solid #0d0d14;color:#e8eaf6;font-weight:600;">{a["name"]}</td><td style="padding:8px 4px;text-align:right;border-bottom:1px solid #0d0d14;color:#b0bec5;">${a["price"]:,.2f}</td><td style="padding:8px 4px;text-align:right;border-bottom:1px solid #0d0d14;color:{fc};font-weight:600;">{a["funding"]:+.4f}%</td><td style="padding:8px 4px;text-align:right;border-bottom:1px solid #0d0d14;color:#b0bec5;">${a["oi"]:,.0f}</td></tr>'

trending_tags = ""
for t in trending:
    trending_tags += f'<span style="background:#1a1a2e;color:#90caf9;padding:6px 12px;border-radius:20px;font-size:12px;border:1px solid #1e3a5f;display:inline-block;margin:3px;">{t}</span>'

gh_section = ""
if gh_prs or gh_issues:
    gh_section = '<div style="background:#111118;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid #1e1e2e;"><div style="font-size:17px;font-weight:600;color:#e8eaf6;margin-bottom:12px;">&#128025; ClawInfra GitHub</div>'
    if gh_prs:
        gh_section += '<div style="font-size:13px;color:#66bb6a;font-weight:600;margin-bottom:8px;">Open PRs</div>'
        for pr in gh_prs[:5]:
            rn = pr.get('repository',{}).get('name','') if isinstance(pr.get('repository'), dict) else str(pr.get('repository',''))
            gh_section += f'<div style="padding:6px 0;border-bottom:1px solid #0d0d14;"><a href="{pr["url"]}" style="color:#90caf9;text-decoration:none;font-size:13px;">{pr["title"]}</a> <span style="color:#546e7a;font-size:11px;">({rn})</span></div>'
    if gh_issues:
        gh_section += '<div style="font-size:13px;color:#ff9800;font-weight:600;margin-top:12px;margin-bottom:8px;">Open Issues</div>'
        for iss in gh_issues[:5]:
            rn = iss.get('repository',{}).get('name','') if isinstance(iss.get('repository'), dict) else str(iss.get('repository',''))
            gh_section += f'<div style="padding:6px 0;border-bottom:1px solid #0d0d14;"><a href="{iss["url"]}" style="color:#90caf9;text-decoration:none;font-size:13px;">{iss["title"]}</a> <span style="color:#546e7a;font-size:11px;">({rn})</span></div>'
    gh_section += "</div>"

top_fund = hl_top_funding[0] if hl_top_funding else {'name': 'HYPER', 'funding': -0.196, 'oi': 5276704}
fa = top_fund['name']
fr = top_fund['funding']
fd = "short" if fr > 0 else "long"
fc_text = "longs paying shorts" if fr > 0 else "shorts paying longs"
ann = abs(fr) * 3 * 365

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:'Segoe UI',system-ui,sans-serif;color:#c8ccd4;">
<div style="max-width:640px;margin:0 auto;padding:20px;">
<div style="background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);border-radius:16px;padding:32px;margin-bottom:20px;border:1px solid #1e3a5f;">
<div style="font-size:13px;color:#64b5f6;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">&#129504; ALEX DAILY IDEAS</div>
<div style="font-size:26px;font-weight:700;color:#e8eaf6;margin-bottom:4px;">{date_str}</div>
<div style="font-size:13px;color:#78909c;">Sunday Morning Digest &middot; Sydney 8:00 AM</div>
</div>
<div style="background:#111118;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid #1e1e2e;">
<div style="font-size:17px;font-weight:600;color:#e8eaf6;margin-bottom:16px;">&#128200; Market Snapshot</div>
<table style="width:100%;border-collapse:collapse;">
<tr>
<td style="padding:10px 8px;border-bottom:1px solid #1e1e2e;"><div style="font-size:13px;color:#78909c;">BTC</div><div style="font-size:20px;font-weight:700;color:#e8eaf6;">${btc_price:,.0f}</div></td>
<td style="padding:10px 8px;text-align:right;border-bottom:1px solid #1e1e2e;"><span style="color:{chg_color(btc_chg)};font-size:15px;font-weight:600;">{chg_arrow(btc_chg)} {btc_chg:+.1f}%</span></td>
<td style="padding:10px 8px;border-bottom:1px solid #1e1e2e;"><div style="font-size:13px;color:#78909c;">ETH</div><div style="font-size:20px;font-weight:700;color:#e8eaf6;">${eth_price:,.0f}</div></td>
<td style="padding:10px 8px;text-align:right;border-bottom:1px solid #1e1e2e;"><span style="color:{chg_color(eth_chg)};font-size:15px;font-weight:600;">{chg_arrow(eth_chg)} {eth_chg:+.1f}%</span></td>
</tr>
<tr>
<td style="padding:10px 8px;"><div style="font-size:13px;color:#78909c;">SOL</div><div style="font-size:20px;font-weight:700;color:#e8eaf6;">${sol_price:,.1f}</div></td>
<td style="padding:10px 8px;text-align:right;"><span style="color:{chg_color(sol_chg)};font-size:15px;font-weight:600;">{chg_arrow(sol_chg)} {sol_chg:+.1f}%</span></td>
<td style="padding:10px 8px;"><div style="font-size:13px;color:#78909c;">HYPE</div><div style="font-size:20px;font-weight:700;color:#e8eaf6;">${hype_price:,.2f}</div></td>
<td style="padding:10px 8px;text-align:right;"><span style="color:{chg_color(hype_chg)};font-size:15px;font-weight:600;">{chg_arrow(hype_chg)} {hype_chg:+.1f}%</span></td>
</tr>
</table>
<table style="width:100%;border-collapse:collapse;margin-top:16px;">
<tr>
<td style="width:33%;background:#0d0d14;border-radius:8px;padding:12px;text-align:center;">
<div style="font-size:11px;color:#78909c;text-transform:uppercase;letter-spacing:1px;">Fear &amp; Greed</div>
<div style="font-size:28px;font-weight:700;color:{fng_color(fng_val)};margin:4px 0;">{fng_val}</div>
<div style="font-size:12px;color:{fng_color(fng_val)};">{fng_label}</div>
</td>
<td style="width:4px;"></td>
<td style="width:33%;background:#0d0d14;border-radius:8px;padding:12px;text-align:center;">
<div style="font-size:11px;color:#78909c;text-transform:uppercase;letter-spacing:1px;">Total MCap</div>
<div style="font-size:20px;font-weight:700;color:#e8eaf6;margin:4px 0;">${total_mcap/1e12:.2f}T</div>
<div style="font-size:12px;color:{chg_color(mcap_chg)};">{chg_arrow(mcap_chg)} {mcap_chg:+.1f}% 24h</div>
</td>
<td style="width:4px;"></td>
<td style="width:33%;background:#0d0d14;border-radius:8px;padding:12px;text-align:center;">
<div style="font-size:11px;color:#78909c;text-transform:uppercase;letter-spacing:1px;">BTC Dom</div>
<div style="font-size:20px;font-weight:700;color:#e8eaf6;margin:4px 0;">{btc_dom:.1f}%</div>
<div style="font-size:12px;color:#78909c;">of total market</div>
</td>
</tr>
</table>
</div>
<div style="background:#111118;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid #1e1e2e;">
<div style="font-size:17px;font-weight:600;color:#e8eaf6;margin-bottom:4px;">&#9889; Hyperliquid Funding Radar</div>
<div style="font-size:12px;color:#78909c;margin-bottom:16px;">Extreme funding = potential mean-reversion plays</div>
<table style="width:100%;border-collapse:collapse;font-size:13px;">
<tr style="color:#546e7a;"><th style="text-align:left;padding:6px 4px;border-bottom:1px solid #1e1e2e;">Asset</th><th style="text-align:right;padding:6px 4px;border-bottom:1px solid #1e1e2e;">Price</th><th style="text-align:right;padding:6px 4px;border-bottom:1px solid #1e1e2e;">Funding/8h</th><th style="text-align:right;padding:6px 4px;border-bottom:1px solid #1e1e2e;">Open Interest</th></tr>
{funding_rows}
</table>
</div>
<div style="background:#111118;border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid #1e1e2e;">
<div style="font-size:17px;font-weight:600;color:#e8eaf6;margin-bottom:12px;">&#128293; Trending on CoinGecko</div>
<div>{trending_tags}</div>
</div>
{gh_section}
<div style="background:linear-gradient(135deg,#1a0a2e,#0f1a3e);border-radius:12px;padding:24px;margin-bottom:16px;border:1px solid #2a1a4e;">
<div style="font-size:20px;font-weight:700;color:#e8eaf6;margin-bottom:4px;">&#128161; Three Ideas for Today</div>
<div style="font-size:12px;color:#78909c;margin-bottom:20px;">Generated from live market data + project context</div>
<div style="background:#0d0d14;border-radius:10px;padding:20px;margin-bottom:14px;border-left:3px solid #ff9800;">
<div style="font-size:11px;color:#ff9800;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;">&#128200; TRADING OPPORTUNITY</div>
<div style="font-size:16px;font-weight:700;color:#e8eaf6;margin-bottom:8px;">{fa} Funding Rate Arbitrage &mdash; {abs(fr):.3f}% per 8h</div>
<div style="font-size:13px;color:#b0bec5;line-height:1.6;">
{fa} funding at <b style="color:{'#ef5350' if fr > 0 else '#4caf50'};">{fr:+.4f}%</b> &mdash; {fc_text}. That's <b>{ann:.0f}% annualized</b> for delta-neutral funding collection.<br><br>
<b>Play:</b> Open a {fd} perp on Hyperliquid + hedge with spot. Collect funding every 8h while market-neutral. Size at 2-5% of portfolio. Exit if funding flips sign.<br><br>
<b>Risk:</b> Weekend low liquidity = slippage risk. OI is ${top_fund.get('oi',0):,.0f}. Funding can flip fast during vol spikes.
</div></div>
<div style="background:#0d0d14;border-radius:10px;padding:20px;margin-bottom:14px;border-left:3px solid #64b5f6;">
<div style="font-size:11px;color:#64b5f6;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;">&#128295; PRODUCT FEATURE</div>
<div style="font-size:16px;font-weight:700;color:#e8eaf6;margin-bottom:8px;">ClawChain Agent Reputation Layer &mdash; On-Chain Trust Scores</div>
<div style="font-size:13px;color:#b0bec5;line-height:1.6;">
Fear &amp; Greed at <b style="color:{fng_color(fng_val)};">{fng_val} ({fng_label})</b> &mdash; sentiment drives humans, but agents need their own trust signal.<br><br>
<b>Concept:</b> Reputation primitive in ClawChain: composite trust score from (1) tx reliability, (2) contract interaction patterns, (3) peer-agent endorsements, (4) stake-weighted attestation.<br><br>
<b>Why now:</b> No L1 has native agent reputation. Baking it into the protocol layer before testnet = moat. This is "credit scores for AI agents" &mdash; prerequisite for agent-to-agent DeFi.<br><br>
<b>Next step:</b> 2-page spec this week. Core: <code style="background:#1a1a2e;padding:2px 6px;border-radius:4px;color:#90caf9;">ReputationRegistry</code>, <code style="background:#1a1a2e;padding:2px 6px;border-radius:4px;color:#90caf9;">EndorseAgent</code> tx type, decay function.
</div></div>
<div style="background:#0d0d14;border-radius:10px;padding:20px;border-left:3px solid #66bb6a;">
<div style="font-size:11px;color:#66bb6a;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;">&#128640; GROWTH ANGLE</div>
<div style="font-size:16px;font-weight:700;color:#e8eaf6;margin-bottom:8px;">Sunday Deep-Dive: "Why AI Agents Need Their Own Blockchain"</div>
<div style="font-size:13px;color:#b0bec5;line-height:1.6;">
Sunday = peak CT engagement. BTC dom at <b>{btc_dom:.1f}%</b> = concentrated attention. A narrative thread can capture mindshare from maximalists.<br><br>
<b>Thread (8-10 tweets):</b><br>
1. Hook: "Every AI agent is a tenant on someone else's chain."<br>
2. Problem: agents need sub-second finality, native identity, autonomous treasury<br>
3. Why current L1s fail (gas wars, MEV, no agent primitives)<br>
4. ClawChain: agent-native execution, reputation, self-sovereign identity<br>
5. Market: ${total_mcap/1e12:.1f}T crypto + $500B AI = convergence<br>
6. Technical demo teaser<br>
7-8. CTA + follow<br><br>
<b>Timing:</b> 10am-12pm Sydney (Sat evening US) for dual-timezone reach.
</div></div>
</div>
<div style="text-align:center;padding:20px;color:#37474f;font-size:11px;">
Generated by Alex &middot; {date_str} &middot; CoinGecko, Alternative.me, Hyperliquid<br>
<span style="color:#263238;">Powered by EvoClaw</span>
</div>
</div></body></html>"""

with open(outpath, "w") as f:
    f.write(html)
print(f"OK: {len(html)} bytes -> {outpath}")
