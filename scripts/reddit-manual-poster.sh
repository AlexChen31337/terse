#!/bin/bash

# Reddit Manual Posting Helper
# Opens browser with post pre-filled for manual review and posting

SUBREDDIT=$1
TITLE=$2
CONTENT_FILE=$3

if [ -z "$SUBREDDIT" ] || [ -z "$TITLE" ] || [ -z "$CONTENT_FILE" ]; then
    echo "Usage: $0 <subreddit> <title> <content-file>"
    echo "Example: $0 cryptocurrency 'ClawChain Post' clawchain-reddit-post.md"
    exit 1
fi

CONTENT=$(cat "$CONTENT_FILE")

echo "🌐 Opening Reddit for r/$SUBREDDIT..."
echo "📝 Title: $TITLE"
echo "📄 Content from: $CONTENT_FILE"
echo ""
echo "Steps:"
echo "1. Browser will open to submit page"
echo "2. Title and content will be in clipboard"
echo "3. Paste content (Ctrl+V)"
echo "4. Review and click Post"
echo ""

# Copy content to clipboard
echo "$CONTENT" | xclip -selection clipboard 2>/dev/null || echo "$CONTENT" | pbcopy 2>/dev/null || echo "⚠️  Clipboard not available"

# Open browser
xdg-open "https://www.reddit.com/r/$SUBREDDIT/submit?type=SELF&title=$(echo "$TITLE" | jq -sRr @uri)" &

echo "✅ Browser opened. Content in clipboard. Paste and post when ready!"
