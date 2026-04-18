#!/bin/bash
# Migration script to move OpenClaw workspace to new host
# Target: bowen@10.0.0.14

set -e

TARGET_USER="bowen"
TARGET_HOST="10.0.0.14"
TARGET_PASSWORD="bowen@2025"

echo "=========================================="
echo "OpenClaw Migration to New Host"
echo "=========================================="
echo "Target: ${TARGET_USER}@${TARGET_HOST}"
echo ""

# Step 1: Create backup archives
echo "[1/5] Creating backup archives..."
cd ~

# Workspace backup
echo "  - Backing up clawd workspace..."
tar -czf /tmp/clawd-backup.tar.gz clawd/ 2>/dev/null || echo "    Warning: Some files may have been skipped"

# Config backup (excluding sessions to reduce size)
echo "  - Backing up OpenClaw config..."
tar -czf /tmp/clawdbot-config.tar.gz \
  --exclude='.clawdbot/agents/*/sessions/*.jsonl' \
  --exclude='.clawdbot/agents/*/sessions/*.deleted.*' \
  .clawdbot/ 2>/dev/null || echo "    Warning: Some files may have been skipped"

# Skills backup
echo "  - Backing up skills..."
if [ -d ~/.clawdbot/skills ]; then
  tar -czf /tmp/clawdbot-skills.tar.gz .clawdbot/skills/ 2>/dev/null
fi

echo "  ✓ Backups created"
echo ""

# Step 2: Test SSH connection
echo "[2/5] Testing connection to target host..."
sshpass -p "${TARGET_PASSWORD}" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_HOST} "echo 'Connection successful'" || {
  echo "  ✗ Failed to connect. Please check:"
  echo "    - Host is reachable: ping 10.0.0.14"
  echo "    - SSH is running on target"
  echo "    - Username/password are correct"
  echo "    - Install sshpass if missing: sudo apt install sshpass"
  exit 1
}
echo "  ✓ Connection established"
echo ""

# Step 3: Transfer files
echo "[3/5] Transferring files to target host..."
echo "  - Transferring clawd workspace (~$(du -sh /tmp/clawd-backup.tar.gz | cut -f1))..."
sshpass -p "${TARGET_PASSWORD}" scp -o StrictHostKeyChecking=no \
  /tmp/clawd-backup.tar.gz ${TARGET_USER}@${TARGET_HOST}:~/

echo "  - Transferring OpenClaw config (~$(du -sh /tmp/clawdbot-config.tar.gz | cut -f1))..."
sshpass -p "${TARGET_PASSWORD}" scp -o StrictHostKeyChecking=no \
  /tmp/clawdbot-config.tar.gz ${TARGET_USER}@${TARGET_HOST}:~/

if [ -f /tmp/clawdbot-skills.tar.gz ]; then
  echo "  - Transferring skills (~$(du -sh /tmp/clawdbot-skills.tar.gz | cut -f1))..."
  sshpass -p "${TARGET_PASSWORD}" scp -o StrictHostKeyChecking=no \
    /tmp/clawdbot-skills.tar.gz ${TARGET_USER}@${TARGET_HOST}:~/
fi

echo "  ✓ Files transferred"
echo ""

# Step 4: Extract on target
echo "[4/5] Extracting files on target host..."
sshpass -p "${TARGET_PASSWORD}" ssh -o StrictHostKeyChecking=no ${TARGET_USER}@${TARGET_HOST} << 'ENDSSH'
  echo "  - Extracting clawd workspace..."
  tar -xzf ~/clawd-backup.tar.gz -C ~/
  
  echo "  - Extracting OpenClaw config..."
  tar -xzf ~/clawdbot-config.tar.gz -C ~/
  
  if [ -f ~/clawdbot-skills.tar.gz ]; then
    echo "  - Extracting skills..."
    tar -xzf ~/clawdbot-skills.tar.gz -C ~/
  fi
  
  echo "  - Cleaning up archives..."
  rm -f ~/clawd-backup.tar.gz ~/clawdbot-config.tar.gz ~/clawdbot-skills.tar.gz
  
  echo "  ✓ Files extracted"
ENDSSH
echo ""

# Step 5: Setup instructions
echo "[5/5] Migration complete!"
echo ""
echo "=========================================="
echo "Next Steps on Target Host (${TARGET_HOST})"
echo "=========================================="
echo ""
echo "1. SSH into the new host:"
echo "   ssh ${TARGET_USER}@${TARGET_HOST}"
echo ""
echo "2. Install dependencies (if not already installed):"
echo "   # Node.js & npm"
echo "   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
echo "   sudo apt-get install -y nodejs"
echo "   "
echo "   # Python packages"
echo "   pip3 install requests python-dotenv"
echo "   "
echo "   # OpenClaw"
echo "   npm install -g openclaw"
echo ""
echo "3. Start OpenClaw gateway:"
echo "   cd ~/clawd"
echo "   openclaw gateway start"
echo ""
echo "4. Verify migration:"
echo "   openclaw status"
echo "   ls -la ~/clawd/"
echo ""
echo "=========================================="
echo "Files transferred:"
echo "  ✓ ~/clawd/ (workspace, strategies, memory)"
echo "  ✓ ~/.clawdbot/ (config, agents, skills)"
echo "=========================================="
echo ""

# Cleanup local backups
echo "Cleaning up local backup files..."
rm -f /tmp/clawd-backup.tar.gz /tmp/clawdbot-config.tar.gz /tmp/clawdbot-skills.tar.gz

echo "✓ Migration complete!"
