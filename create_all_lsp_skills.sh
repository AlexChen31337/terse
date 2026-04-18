#!/bin/bash
set -e

SKILL_CREATOR="/home/bowen/.local/share/fnm/node-versions/v22.22.0/installation/lib/node_modules/openclaw/skills/skill-creator/scripts/package_skill.py"
SKILLS_DIR="/home/bowen/clawd/skills"
INSTALL_DIR="/home/bowen/.openclaw/skills"

echo "📦 Packaging and installing LSP skills..."

for skill in rust-analyzer-lsp clangd-lsp; do
  echo "  → $skill"
  python3 "$SKILL_CREATOR" "$SKILLS_DIR/$skill" > /dev/null
  cp -r "$SKILLS_DIR/$skill" "$INSTALL_DIR/"
done

echo "✅ All LSP skills packaged and installed!"
echo ""
echo "Verifying..."
openclaw skills list | grep -E "lsp" | grep "ready"
