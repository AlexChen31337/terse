#!/bin/bash
# Complete automated migration to new host
# Target: bowen@10.0.0.14

set -e

TARGET_USER="bowen"
TARGET_HOST="10.0.0.14"
TARGET_PASSWORD="bowen@2025"

echo "=========================================="
echo "OpenClaw Complete Migration"
echo "=========================================="
echo "Target: ${TARGET_USER}@${TARGET_HOST}"
echo ""

# Step 1: Create backup archives
echo "[1/7] Creating backup archives..."
cd ~

echo "  - Backing up clawd workspace..."
tar -czf /tmp/clawd-backup.tar.gz clawd/ 2>/dev/null || echo "    Warning: Some files skipped"

echo "  - Backing up OpenClaw config..."
tar -czf /tmp/clawdbot-config.tar.gz \
  --exclude='.clawdbot/agents/*/sessions/*.jsonl' \
  --exclude='.clawdbot/agents/*/sessions/*.deleted.*' \
  .clawdbot/ 2>/dev/null || echo "    Warning: Some files skipped"

if [ -d ~/.clawdbot/skills ]; then
  echo "  - Backing up skills..."
  tar -czf /tmp/clawdbot-skills.tar.gz .clawdbot/skills/ 2>/dev/null
fi

echo "  ✓ Backups created"
echo ""

# Step 2: Test connection
echo "[2/7] Testing connection..."
sshpass -p "${TARGET_PASSWORD}" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_HOST} "echo 'Connected'" || {
  echo "  ✗ Connection failed"
  exit 1
}
echo "  ✓ Connection successful"
echo ""

# Step 3: Transfer files
echo "[3/7] Transferring files..."
echo "  - Workspace (~$(du -sh /tmp/clawd-backup.tar.gz 2>/dev/null | cut -f1))..."
sshpass -p "${TARGET_PASSWORD}" scp -o StrictHostKeyChecking=no \
  /tmp/clawd-backup.tar.gz ${TARGET_USER}@${TARGET_HOST}:~/

echo "  - Config (~$(du -sh /tmp/clawdbot-config.tar.gz 2>/dev/null | cut -f1))..."
sshpass -p "${TARGET_PASSWORD}" scp -o StrictHostKeyChecking=no \
  /tmp/clawdbot-config.tar.gz ${TARGET_USER}@${TARGET_HOST}:~/

if [ -f /tmp/clawdbot-skills.tar.gz ]; then
  echo "  - Skills..."
  sshpass -p "${TARGET_PASSWORD}" scp -o StrictHostKeyChecking=no \
    /tmp/clawdbot-skills.tar.gz ${TARGET_USER}@${TARGET_HOST}:~/
fi

echo "  ✓ Files transferred"
echo ""

# Step 4: Extract files
echo "[4/7] Extracting files on target..."
sshpass -p "${TARGET_PASSWORD}" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_HOST} << 'ENDSSH'
  tar -xzf ~/clawd-backup.tar.gz -C ~/ 2>/dev/null
  tar -xzf ~/clawdbot-config.tar.gz -C ~/ 2>/dev/null
  [ -f ~/clawdbot-skills.tar.gz ] && tar -xzf ~/clawdbot-skills.tar.gz -C ~/ 2>/dev/null
  rm -f ~/*.tar.gz
  echo "  ✓ Files extracted"
ENDSSH
echo ""

# Step 5: Install fnm and Node.js
echo "[5/7] Installing fnm and Node.js on target..."
sshpass -p "${TARGET_PASSWORD}" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_HOST} << 'ENDSSH'
  echo "  - Installing fnm..."
  
  # Install fnm if not already installed
  if ! command -v fnm &> /dev/null; then
    curl -fsSL https://fnm.vercel.app/install | bash -s -- --skip-shell
    export PATH="$HOME/.local/share/fnm:$PATH"
    eval "$(fnm env --use-on-cd)"
  else
    echo "    fnm already installed"
  fi
  
  # Add fnm to shell configs if not already there
  for rc in ~/.bashrc ~/.zshrc; do
    if [ -f "$rc" ] && ! grep -q "fnm env" "$rc"; then
      echo '' >> "$rc"
      echo '# fnm' >> "$rc"
      echo 'export PATH="$HOME/.local/share/fnm:$PATH"' >> "$rc"
      echo 'eval "$(fnm env --use-on-cd)"' >> "$rc"
    fi
  done
  
  # Source fnm
  export PATH="$HOME/.local/share/fnm:$PATH"
  eval "$(fnm env --use-on-cd)"
  
  echo "  - Installing Node.js v20 LTS..."
  fnm install 20
  fnm use 20
  fnm default 20
  
  # Verify installation
  node --version
  npm --version
  
  echo "  ✓ Node.js installed"
ENDSSH
echo ""

# Step 6: Install OpenClaw and dependencies
echo "[6/7] Installing OpenClaw and dependencies..."
sshpass -p "${TARGET_PASSWORD}" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_HOST} << 'ENDSSH'
  # Source fnm
  export PATH="$HOME/.local/share/fnm:$PATH"
  eval "$(fnm env --use-on-cd)"
  
  echo "  - Installing Python packages..."
  pip3 install --user requests python-dotenv 2>/dev/null || echo "    (may already be installed)"
  
  echo "  - Installing OpenClaw globally..."
  npm install -g openclaw
  
  echo "  - Verifying installation..."
  which openclaw
  openclaw --version
  
  echo "  ✓ Dependencies installed"
ENDSSH
echo ""

# Step 7: Start OpenClaw on new host
echo "[7/7] Starting OpenClaw on target host..."
sshpass -p "${TARGET_PASSWORD}" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_HOST} << 'ENDSSH'
  # Source fnm
  export PATH="$HOME/.local/share/fnm:$PATH"
  eval "$(fnm env --use-on-cd)"
  
  cd ~/clawd
  
  echo "  - Checking OpenClaw status..."
  openclaw gateway status || echo "    Gateway not running (expected)"
  
  echo "  - Starting OpenClaw gateway..."
  openclaw gateway start
  
  sleep 3
  
  echo "  - Verifying gateway started..."
  openclaw gateway status
  
  echo "  ✓ OpenClaw is running"
ENDSSH
echo ""

# Cleanup
echo "Cleaning up local backup files..."
rm -f /tmp/clawd-backup.tar.gz /tmp/clawdbot-config.tar.gz /tmp/clawdbot-skills.tar.gz

echo ""
echo "=========================================="
echo "✅ Migration Complete!"
echo "=========================================="
echo ""
echo "OpenClaw is now running on ${TARGET_HOST}"
echo ""
echo "To access the new instance:"
echo "  ssh ${TARGET_USER}@${TARGET_HOST}"
echo "  cd ~/clawd"
echo "  openclaw status"
echo ""
echo "Migrated components:"
echo "  ✓ Workspace (strategies, memory, logs)"
echo "  ✓ OpenClaw config & credentials"
echo "  ✓ Skills (WEEX trading, etc.)"
echo "  ✓ fnm + Node.js v20"
echo "  ✓ OpenClaw gateway (running)"
echo ""
echo "=========================================="
