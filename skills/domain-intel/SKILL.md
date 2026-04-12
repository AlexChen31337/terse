---
name: domain-intel
description: "Passive domain reconnaissance — DNS, SSL certs, WHOIS, subdomains, HTTP headers. No API keys needed."
version: 1.0.0
---

# Domain Intel — Passive Reconnaissance

## When to Use
- Investigating a domain's infrastructure
- Checking SSL certificate details and expiry
- DNS record enumeration
- Subdomain discovery via Certificate Transparency
- Security header analysis
- Bulk domain comparison

## Procedure

1. **DNS Records** — Query A, AAAA, MX, NS, TXT, CNAME, SOA:
   ```bash
   uv run python skills/domain-intel/scripts/domain_intel.py dns example.com
   ```

2. **SSL Certificate** — Issuer, subject, SANs, expiry, algorithm:
   ```bash
   uv run python skills/domain-intel/scripts/domain_intel.py ssl example.com
   ```

3. **WHOIS** — Registrar, dates, nameservers:
   ```bash
   uv run python skills/domain-intel/scripts/domain_intel.py whois example.com
   ```

4. **Subdomains** — Certificate Transparency (crt.sh) + common prefixes:
   ```bash
   uv run python skills/domain-intel/scripts/domain_intel.py subdomains example.com
   ```

5. **HTTP Headers** — Security header analysis (HSTS, CSP, X-Frame-Options):
   ```bash
   uv run python skills/domain-intel/scripts/domain_intel.py headers example.com
   ```

6. **Full Report** — All of the above:
   ```bash
   uv run python skills/domain-intel/scripts/domain_intel.py full example.com
   ```

7. **Bulk Analysis** — Multiple domains:
   ```bash
   uv run python skills/domain-intel/scripts/domain_intel.py bulk example.com example.org
   ```

Add `--json` to any command for JSON output.

## Pitfalls
- WHOIS may be rate-limited — don't bulk-query more than ~10 domains
- crt.sh can be slow (10-30s) — be patient
- Some domains block DNS queries from certain providers
- **Passive only** — no port scanning, no active probing beyond standard HTTP/HTTPS
- WHOIS data is often redacted (GDPR)

## Verification
- DNS records match expected values
- SSL cert shows correct domain and valid dates
- Output is well-formatted markdown tables
