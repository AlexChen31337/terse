#!/bin/bash
# Complete automated migration with prerequisites
# Target: bowen@10.0.0.14

set -e

TARGET_USER="bowen"
TARGET_HOST="10.0.0.14"
TARGET_PASSWORD="bowen@2025"

echo "=========================================="
echo "OpenClaw Complete Migration v2"
echo "=========================================="
echo "Target: ${TARGET_USER}@${TARGET_HOST}"
echo ""

# Step 1: Create backup archives
echo "[1/8] Creating backup archives..."
cd ~

echo "  - Backing up clawd workspace..."
tar -czf /tmp/clawd-backup.tar.gz clawd/ 2>/dev/null || true

echo "  - Backing up OpenClaw config..."
tar -czf /tmp/clawdbot-config.tar.gz \
  --exclude='.clawdbot/agents/*/sessions/*.jsonl' \
  --exclude='.clawdbot/agents/*/sessions/*.deleted.*' \
  .clawdbot/ 2>/dev/null || true

if [ -d ~/.clawdbot/skills ]; then
  echo "  - Backing up skills..."
  tar -czf /tmp/clawdbot-skills.tar.gz .clawdbot/skills/ 2>/dev/null || true
fi

echo "  ✓ Backups created"
echo ""

# Step 2: Test connection
echo "[2/8] Testing connection..."
sshpass -p "${TARGET_PASSWORD}" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_HOST} "echo 'Connected'" || {
  echo "  ✗ Connection failed"
  exit 1
}
echo "  ✓ Connection successful"
echo ""

# Step 3: Install prerequisites (curl, wget, etc.)
echo "[3/8] Installing prerequisites on target..."
sshpass -p "${TARGET_PASSWORD}" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_HOST} << 'ENDSSH'
  echo "  - Installing curl, wget, build tools..."
  echo "${TARGET_PASSWORD}" | sudo -S apt-get update -qq
  echo "${TARGET_PASSWORD}" | sudo -S apt-get install -y -qq curl wget build-essential python3-pip unzip
  echo "  ✓ Prerequisites installed"
ENDSSH
echo ""

# Step 4: Transfer files
echo "[4/8] Transferring files..."
echo "  - Workspace..."
sshpass -p "${TARGET_PASSWORD}" scp -o StrictHostKeyChecking=no \
  /tmp/clawd-backup.tar.gz ${TARGET_USER}@${TARGET_HOST}:~/

echo "  - Config..."
sshpass -p "${TARGET_PASSWORD}" scp -o StrictHostKeyChecking=no \
  /tmp/clawdbot-config.tar.gz ${TARGET_USER}@${TARGET_HOST}:~/

if [ -f /tmp/clawdbot-skills.tar.gz ]; then
  echo "  - Skills..."
  sshpass -p "${TARGET_PASSWORD}" scp -o StrictHostKeyChecking=no \
    /tmp/clawdbot-skills.tar.gz ${TARGET_USER}@${TARGET_HOST}:~/
fi

echo "  ✓ Files transferred"
echo ""

# Step 5: Extract files
echo "[5/8] Extracting files on target..."
sshpass -p "${TARGET_PASSWORD}" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_HOST} << 'ENDSSH'
  tar -xzf ~/clawd-backup.tar.gz -C ~/ 2>/dev/null
  tar -xzf ~/clawdbot-config.tar.gz -C ~/ 2>/dev/null
  [ -f ~/clawdbot-skills.tar.gz ] && tar -xzf ~/clawdbot-skills.tar.gz -C ~/ 2>/dev/null
  rm -f ~/*.tar.gz
  echo "  ✓ Files extracted"
ENDSSH
echo ""

# Step 6: Install fnm and Node.js
echo "[6/8] Installing fnm and Node.js..."
sshpass -p "${TARGET_PASSWORD}" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_HOST} << 'ENDSSH'
  echo "  - Installing fnm..."
  curl -fsSL https://fnm.vercel.app/install | bash -s -- --skip-shell
  
  # Add fnm to PATH for current session
  export PATH="$HOME/.local/share/fnm:$PATH"
  eval "$($HOME/.local/share/fnm/fnm env)"
  
  # Add fnm to shell configs
  for rc in ~/.bashrc ~/.zshrc ~/.profile; do
    if [ -f "$rc" ] && ! grep -q "fnm env" "$rc"; then
      echo '' >> "$rc"
      echo '# fnm' >> "$rc"
      echo 'export PATH="$HOME/.local/share/fnm:$PATH"' >> "$rc"
      echo 'eval "$(fnm env --use-on-cd)"' >> "$rc"
    fi
  done
  
  echo "  - Installing Node.js v20 LTS..."
  $HOME/.local/share/fnm/fnm install 20
  $HOME/.local/share/fnm/fnm use 20
  $HOME/.local/share/fnm/fnm default 20
  
  # Verify
  $HOME/.local/share/fnm/fnm current
  
  echo "  ✓ fnm and Node.js installed"
ENDSSH
echo ""

# Step 7: Install OpenClaw and dependencies
echo "[7/8] Installing OpenClaw..."
sshpass -p "${TARGET_PASSWORD}" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_HOST} << 'ENDSSH'
  export PATH="$HOME/.local/share/fnm:$PATH"
  eval "$($HOME/.local/share/fnm/fnm env)"
  
  echo "  - Installing Python packages..."
  pip3 install --user requests python-dotenv 2>&1 | grep -v "already satisfied" || true
  
  echo "  - Installing OpenClaw globally..."
  npm install -g openclaw
  
  echo "  - Verifying installation..."
  openclaw --version
  
  echo "  ✓ OpenClaw installed"
ENDSSH
echo ""

# Step 8: Start OpenClaw
echo "[8/8] Starting OpenClaw gateway..."
sshpass -p "${TARGET_PASSWORD}" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_HOST} << 'ENDSSH'
  export PATH="$HOME/.local/share/fnm:$PATH"
  eval "$($HOME/.local/share/fnm/fnm env)"
  
  cd ~/clawd
  
  echo "  - Starting gateway..."
  openclaw gateway start
  
  sleep 3
  
  echo "  - Checking status..."
  openclaw status
  
  echo "  ✓ OpenClaw is running"
ENDSSH
echo ""

# Cleanup
rm -f /tmp/clawd-backup.tar.gz /tmp/clawdbot-config.tar.gz /tmp/clawdbot-skills.tar.gz

echo ""
echo "=========================================="
echo "✅ MIGRATION COMPLETE!"
echo "=========================================="
echo ""
echo "OpenClaw is now running on ${TARGET_HOST}"
echo ""
echo "Connect to the new host:"
echo "  ssh ${TARGET_USER}@${TARGET_HOST}"
echo ""
echo "All your data has been migrated:"
echo "  ✓ ~/clawd/ (workspace, strategies, memory)"
echo "  ✓ ~/.clawdbot/ (config, credentials, skills)"
echo "  ✓ Node.js v20 (via fnm)"
echo "  ✓ OpenClaw gateway (running)"
echo ""
echo "=========================================="
