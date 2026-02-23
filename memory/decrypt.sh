#!/bin/bash
# Decrypt a sensitive file and output to stdout
# Usage: ./decrypt.sh <filename> (e.g., ./decrypt.sh moltbook-credentials.json)
#
# Supports two backends:
#   1. OpenSSL AES-256 (primary): memory/encrypted/<filename>.enc + encrypted/.key
#   2. GPG (legacy): memory/<filename>.gpg
#
# Only ONE backend runs per invocation. Never concatenates outputs.

set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
KEY_FILE="$SCRIPT_DIR/encrypted/.key"
ENC_FILE="$SCRIPT_DIR/encrypted/$1.enc"
GPG_FILE="$HOME/clawd/memory/$1.gpg"

# Try OpenSSL backend first (primary)
if [ -f "$ENC_FILE" ]; then
  if [ ! -f "$KEY_FILE" ]; then
    echo "ERROR: Key file not found: $KEY_FILE" >&2
    exit 1
  fi
  openssl enc -aes-256-cbc -d -salt -pbkdf2 -in "$ENC_FILE" -pass "pass:$(cat "$KEY_FILE")"
  exit $?
fi

# Fall back to GPG backend (legacy)
if [ -f "$GPG_FILE" ]; then
  if ! gpg --decrypt --batch --quiet --output - "$GPG_FILE" 2>/dev/null; then
    echo "ERROR: GPG decryption failed for $GPG_FILE" >&2
    exit 1
  fi
  exit 0
fi

# Neither backend has this file
echo "ERROR: No encrypted file found for '$1'" >&2
echo "  Checked: $ENC_FILE" >&2
echo "  Checked: $GPG_FILE" >&2
exit 1
