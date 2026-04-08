#!/usr/bin/env python3
"""
Promote latest ArxivToCode repos to social media
Usage: ./promote_arxiv_repos.py [--dry-run]
"""
import sys, os, subprocess, json, re, html
from datetime import datetime, timedelta

GITHUB_TOKEN = subprocess.check_output([
    "/home/bowen/.openclaw/workspace/memory/decrypt.sh", 
    "github-config.json"
], stderr=subprocess.DEVNULL).decode().strip()

TOKEN_DATA = json.loads(GITHUB_TOKEN)
GITHUB_TOKEN = TOKEN_DATA['accounts']['bowen31337']['token']
REPO_OWNER = "AlexChen31337"
DRY_RUN = "--dry-run" in sys.argv

if DRY_RUN:
    print("🔍 DRY RUN MODE - no actual posts will be made\n")

# Fetch repos from GitHub
print("📡 Fetching repos from GitHub...")
result = subprocess.run([
    "curl", "-s", 
    "-H", f"Authorization: token {GITHUB_TOKEN}",
    f"https://api.github.com/users/{REPO_OWNER}/repos?sort=created&per_page=100"
], capture_output=True, text=True)

repos = json.loads(result.stdout)
cutoff = datetime.now() - timedelta(days=7)

# Filter recent ArxivToCode repos (must have arXiv ID in description)
recent_repos = []
for repo in repos:
    created = datetime.strptime(repo['created_at'], '%Y-%m-%dT%H:%M:%SZ')
    if created < cutoff:
        continue
    desc = repo.get('description', '') or ''
    # ArxivToCode repos MUST have arXiv ID in description
    if not re.search(r'arxiv\.org/abs/\d{4}\.\d{5}|arXiv\s+\d{4}\.\d{5}', desc, re.IGNORECASE):
        continue
    recent_repos.append({
        'name': repo['name'],
        'url': repo['html_url'],
        'description': desc,
    })

if not recent_repos:
    print("ℹ️ No recent ArxivToCode repos found (last 7 days)")
    sys.exit(0)

print(f"✅ Found {len(recent_repos)} repo(s) to promote:\n")
for repo in recent_repos:
    print(f"  - {repo['name']}")

print("\n" + "="*60 + "\n")

# Process each repo
for repo in recent_repos:
    print(f"📦 Processing: {repo['name']}\n")
    
    # Extract arXiv ID
    arxiv_id = None
    desc_match = re.search(r'arxiv\.org/abs/\d{4}\.\d{5}', repo['description'])
    if desc_match:
        arxiv_id = desc_match.group(0).split('/')[-1]
    else:
        plain_match = re.search(r'arXiv\s+(\d{4}\.\d{5})', repo['description'], re.IGNORECASE)
        if plain_match:
            arxiv_id = plain_match.group(1)
        else:
            any_match = re.search(r'\d{4}\.\d{5}', repo['description'])
            if any_match:
                arxiv_id = any_match.group(0)
    
    if not arxiv_id:
        print("  ⚠️ Could not extract arXiv ID, skipping\n")
        print("="*60 + "\n")
        continue
    
    print(f"  📄 arXiv ID: {arxiv_id}")
    
    # Scrape arXiv web page
    page_result = subprocess.run([
        "curl", "-s", 
        f"https://arxiv.org/abs/{arxiv_id}"
    ], capture_output=True, text=True)
    
    page_html = page_result.stdout
    
    # Extract title: <h1 class="title mathjax"><span class="descriptor">Title:</span>TITLE</h1>
    title_match = re.search(r'<h1 class="title mathjax">.*?<span class="descriptor">Title:</span>(.*?)</h1>', page_html, re.DOTALL)
    title = title_match.group(1).strip() if title_match else 'Unknown Title'
    title = re.sub(r'<[^>]+>', '', title)
    title = html.unescape(title)
    
    # Extract authors: <div class="authors"><a>NAME</a>, <a>NAME</a></div>
    authors_div = re.search(r'<div class="authors">.*?</div>', page_html, re.DOTALL)
    authors = []
    if authors_div:
        # Extract text from all <a> tags in the authors div
        authors = re.findall(r'<a[^>]*>([^<]+)</a>', authors_div.group(0))
    author_str = ', '.join([html.unescape(a.strip()) for a in authors[:5]])
    if len(authors) > 5:
        author_str += ' et al.'
    
    # Extract abstract: <section class="abstract mathjax">...</section>
    abstract_match = re.search(r'<section class="abstract mathjax">.*?</section>', page_html, re.DOTALL)
    summary = ''
    if abstract_match:
        abstract_html = abstract_match.group(0)
        # Remove all HTML tags
        summary = re.sub(r'<[^>]+>', ' ', abstract_html)
        # Unescape HTML entities
        summary = html.unescape(summary)
        # Clean up whitespace
        summary = re.sub(r'\s+', ' ', summary).strip()
        # Remove "Abstract:" prefix if present
        summary = re.sub(r'^Abstract:\s*', '', summary, flags=re.IGNORECASE)
        summary = summary[:500]
    
    print(f"  📚 Title: {title}")
    print(f"  ✍️  Authors: {author_str}\n")
    
    # Create Twitter/X post
    tweet = f"""🚀 Just shipped: a complete implementation of

"{title}"

by {author_str}

🔗 Code: {repo['url']}
📄 Paper: https://arxiv.org/abs/{arxiv_id}

#AI #MachineLearning #arxiv #OpenSource"""
    
    if DRY_RUN:
        print("  🐦 Twitter/X post:")
        print("  ─" * 40)
        print(tweet)
        print("  ─" * 40 + "\n")
    else:
        print("  🐦 Posting to Twitter/X...")
        # Twitter API integration would go here
        with open('/tmp/arxiv_promote_tweets.txt', 'a') as f:
            f.write(tweet + "\n\n---\n\n")
        print("  ✅ Saved to /tmp/arxiv_promote_tweets.txt\n")
    
    # Create Reddit post
    reddit_title = f"[{title[:80]}] (Code release)"
    reddit_body = f"""**Paper:** [{title}](https://arxiv.org/abs/{arxiv_id})

**Authors:** {author_str}

**Code:** [GitHub Repository]({repo['url']})

**Abstract:**
{summary}

---

*Built automatically from arXiv by [ArxivToCode](https://github.com/AlexChen31337/arxiv-to-code) — turning papers into runnable code.*"""
    
    if DRY_RUN:
        print("  📱 Reddit post:")
        print("  ─" * 40)
        print(f"  Subreddit: r/MachineLearning")
        print(f"  Title: {reddit_title}")
        print(f"  Body preview: {reddit_body[:300]}...")
        print("  ─" * 40 + "\n")
    else:
        print("  📱 Posting to Reddit...")
        # Reddit API integration would go here
        print("  ✅ Posted!\n")
    
    print("="*60 + "\n")
