#!/usr/bin/env python3
"""Passive domain reconnaissance — DNS, SSL, WHOIS, subdomains, HTTP headers."""

import argparse
import json
import socket
import ssl
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def dns_lookup(domain: str) -> dict:
    """Query DNS records using dig."""
    records = {}
    record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]

    for rtype in record_types:
        try:
            result = subprocess.run(
                ["dig", "+short", domain, rtype],
                capture_output=True, text=True, timeout=10
            )
            output = result.stdout.strip()
            if output:
                records[rtype] = output.split("\n")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to socket for A records
            if rtype == "A":
                try:
                    ips = socket.getaddrinfo(domain, None, socket.AF_INET)
                    records["A"] = list(set(addr[4][0] for addr in ips))
                except socket.gaierror:
                    pass

    return records


def ssl_inspect(domain: str, port: int = 443) -> dict:
    """Inspect SSL certificate."""
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as sock:
            sock.settimeout(10)
            sock.connect((domain, port))
            cert = sock.getpeercert()

        return {
            "subject": dict(x[0] for x in cert.get("subject", ())),
            "issuer": dict(x[0] for x in cert.get("issuer", ())),
            "sans": [entry[1] for entry in cert.get("subjectAltName", ())],
            "not_before": cert.get("notBefore", ""),
            "not_after": cert.get("notAfter", ""),
            "serial": cert.get("serialNumber", ""),
            "version": cert.get("version", ""),
        }
    except Exception as e:
        return {"error": str(e)}


def whois_lookup(domain: str) -> dict:
    """WHOIS lookup via CLI."""
    try:
        result = subprocess.run(
            ["whois", domain],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout

        info = {}
        field_map = {
            "Registrar:": "registrar",
            "Creation Date:": "created",
            "Updated Date:": "updated",
            "Registry Expiry Date:": "expires",
            "Expiration Date:": "expires",
            "Name Server:": "nameservers",
        }

        nameservers = []
        for line in output.split("\n"):
            line = line.strip()
            for prefix, key in field_map.items():
                if line.startswith(prefix):
                    value = line[len(prefix):].strip()
                    if key == "nameservers":
                        nameservers.append(value.lower())
                    elif key not in info:
                        info[key] = value

        if nameservers:
            info["nameservers"] = nameservers

        return info
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"error": str(e)}


