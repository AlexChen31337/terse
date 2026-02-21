#!/bin/bash
# Decrypt a sensitive file and output to stdout
# Usage: ./decrypt.sh <filename> (e.g., ./decrypt.sh moltbook-credentials.json)
KEY_FILE="$(dirname "$0")/encrypted/.key"
ENC_FILE="$(dirname "$0")/encrypted/$1.enc"

if [ ! -f "$ENC_FILE" ]; then
  echo "ERROR: Encrypted file not found: $ENC_FILE" >&2
  exit 1
fi

openssl enc -aes-256-cbc -d -salt -pbkdf2 -in "$ENC_FILE" -pass "pass:$(cat "$KEY_FILE")"
gpg --decrypt --batch --quiet --output - "$HOME/clawd/memory/$1.gpg" 2>/dev/null || echo "DECRYPT_ERROR"
