#!/bin/bash
# Promote latest ArxivToCode repos to social media
# Usage: ./promote_arxiv_repos.sh [--dry-run]

set -euo pipefail

WORKSPACE="$HOME/.openclaw/workspace"
SCRIPTS="$WORKSPACE/scripts"
GITHUB_TOKEN="$("$SCRIPTS/decrypt.sh" github-config.json 2>/dev/null | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['accounts']['bowen31337']['token'])")"
REPO_OWNER="Arxiv-to-code"
TEMP_JSON=$(mktemp)

# Dry run mode
DRY_RUN="${1:-}"
if [[ "$DRY_RUN" == "--dry-run" ]]; then
    echo "🔍 DRY RUN MODE - no actual posts will be made"
    echo ""
fi

# Get repos from GitHub API
echo "📡 Fetching repos from GitHub..."
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/users/$REPO_OWNER/repos?sort=created&per_page=100" > "$TEMP_JSON"

# Extract and filter repos using Python
REPOS=$(python3 << PYTHON
import sys, json
from datetime import datetime, timedelta

with open('$TEMP_JSON') as f:
    repos = json.load(f)

cutoff = datetime.now() - timedelta(days=7)

for repo in repos:
    created = datetime.strptime(repo['created_at'], '%Y-%m-%dT%H:%M:%SZ')
    if created < cutoff:
        continue
    name = repo['name']
    # ArxivToCode repos have long names (paper title)
    if len(name) < 30:
        continue
    print(f"{name}|{repo['html_url']}|{repo.get('description','') or ''}")
PYTHON
)

rm -f "$TEMP_JSON"

if [[ -z "$REPOS" ]]; then
    echo "ℹ️ No recent ArxivToCode repos found (last 7 days)"
    exit 0
fi

echo "✅ Found repos to promote:"
echo "$REPOS"
echo ""

# Process each repo
while IFS='|' read -r name url desc; do
    echo "📦 Processing: $name"
    
    # Extract arXiv ID from description or name
    ARXIV_ID=$(echo "$desc" | grep -oP 'arxiv\.org/abs/\K\d{4}\.\d{5}' | head -1 || echo "")
    
    if [[ -z "$ARXIV_ID" ]]; then
        # Try to extract from repo name pattern
        ARXIV_ID=$(echo "$name" | grep -oP '\d{4}\.\d{5}' || echo "")
    fi
    
    if [[ -z "$ARXIV_ID" ]]; then
        echo "  ⚠️ Could not extract arXiv ID, skipping"
        echo ""
        continue
    fi
    
    echo "  📄 arXiv ID: $ARXIV_ID"
    
    # Get paper details from arXiv API
    PAPER_INFO=$(curl -s "http://export.arxiv.org/api/query?id_list=$ARXIV_ID" | python3 << PYTHON
import sys, re
data = sys.stdin.read()
title = re.search(r'<title>(.*?)</title>', data, re.DOTALL)
title = title.group(1).strip() if title else 'Unknown Title'
authors = re.findall(r'<name>(.*?)</name>', data)
author_str = ', '.join(authors[:5])
if len(authors) > 5:
    author_str += ' et al.'
summary = re.search(r'<summary>(.*?)</summary>', data, re.DOTALL)
summary = summary.group(1).strip() if summary else ''
summary = re.sub(r'\s+', ' ', summary)[:500]
print(f"{title}|{author_str}|{summary}")
PYTHON
)
    
    IFS='|' read -r title authors summary <<< "$PAPER_INFO"
    
    echo "  📚 Title: $title"
    echo "  ✍️  Authors: $authors"
    
    # Create Twitter/X post
    TWEET="🚀 Just shipped: a complete implementation of

\"$title\"

by $authors

🔗 Code: $url
📄 Paper: https://arxiv.org/abs/$ARXIV_ID

#AI #MachineLearning #arxiv #OpenSource"

    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        echo ""
        echo "  🐦 Twitter/X post:"
        echo "  ──────────────────────────────────────────"
        echo "$TWEET"
        echo "  ──────────────────────────────────────────"
        echo ""
    else
        # Post to Twitter (requires Twitter API setup)
        echo "  🐦 Posting to Twitter/X..."
        # This is where we'd integrate Twitter API
        # For now, just save to a file
        echo "$TWEET" >> /tmp/arxiv_promote_tweets.txt
        echo "  ✅ Saved to /tmp/arxiv_promote_tweets.txt"
    fi
    
    # Create Reddit post
    REDDIT_TITLE="[$(echo $title | head -c 80)] (Code release)"
    REDDIT_BODY="**Paper:** [$title](https://arxiv.org/abs/$ARXIV_ID)

**Authors:** $authors

**Code:** [GitHub Repository]($url)

**Abstract:**
$summary

---

*Built automatically from arXiv by [ArxivToCode](https://github.com/AlexChen31337/arxiv-to-code) — turning papers into runnable code.*"

    if [[ "$DRY_RUN" == "--dry-run" ]]; then
        echo "  📱 Reddit post:"
        echo "  ──────────────────────────────────────────"
        echo "  Subreddit: r/MachineLearning"
        echo "  Title: $REDDIT_TITLE"
        echo "  Body preview: ${REDDIT_BODY:0:300}..."
        echo "  ──────────────────────────────────────────"
        echo ""
    else
        echo "  📱 Posting to Reddit..."
        # This is where we'd integrate Reddit API
        echo "$REDDIT_TITLE" >> /tmp/arxiv_promote_reddit_titles.txt
        echo "  ✅ Saved to /tmp/arxiv_promote_reddit_titles.txt"
    fi
    
    echo "────────────────────────────────────────────────"
    echo ""
done <<< "$REPOS"
