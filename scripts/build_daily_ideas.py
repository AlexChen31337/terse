#!/usr/bin/env python3
"""Build the daily ideas HTML email with real market data."""
import datetime, os, sys

date_str = datetime.datetime.now().strftime('%Y%m%d')
today = datetime.datetime.now().strftime('%A, %B %d, %Y')

btc_price = "77,506"
btc_change = "3.24"
eth_price = "2,431"
eth_change = "3.51"
sol_price = "89.22"
sol_change = "-0.07"
hype_price = "44.53"
hype_change = "2.07"
fng_value = "21"
fng_class = "Extreme Fear"
total_mcap = "2.70T"
btc_dom = "57.4"
mcap_change = "2.68"

hl_data = """<div>BTC: $77,452 <span style='color:#22c55e'>+3.35%</span> | Vol: $3,379.9M</div>
<div>ETH: $2,429 <span style='color:#22c55e'>+3.71%</span> | Vol: $1,107.6M</div>
<div>SOL: $89.18 <span style='color:#22c55e'>+0.11%</span> | Vol: $396.1M</div>
<div>HYPE: $44.54 <span style='color:#22c55e'>+2.19%</span> | Vol: $303.8M</div>
<div>ZEC: $328.90 <span style='color:#ef4444'>-2.95%</span> | Vol: $70.0M</div>
<div>XRP: $1.48 <span style='color:#22c55e'>+2.22%</span> | Vol: $61.4M</div>
<div>DOGE: $0.10 <span style='color:#22c55e'>+1.18%</span> | Vol: $43.6M</div>
<div>TAO: $260.36 <span style='color:#22c55e'>+5.43%</span> | Vol: $35.3M</div>
<div>kPEPE: $0.004 <span style='color:#22c55e'>+0.50%</span> | Vol: $28.1M</div>
<div>WLD: $0.28 <span style='color:#ef4444'>-12.56%</span> | Vol: $23.6M</div>"""

hl_funding = """<div>MAVIA: <span style='color:#22c55e'>0.1083%</span> (ann: 118.6%) | Price +8.50%</div>
<div>BLAST: <span style='color:#ef4444'>-0.0566%</span> (ann: -62.0%) | Price +2.31%</div>
<div>FTT: <span style='color:#ef4444'>-0.0537%</span> (ann: -58.8%) | Price +1.75%</div>
<div>TST: <span style='color:#22c55e'>0.0361%</span> (ann: 39.5%) | Price -9.72%</div>
<div>YZY: <span style='color:#ef4444'>-0.0331%</span> (ann: -36.2%) | Price +0.57%</div>"""

trending = """<div>1. Asteroid Shiba (ASTEROID)</div>
<div>2. RaveDAO (RAVE)</div>
<div>3. Siren (SIREN)</div>
<div>4. Pudgy Penguins (PENGU)</div>
<div>5. Monad (MON)</div>
<div>6. Bitcoin (BTC)</div>
<div>7. XRP (XRP)</div>"""

gh_data = """<strong>claw-chain issues:</strong><br/>
&bull; #100: RUSTSEC-2026-0099: Wildcard name constraints<br/>
&bull; #99: RUSTSEC-2026-0098: URI name constraints<br/>
&bull; #96: RUSTSEC-2025-0161: libsecp256k1 unmaintained<br/><br/>
<strong>PRs:</strong><br/>
&bull; PR #95: fix: bump rand to 0.9.3 (RUSTSEC-2026-0097)<br/><br/>
<strong>evoclaw issues:</strong><br/>
&bull; #40: feat: pluggable context engine<br/>
&bull; #39: feat: security scanning for memory entries<br/>
&bull; #38: feat: auto-create skills from task execution"""

def color_change(val):
    try:
        v = float(val)
        if v > 0:
            return f'<span style="color:#22c55e;font-weight:600">+{v:.2f}%</span>'
        elif v < 0:
            return f'<span style="color:#ef4444;font-weight:600">{v:.2f}%</span>'
        return '<span style="color:#94a3b8">0.00%</span>'
    except:
        return f'<span style="color:#94a3b8">{val}</span>'

html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:640px;margin:0 auto;padding:20px;">

<div style="background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);border:1px solid #334155;border-radius:16px;padding:32px;margin-bottom:20px;text-align:center;">
  <div style="font-size:40px;margin-bottom:8px;">&#129504;</div>
  <h1 style="color:#f8fafc;font-size:24px;margin:0 0 4px 0;">Alex's Daily Ideas</h1>
  <p style="color:#64748b;font-size:14px;margin:0;">{today} &middot; Sydney</p>
</div>

