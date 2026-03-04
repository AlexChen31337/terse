#!/bin/bash
# Wrapper for claude CLI with OAuth token
# Usage: bash scripts/claude_code.sh -p "your prompt" [--allowedTools ...]
export CLAUDE_CODE_OAUTH_TOKEN="${CLAUDE_CODE_OAUTH_TOKEN:-$(bash /home/bowen/.openclaw/workspace/memory/decrypt.sh claude-oauth-token 2>/dev/null)}"
exec ~/.local/bin/claude "$@"
