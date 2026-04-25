#!/bin/bash
# deploy.sh -- install llama-egress-proxy on the GPU server
# Usage: bash deploy.sh
set -euo pipefail

GPU_HOST="${GPU_HOST:-peter@10.0.0.30}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519_alexchen}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Deploying llama-egress-proxy to $GPU_HOST"

# Copy proxy files
ssh -i "$SSH_KEY" "$GPU_HOST" "mkdir -p ~/llama-egress-proxy"
scp -i "$SSH_KEY" \
    "$SCRIPT_DIR/proxy.py" \
    "$SCRIPT_DIR/requirements.txt" \
    "$SCRIPT_DIR/test_sanitize.py" \
    "$GPU_HOST:~/llama-egress-proxy/"

# Install Python deps
ssh -i "$SSH_KEY" "$GPU_HOST" "pip3 install --user -r ~/llama-egress-proxy/requirements.txt -q"

# Run unit tests on server
echo "==> Running sanitise tests on server..."
ssh -i "$SSH_KEY" "$GPU_HOST" "python3 ~/llama-egress-proxy/test_sanitize.py"

# Install + enable systemd unit
scp -i "$SSH_KEY" \
    "$SCRIPT_DIR/llama-egress-proxy.service" \
    "$GPU_HOST:~/.config/systemd/user/"

ssh -i "$SSH_KEY" "$GPU_HOST" "systemctl --user daemon-reload && systemctl --user enable llama-egress-proxy.service"

# Start / restart
ssh -i "$SSH_KEY" "$GPU_HOST" \
    "systemctl --user is-active llama-egress-proxy.service && \
     systemctl --user restart llama-egress-proxy.service || \
     systemctl --user start llama-egress-proxy.service"

sleep 3

echo "==> Status:"
ssh -i "$SSH_KEY" "$GPU_HOST" "systemctl --user status llama-egress-proxy.service --no-pager"

echo ""
echo "==> Health check:"
ssh -i "$SSH_KEY" "$GPU_HOST" "curl -s http://127.0.0.1:8082/health"

echo ""
echo "==> Done."
echo "    Update OpenClaw provider: openclaw config patch models.providers.gpu-server-35b.baseUrl http://10.0.0.30:8082"