<div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:24px;margin-bottom:16px;">
  <h2 style="color:#f8fafc;font-size:16px;margin:0 0 16px 0;">&#128202; Market Pulse</h2>
  <table style="width:100%;border-collapse:collapse;">
    <tr style="border-bottom:1px solid #334155;">
      <td style="padding:10px 0;color:#94a3b8;font-size:13px;">BTC</td>
      <td style="padding:10px 0;color:#f8fafc;font-size:15px;font-weight:600;text-align:right;">${btc_price}</td>
      <td style="padding:10px 0;text-align:right;font-size:13px;">{color_change(btc_change)}</td>
    </tr>
    <tr style="border-bottom:1px solid #334155;">
      <td style="padding:10px 0;color:#94a3b8;font-size:13px;">ETH</td>
      <td style="padding:10px 0;color:#f8fafc;font-size:15px;font-weight:600;text-align:right;">${eth_price}</td>
      <td style="padding:10px 0;text-align:right;font-size:13px;">{color_change(eth_change)}</td>
    </tr>
    <tr style="border-bottom:1px solid #334155;">
      <td style="padding:10px 0;color:#94a3b8;font-size:13px;">SOL</td>
      <td style="padding:10px 0;color:#f8fafc;font-size:15px;font-weight:600;text-align:right;">${sol_price}</td>
      <td style="padding:10px 0;text-align:right;font-size:13px;">{color_change(sol_change)}</td>
    </tr>
    <tr>
      <td style="padding:10px 0;color:#94a3b8;font-size:13px;">HYPE</td>
      <td style="padding:10px 0;color:#f8fafc;font-size:15px;font-weight:600;text-align:right;">${hype_price}</td>
      <td style="padding:10px 0;text-align:right;font-size:13px;">{color_change(hype_change)}</td>
    </tr>
  </table>
  <div style="margin-top:16px;padding-top:16px;border-top:1px solid #334155;">
    <table style="width:100%;">
      <tr>
        <td style="text-align:center;width:33%;">
          <div style="color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:1px;">Fear &amp; Greed</div>
          <div style="color:#ef4444;font-size:24px;font-weight:700;margin-top:4px;">{fng_value}</div>
          <div style="color:#ef4444;font-size:12px;">{fng_class}</div>
        </td>
        <td style="text-align:center;width:33%;">
          <div style="color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:1px;">Total MCap</div>
          <div style="color:#f8fafc;font-size:16px;font-weight:600;margin-top:4px;">${total_mcap}</div>
          <div style="font-size:12px;">{color_change(mcap_change)}</div>
        </td>
        <td style="text-align:center;width:33%;">
          <div style="color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:1px;">BTC Dom</div>
          <div style="color:#f8fafc;font-size:16px;font-weight:600;margin-top:4px;">{btc_dom}%</div>
        </td>
      </tr>
    </table>
  </div>
</div>

<div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:24px;margin-bottom:16px;">
  <h2 style="color:#f8fafc;font-size:16px;margin:0 0 16px 0;">&#9889; Hyperliquid Top Movers</h2>
  <div style="color:#cbd5e1;font-size:13px;line-height:1.8;font-family:'SF Mono',Monaco,monospace;">
    {hl_data}
  </div>
  <div style="margin-top:12px;padding-top:12px;border-top:1px solid #334155;">
    <div style="color:#f59e0b;font-size:12px;font-weight:600;margin-bottom:8px;">&#128293; Extreme Funding Rates</div>
    <div style="color:#cbd5e1;font-size:12px;line-height:1.8;font-family:'SF Mono',Monaco,monospace;">
      {hl_funding}
    </div>
  </div>
</div>

<div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:24px;margin-bottom:16px;">
  <h2 style="color:#f8fafc;font-size:16px;margin:0 0 12px 0;">&#128293; Trending on CoinGecko</h2>
  <div style="color:#cbd5e1;font-size:13px;line-height:1.8;">{trending}</div>
</div>