def discover_subdomains(domain: str) -> list[dict]:
    """Subdomain discovery via crt.sh + common prefixes."""
    found = {}

    # Certificate Transparency via crt.sh
    try:
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        req = urllib.request.Request(url, headers={"User-Agent": "domain-intel/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            for entry in data:
                name = entry.get("name_value", "").strip().lower()
                for sub in name.split("\n"):
                    sub = sub.strip()
                    if sub.endswith(f".{domain}") or sub == domain:
                        if sub not in found:
                            found[sub] = {"source": "crt.sh"}
    except Exception:
        pass

    # Common subdomain brute-force
    common_file = os.path.join(os.path.dirname(__file__), "..", "references", "common-subdomains.txt")
    common_prefixes = ["www", "mail", "ftp", "api", "dev", "staging", "admin", "blog",
                       "shop", "app", "cdn", "docs", "git", "jenkins", "ci", "test",
                       "beta", "portal", "vpn", "remote", "ns1", "ns2", "mx", "smtp",
                       "imap", "pop", "webmail", "dashboard", "status", "monitor"]

    if os.path.exists(common_file):
        with open(common_file) as f:
            common_prefixes = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    def check_subdomain(prefix):
        sub = f"{prefix}.{domain}"
        try:
            socket.getaddrinfo(sub, None, socket.AF_INET)
            return sub, {"source": "dns-brute", "resolves": True}
        except socket.gaierror:
            return None, None

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(check_subdomain, p): p for p in common_prefixes}
        for future in as_completed(futures):
            sub, info = future.result()
            if sub and sub not in found:
                found[sub] = info

    # Resolve IPs for crt.sh findings
    results = []
    for sub, info in sorted(found.items()):
        try:
            ips = socket.getaddrinfo(sub, None, socket.AF_INET)
            ip = ips[0][4][0] if ips else "—"
        except socket.gaierror:
            ip = "—"
        results.append({"subdomain": sub, "ip": ip, "source": info["source"]})

    return results


def check_headers(domain: str) -> dict:
    """Check HTTP security headers."""
    try:
        url = f"https://{domain}"
        req = urllib.request.Request(url, headers={"User-Agent": "domain-intel/1.0"}, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            headers = dict(resp.headers)
    except Exception:
        try:
            url = f"http://{domain}"
            req = urllib.request.Request(url, headers={"User-Agent": "domain-intel/1.0"}, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as resp:
                headers = dict(resp.headers)
        except Exception as e:
            return {"error": str(e)}

    security_headers = {
        "Strict-Transport-Security": headers.get("Strict-Transport-Security", "❌ Missing"),
        "Content-Security-Policy": headers.get("Content-Security-Policy", "❌ Missing"),
        "X-Frame-Options": headers.get("X-Frame-Options", "❌ Missing"),
        "X-Content-Type-Options": headers.get("X-Content-Type-Options", "❌ Missing"),
        "X-XSS-Protection": headers.get("X-XSS-Protection", "❌ Missing"),
        "Referrer-Policy": headers.get("Referrer-Policy", "❌ Missing"),
        "Permissions-Policy": headers.get("Permissions-Policy", "❌ Missing"),
    }

    server = headers.get("Server", "—")
    return {"security_headers": security_headers, "server": server}


# --- Formatters ---

def format_dns(domain: str, records: dict, as_json: bool = False) -> str:
    if as_json:
        return json.dumps({"domain": domain, "records": records}, indent=2)
    lines = [f"## DNS Records — {domain}\n", "| Type | Value |", "|------|-------|"]
    for rtype, values in sorted(records.items()):
        for v in values:
            lines.append(f"| {rtype} | `{v}` |")
    if not records:
        lines.append("| — | No records found |")
    return "\n".join(lines)


def format_ssl(domain: str, cert: dict, as_json: bool = False) -> str:
    if as_json:
        return json.dumps({"domain": domain, "certificate": cert}, indent=2)
    if "error" in cert:
        return f"## SSL Certificate — {domain}\n\n❌ Error: {cert['error']}"
    lines = [f"## SSL Certificate — {domain}\n"]
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| Subject | {cert.get('subject', {}).get('commonName', '—')} |")
    lines.append(f"| Issuer | {cert.get('issuer', {}).get('organizationName', '—')} |")
    lines.append(f"| SANs | {', '.join(cert.get('sans', [])[:10])} |")
    lines.append(f"| Valid From | {cert.get('not_before', '—')} |")
    lines.append(f"| Valid Until | {cert.get('not_after', '—')} |")
    lines.append(f"| Serial | {cert.get('serial', '—')} |")
    return "\n".join(lines)


def format_whois(domain: str, info: dict, as_json: bool = False) -> str:
    if as_json:
        return json.dumps({"domain": domain, "whois": info}, indent=2)
    if "error" in info:
        return f"## WHOIS — {domain}\n\n❌ Error: {info['error']}"
    lines = [f"## WHOIS — {domain}\n", "| Field | Value |", "|-------|-------|"]
    for key, value in info.items():
        if isinstance(value, list):
            value = ", ".join(value)
        lines.append(f"| {key.title()} | {value} |")
    return "\n".join(lines)


def format_subdomains(domain: str, subs: list, as_json: bool = False) -> str:
    if as_json:
        return json.dumps({"domain": domain, "subdomains": subs}, indent=2)
    lines = [f"## Subdomains — {domain} ({len(subs)} found)\n",
             "| Subdomain | IP | Source |", "|-----------|-----|--------|"]
    for s in subs[:100]:  # Cap at 100
        lines.append(f"| {s['subdomain']} | {s['ip']} | {s['source']} |")
    return "\n".join(lines)


def format_headers(domain: str, info: dict, as_json: bool = False) -> str:
    if as_json:
        return json.dumps({"domain": domain, "headers": info}, indent=2)
    if "error" in info:
        return f"## HTTP Headers — {domain}\n\n❌ Error: {info['error']}"
    lines = [f"## HTTP Security Headers — {domain}\n",
             f"**Server:** {info.get('server', '—')}\n",
             "| Header | Value |", "|--------|-------|"]
    for header, value in info.get("security_headers", {}).items():
        status = "✅" if not value.startswith("❌") else ""
        display = value[:80] if not value.startswith("❌") else value
        lines.append(f"| {header} | {status} {display} |")
    return "\n".join(lines)


import os  # needed for common_file path


def main():
    parser = argparse.ArgumentParser(description="Passive domain reconnaissance")
    parser.add_argument("command", choices=["dns", "ssl", "whois", "subdomains", "headers", "full", "bulk"])
    parser.add_argument("domains", nargs="+", help="Domain(s) to investigate")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    as_json = args.json

    if args.command == "bulk":
        for domain in args.domains:
            print(f"\n# Full Report — {domain}\n")
            print(format_dns(domain, dns_lookup(domain), as_json))
            print(format_ssl(domain, ssl_inspect(domain), as_json))
            print(format_whois(domain, whois_lookup(domain), as_json))
            print(format_headers(domain, check_headers(domain), as_json))
            print(format_subdomains(domain, discover_subdomains(domain), as_json))
            print("\n---\n")
        return

    domain = args.domains[0]

    if args.command == "dns":
        print(format_dns(domain, dns_lookup(domain), as_json))
    elif args.command == "ssl":
        print(format_ssl(domain, ssl_inspect(domain), as_json))
    elif args.command == "whois":
        print(format_whois(domain, whois_lookup(domain), as_json))
    elif args.command == "subdomains":
        print(format_subdomains(domain, discover_subdomains(domain), as_json))
    elif args.command == "headers":
        print(format_headers(domain, check_headers(domain), as_json))
    elif args.command == "full":
        print(f"# Full Report — {domain}\n")
        print(format_dns(domain, dns_lookup(domain), as_json))
        print()
        print(format_ssl(domain, ssl_inspect(domain), as_json))
        print()
        print(format_whois(domain, whois_lookup(domain), as_json))
        print()
        print(format_headers(domain, check_headers(domain), as_json))
        print()
        print(format_subdomains(domain, discover_subdomains(domain), as_json))


if __name__ == "__main__":
    main()
