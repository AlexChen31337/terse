#!/bin/bash

# Get Turso credentials
echo "Decrypting Turso credentials..."
TURSO_CREDENTIALS=$(cat memory/encrypted/turso-credentials.json.enc)

# Extract URL and token using Python
TURSO_URL=$(echo "$TURSO_CREDENTIALS" | python3 -c "import json,sys;print(json.load(sys.stdin)['database_url'])")
TURSO_TOKEN=$(echo "$TURSO_CREDENTIALS" | python3 -c "import json,sys;print(json.load(sys.stdin)['auth_token'])")

echo "Turso URL: $TURSO_URL"
echo "Turso Token: ${TURSO_TOKEN:0:20}..."  # Show first 20 chars for verification

# Export to environment variables
export TURSO_URL="$TURSO_URL"
export TURSO_TOKEN="$TURSO_TOKEN"