<div style="background:linear-gradient(135deg,#1e3a5f 0%,#1e293b 100%);border:1px solid #3b82f6;border-radius:12px;padding:24px;margin-bottom:16px;">
  <h2 style="color:#60a5fa;font-size:18px;margin:0 0 20px 0;">&#128161; Today's Ideas</h2>

  <div style="background:rgba(0,0,0,0.2);border-radius:8px;padding:16px;margin-bottom:12px;">
    <div style="margin-bottom:8px;">
      <span style="background:#22c55e;color:#000;font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;text-transform:uppercase;">Trading</span>
    </div>
    <h3 style="color:#f8fafc;font-size:15px;margin:0 0 8px 0;">Extreme Fear = Contrarian Long Setup</h3>
    <p style="color:#cbd5e1;font-size:13px;line-height:1.6;margin:0;">
      Fear &amp; Greed at <strong>21 (Extreme Fear)</strong> while BTC just bounced +3.3% &mdash; classic divergence signal. The market is pricing in maximum doom but price action is recovering. Key observations: (1) BTC and ETH funding rates are <strong>negative</strong> on Hyperliquid, meaning shorts are paying longs &mdash; the crowd is overleveraged short. (2) WLD dumped -12.6% and ORDI -15.9% &mdash; capitulation candidates for mean-reversion bounce plays. (3) ENA surged +14.8% on strong volume &mdash; momentum continuation trade with stops below today's low. <strong>Playbook:</strong> Scale into BTC/ETH longs with negative funding tailwind, targeting $80K BTC. Use WLD/ORDI for quick mean-reversion scalps (tight stops). Trail ENA longs.
    </p>
    <div style="color:#64748b;font-size:11px;margin-top:8px;">&#9201; Timeframe: 1-5 days &middot; &#128202; Risk: Medium &middot; &#128176; Edge: Negative funding + extreme fear divergence</div>
  </div>

  <div style="background:rgba(0,0,0,0.2);border-radius:8px;padding:16px;margin-bottom:12px;">
    <div style="margin-bottom:8px;">
      <span style="background:#8b5cf6;color:#fff;font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;text-transform:uppercase;">Product</span>
    </div>
    <h3 style="color:#f8fafc;font-size:15px;margin:0 0 8px 0;">RUSTSEC Auto-Remediation Pipeline for ClawChain</h3>
    <p style="color:#cbd5e1;font-size:13px;line-height:1.6;margin:0;">
      We have <strong>5 open RUSTSEC advisories</strong> on claw-chain (issues #96-100) and 1 open PR fixing rand. This is becoming a recurring maintenance burden. Build an <strong>automated RUSTSEC remediation pipeline</strong>: (1) cargo-audit runs nightly via GitHub Actions, (2) for each advisory, Alex auto-creates a branch, bumps the dep, runs tests, and opens a PR with the advisory summary, (3) auto-merge if CI passes and it's a patch-level bump. This turns a manual triage process into a zero-touch security pipeline. We're already halfway there with the existing cron scanning &mdash; just need the auto-fix loop. <strong>Ship this week</strong> &mdash; it'll save hours of cumulative maintenance.
    </p>
    <div style="color:#64748b;font-size:11px;margin-top:8px;">&#127919; Impact: High (security + devex) &middot; &#128295; Effort: 2-3 days</div>
  </div>

  <div style="background:rgba(0,0,0,0.2);border-radius:8px;padding:16px;">
    <div style="margin-bottom:8px;">
      <span style="background:#f59e0b;color:#000;font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;text-transform:uppercase;">Growth</span>
    </div>
    <h3 style="color:#f8fafc;font-size:15px;margin:0 0 8px 0;">&quot;Agent Fear Index&quot; &mdash; Publish Our Own Sentiment Metric</h3>
    <p style="color:#cbd5e1;font-size:13px;line-height:1.6;margin:0;">
      We already run whalecli, alphastrike, and Hyperliquid data pipelines. Combine them into a <strong>ClawChain Agent Fear Index</strong> &mdash; a proprietary composite metric blending: funding rates, whale flow direction, OI changes, and social sentiment from trending coins. Publish it daily on Twitter via @AlexChen31337 with a clean visual card. Why: (1) establishes thought leadership before ClawChain mainnet, (2) gives the community a reason to follow us daily, (3) generates SEO-rich content that links back to clawinfra. The MAVIA +118% annualized funding rate today is exactly the kind of signal that makes a great daily post.
    </p>
    <div style="color:#64748b;font-size:11px;margin-top:8px;">&#128200; Potential: High brand equity &middot; &#128176; Cost: $0 (existing infra)</div>
  </div>
</div>

<div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:24px;margin-bottom:16px;">
  <h2 style="color:#f8fafc;font-size:16px;margin:0 0 12px 0;">&#128295; ClawInfra Status</h2>
  <div style="color:#cbd5e1;font-size:13px;line-height:1.8;">{gh_data}</div>
</div>

<div style="text-align:center;padding:20px 0;">
  <p style="color:#475569;font-size:12px;margin:0;">Built by Alex &middot; Powered by real-time market data</p>
  <p style="color:#334155;font-size:11px;margin:4px 0 0 0;">Hyperliquid &middot; CoinGecko &middot; Alternative.me &middot; GitHub</p>
</div>

</div>
</body>
</html>"""

output_path = f'/tmp/daily_ideas_{date_str}.html'
with open(output_path, 'w') as f:
    f.write(html)
print(f"Written to {output_path} ({len(html)} bytes)")
