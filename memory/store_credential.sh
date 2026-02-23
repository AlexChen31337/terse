#!/bin/bash
# store_credential.sh — Safe credential storage with validation
#
# Usage:
#   store_credential.sh <name> <value> [--type hex|str|json]
#
# Validates the value before writing. Refuses to store:
#   - Empty values
#   - Values containing ERROR, DECRYPT_ERROR, null, undefined
#   - Hex keys shorter than 60 chars (too short to be a real key)
#
# Stores to: memory/encrypted/<name>.enc (AES-256)

set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
NAME="${1:-}"
VALUE="${2:-}"
TYPE="${3:-str}"

if [ -z "$NAME" ] || [ -z "$VALUE" ]; then
  echo "Usage: store_credential.sh <name> <value> [--type hex|str|json]" >&2
  exit 1
fi

# ── Validation ──────────────────────────────────────────────────────────────

# Reject known error strings
for bad in "DECRYPT_ERROR" "ERROR" "null" "undefined" "None" "FAILED"; do
  if echo "$VALUE" | grep -qi "$bad"; then
    echo "❌ REFUSED: Value contains error string '$bad' — refusing to store corrupted credential." >&2
    echo "   Value was: ${VALUE:0:30}..." >&2
    exit 1
  fi
done

# Reject empty/whitespace
if [ -z "$(echo "$VALUE" | tr -d '[:space:]')" ]; then
  echo "❌ REFUSED: Value is empty." >&2
  exit 1
fi

# Type-specific validation
if [ "$TYPE" = "hex" ]; then
  # Strip 0x prefix for length check
  HEX="${VALUE#0x}"
  if [ "${#HEX}" -lt 60 ]; then
    echo "❌ REFUSED: Hex key too short (${#HEX} chars, expected ≥60)." >&2
    exit 1
  fi
  if ! echo "$HEX" | grep -qE '^[0-9a-fA-F]+$'; then
    echo "❌ REFUSED: Value is not valid hex." >&2
    exit 1
  fi
fi

if [ "$TYPE" = "json" ]; then
  if ! echo "$VALUE" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    echo "❌ REFUSED: Value is not valid JSON." >&2
    exit 1
  fi
fi

# ── Encrypt and store ────────────────────────────────────────────────────────

KEY_FILE="$SCRIPT_DIR/encrypted/.key"
ENC_FILE="$SCRIPT_DIR/encrypted/${NAME}.enc"

if [ ! -f "$KEY_FILE" ]; then
  echo "❌ Key file not found: $KEY_FILE" >&2
  exit 1
fi

mkdir -p "$SCRIPT_DIR/encrypted"
echo -n "$VALUE" | openssl enc -aes-256-cbc -salt -pbkdf2 -out "$ENC_FILE" -pass "pass:$(cat "$KEY_FILE")"

echo "✅ Stored '$NAME' securely (${#VALUE} chars, type=$TYPE)"
echo "   File: $ENC_FILE"
